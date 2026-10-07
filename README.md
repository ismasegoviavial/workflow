# 🚀 Workflow Engine Platform (Multi-Tenant, GCP, SQL Server / Oracle)

Plataforma empresarial de **creación y orquestación de workflows configurables estilo n8n**, diseñada para operar en **Google Cloud Platform (GCP)** con soporte multi-empresa estricto, esquemas dinámicos JSON, roles de Editor/Revisor basados en Google Workspace, botón de retroceso (*Volver*) y fábrica de microservicios en carriles paralelos.

---

## 🏛️ Arquitectura del Sistema

```
workflow-engine-platform/
├── .github/workflows/          # Pipelines CI/CD para Cloud Run
│   └── ci-cd.yml
├── apps/
│   ├── web-builder/            # Frontend (Canvas n8n style + Forms + Portal Operativo)
│   │   ├── src/
│   │   │   ├── components/     # Canvas visual, Forms Dinámicos, Review Modal
│   │   │   └── types.ts        # Tipos e interfaces TypeScript
│   │   └── package.json
│   └── workflow-engine-api/    # Backend Core (FastAPI / SQLAlchemy)
│       ├── src/
│       │   ├── middleware/     # Tenant Context & Google Workspace Auth
│       │   ├── models/         # Modelos de BD relacionales con JSON semi-estructurado
│       │   ├── routers/        # Endpoints de Workflows, Ejecuciones y Catálogo
│       │   ├── services/       # Motor de estados, DAG transitions, Rollback y Schemas
│       │   └── main.py
│       ├── Dockerfile
│       └── requirements.txt
├── services/                   # Fábrica de Microservicios Desacoplados
│   ├── srv-pdf-reader/         # Microservicio de extracción OCR de PDFs
│   └── srv-date-calculator/    # Microservicio de cálculo de plazos y días hábiles
├── database/
│   └── sqlserver/
│       ├── 01_schema.sql       # DDL Multi-Tenant con claves compuestas e índices
│       └── 02_seed_data.sql     # Datos demo, catálogo de microservicios y workflow
├── terraform/                  # Infraestructura como Código para GCP
│   └── main.tf                 # Cloud SQL (Private IP), VPC, Secrets e IAM
└── README.md
```

---

## 🔑 Características Principales

### 1. Aislamiento Multi-Tenant Absoluto
* Cada tabla posee clave primaria y foránea compuesta obligatoria con `company_id`.
* Índices compuestos en disco `(company_id, ...)` garantizan particionamiento lógico y cero fuga de datos entre empresas.
* Claves de ejecución únicas y correlativas: `{COMPANY_CODE}-{WORKFLOW_CODE}-{AÑO}-{SECUENCIA}` (ej. `ACME-CONTRATOS-2026-00001`).

### 2. Roles por Subetapa (Google Workspace)
* Cada subetapa define su grupo de Google Workspace para **Editor** (ej: `operaciones@acme.com`) y para **Revisor** (ej: `finanzas@acme.com`).
* El editor completa y valida el formulario según el `input_schema`.
* El revisor valida, aprueba o rechaza con observaciones.

### 3. Mecanismo de Retroceso (Botón "Volver")
* Permite retroceder a la subetapa/etapa anterior en cualquier momento (excepto en la primera subetapa de la Etapa 1).
* Genera una nueva `iteration` (versión borrador) manteniendo el historial previo intacto en `execution_audit_log` para auditoría total.

### 4. Fábrica / Catálogo de Microservicios Desacoplado
* Microservicios independientes en Cloud Run registrados en `service_catalog`.
* El motor se comunica mediante contratos OpenAPI / JSON Schema inyectando y extrayendo datos sin acoplar la lógica de negocio.

---

## 🛠️ Ejecución Local para Desarrollo

### 1. Backend Core (FastAPI)
```bash
cd apps/workflow-engine-api
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
```
* Documentación interactiva Swagger: `http://localhost:8000/docs`

### 2. Microservicios de Prueba
```bash
# Microservicio de Lectura de PDFs:
cd services/srv-pdf-reader
python -m uvicorn main:app --reload --port 8001

# Microservicio Calculador de Fechas:
cd services/srv-date-calculator
python -m uvicorn main:app --reload --port 8002
```

---

## 🛡️ Seguridad en Google Cloud Platform (GCP)
* **Cloud SQL sin IP Pública:** Configurado con *Private Service Access (VPC Peering)*.
* **Cifrado CMEK & TDE:** Claves criptográficas gestionadas con Google Cloud KMS.
* **URLs Firmadas:** Los PDFs y archivos anexos se visualizan únicamente mediante Signed URLs temporales de Cloud Storage.
* **Google Secret Manager:** Credenciales y llaves inyectadas en tiempo de ejecución.
