import json
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.database import get_db
from src.models.entities import ServiceCatalog
from src.middleware.tenant import get_tenant_context, TenantContext

router = APIRouter(prefix="/api/v1/catalog", tags=["Microservices Catalog"])

class ServiceRegisterRequest(BaseModel):
    service_key: str
    name: str
    endpoint_url: str
    auth_type: str = "GCP_IAM"
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    is_private_to_company: bool = False

@router.get("")
def list_available_services(
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Lista todos los microservicios disponibles (globales + privados de la empresa)"""
    services = db.query(ServiceCatalog).filter(
        or_(
            ServiceCatalog.company_id == None,
            ServiceCatalog.company_id == tenant.company_id
        ),
        ServiceCatalog.is_active == True
    ).all()

    return [
        {
            "id": s.id,
            "service_key": s.service_key,
            "name": s.name,
            "endpoint_url": s.endpoint_url,
            "auth_type": s.auth_type,
            "is_global": s.company_id is None,
            "input_schema": json.loads(s.input_schema or "{}"),
            "output_schema": json.loads(s.output_schema or "{}")
        } for s in services
    ]

@router.post("")
def register_service(
    request: ServiceRegisterRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Registra un nuevo microservicio en la fábrica/catálogo"""
    company_id = tenant.company_id if request.is_private_to_company else None

    existing = db.query(ServiceCatalog).filter(ServiceCatalog.service_key == request.service_key).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe un microservicio con la clave '{request.service_key}'.")

    service = ServiceCatalog(
        company_id=company_id,
        service_key=request.service_key,
        name=request.name,
        endpoint_url=request.endpoint_url,
        auth_type=request.auth_type,
        input_schema=json.dumps(request.input_schema),
        output_schema=json.dumps(request.output_schema)
    )
    db.add(service)
    db.commit()
    db.refresh(service)

    return {"id": service.id, "service_key": service.service_key, "message": "Microservicio registrado exitosamente."}
