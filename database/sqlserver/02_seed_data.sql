-- =====================================================================================
-- SEED DATA: EMPRESA DEMO, SERVICIOS DE CATÁLOGO Y WORKFLOW INICIAL
-- =====================================================================================

-- 1. Crear Empresa Demo
DECLARE @CompanyId UNIQUEIDENTIFIER = NEWID();
INSERT INTO companies (id, company_code, name, google_workspace_domain)
VALUES (@CompanyId, 'DEMOCORP', 'Demo Corporation', 'democorp.com');

-- 2. Registrar Microservicios en el Catálogo Global
DECLARE @SrvPdfId UNIQUEIDENTIFIER = NEWID();
INSERT INTO service_catalog (id, company_id, service_key, name, endpoint_url, input_schema, output_schema)
VALUES (
    @SrvPdfId,
    NULL, -- Global
    'SRV_PDF_READER',
    'Lector / Extractor OCR de Documentos PDF',
    'https://srv-pdf-reader-xyz-uc.a.run.app/api/v1/extract',
    '{
        "type": "object",
        "required": ["pdf_url"],
        "properties": {
            "pdf_url": {"type": "string", "title": "URL del PDF"},
            "extract_tables": {"type": "boolean", "default": true}
        }
    }',
    '{
        "type": "object",
        "properties": {
            "text_content": {"type": "string"},
            "extracted_rut": {"type": "string"},
            "document_date": {"type": "string"},
            "page_count": {"type": "integer"}
        }
    }'
);

DECLARE @SrvDateCalcId UNIQUEIDENTIFIER = NEWID();
INSERT INTO service_catalog (id, company_id, service_key, name, endpoint_url, input_schema, output_schema)
VALUES (
    @SrvDateCalcId,
    NULL, -- Global
    'SRV_DATE_CALCULATOR',
    'Calculador de Días Hábiles y Fechas de Vencimiento',
    'https://srv-date-calculator-xyz-uc.a.run.app/api/v1/calculate',
    '{
        "type": "object",
        "required": ["start_date", "business_days_to_add"],
        "properties": {
            "start_date": {"type": "string", "format": "date"},
            "business_days_to_add": {"type": "integer"}
        }
    }',
    '{
        "type": "object",
        "properties": {
            "due_date": {"type": "string", "format": "date"},
            "is_weekend": {"type": "boolean"},
            "calculated_at": {"type": "string"}
        }
    }'
);

-- 3. Crear Workflow Demo: "Aprobación y Emisión de Contratos"
DECLARE @WorkflowId UNIQUEIDENTIFIER = NEWID();
INSERT INTO workflows (id, company_id, code, name, description, version)
VALUES (
    @WorkflowId,
    @CompanyId,
    'CONTRATOS_SERVICIOS',
    'Flujo de Aprobación y Emisión de Contratos de Servicios',
    'Workflow de 2 etapas con subetapas de validación de antecedentes y cálculo de fechas',
    1
);

-- 4. Etapa 1: "Recepción y Validación de Proveedor"
DECLARE @Stage1Id UNIQUEIDENTIFIER = NEWID();
INSERT INTO stages (id, company_id, workflow_id, stage_key, title, is_initial, is_final, order_index)
VALUES (
    @Stage1Id,
    @CompanyId,
    @WorkflowId,
    'ETAPA_01_RECEPCION',
    'Recepción y Validación de Antecedentes',
    1, -- Inicial
    0,
    1
);

-- 5. Subetapa 1.1: Ingreso de Datos del Proveedor
DECLARE @Substage1_1Id UNIQUEIDENTIFIER = NEWID();
INSERT INTO substages (
    id, company_id, stage_id, substage_key, title, is_initial,
    editor_workspace_group, reviewer_workspace_group,
    input_schema, output_schema
)
VALUES (
    @Substage1_1Id,
    @CompanyId,
    @Stage1Id,
    'SUB_DATOS_PROVEEDOR',
    'Ingreso de Datos y Antecedentes del Proveedor',
    1,
    'operaciones@democorp.com',
    'supervisores@democorp.com',
    '{
        "type": "object",
        "required": ["rut", "razon_social", "monto_contrato"],
        "properties": {
            "rut": {"type": "string", "title": "RUT Proveedor"},
            "razon_social": {"type": "string", "title": "Razón Social"},
            "monto_contrato": {"type": "number", "title": "Monto Total (CLP)"},
            "documento_pdf_url": {"type": "string", "title": "URL Certificado / Estatuto"}
        }
    }',
    '{
        "type": "object",
        "properties": {
            "proveedor_validado": {"type": "boolean"},
            "rut_normalizado": {"type": "string"},
            "monto_aprobado": {"type": "number"}
        }
    }'
);

-- 6. Subetapa 1.2: Cálculo de Plazo y Vigencia (Consume Microservicio Calculador)
DECLARE @Substage1_2Id UNIQUEIDENTIFIER = NEWID();
INSERT INTO substages (
    id, company_id, stage_id, substage_key, title, is_initial, service_id,
    editor_workspace_group, reviewer_workspace_group,
    input_schema, output_schema, input_mapping
)
VALUES (
    @Substage1_2Id,
    @CompanyId,
    @Stage1Id,
    'SUB_CALCULO_PLAZOS',
    'Determinación de Plazos y Fecha Límite',
    0,
    @SrvDateCalcId,
    'operaciones@democorp.com',
    'legales@democorp.com',
    '{
        "type": "object",
        "required": ["start_date", "business_days_to_add"],
        "properties": {
            "start_date": {"type": "string", "format": "date", "title": "Fecha Inicio Vigencia"},
            "business_days_to_add": {"type": "integer", "title": "Días Hábiles de Plazo"}
        }
    }',
    '{
        "type": "object",
        "properties": {
            "due_date": {"type": "string", "title": "Fecha de Vencimiento"},
            "vigencia_aprobada": {"type": "boolean"}
        }
    }',
    '{"start_date": "$.current_date", "business_days_to_add": 30}'
);

-- Conectar Subetapas 1.1 -> 1.2
INSERT INTO substage_transitions (company_id, stage_id, from_substage_id, to_substage_id)
VALUES (@CompanyId, @Stage1Id, @Substage1_1Id, @Substage1_2Id);

-- 7. Etapa 2: "Firma y Emisión Final"
DECLARE @Stage2Id UNIQUEIDENTIFIER = NEWID();
INSERT INTO stages (id, company_id, workflow_id, stage_key, title, is_initial, is_final, order_index)
VALUES (
    @Stage2Id,
    @CompanyId,
    @WorkflowId,
    'ETAPA_02_EMISION',
    'Firma y Emisión de Documento Contractual',
    0,
    1, -- Final
    2
);

-- Conectar Etapa 1 -> Etapa 2
INSERT INTO stage_transitions (company_id, workflow_id, from_stage_id, to_stage_id)
VALUES (@CompanyId, @WorkflowId, @Stage1Id, @Stage2Id);
