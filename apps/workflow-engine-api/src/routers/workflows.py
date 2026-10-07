import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.entities import Workflow, Stage, Substage, StageTransition, SubstageTransition
from src.middleware.tenant import get_tenant_context, TenantContext

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows & Config"])

# Schemas
class SubstageCreate(BaseModel):
    substage_key: str
    title: str
    is_initial: bool = False
    service_id: Optional[str] = None
    editor_workspace_group: str
    reviewer_workspace_group: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    input_mapping: Optional[Dict[str, Any]] = None

class StageCreate(BaseModel):
    stage_key: str
    title: str
    is_initial: bool = False
    is_final: bool = False
    order_index: int = 0
    substages: List[SubstageCreate] = []

class WorkflowCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    stages: List[StageCreate] = []

class CloneSubstageRequest(BaseModel):
    source_substage_id: str
    target_stage_id: str
    new_substage_key: str
    new_title: str

@router.get("")
def list_workflows(
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Lista todos los workflows de la empresa del usuario autenticado"""
    workflows = db.query(Workflow).filter(
        Workflow.company_id == tenant.company_id,
        Workflow.is_active == True
    ).all()
    return workflows

@router.get("/{workflow_id}")
def get_workflow_details(
    workflow_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Retorna la estructura completa del workflow con sus etapas y subetapas"""
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.company_id == tenant.company_id
    ).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado.")

    stages = db.query(Stage).filter(
        Stage.workflow_id == wf.id,
        Stage.company_id == tenant.company_id
    ).order_by(Stage.order_index).all()

    stages_data = []
    for s in stages:
        substages = db.query(Substage).filter(
            Substage.stage_id == s.id,
            Substage.company_id == tenant.company_id
        ).all()
        
        stages_data.append({
            "id": s.id,
            "stage_key": s.stage_key,
            "title": s.title,
            "is_initial": s.is_initial,
            "is_final": s.is_final,
            "order_index": s.order_index,
            "substages": [
                {
                    "id": sub.id,
                    "substage_key": sub.substage_key,
                    "title": sub.title,
                    "is_initial": sub.is_initial,
                    "service_id": sub.service_id,
                    "editor_workspace_group": sub.editor_workspace_group,
                    "reviewer_workspace_group": sub.reviewer_workspace_group,
                    "input_schema": json.loads(sub.input_schema or "{}"),
                    "output_schema": json.loads(sub.output_schema or "{}"),
                    "input_mapping": json.loads(sub.input_mapping or "{}"),
                    "is_clonable": sub.is_clonable
                } for sub in substages
            ]
        })

    # Transiciones
    stage_trans = db.query(StageTransition).filter(
        StageTransition.workflow_id == wf.id,
        StageTransition.company_id == tenant.company_id
    ).all()

    return {
        "id": wf.id,
        "code": wf.code,
        "name": wf.name,
        "description": wf.description,
        "version": wf.version,
        "stages": stages_data,
        "transitions": [
            {
                "from_stage_id": t.from_stage_id,
                "to_stage_id": t.to_stage_id,
                "condition_expression": t.condition_expression
            } for t in stage_trans
        ]
    }

@router.post("")
def create_workflow(
    payload: WorkflowCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Crea un nuevo workflow completo con etapas y subetapas para la empresa"""
    existing = db.query(Workflow).filter(
        Workflow.company_id == tenant.company_id,
        Workflow.code == payload.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe un workflow con código '{payload.code}'.")

    wf = Workflow(
        company_id=tenant.company_id,
        code=payload.code,
        name=payload.name,
        description=payload.description
    )
    db.add(wf)
    db.flush()

    prev_stage_id = None
    for stage_data in payload.stages:
        stage = Stage(
            company_id=tenant.company_id,
            workflow_id=wf.id,
            stage_key=stage_data.stage_key,
            title=stage_data.title,
            is_initial=stage_data.is_initial,
            is_final=stage_data.is_final,
            order_index=stage_data.order_index
        )
        db.add(stage)
        db.flush()

        # Conectar etapa con la previa por defecto
        if prev_stage_id:
            db.add(StageTransition(
                company_id=tenant.company_id,
                workflow_id=wf.id,
                from_stage_id=prev_stage_id,
                to_stage_id=stage.id
            ))
        prev_stage_id = stage.id

        prev_sub_id = None
        for sub_data in stage_data.substages:
            sub = Substage(
                company_id=tenant.company_id,
                stage_id=stage.id,
                substage_key=sub_data.substage_key,
                title=sub_data.title,
                is_initial=sub_data.is_initial,
                service_id=sub_data.service_id,
                editor_workspace_group=sub_data.editor_workspace_group,
                reviewer_workspace_group=sub_data.reviewer_workspace_group,
                input_schema=json.dumps(sub_data.input_schema),
                output_schema=json.dumps(sub_data.output_schema),
                input_mapping=json.dumps(sub_data.input_mapping or {})
            )
            db.add(sub)
            db.flush()

            if prev_sub_id:
                db.add(SubstageTransition(
                    company_id=tenant.company_id,
                    stage_id=stage.id,
                    from_substage_id=prev_sub_id,
                    to_substage_id=sub.id
                ))
            prev_sub_id = sub.id

    db.commit()
    db.refresh(wf)
    return {"id": wf.id, "code": wf.code, "message": "Workflow creado exitosamente."}

@router.post("/substages/clone")
def clone_substage(
    request: CloneSubstageRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Clona una subetapa existente para reutilizar sus campos, esquemas y roles
    en otra etapa del workflow o en otro workflow de la misma empresa.
    """
    source_sub = db.query(Substage).filter(
        Substage.id == request.source_substage_id,
        Substage.company_id == tenant.company_id
    ).first()
    if not source_sub:
        raise HTTPException(status_code=404, detail="Subetapa origen no encontrada.")

    target_stage = db.query(Stage).filter(
        Stage.id == request.target_stage_id,
        Stage.company_id == tenant.company_id
    ).first()
    if not target_stage:
        raise HTTPException(status_code=404, detail="Etapa destino no encontrada.")

    cloned_substage = Substage(
        company_id=tenant.company_id,
        stage_id=target_stage.id,
        substage_key=request.new_substage_key,
        title=request.new_title,
        is_initial=False,
        service_id=source_sub.service_id,
        editor_workspace_group=source_sub.editor_workspace_group,
        reviewer_workspace_group=source_sub.reviewer_workspace_group,
        input_schema=source_sub.input_schema,
        output_schema=source_sub.output_schema,
        input_mapping=source_sub.input_mapping,
        is_clonable=True,
        template_origin_id=source_sub.id
    )
    db.add(cloned_substage)
    db.commit()
    db.refresh(cloned_substage)

    return {
        "id": cloned_substage.id,
        "substage_key": cloned_substage.substage_key,
        "title": cloned_substage.title,
        "message": "Subetapa clonada exitosamente."
    }
