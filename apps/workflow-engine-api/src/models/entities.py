import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    google_workspace_domain = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workflows = relationship("Workflow", back_populates="company", cascade="all, delete-orphan")


class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uk_company_workflow_code"),
    )
    
    company = relationship("Company", back_populates="workflows")
    stages = relationship("Stage", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class Stage(Base):
    __tablename__ = "stages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    stage_key = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    is_initial = Column(Boolean, default=False)
    is_final = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "workflow_id", "stage_key", name="uk_stage_key"),
    )
    
    workflow = relationship("Workflow", back_populates="stages")
    substages = relationship("Substage", back_populates="stage", cascade="all, delete-orphan")


class StageTransition(Base):
    __tablename__ = "stage_transitions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    from_stage_id = Column(String(36), ForeignKey("stages.id"), nullable=False)
    to_stage_id = Column(String(36), ForeignKey("stages.id"), nullable=False)
    condition_expression = Column(Text, nullable=True)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class ServiceCatalog(Base):
    __tablename__ = "service_catalog"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True) # None = Global
    service_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="GCP_IAM")
    input_schema = Column(Text, nullable=False, default="{}") # JSON String
    output_schema = Column(Text, nullable=False, default="{}") # JSON String
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Substage(Base):
    __tablename__ = "substages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), nullable=False)
    stage_id = Column(String(36), ForeignKey("stages.id", ondelete="CASCADE"), nullable=False)
    substage_key = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    is_initial = Column(Boolean, default=False)
    service_id = Column(String(36), ForeignKey("service_catalog.id"), nullable=True)
    
    # Roles mapeados a Google Workspace
    editor_workspace_group = Column(String(255), nullable=False)
    reviewer_workspace_group = Column(String(255), nullable=False)
    
    # Schemas JSON (guardados como Text / JSON)
    input_schema = Column(Text, nullable=False, default="{}")
    output_schema = Column(Text, nullable=False, default="{}")
    input_mapping = Column(Text, nullable=True, default="{}")
    
    is_clonable = Column(Boolean, default=True)
    template_origin_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "stage_id", "substage_key", name="uk_substage_key"),
    )
    
    stage = relationship("Stage", back_populates="substages")
    service = relationship("ServiceCatalog")


class SubstageTransition(Base):
    __tablename__ = "substage_transitions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), nullable=False)
    stage_id = Column(String(36), ForeignKey("stages.id"), nullable=False)
    from_substage_id = Column(String(36), ForeignKey("substages.id"), nullable=False)
    to_substage_id = Column(String(36), ForeignKey("substages.id"), nullable=False)
    condition_expression = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    execution_code = Column(String(100), nullable=False) # Clave consistente
    
    current_stage_id = Column(String(36), ForeignKey("stages.id"), nullable=True)
    current_substage_id = Column(String(36), ForeignKey("substages.id"), nullable=True)
    status = Column(String(50), default="IN_PROGRESS") 
    # 'IN_PROGRESS', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'COMPLETED', 'ROLLED_BACK'
    
    context_data = Column(Text, default="{}")
    started_by_email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "execution_code", name="uk_company_execution_code"),
    )
    
    workflow = relationship("Workflow", back_populates="executions")
    substage_executions = relationship("SubstageExecution", back_populates="workflow_execution", cascade="all, delete-orphan")


class SubstageExecution(Base):
    __tablename__ = "substage_executions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), nullable=False)
    workflow_execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    substage_id = Column(String(36), ForeignKey("substages.id"), nullable=False)
    iteration = Column(Integer, default=1, nullable=False) # Para 'Volver' y reintentos
    
    status = Column(String(50), default="DRAFT")
    # 'DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'ROLLED_BACK', 'COMPLETED'
    
    input_payload = Column(Text, default="{}")
    output_payload = Column(Text, default="{}")
    
    edited_by_email = Column(String(255), nullable=True)
    edited_at = Column(DateTime, nullable=True)
    reviewed_by_email = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "workflow_execution_id", "substage_id", "iteration", name="uk_exec_substage_iter"),
    )
    
    workflow_execution = relationship("WorkflowExecution", back_populates="substage_executions")
    substage = relationship("Substage")


class ExecutionAuditLog(Base):
    __tablename__ = "execution_audit_log"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), nullable=False)
    workflow_execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    substage_execution_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False) # 'EDIT_SAVED', 'APPROVED', 'REJECTED', 'ROLLBACK_TRIGGERED'
    performed_by_email = Column(String(255), nullable=False)
    user_roles = Column(Text, nullable=False) # JSON o lista de grupos
    payload_snapshot = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
