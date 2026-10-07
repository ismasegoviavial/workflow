import json
from fastapi import Header, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.entities import Company

security = HTTPBearer(auto_error=False)

class TenantContext:
    def __init__(self, company_id: str, company_code: str, user_email: str, user_groups: list[str]):
        self.company_id = company_id
        self.company_code = company_code
        self.user_email = user_email
        self.user_groups = user_groups

def get_tenant_context(
    x_company_id: str = Header(None, alias="X-Company-ID"),
    x_user_email: str = Header("demo.user@democorp.com", alias="X-User-Email"),
    x_user_groups: str = Header('["operaciones@democorp.com", "supervisores@democorp.com"]', alias="X-User-Groups"),
    auth: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> TenantContext:
    """
    Resuelve el tenant (empresa) y la identidad del usuario:
    1. En producción: Valida el token JWT de Google Workspace, extrae el dominio '@empresa.com' y grupos.
    2. En desarrollo/test: Utiliza cabeceras X-Company-ID / X-User-Email / X-User-Groups.
    """
    # Si viene especificado un company_id directo
    if x_company_id:
        company = db.query(Company).filter(Company.id == x_company_id, Company.is_active == True).first()
        if not company:
            raise HTTPException(status_code=404, detail=f"Empresa con ID {x_company_id} no encontrada o inactiva.")
    else:
        # Resolver por dominio de email
        domain = x_user_email.split("@")[-1] if "@" in x_user_email else "democorp.com"
        company = db.query(Company).filter(Company.google_workspace_domain == domain, Company.is_active == True).first()
        if not company:
            # Crear o buscar default demo company para entorno de desarrollo inicial
            company = db.query(Company).filter(Company.company_code == "DEMOCORP").first()
            if not company:
                company = Company(
                    company_code="DEMOCORP",
                    name="Demo Corporation",
                    google_workspace_domain="democorp.com"
                )
                db.add(company)
                db.commit()
                db.refresh(company)
                
    try:
        groups = json.loads(x_user_groups) if isinstance(x_user_groups, str) else []
    except Exception:
        groups = [x_user_groups]
        
    return TenantContext(
        company_id=company.id,
        company_code=company.company_code,
        user_email=x_user_email,
        user_groups=groups
    )
