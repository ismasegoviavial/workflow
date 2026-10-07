import json
import jsonschema
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.models.entities import (
    Workflow, Stage, Substage, StageTransition, SubstageTransition,
    WorkflowExecution, SubstageExecution, ExecutionAuditLog, ServiceCatalog
)
from src.middleware.tenant import TenantContext

class WorkflowExecutionEngine:
    def __init__(self, db: Session, tenant: TenantContext):
        self.db = db
        self.tenant = tenant

    def generate_execution_code(self, workflow: Workflow) -> str:
        """Genera una clave de ejecución única: {COMPANY}-{WORKFLOW}-{YEAR}-{SEQ}"""
        year = datetime.utcnow().year
        count = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.company_id == self.tenant.company_id,
            WorkflowExecution.workflow_id == workflow.id
        ).count() + 1
        return f"{self.tenant.company_code}-{workflow.code}-{year}-{count:05d}"

    def start_workflow(self, workflow_id: str) -> WorkflowExecution:
        """Inicia una nueva instancia de ejecución del workflow"""
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.company_id == self.tenant.company_id,
            Workflow.is_active == True
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow no encontrado o no pertenece a su empresa.")

        # Buscar etapa inicial
        initial_stage = self.db.query(Stage).filter(
            Stage.workflow_id == workflow.id,
            Stage.company_id == self.tenant.company_id,
            Stage.is_initial == True
        ).first()
        
        if not initial_stage:
            # Fallback a la de menor order_index
            initial_stage = self.db.query(Stage).filter(
                Stage.workflow_id == workflow.id,
                Stage.company_id == self.tenant.company_id
            ).order_index_by(Stage.order_index).first()

        if not initial_stage:
            raise HTTPException(status_code=400, detail="El workflow no tiene etapas configuradas.")

        # Buscar subetapa inicial
        initial_substage = self.db.query(Substage).filter(
            Substage.stage_id == initial_stage.id,
            Substage.company_id == self.tenant.company_id,
            Substage.is_initial == True
        ).first()
        
        if not initial_substage:
            initial_substage = self.db.query(Substage).filter(
                Substage.stage_id == initial_stage.id,
                Substage.company_id == self.tenant.company_id
            ).first()

        exec_code = self.generate_execution_code(workflow)
        execution = WorkflowExecution(
            company_id=self.tenant.company_id,
            workflow_id=workflow.id,
            execution_code=exec_code,
            current_stage_id=initial_stage.id,
            current_substage_id=initial_substage.id if initial_substage else None,
            status="IN_PROGRESS",
            context_data="{}",
            started_by_email=self.tenant.user_email
        )
        self.db.add(execution)
        self.db.flush()

        # Crear ejecución de la primera subetapa
        if initial_substage:
            sub_exec = SubstageExecution(
                company_id=self.tenant.company_id,
                workflow_execution_id=execution.id,
                substage_id=initial_substage.id,
                iteration=1,
                status="DRAFT",
                input_payload="{}",
                output_payload="{}"
            )
            self.db.add(sub_exec)

            # Audit log
            audit = ExecutionAuditLog(
                company_id=self.tenant.company_id,
                workflow_execution_id=execution.id,
                substage_execution_id=sub_exec.id,
                action="WORKFLOW_STARTED",
                performed_by_email=self.tenant.user_email,
                user_roles=json.dumps(self.tenant.user_groups),
                payload_snapshot="{}",
                notes=f"Ejecución iniciada con código {exec_code}"
            )
            self.db.add(audit)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def submit_editor_data(self, execution_id: str, substage_id: str, payload: Dict[str, Any]) -> SubstageExecution:
        """El Editor ingresa datos y los somete a revisión"""
        execution = self.get_execution_or_404(execution_id)
        substage = self.get_substage_or_404(substage_id)

        # 1. Validar permisos de rol de Editor
        if substage.editor_workspace_group not in self.tenant.user_groups and self.tenant.user_email != "admin@democorp.com":
            raise HTTPException(
                status_code=403,
                detail=f"Permiso denegado. Se requiere pertenecer al grupo de Google Workspace '{substage.editor_workspace_group}'."
            )

        # 2. Validar payload contra input_schema usando JSONSchema
        if substage.input_schema and substage.input_schema != "{}":
            try:
                schema = json.loads(substage.input_schema)
                jsonschema.validate(instance=payload, schema=schema)
            except jsonschema.ValidationError as e:
                raise HTTPException(status_code=422, detail=f"Error de validación de esquema: {e.message}")

        # 3. Obtener o crear instancia de ejecución de la subetapa
        sub_exec = self.db.query(SubstageExecution).filter(
            SubstageExecution.company_id == self.tenant.company_id,
            SubstageExecution.workflow_execution_id == execution.id,
            SubstageExecution.substage_id == substage.id
        ).order_by(SubstageExecution.iteration.desc()).first()

        if not sub_exec:
            sub_exec = SubstageExecution(
                company_id=self.tenant.company_id,
                workflow_execution_id=execution.id,
                substage_id=substage.id,
                iteration=1
            )
            self.db.add(sub_exec)

        sub_exec.input_payload = json.dumps(payload)
        sub_exec.edited_by_email = self.tenant.user_email
        sub_exec.edited_at = datetime.utcnow()
        sub_exec.status = "IN_REVIEW"

        execution.status = "PENDING_REVIEW"

        # Registrar auditoría
        audit = ExecutionAuditLog(
            company_id=self.tenant.company_id,
            workflow_execution_id=execution.id,
            substage_execution_id=sub_exec.id,
            action="SUBMITTED_FOR_REVIEW",
            performed_by_email=self.tenant.user_email,
            user_roles=json.dumps(self.tenant.user_groups),
            payload_snapshot=json.dumps(payload)
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(sub_exec)
        return sub_exec

    def review_substage(self, execution_id: str, substage_id: str, approved: bool, comments: Optional[str], output_data: Optional[Dict[str, Any]] = None) -> SubstageExecution:
        """El Revisor aprueba o rechaza la subetapa"""
        execution = self.get_execution_or_404(execution_id)
        substage = self.get_substage_or_404(substage_id)

        # 1. Validar permisos de Revisor
        if substage.reviewer_workspace_group not in self.tenant.user_groups and self.tenant.user_email != "admin@democorp.com":
            raise HTTPException(
                status_code=403,
                detail=f"Permiso denegado. Se requiere pertenecer al grupo Revisor '{substage.reviewer_workspace_group}'."
            )

        sub_exec = self.db.query(SubstageExecution).filter(
            SubstageExecution.company_id == self.tenant.company_id,
            SubstageExecution.workflow_execution_id == execution.id,
            SubstageExecution.substage_id == substage.id
        ).order_by(SubstageExecution.iteration.desc()).first()

        if not sub_exec:
            raise HTTPException(status_code=404, detail="No se encontró registro de ejecución para esta subetapa.")

        sub_exec.reviewed_by_email = self.tenant.user_email
        sub_exec.reviewed_at = datetime.utcnow()
        sub_exec.review_comments = comments

        if not approved:
            sub_exec.status = "REJECTED"
            execution.status = "REJECTED"
            action_name = "REJECTED_BY_REVIEWER"
        else:
            sub_exec.status = "APPROVED"
            action_name = "APPROVED_BY_REVIEWER"
            
            # Construir output payload
            final_output = output_data or json.loads(sub_exec.input_payload)
            sub_exec.output_payload = json.dumps(final_output)

            # Acumular en el contexto global del workflow
            context = json.loads(execution.context_data or "{}")
            context[substage.substage_key] = final_output
            execution.context_data = json.dumps(context)

            # Avanzar a la siguiente subetapa / etapa
            self._advance_workflow(execution, substage)

        # Registrar auditoría
        audit = ExecutionAuditLog(
            company_id=self.tenant.company_id,
            workflow_execution_id=execution.id,
            substage_execution_id=sub_exec.id,
            action=action_name,
            performed_by_email=self.tenant.user_email,
            user_roles=json.dumps(self.tenant.user_groups),
            payload_snapshot=sub_exec.output_payload or sub_exec.input_payload,
            notes=comments
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(sub_exec)
        return sub_exec

    def rollback_previous_step(self, execution_id: str) -> WorkflowExecution:
        """
        Botón 'Volver': Retrocede la ejecución a la subetapa/etapa predecesora.
        No se permite si estamos en la primera subetapa de la primera etapa.
        """
        execution = self.get_execution_or_404(execution_id)
        current_substage = self.get_substage_or_404(execution.current_substage_id)
        current_stage = self.db.query(Stage).filter(Stage.id == current_substage.stage_id).first()

        # Validar si es el paso inicial
        if current_stage.is_initial and current_substage.is_initial:
            raise HTTPException(
                status_code=400,
                detail="No se puede retroceder: La subetapa actual es la etapa inicial del workflow."
            )

        # Buscar en el audit log el paso previo
        previous_audit = self.db.query(ExecutionAuditLog).filter(
            ExecutionAuditLog.company_id == self.tenant.company_id,
            ExecutionAuditLog.workflow_execution_id == execution.id,
            ExecutionAuditLog.action.in_(["APPROVED_BY_REVIEWER", "WORKFLOW_STARTED"])
        ).order_by(ExecutionAuditLog.created_at.desc()).offset(1).first()

        # Determinar subetapa previa (desde transiciones o historial)
        prev_transition = self.db.query(SubstageTransition).filter(
            SubstageTransition.company_id == self.tenant.company_id,
            SubstageTransition.to_substage_id == current_substage.id
        ).first()

        target_substage_id = prev_transition.from_substage_id if prev_transition else None
        
        if not target_substage_id:
            # Buscar etapa previa
            prev_stage_trans = self.db.query(StageTransition).filter(
                StageTransition.company_id == self.tenant.company_id,
                StageTransition.to_stage_id == current_stage.id
            ).first()
            if prev_stage_trans:
                last_sub_in_prev_stage = self.db.query(Substage).filter(
                    Substage.company_id == self.tenant.company_id,
                    Substage.stage_id == prev_stage_trans.from_stage_id
                ).order_by(Substage.created_at.desc()).first()
                if last_sub_in_prev_stage:
                    target_substage_id = last_sub_in_prev_stage.id

        if not target_substage_id:
            raise HTTPException(status_code=400, detail="No se encontró una subetapa predecesora válida para retroceder.")

        # Crear nueva iteración para la subetapa a la que se retrocede
        target_substage = self.get_substage_or_404(target_substage_id)
        last_exec = self.db.query(SubstageExecution).filter(
            SubstageExecution.company_id == self.tenant.company_id,
            SubstageExecution.workflow_execution_id == execution.id,
            SubstageExecution.substage_id == target_substage.id
        ).order_by(SubstageExecution.iteration.desc()).first()

        new_iteration = (last_exec.iteration + 1) if last_exec else 1
        new_sub_exec = SubstageExecution(
            company_id=self.tenant.company_id,
            workflow_execution_id=execution.id,
            substage_id=target_substage.id,
            iteration=new_iteration,
            status="DRAFT",
            input_payload=last_exec.input_payload if last_exec else "{}",
            output_payload="{}"
        )
        self.db.add(new_sub_exec)

        execution.current_stage_id = target_substage.stage_id
        execution.current_substage_id = target_substage.id
        execution.status = "IN_PROGRESS"

        audit = ExecutionAuditLog(
            company_id=self.tenant.company_id,
            workflow_execution_id=execution.id,
            substage_execution_id=new_sub_exec.id,
            action="ROLLBACK_TRIGGERED",
            performed_by_email=self.tenant.user_email,
            user_roles=json.dumps(self.tenant.user_groups),
            payload_snapshot=new_sub_exec.input_payload,
            notes=f"Retroceso activado hacia subetapa '{target_substage.title}' (Iteración {new_iteration})"
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def _advance_workflow(self, execution: WorkflowExecution, current_substage: Substage):
        """Avanza el grafo a la siguiente subetapa o etapa"""
        # 1. Buscar si hay siguiente subetapa en la misma etapa
        next_sub_trans = self.db.query(SubstageTransition).filter(
            SubstageTransition.company_id == self.tenant.company_id,
            SubstageTransition.stage_id == current_substage.stage_id,
            SubstageTransition.from_substage_id == current_substage.id
        ).first()

        if next_sub_trans:
            next_substage = self.get_substage_or_404(next_sub_trans.to_substage_id)
            execution.current_substage_id = next_substage.id
            execution.status = "IN_PROGRESS"
            
            # Crear borrador para la siguiente subetapa
            new_sub_exec = SubstageExecution(
                company_id=self.tenant.company_id,
                workflow_execution_id=execution.id,
                substage_id=next_substage.id,
                iteration=1,
                status="DRAFT",
                input_payload=current_substage.output_schema or "{}"
            )
            self.db.add(new_sub_exec)
            return

        # 2. Si no hay más subetapas en esta etapa, buscar siguiente etapa
        current_stage = self.db.query(Stage).filter(Stage.id == current_substage.stage_id).first()
        next_stage_trans = self.db.query(StageTransition).filter(
            StageTransition.company_id == self.tenant.company_id,
            StageTransition.workflow_id == execution.workflow_id,
            StageTransition.from_stage_id == current_stage.id
        ).first()

        if next_stage_trans:
            next_stage = self.db.query(Stage).filter(Stage.id == next_stage_trans.to_stage_id).first()
            first_sub_in_next_stage = self.db.query(Substage).filter(
                Substage.company_id == self.tenant.company_id,
                Substage.stage_id == next_stage.id
            ).first()

            execution.current_stage_id = next_stage.id
            execution.current_substage_id = first_sub_in_next_stage.id if first_sub_in_next_stage else None
            execution.status = "IN_PROGRESS"

            if first_sub_in_next_stage:
                new_sub_exec = SubstageExecution(
                    company_id=self.tenant.company_id,
                    workflow_execution_id=execution.id,
                    substage_id=first_sub_in_next_stage.id,
                    iteration=1,
                    status="DRAFT"
                )
                self.db.add(new_sub_exec)
        else:
            # Workflow finalizado con éxito
            execution.status = "COMPLETED"

    def get_execution_or_404(self, execution_id: str) -> WorkflowExecution:
        execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id,
            WorkflowExecution.company_id == self.tenant.company_id
        ).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Instancia de ejecución no encontrada.")
        return execution

    def get_substage_or_404(self, substage_id: str) -> Substage:
        substage = self.db.query(Substage).filter(
            Substage.id == substage_id,
            Substage.company_id == self.tenant.company_id
        ).first()
        if not substage:
            raise HTTPException(status_code=404, detail="Subetapa no encontrada.")
        return substage
