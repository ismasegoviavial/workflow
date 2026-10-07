-- =====================================================================================
-- MULTI-TENANT WORKFLOW ENGINE - SCHEMA DDL (SQL SERVER 2019 / 2022 / CLOUD SQL)
-- =====================================================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'companies')
BEGIN
    CREATE TABLE companies (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        company_code NVARCHAR(20) NOT NULL UNIQUE, -- Ej: 'ACME', 'LATAM_CORP'
        name NVARCHAR(255) NOT NULL,
        google_workspace_domain NVARCHAR(255) NOT NULL UNIQUE, -- Ej: 'acme.com'
        is_active BIT DEFAULT 1,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
    CREATE INDEX idx_companies_domain ON companies(google_workspace_domain);
END;

-- 2. Catálogo de Workflows (Aislado por Empresa)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'workflows')
BEGIN
    CREATE TABLE workflows (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES companies(id) ON DELETE CASCADE,
        code NVARCHAR(50) NOT NULL, -- Ej: 'COMPRA_DIRECTA'
        name NVARCHAR(255) NOT NULL,
        description NVARCHAR(MAX),
        version INT NOT NULL DEFAULT 1,
        is_active BIT DEFAULT 1,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_workflows PRIMARY KEY (company_id, id),
        CONSTRAINT uk_company_workflow_code UNIQUE (company_id, code)
    );
    CREATE INDEX idx_workflows_lookup ON workflows(company_id, is_active, created_at);
END;

-- 3. Etapas del Workflow (Nodos del Grafo)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'stages')
BEGIN
    CREATE TABLE stages (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL,
        workflow_id UNIQUEIDENTIFIER NOT NULL,
        stage_key NVARCHAR(100) NOT NULL, -- Ej: 'FASE_EVALUACION'
        title NVARCHAR(255) NOT NULL,
        is_initial BIT DEFAULT 0,
        is_final BIT DEFAULT 0,
        order_index INT NOT NULL DEFAULT 0,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_stages PRIMARY KEY (company_id, id),
        CONSTRAINT fk_stages_workflow FOREIGN KEY (company_id, workflow_id) 
            REFERENCES workflows(company_id, id) ON DELETE CASCADE,
        CONSTRAINT uk_stage_key UNIQUE (company_id, workflow_id, stage_key)
    );
END;

-- 4. Transiciones Configurables entre Etapas (Grafos / Bifurcaciones)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'stage_transitions')
BEGIN
    CREATE TABLE stage_transitions (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL,
        workflow_id UNIQUEIDENTIFIER NOT NULL,
        from_stage_id UNIQUEIDENTIFIER NOT NULL,
        to_stage_id UNIQUEIDENTIFIER NOT NULL,
        condition_expression NVARCHAR(MAX), -- JSONPath / Expresión lógica (ej: "$.monto > 10000")
        priority INT DEFAULT 1,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_stage_transitions PRIMARY KEY (company_id, id),
        CONSTRAINT fk_trans_from_stage FOREIGN KEY (company_id, from_stage_id) 
            REFERENCES stages(company_id, id),
        CONSTRAINT fk_trans_to_stage FOREIGN KEY (company_id, to_stage_id) 
            REFERENCES stages(company_id, id)
    );
    CREATE INDEX idx_stage_transitions ON stage_transitions(company_id, workflow_id, from_stage_id);
END;

-- 5. Catálogo de Microservicios (Fábrica / Integraciones Desacopladas)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'service_catalog')
BEGIN
    CREATE TABLE service_catalog (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NULL FOREIGN KEY REFERENCES companies(id), -- NULL = Servicio global del sistema
        service_key NVARCHAR(100) NOT NULL,
        name NVARCHAR(255) NOT NULL,
        endpoint_url NVARCHAR(500) NOT NULL,
        auth_type NVARCHAR(50) DEFAULT 'GCP_IAM',
        input_schema NVARCHAR(MAX) NOT NULL,
        output_schema NVARCHAR(MAX) NOT NULL,
        is_active BIT DEFAULT 1,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT ck_srv_input_json CHECK (ISJSON(input_schema) = 1),
        CONSTRAINT ck_srv_output_json CHECK (ISJSON(output_schema) = 1)
    );
    CREATE INDEX idx_service_catalog ON service_catalog(company_id, service_key);
END;

-- 6. Subetapas (Formularios, Roles, Schemas Dinámicos)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'substages')
BEGIN
    CREATE TABLE substages (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL,
        stage_id UNIQUEIDENTIFIER NOT NULL,
        substage_key NVARCHAR(100) NOT NULL,
        title NVARCHAR(255) NOT NULL,
        is_initial BIT DEFAULT 0,
        service_id UNIQUEIDENTIFIER NULL FOREIGN KEY REFERENCES service_catalog(id),
        
        -- Roles mapeados a Google Workspace de la empresa
        editor_workspace_group NVARCHAR(255) NOT NULL, -- Ej: 'analistas@acme.com'
        reviewer_workspace_group NVARCHAR(255) NOT NULL, -- Ej: 'jefaturas@acme.com'
        
        -- Esquemas de datos JSON
        input_schema NVARCHAR(MAX) NOT NULL DEFAULT '{}',
        output_schema NVARCHAR(MAX) NOT NULL DEFAULT '{}',
        input_mapping NVARCHAR(MAX) DEFAULT '{}',
        
        -- Clonación y plantillas
        is_clonable BIT DEFAULT 1,
        template_origin_id UNIQUEIDENTIFIER NULL,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_substages PRIMARY KEY (company_id, id),
        CONSTRAINT fk_substages_stage FOREIGN KEY (company_id, stage_id) 
            REFERENCES stages(company_id, id) ON DELETE CASCADE,
        CONSTRAINT uk_substage_key UNIQUE (company_id, stage_id, substage_key),
        CONSTRAINT ck_sub_input_json CHECK (ISJSON(input_schema) = 1),
        CONSTRAINT ck_sub_output_json CHECK (ISJSON(output_schema) = 1)
    );
END;

-- 7. Transiciones entre Subetapas
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'substage_transitions')
BEGIN
    CREATE TABLE substage_transitions (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL,
        stage_id UNIQUEIDENTIFIER NOT NULL,
        from_substage_id UNIQUEIDENTIFIER NOT NULL,
        to_substage_id UNIQUEIDENTIFIER NOT NULL,
        condition_expression NVARCHAR(MAX),
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_substage_transitions PRIMARY KEY (company_id, id),
        CONSTRAINT fk_sub_trans_from FOREIGN KEY (company_id, from_substage_id) 
            REFERENCES substages(company_id, id),
        CONSTRAINT fk_sub_trans_to FOREIGN KEY (company_id, to_substage_id) 
            REFERENCES substages(company_id, id)
    );
END;

-- 8. Instancias de Ejecución (Clave de Consistencia Multi-Tenant)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'workflow_executions')
BEGIN
    CREATE TABLE workflow_executions (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES companies(id),
        workflow_id UNIQUEIDENTIFIER NOT NULL,
        execution_code NVARCHAR(100) NOT NULL, -- Ej: 'ACME-ONBOARD-2026-0001'
        
        current_stage_id UNIQUEIDENTIFIER NULL,
        current_substage_id UNIQUEIDENTIFIER NULL,
        status NVARCHAR(50) NOT NULL DEFAULT 'IN_PROGRESS',
        -- 'IN_PROGRESS', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'COMPLETED', 'ROLLED_BACK'
        
        context_data NVARCHAR(MAX) NOT NULL DEFAULT '{}',
        started_by_email NVARCHAR(255) NOT NULL,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_workflow_executions PRIMARY KEY (company_id, id),
        CONSTRAINT fk_wf_exec_workflow FOREIGN KEY (company_id, workflow_id) 
            REFERENCES workflows(company_id, id),
        CONSTRAINT uk_company_execution_code UNIQUE (company_id, execution_code),
        CONSTRAINT ck_wf_context_json CHECK (ISJSON(context_data) = 1)
    );
    CREATE INDEX idx_wf_exec_lookup ON workflow_executions(company_id, workflow_id, status, created_at);
END;

-- 9. Ejecución de Subetapas (Historial, Iteraciones y Mecanismo Volver)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'substage_executions')
BEGIN
    CREATE TABLE substage_executions (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL,
        workflow_execution_id UNIQUEIDENTIFIER NOT NULL,
        substage_id UNIQUEIDENTIFIER NOT NULL,
        iteration INT NOT NULL DEFAULT 1,
        
        status NVARCHAR(50) NOT NULL DEFAULT 'DRAFT',
        -- 'DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'ROLLED_BACK', 'COMPLETED'
        
        input_payload NVARCHAR(MAX) NOT NULL DEFAULT '{}',
        output_payload NVARCHAR(MAX) NOT NULL DEFAULT '{}',
        
        edited_by_email NVARCHAR(255),
        edited_at DATETIMEOFFSET,
        reviewed_by_email NVARCHAR(255),
        reviewed_at DATETIMEOFFSET,
        review_comments NVARCHAR(MAX),
        
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_substage_executions PRIMARY KEY (company_id, id),
        CONSTRAINT fk_sub_exec_wf FOREIGN KEY (company_id, workflow_execution_id) 
            REFERENCES workflow_executions(company_id, id) ON DELETE CASCADE,
        CONSTRAINT fk_sub_exec_substage FOREIGN KEY (company_id, substage_id) 
            REFERENCES substages(company_id, id),
        CONSTRAINT uk_exec_substage_iter UNIQUE (company_id, workflow_execution_id, substage_id, iteration),
        CONSTRAINT ck_exec_input_json CHECK (ISJSON(input_payload) = 1),
        CONSTRAINT ck_exec_output_json CHECK (ISJSON(output_payload) = 1)
    );
    CREATE INDEX idx_sub_exec_lookup ON substage_executions(company_id, workflow_execution_id, substage_id, status);
END;

-- 10. Auditoría y Trazabilidad (Rollback Log)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'execution_audit_log')
BEGIN
    CREATE TABLE execution_audit_log (
        id UNIQUEIDENTIFIER DEFAULT NEWID(),
        company_id UNIQUEIDENTIFIER NOT NULL,
        workflow_execution_id UNIQUEIDENTIFIER NOT NULL,
        substage_execution_id UNIQUEIDENTIFIER NULL,
        action NVARCHAR(100) NOT NULL, -- 'EDIT_SAVED', 'APPROVED', 'REJECTED', 'ROLLBACK_TRIGGERED'
        performed_by_email NVARCHAR(255) NOT NULL,
        user_roles NVARCHAR(MAX) NOT NULL,
        payload_snapshot NVARCHAR(MAX) NOT NULL,
        notes NVARCHAR(MAX),
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        
        CONSTRAINT pk_execution_audit_log PRIMARY KEY (company_id, id),
        CONSTRAINT fk_audit_wf_exec FOREIGN KEY (company_id, workflow_execution_id) 
            REFERENCES workflow_executions(company_id, id) ON DELETE CASCADE
    );
    CREATE INDEX idx_audit_log_lookup ON execution_audit_log(company_id, workflow_execution_id, created_at);
END;
