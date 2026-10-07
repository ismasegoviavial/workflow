import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.middleware.tenant import get_tenant_context, TenantContext
from src.services.execution_engine import WorkflowExecutionEngine
from src.models.entities import WorkflowExecution, SubstageExecution, ExecutionAuditLog, Stage, Substage

router = APIRouter(prefix="/api/v1/executions", tags=["Executions & Runtime"])

class StartExecutionRequest(BaseModel):
    workflow_id: str

class SubmitDataRequest(BaseModel):
    payload: Dict[str, Any]

class ReviewDecisionRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None

@router.post("/start")
def start_execution(
    request: StartExecutionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Inicia una nueva instancia de ejecución del workflow con clave consistente"""
    engine = WorkflowExecutionEngine(db, tenant)
    exec_inst = engine.start_workflow(request.workflow_id)
    return {
        "execution_id": exec_inst.id,
        "execution_code": exec_inst.execution_code,
        "current_stage_id": exec_inst.current_stage_id,
        "current_substage_id": exec_inst.current_substage_id,
        "status": exec_inst.status,
        "message": f"Instancia {exec_inst.execution_code} iniciada correctamente."
    }

@router.get("/{execution_id}")
def get_execution_state(
    execution_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Obtiene el estado en tiempo real de la ejecución, subetapa actual, roles y si puede Volver"""
    engine = WorkflowExecutionEngine(db, tenant)
    execution = engine.get_execution_or_404(execution_id)

    # Subetapa actual y etapa actual
    current_stage = db.query(Stage).filter(Stage.id == execution.current_stage_id).first() if execution.current_stage_id else None
    current_sub = db.query(Substage).filter(Substage.id == execution.current_substage_id).first() if execution.current_substage_id else None
    
    # Subetapa execution activa
    active_sub_exec = None
    if current_sub:
        active_sub_exec = db.query(SubstageExecution).filter(
            SubstageExecution.company_id == tenant.company_id,
            SubstageExecution.workflow_execution_id == execution.id,
            SubstageExecution.substage_id == current_sub.id
        ).order_by(SubstageExecution.iteration.desc()).first()

    # ¿Se puede presionar 'Volver'?
    can_rollback = False
    if current_stage and current_sub:
        can_rollback = not (current_stage.is_initial and current_sub.is_initial)

    # Roles del usuario actual
    is_editor = current_sub.editor_workspace_group in tenant.user_groups if current_sub else False
    is_reviewer = current_sub.reviewer_workspace_group in tenant.user_groups if current_sub else False

    return {
        "id": execution.id,
        "execution_code": execution.execution_code,
        "status": execution.status,
        "current_stage": {
            "id": current_stage.id,
            "stage_key": current_stage.stage_key,
            "title": current_stage.title,
            "is_initial": current_stage.is_initial
        } if current_stage else None,
        "current_substage": {
            "id": current_sub.id,
            "substage_key": current_sub.substage_key,
            "title": current_sub.title,
            "is_initial": current_sub.is_initial,
            "editor_group": current_sub.editor_workspace_group,
            "reviewer_group": current_sub.reviewer_workspace_group,
            "input_schema": json.loads(current_sub.input_schema or "{}"),
            "output_schema": json.loads(current_sub.output_schema or "{}"),
            "current_payload": json.loads(active_sub_exec.input_payload or "{}") if active_sub_exec else {}
        } if current_sub else None,
        "user_permissions": {
            "user_email": tenant.user_email,
            "is_editor": is_editor,
            "is_reviewer": is_reviewer
        },
        "can_rollback": can_rollback,
        "context_data": json.loads(execution.context_data or "{}")
    }

@router.post("/{execution_id}/substages/{substage_id}/submit")
def submit_substage_data(
    execution_id: str,
    substage_id: str,
    body: SubmitDataRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Acción del Editor: Envía los datos validados a revisión"""
    engine = WorkflowExecutionEngine(db, tenant)
    sub_exec = engine.submit_editor_data(execution_id, substage_id, body.payload)
    return {
        "status": sub_exec.status,
        "iteration": sub_exec.iteration,
        "message": "Datos guardados y enviados a revisión."
    }

@router.post("/{execution_id}/substages/{substage_id}/review")
def review_substage_decision(
    execution_id: str,
    substage_id: str,
    body: ReviewDecisionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Acción del Revisor: Aprueba o rechaza los datos de la subetapa"""
    engine = WorkflowExecutionEngine(db, tenant)
    sub_exec = engine.review_substage(execution_id, substage_id, body.approved, body.comments, body.output_data)
    return {
        "status": sub_exec.status,
        "reviewed_by": sub_exec.reviewed_by_email,
        "message": "Aprobado y avanzado a la siguiente fase." if body.approved else "Rechazado y devuelto a edición."
    }

@router.post("/{execution_id}/rollback")
def rollback_step(
    execution_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Botón 'Volver': Retrocede la ejecución a la subetapa/etapa anterior conservando el historial"""
    engine = WorkflowExecutionEngine(db, tenant)
    exec_inst = engine.rollback_previous_step(execution_id)
    return {
        "message": "Retroceso ejecutado exitosamente.",
        "execution_id": exec_inst.id,
        "current_substage_id": exec_inst.current_substage_id,
        "status": exec_inst.status
    }

@router.get("/{execution_id}/audit")
def get_execution_audit_trail(
    execution_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Retorna la línea de tiempo completa de auditoría e iteraciones"""
    logs = db.query(ExecutionAuditLog).filter(
        ExecutionAuditLog.workflow_execution_id == execution_id,
        ExecutionAuditLog.company_id == tenant.company_id
    ).order_by(ExecutionAuditLog.created_at.asc()).all()

    return [
        {
            "id": log.id,
            "action": log.action,
            "performed_by_email": log.performed_by_email,
            "user_roles": json.loads(log.user_roles or "[]"),
            "payload_snapshot": json.loads(log.payload_snapshot or "{}"),
            "notes": log.notes,
            "timestamp": log.created_at.isoformat()
        } for log in logs
    ]
