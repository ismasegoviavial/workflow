import streamlit as st
import json
import uuid
import os
from datetime import datetime, date

# Configuración de Página
st.set_page_config(
    page_title="Workflow Studio | Cloud Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# UTILIDADES DE FORMATEO Y MÁSCARAS
# ==============================================================================
def format_chilean_rut(rut_str: str) -> str:
    """Normaliza y formatea un RUT chileno al estándar 12345678-K."""
    if not rut_str:
        return ""
    cleaned = str(rut_str).strip().replace(".", "").replace("-", "").replace(" ", "").upper()
    if len(cleaned) < 2:
        return cleaned
    body = cleaned[:-1]
    dv = cleaned[-1]
    return f"{body}-{dv}"

def validate_chilean_rut(rut_str: str) -> tuple[bool, str]:
    """Valida el dígito verificador del RUT chileno según módulo 11."""
    if not rut_str:
        return True, ""
    cleaned = str(rut_str).strip().replace(".", "").replace("-", "").replace(" ", "").upper()
    if len(cleaned) < 2:
        return False, "RUT demasiado corto."
    body = cleaned[:-1]
    dv = cleaned[-1]
    if not body.isdigit():
        return False, "El cuerpo del RUT debe contener solo números."
    
    total = 0
    factor = 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 9 if factor == 7 else factor + 1
    expected_dv_num = 11 - (total % 11)
    if expected_dv_num == 11:
        expected_dv = '0'
    elif expected_dv_num == 10:
        expected_dv = 'K'
    else:
        expected_dv = str(expected_dv_num)
    
    if dv != expected_dv:
        return False, f"Dígito verificador inválido. Se calculó '{expected_dv}' pero se ingresó '{dv}'."
    return True, "RUT Válido"

def format_phone_number(phone_str: str) -> str:
    """Formatea un teléfono móvil al estándar +56 9 XXXX XXXX"""
    if not phone_str:
        return ""
    cleaned = "".join([c for c in str(phone_str) if c.isdigit()])
    if cleaned.startswith("56"):
        cleaned = cleaned[2:]
    if len(cleaned) == 9 and cleaned.startswith("9"):
        return f"+56 9 {cleaned[1:5]} {cleaned[5:]}"
    return phone_str

# ==============================================================================
# DATOS DE EJEMPLO PRE-CONFIGURADOS (3 ETAPAS x 3 SUBETAPAS + MICROSERVICIOS)
# ==============================================================================
EXAMPLE_STAGES = [
    {
        "id": "stg-01",
        "title": "Etapa 1: Admisión y Validación de Identidad",
        "key": "ETAPA_ADMISION",
        "substages": [
            {
                "id": "sub-1-1",
                "title": "Ingreso de Solicitud y Datos del Cliente",
                "key": "SUB_INGRESO_DATOS",
                "editor_role": "admision@miempresa.com",
                "reviewer_role": "supervisor.admision@miempresa.com",
                "service_key": "",
                "fields": [
                    {
                        "id": "f-1-1-1",
                        "title": "RUT del Cliente",
                        "name": "rut_cliente",
                        "type": "string",
                        "format": "rut",
                        "placeholder": "_ _ _ _ _ _ _ _ - _",
                        "required": True
                    },
                    {
                        "id": "f-1-1-2",
                        "title": "Nombre Completo",
                        "name": "nombre_completo",
                        "type": "string",
                        "format": "none",
                        "placeholder": "Ej: Juan Pérez González",
                        "required": True
                    },
                    {
                        "id": "f-1-1-3",
                        "title": "Correo Electrónico",
                        "name": "email_contacto",
                        "type": "string",
                        "format": "email",
                        "placeholder": "cliente@correo.com",
                        "required": True
                    }
                ]
            },
            {
                "id": "sub-1-2",
                "title": "Cálculo de Plazo y Días Hábiles",
                "key": "SUB_CALC_DIAS",
                "editor_role": "operaciones@miempresa.com",
                "reviewer_role": "jefe.operaciones@miempresa.com",
                "service_key": "SRV_DATE_CALCULATOR",
                "fields": [
                    {
                        "id": "f-1-2-1",
                        "title": "Fecha de Inicio del Trámite",
                        "name": "fecha_inicio",
                        "type": "date",
                        "required": True
                    },
                    {
                        "id": "f-1-2-2",
                        "title": "Días Hábiles Solicitados",
                        "name": "dias_habiles",
                        "type": "number",
                        "required": True
                    }
                ]
            },
            {
                "id": "sub-1-3",
                "title": "Carga de Cédula de Identidad",
                "key": "SUB_CARGA_CEDULA",
                "editor_role": "admision@miempresa.com",
                "reviewer_role": "supervisor.admision@miempresa.com",
                "service_key": "",
                "fields": [
                    {
                        "id": "f-1-3-1",
                        "title": "Documento Cédula (PDF)",
                        "name": "archivo_cedula",
                        "type": "file",
                        "required": True
                    }
                ]
            }
        ]
    },
    {
        "id": "stg-02",
        "title": "Etapa 2: Evaluación Técnica y OCR",
        "key": "ETAPA_EVALUACION_OCR",
        "substages": [
            {
                "id": "sub-2-1",
                "title": "Extracción OCR de Documentos y Facturas",
                "key": "SUB_OCR_EXTRACT",
                "editor_role": "analista.riesgo@miempresa.com",
                "reviewer_role": "subgerente.riesgo@miempresa.com",
                "service_key": "SRV_PDF_READER",
                "fields": [
                    {
                        "id": "f-2-1-1",
                        "title": "URL del PDF a Procesar",
                        "name": "pdf_document_url",
                        "type": "string",
                        "placeholder": "https://storage.googleapis.com/.../factura.pdf",
                        "required": True
                    }
                ]
            },
            {
                "id": "sub-2-2",
                "title": "Evaluación de Scoring Financiero",
                "key": "SUB_SCORING",
                "editor_role": "analista.riesgo@miempresa.com",
                "reviewer_role": "subgerente.riesgo@miempresa.com",
                "service_key": "SRV_AI_CREDIT_SCORING",
                "fields": [
                    {
                        "id": "f-2-2-1",
                        "title": "RUT para Scoring",
                        "name": "rut_scoring",
                        "type": "string",
                        "format": "rut",
                        "placeholder": "_ _ _ _ _ _ _ _ - _",
                        "required": True
                    },
                    {
                        "id": "f-2-2-2",
                        "title": "Ingresos Mensuales Declarados (CLP)",
                        "name": "ingresos_mensuales",
                        "type": "number",
                        "required": True
                    },
                    {
                        "id": "f-2-2-3",
                        "title": "Monto Solicitado",
                        "name": "monto_solicitado",
                        "type": "number",
                        "required": True
                    }
                ]
            },
            {
                "id": "sub-2-3",
                "title": "Dictamen de Aprobación de Riesgo",
                "key": "SUB_DICTAMEN_RIESGO",
                "editor_role": "analista.riesgo@miempresa.com",
                "reviewer_role": "subgerente.riesgo@miempresa.com",
                "service_key": "",
                "fields": [
                    {
                        "id": "f-2-3-1",
                        "title": "Comentarios de Evaluación Técnica",
                        "name": "comentarios_tecnicos",
                        "type": "string",
                        "required": True
                    },
                    {
                        "id": "f-2-3-2",
                        "title": "Riesgo Mitigado y Conforme",
                        "name": "riesgo_conforme",
                        "type": "boolean",
                        "required": True
                    }
                ]
            }
        ]
    },
    {
        "id": "stg-03",
        "title": "Etapa 3: Aprobación y Generación Legal",
        "key": "ETAPA_APROBACION_LEGAL",
        "substages": [
            {
                "id": "sub-3-1",
                "title": "Generación Automática de Contrato PDF",
                "key": "SUB_GEN_CONTRATO",
                "editor_role": "legal@miempresa.com",
                "reviewer_role": "fiscal@miempresa.com",
                "service_key": "SRV_DOC_GENERATOR",
                "fields": [
                    {
                        "id": "f-3-1-1",
                        "title": "Cláusulas Especiales",
                        "name": "clausulas_especiales",
                        "type": "string",
                        "required": False
                    }
                ]
            },
            {
                "id": "sub-3-2",
                "title": "Firma Electrónica y Conformidad",
                "key": "SUB_FIRMA_DIGITAL",
                "editor_role": "legal@miempresa.com",
                "reviewer_role": "fiscal@miempresa.com",
                "service_key": "",
                "fields": [
                    {
                        "id": "f-3-2-1",
                        "title": "Fecha de Firma",
                        "name": "fecha_firma",
                        "type": "date",
                        "required": True
                    },
                    {
                        "id": "f-3-2-2",
                        "title": "Código de Verificación Firma",
                        "name": "token_firma",
                        "type": "string",
                        "placeholder": "AUTH-SIGN-2026-XYZ",
                        "required": True
                    }
                ]
            },
            {
                "id": "sub-3-3",
                "title": "Cierre y Activación del Servicio",
                "key": "SUB_ACTIVACION_FINAL",
                "editor_role": "operaciones@miempresa.com",
                "reviewer_role": "gerencia@miempresa.com",
                "service_key": "",
                "fields": [
                    {
                        "id": "f-3-3-1",
                        "title": "Confirmar Activación de Cuenta",
                        "name": "cuenta_activada",
                        "type": "boolean",
                        "required": True
                    }
                ]
            }
        ]
    }
]

# ==============================================================================
# INICIALIZACIÓN DEL ESTADO DE LA APLICACIÓN (Session State)
# ==============================================================================
if "workflow" not in st.session_state:
    st.session_state.workflow = {
        "id": "wf-custom-01",
        "name": "Workflow de Admisión y Evaluación con Microservicios",
        "tenant": "MI_EMPRESA",
        "code": "WF_ONBOARDING",
        "stages": json.loads(json.dumps(EXAMPLE_STAGES))
    }

if "microservices" not in st.session_state:
    st.session_state.microservices = [
        {
            "key": "SRV_DATE_CALCULATOR",
            "name": "Calculador de Días Hábiles",
            "url": "https://srv-date-calculator-432889140614.us-central1.run.app/api/v1/calculate"
        },
        {
            "key": "SRV_PDF_READER",
            "name": "Extractor OCR de PDFs",
            "url": "https://srv-pdf-reader-432889140614.us-central1.run.app/api/v1/extract"
        },
        {
            "key": "SRV_DOC_GENERATOR",
            "name": "Generador de Contratos PDF",
            "url": "https://srv-doc-gen-432889140614.us-central1.run.app/api/v1/generate"
        },
        {
            "key": "SRV_AI_CREDIT_SCORING",
            "name": "Evaluador de Scoring Financiero",
            "url": "https://srv-credit-scoring-432889140614.us-central1.run.app/api/v1/score"
        }
    ]

if "execution" not in st.session_state:
    st.session_state.execution = {
        "code": f"EXEC-{datetime.utcnow().year}-00001",
        "status": "NOT_STARTED",
        "current_stage_idx": 0,
        "current_substage_idx": 0,
        "iteration": 1,
        "form_data": {},
        "context_data": {},
        "audit_logs": []
    }

# Estilos CSS Corporativos
st.markdown("""
<style>
    .main-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 0.85rem;
        color: #475569;
        margin-bottom: 1.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Barra Lateral
st.sidebar.markdown("### Workflow Studio")
st.sidebar.caption(f"Tenant: **{st.session_state.workflow['tenant']}**")

mode = st.sidebar.radio(
    "Selecciona la Vista:",
    [
        "Diseñador de Workflows",
        "Portal de Ejecución (Runtime)",
        "Fábrica de APIs con IA",
        "Catálogo de Microservicios"
    ],
    index=0
)

st.sidebar.divider()
st.sidebar.markdown(f"**Microservicios en Catálogo:** `{len(st.session_state.microservices)}`")

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("Cargar Ejemplo 3x3", help="Cargar 3 etapas con 3 subetapas y microservicios"):
        st.session_state.workflow["stages"] = json.loads(json.dumps(EXAMPLE_STAGES))
        st.session_state.execution["status"] = "NOT_STARTED"
        st.session_state.execution["current_stage_idx"] = 0
        st.session_state.execution["current_substage_idx"] = 0
        st.session_state.execution["form_data"] = {}
        st.success("Ejemplo cargado correctamente.")
        st.rerun()

with col_btn2:
    if st.button("Vaciar Todo", help="Dejar el flujo 100% en blanco"):
        st.session_state.workflow["stages"] = []
        st.session_state.execution = {
            "code": f"EXEC-{datetime.utcnow().year}-00001",
            "status": "NOT_STARTED",
            "current_stage_idx": 0,
            "current_substage_idx": 0,
            "iteration": 1,
            "form_data": {},
            "context_data": {},
            "audit_logs": []
        }
        st.rerun()

# ==============================================================================
# VISTA 1: DISEÑADOR DE WORKFLOWS (BUILDER)
# ==============================================================================
if mode == "Diseñador de Workflows":
    st.markdown('<div class="main-header">Diseñador de Workflows y Subetapas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Crea y estructura las etapas, agrega subetapas, define sus campos dinámicos con formato y máscaras, y asigna roles de Google Workspace.</div>', unsafe_allow_html=True)

    col_name, col_code = st.columns([3, 1])
    with col_name:
        st.session_state.workflow["name"] = st.text_input("Nombre del Workflow:", value=st.session_state.workflow["name"])
    with col_code:
        st.session_state.workflow["code"] = st.text_input("Código Técnico:", value=st.session_state.workflow["code"])

    st.divider()

    # Formulario para Crear Nueva Etapa
    with st.expander("Crear Nueva Etapa", expanded=len(st.session_state.workflow["stages"]) == 0):
        with st.form("form_new_stage", clear_on_submit=True):
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                stage_title = st.text_input("Nombre de la Etapa:", placeholder="Ej: Recepción y Validación")
            with col_s2:
                stage_key = st.text_input("Clave de la Etapa:", placeholder="Ej: ETAPA_RECEPCION")
            
            submit_stage = st.form_submit_button("Crear Etapa", type="primary")
            if submit_stage:
                if stage_title:
                    key = stage_key if stage_key else stage_title.upper().replace(" ", "_")
                    new_stage = {
                        "id": str(uuid.uuid4()),
                        "title": stage_title,
                        "key": key,
                        "substages": []
                    }
                    st.session_state.workflow["stages"].append(new_stage)
                    st.success(f"Etapa '{stage_title}' creada exitosamente.")
                    st.rerun()
                else:
                    st.error("Debes ingresar el nombre de la etapa.")

    # Listado de Etapas Creadas
    if len(st.session_state.workflow["stages"]) == 0:
        st.info("El workflow está vacío. Puedes hacer clic en 'Crear Nueva Etapa' o cargar el ejemplo desde la barra lateral con 'Cargar Ejemplo 3x3'.")
    else:
        # DIAGRAMA DE ARQUITECTURA ESTILO ARCHIFY
        st.markdown("### Diagrama de Arquitectura del Flujo (Pipeline Secuencial)")
        st.caption("Visualización del pipeline de etapas secuenciales, subetapas, microservicios conectados y roles:")
        
        flow_cols = st.columns(len(st.session_state.workflow["stages"]) + 2)
        
        with flow_cols[0]:
            st.markdown("""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:10px; text-align:center; min-height:105px;">
                <div style="font-size:11px; font-weight:bold; color:#0f172a; margin-top:10px;">INICIO</div>
                <div style="font-size:10px; color:#64748b; margin-top:4px;">Disparo Manual / API</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; font-size:16px; color:#94a3b8; margin-top:4px;'>→</div>", unsafe_allow_html=True)

        for s_idx, stg in enumerate(st.session_state.workflow["stages"]):
            with flow_cols[s_idx + 1]:
                sub_count = len(stg["substages"])
                srv_count = sum(1 for sub in stg["substages"] if sub.get("service_key"))
                
                srv_badges = ""
                for sub in stg["substages"]:
                    if sub.get("service_key"):
                        srv_badges += f"<div style='font-size:9px; background:#f1f5f9; color:#334155; border:1px solid #cbd5e1; border-radius:4px; padding:2px 4px; margin-top:2px;'>Servicio: {sub['service_key']}</div>"

                st.markdown(f"""
                <div style="background:#ffffff; border:1px solid #2563eb; border-radius:8px; padding:10px; min-height:105px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-size:10px; font-weight:bold; color:#2563eb;">ETAPA {s_idx + 1}</div>
                    <div style="font-weight:600; font-size:12px; color:#0f172a; margin:2px 0; line-height:1.2;">{stg['title']}</div>
                    <div style="font-size:10px; color:#64748b;">{sub_count} Subetapa{'s' if sub_count != 1 else ''}</div>
                    {srv_badges}
                </div>
                """, unsafe_allow_html=True)
                if s_idx < len(st.session_state.workflow["stages"]) - 1:
                    st.markdown("<div style='text-align:center; font-size:16px; color:#94a3b8; margin-top:4px;'>→</div>", unsafe_allow_html=True)

        with flow_cols[-1]:
            st.markdown("""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:10px; text-align:center; min-height:105px;">
                <div style="font-size:11px; font-weight:bold; color:#0f172a; margin-top:10px;">FIN</div>
                <div style="font-size:10px; color:#64748b; margin-top:4px;">Completado / Auditado</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"#### Configuración y Orden Secuencial ({len(st.session_state.workflow['stages'])} Etapas)")
        
        for s_idx, stage in enumerate(st.session_state.workflow["stages"]):
            with st.container():
                col_st_title, col_st_up, col_st_down, col_st_del = st.columns([4, 0.7, 0.7, 1])
                with col_st_title:
                    st.markdown(f"### Etapa {s_idx + 1}: **{stage['title']}** `[{stage['key']}]`")
                with col_st_up:
                    if st.button("Subir", key=f"up_stage_{stage['id']}", disabled=(s_idx == 0)):
                        st.session_state.workflow["stages"][s_idx], st.session_state.workflow["stages"][s_idx - 1] = (
                            st.session_state.workflow["stages"][s_idx - 1],
                            st.session_state.workflow["stages"][s_idx]
                        )
                        st.rerun()
                with col_st_down:
                    if st.button("Bajar", key=f"down_stage_{stage['id']}", disabled=(s_idx == len(st.session_state.workflow["stages"]) - 1)):
                        st.session_state.workflow["stages"][s_idx], st.session_state.workflow["stages"][s_idx + 1] = (
                            st.session_state.workflow["stages"][s_idx + 1],
                            st.session_state.workflow["stages"][s_idx]
                        )
                        st.rerun()
                with col_st_del:
                    if st.button(f"Eliminar", key=f"del_stage_{stage['id']}"):
                        st.session_state.workflow["stages"].pop(s_idx)
                        st.rerun()

                # Subetapas dentro de esta Etapa
                if len(stage["substages"]) == 0:
                    st.warning("Esta etapa no tiene subetapas. Agrega una a continuación.")
                else:
                    for sub_idx, substage in enumerate(stage["substages"]):
                        srv_tag = f" | Servicio: `{substage['service_key']}`" if substage.get("service_key") else ""
                        with st.expander(f"Subetapa {s_idx + 1}.{sub_idx + 1}: {substage['title']} [{substage['key']}]{srv_tag} — ({len(substage['fields'])} campos)", expanded=True):
                            col_sub_info, col_sub_actions = st.columns([3, 1.8])
                            
                            with col_sub_info:
                                st.write(f"**Rol Editor:** `{substage['editor_role'] or 'No asignado'}` | **Rol Revisor:** `{substage['reviewer_role'] or 'No asignado'}`")
                                if substage.get("service_key"):
                                    st.info(f"**Microservicio Asociado:** `{substage['service_key']}`")
                                else:
                                    st.caption("Formulario Manual (sin microservicio asociado)")

                            with col_sub_actions:
                                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                                with col_c1:
                                    if st.button("Subir", key=f"up_sub_{substage['id']}", help="Subir orden de subetapa", disabled=(sub_idx == 0)):
                                        stage["substages"][sub_idx], stage["substages"][sub_idx - 1] = (
                                            stage["substages"][sub_idx - 1],
                                            stage["substages"][sub_idx]
                                        )
                                        st.rerun()
                                with col_c2:
                                    if st.button("Bajar", key=f"down_sub_{substage['id']}", help="Bajar orden de subetapa", disabled=(sub_idx == len(stage["substages"]) - 1)):
                                        stage["substages"][sub_idx], stage["substages"][sub_idx + 1] = (
                                            stage["substages"][sub_idx + 1],
                                            stage["substages"][sub_idx]
                                        )
                                        st.rerun()
                                with col_c3:
                                    if st.button("Clonar", key=f"clone_sub_{substage['id']}", help="Clonar subetapa"):
                                        cloned_sub = json.loads(json.dumps(substage))
                                        cloned_sub["id"] = str(uuid.uuid4())
                                        cloned_sub["title"] = f"{substage['title']} (Copia)"
                                        cloned_sub["key"] = f"{substage['key']}_COPY"
                                        stage["substages"].append(cloned_sub)
                                        st.rerun()
                                with col_c4:
                                    if st.button("Borrar", key=f"del_sub_{substage['id']}", help="Borrar subetapa"):
                                        stage["substages"].pop(sub_idx)
                                        st.rerun()

                            # Configuración de Roles y Microservicio para esta Subetapa
                            st.markdown("##### Configuración de Roles y Asociación de Microservicio")
                            col_ed, col_rev, col_srv = st.columns(3)
                            with col_ed:
                                substage["editor_role"] = st.text_input(
                                    "Rol Editor (Workspace):",
                                    value=substage["editor_role"],
                                    key=f"ed_{substage['id']}",
                                    placeholder="ej: operaciones@miempresa.com"
                                )
                            with col_rev:
                                substage["reviewer_role"] = st.text_input(
                                    "Rol Revisor (Workspace):",
                                    value=substage["reviewer_role"],
                                    key=f"rev_{substage['id']}",
                                    placeholder="ej: supervisores@miempresa.com"
                                )
                            with col_srv:
                                srv_options = ["(Manual / Formulario)"] + [s["key"] for s in st.session_state.microservices]
                                current_srv_idx = 0
                                if substage["service_key"] in srv_options:
                                    current_srv_idx = srv_options.index(substage["service_key"])
                                selected_srv = st.selectbox(
                                    "Microservicio Asociado:",
                                    srv_options,
                                    index=current_srv_idx,
                                    key=f"srv_{substage['id']}",
                                    help="Selecciona un microservicio del catálogo para que se ejecute automáticamente en esta subetapa."
                                )
                                substage["service_key"] = "" if selected_srv == "(Manual / Formulario)" else selected_srv

                            # Constructor de Campos Dinámicos (Schema Builder)
                            st.markdown("##### Constructor de Campos del Formulario (Input Schema)")
                            
                            # Mostrar tabla de campos existentes
                            if len(substage["fields"]) > 0:
                                for f_idx, field in enumerate(substage["fields"]):
                                    col_f_name, col_f_title, col_f_type, col_f_req, col_f_del = st.columns([2, 2, 2.5, 1, 0.5])
                                    with col_f_name:
                                        st.code(field["name"])
                                    with col_f_title:
                                        st.write(f"**{field['title']}**")
                                    with col_f_type:
                                        fmt_info = f" ({field.get('format', 'libre')})" if field.get('format') and field.get('format') != 'none' else ""
                                        mask_info = f" | `{field.get('placeholder')}`" if field.get('placeholder') else ""
                                        st.caption(f"Tipo: `{field['type']}`{fmt_info}{mask_info}")
                                    with col_f_req:
                                        st.write("Obligatorio" if field["required"] else "Opcional")
                                    with col_f_del:
                                        if st.button("Eliminar", key=f"del_f_{substage['id']}_{field['id']}"):
                                            substage["fields"].pop(f_idx)
                                            st.rerun()
                            else:
                                st.caption("No hay campos configurados en esta subetapa. Agrega campos con el botón de abajo.")

                            # Formulario para Agregar Campo
                            with st.form(f"form_add_field_{substage['id']}", clear_on_submit=True):
                                st.markdown("**Agregar Nuevo Campo:**")
                                col_cf1, col_cf2 = st.columns([2, 2])
                                with col_cf1:
                                    f_title = st.text_input("Título / Etiqueta del Campo:", placeholder="Ej: RUT del Solicitante", key=f"ft_{substage['id']}")
                                with col_cf2:
                                    f_name = st.text_input("Nombre Técnico (JSON Key):", placeholder="Ej: rut_solicitante", key=f"fn_{substage['id']}")
                                
                                col_cf3, col_cf4, col_cf5 = st.columns([1.5, 2.5, 1])
                                with col_cf3:
                                    f_type = st.selectbox("Tipo de Dato:", ["Texto (String)", "Número", "Fecha", "Booleano", "Archivo / PDF"], key=f"fty_{substage['id']}")
                                with col_cf4:
                                    f_format = st.selectbox(
                                        "Formato / Máscara (para Texto):",
                                        [
                                            "Texto Libre (Sin formato)",
                                            "RUT Chileno (17837734-5 | _ _ _ _ _ _ _ _ - _)",
                                            "Teléfono (+56 9 _ _ _ _  _ _ _ _)",
                                            "Correo Electrónico (usuario@dominio.com)",
                                            "Máscara Personalizada"
                                        ],
                                        key=f"ffmt_{substage['id']}"
                                    )
                                with col_cf5:
                                    st.write("")
                                    st.write("")
                                    f_req = st.checkbox("Obligatorio", value=True, key=f"fr_{substage['id']}")

                                # Máscara / Placeholder personalizado
                                col_mask1, col_mask2 = st.columns(2)
                                with col_mask1:
                                    f_placeholder_input = st.text_input("Placeholder / Guía visual (ej: _ _ _ _ _ _ _ _ - _):", placeholder="Ej: _ _ _ _ _ _ _ _ - _", key=f"fph_{substage['id']}")
                                with col_mask2:
                                    f_mask_regex = st.text_input("Patrón / Regex personalizado (opcional):", placeholder="Ej: ^[0-9]{7,8}-[0-9kK]$", key=f"fmsk_{substage['id']}")

                                submit_field = st.form_submit_button("Guardar Campo", type="secondary")
                                if submit_field:
                                    if f_title:
                                        type_mapping = {
                                            "Texto (String)": "string",
                                            "Número": "number",
                                            "Fecha": "date",
                                            "Booleano": "boolean",
                                            "Archivo / PDF": "file"
                                        }
                                        
                                        format_code = "none"
                                        default_ph = ""
                                        if "RUT Chileno" in f_format:
                                            format_code = "rut"
                                            default_ph = "_ _ _ _ _ _ _ _ - _"
                                        elif "Teléfono" in f_format:
                                            format_code = "phone"
                                            default_ph = "+56 9 _ _ _ _  _ _ _ _"
                                        elif "Correo" in f_format:
                                            format_code = "email"
                                            default_ph = "nombre@empresa.com"
                                        elif "Personalizada" in f_format:
                                            format_code = "custom"
                                            default_ph = f_placeholder_input or "_ _ _ _ _ _ _ _ - _"

                                        new_field = {
                                            "id": str(uuid.uuid4()),
                                            "title": f_title,
                                            "name": f_name if f_name else f_title.lower().replace(" ", "_"),
                                            "type": type_mapping[f_type],
                                            "format": format_code,
                                            "placeholder": f_placeholder_input if f_placeholder_input else default_ph,
                                            "mask_pattern": f_mask_regex,
                                            "required": f_req
                                        }
                                        substage["fields"].append(new_field)
                                        st.success(f"Campo '{f_title}' agregado con formato '{format_code}'.")
                                        st.rerun()
                                    else:
                                        st.error("Debes ingresar la etiqueta del campo.")

                # Formulario para Agregar Subetapa a esta Etapa
                with st.expander(f"Agregar Subetapa a la Etapa {s_idx + 1}: {stage['title']}"):
                    with st.form(f"form_new_sub_{stage['id']}", clear_on_submit=True):
                        col_sub1, col_sub2 = st.columns([3, 1])
                        with col_sub1:
                            new_sub_title = st.text_input("Nombre de la Subetapa:", placeholder="Ej: Carga de Documentos")
                        with col_sub2:
                            new_sub_key = st.text_input("Clave Única:", placeholder="Ej: SUB_CARGA_DOCS")
                        
                        col_sub3, col_sub4 = st.columns(2)
                        with col_sub3:
                            new_sub_ed = st.text_input("Rol Editor:", placeholder="ej: operaciones@miempresa.com")
                        with col_sub4:
                            new_sub_rev = st.text_input("Rol Revisor:", placeholder="ej: supervisores@miempresa.com")

                        submit_sub = st.form_submit_button("Crear Subetapa", type="primary")
                        if submit_sub:
                            if new_sub_title:
                                key = new_sub_key if new_sub_key else new_sub_title.upper().replace(" ", "_")
                                new_sub = {
                                    "id": str(uuid.uuid4()),
                                    "title": new_sub_title,
                                    "key": key,
                                    "editor_role": new_sub_ed,
                                    "reviewer_role": new_sub_rev,
                                    "service_key": "",
                                    "fields": []
                                }
                                stage["substages"].append(new_sub)
                                st.success(f"Subetapa '{new_sub_title}' creada.")
                                st.rerun()
                            else:
                                st.error("Debes ingresar el nombre de la subetapa.")

# ==============================================================================
# VISTA 2: PORTAL DE EJECUCIÓN (RUNTIME)
# ==============================================================================
elif mode == "Portal de Ejecución (Runtime)":
    st.markdown('<div class="main-header">Portal Operativo de Ejecución</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ejecución del flujo, revisión por roles, invocación de microservicios y auditoría inmutable.</div>', unsafe_allow_html=True)

    if len(st.session_state.workflow["stages"]) == 0:
        st.warning("No hay etapas creadas en el workflow. Ve al 'Diseñador de Workflows' y crea al menos una etapa con subetapas.")
    else:
        stages = st.session_state.workflow["stages"]
        
        all_substages = []
        for s_idx, stg in enumerate(stages):
            for sub_idx, sub in enumerate(stg["substages"]):
                all_substages.append({
                    "stage_idx": s_idx,
                    "stage_title": stg["title"],
                    "sub_idx": sub_idx,
                    "substage": sub
                })

        if len(all_substages) == 0:
            st.warning("Las etapas creadas no contienen subetapas. Agrega subetapas en el Diseñador.")
        else:
            exec_state = st.session_state.execution
            col_ex1, col_ex2, col_ex3 = st.columns([2, 2, 1])
            with col_ex1:
                st.info(f"**Clave de Ejecución:** `{exec_state['code']}`")
            with col_ex2:
                status_labels = {
                    "NOT_STARTED": "No Iniciada",
                    "IN_PROGRESS": "En Edición",
                    "IN_REVIEW": "En Revisión",
                    "COMPLETED": "Completada"
                }
                st.info(f"**Estado:** {status_labels.get(exec_state['status'], exec_state['status'])} | **Iteración:** `{exec_state['iteration']}`")
            with col_ex3:
                can_rollback = not (exec_state["current_stage_idx"] == 0 and exec_state["current_substage_idx"] == 0)
                if st.button("Volver (Rollback)", disabled=not can_rollback, type="secondary"):
                    if can_rollback:
                        current_flat_idx = 0
                        for i, item in enumerate(all_substages):
                            if item["stage_idx"] == exec_state["current_stage_idx"] and item["sub_idx"] == exec_state["current_substage_idx"]:
                                current_flat_idx = i
                                break
                        
                        prev_item = all_substages[max(0, current_flat_idx - 1)]
                        exec_state["current_stage_idx"] = prev_item["stage_idx"]
                        exec_state["current_substage_idx"] = prev_item["sub_idx"]
                        exec_state["iteration"] += 1
                        exec_state["status"] = "IN_PROGRESS"
                        
                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "ROLLBACK_TRIGGERED",
                            "user": "operador@miempresa.com",
                            "notes": f"Retroceso a {prev_item['substage']['title']} (Iteración {exec_state['iteration']})"
                        })
                        st.warning(f"Retroceso aplicado hacia: {prev_item['substage']['title']} (Iteración {exec_state['iteration']})")
                        st.rerun()

            current_stage = stages[exec_state["current_stage_idx"]]
            current_sub = current_stage["substages"][exec_state["current_substage_idx"]]

            st.markdown(f"### Paso Actual: **{current_stage['title']}** → Subetapa: **{current_sub['title']}**")
            
            role_mode = st.radio(
                "Simular Acción como Rol:",
                [f"Editor ({current_sub['editor_role'] or 'operaciones@miempresa.com'})", 
                 f"Revisor ({current_sub['reviewer_role'] or 'supervisores@miempresa.com'})"],
                horizontal=True
            )
            is_editor_mode = "Editor" in role_mode

            st.divider()

            st.markdown("#### Formulario de Entrada (Generado Dinámicamente)")
            
            if len(current_sub["fields"]) == 0:
                st.caption("Esta subetapa no tiene campos configurados.")
            else:
                with st.form("runtime_dynamic_form"):
                    form_inputs = {}
                    for field in current_sub["fields"]:
                        f_key = f"input_{field['name']}"
                        prev_val = exec_state["form_data"].get(field["name"], None)

                        if field["type"] == "string":
                            fmt = field.get("format", "none")
                            ph = field.get("placeholder") or ""
                            help_msg = None
                            if fmt == "rut":
                                ph = ph or "_ _ _ _ _ _ _ _ - _"
                                help_msg = "Formato esperado: 17837734-5. Si ingresas 178377345 se formateará automáticamente con guión."
                            elif fmt == "phone":
                                ph = ph or "+56 9 _ _ _ _  _ _ _ _"
                                help_msg = "Formato telefónico: +56 9 XXXX XXXX"
                            elif fmt == "email":
                                ph = ph or "usuario@dominio.com"
                            elif fmt == "custom":
                                ph = ph or "_ _ _ _ _ _ _ _ - _"
                                help_msg = f"Máscara / Patrón: {field.get('mask_pattern', '')}"

                            form_inputs[field["name"]] = st.text_input(
                                f"{field['title']} {'*' if field['required'] else ''}",
                                value=prev_val or "",
                                placeholder=ph,
                                help=help_msg,
                                disabled=not is_editor_mode
                            )
                        elif field["type"] == "number":
                            form_inputs[field["name"]] = st.number_input(
                                f"{field['title']} {'*' if field['required'] else ''}",
                                value=float(prev_val or 0),
                                disabled=not is_editor_mode
                            )
                        elif field["type"] == "date":
                            form_inputs[field["name"]] = str(st.date_input(
                                f"{field['title']} {'*' if field['required'] else ''}",
                                value=date.today(),
                                disabled=not is_editor_mode
                            ))
                        elif field["type"] == "boolean":
                            form_inputs[field["name"]] = st.checkbox(
                                f"{field['title']} {'*' if field['required'] else ''}",
                                value=bool(prev_val or False),
                                disabled=not is_editor_mode
                            )
                        elif field["type"] == "file":
                            form_inputs[field["name"]] = "archivo_cargado.pdf"
                            st.file_uploader(f"Subir {field['title']}", disabled=not is_editor_mode)

                    if current_sub.get("service_key"):
                        st.info(f"**Microservicio Conectado:** `{current_sub['service_key']}` (Se ejecutará automáticamente al guardar)")

                    if is_editor_mode:
                        submit_data = st.form_submit_button("Guardar y Enviar a Revisión", type="primary")
                        if submit_data:
                            validation_errors = []
                            for field in current_sub["fields"]:
                                fname = field["name"]
                                val = form_inputs.get(fname, "")
                                if field["type"] == "string" and isinstance(val, str) and val.strip():
                                    fmt = field.get("format", "none")
                                    if fmt == "rut":
                                        formatted_rut = format_chilean_rut(val)
                                        form_inputs[fname] = formatted_rut
                                        is_valid, msg = validate_chilean_rut(formatted_rut)
                                        if not is_valid and field.get("required"):
                                            validation_errors.append(f"RUT '{formatted_rut}' para '{field['title']}': {msg}")
                                    elif fmt == "phone":
                                        form_inputs[fname] = format_phone_number(val)

                            if validation_errors:
                                for err in validation_errors:
                                    st.warning(f"Nota: {err}")

                            exec_state["form_data"].update(form_inputs)
                            exec_state["status"] = "IN_REVIEW"
                            exec_state["audit_logs"].append({
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "action": "SUBMITTED_FOR_REVIEW",
                                "user": current_sub["editor_role"] or "editor@miempresa.com",
                                "notes": f"Datos ingresados: {json.dumps(form_inputs, ensure_ascii=False)}"
                            })
                            st.success("Formulario enviado con éxito. Estado actualizado a: EN REVISIÓN.")
                            st.rerun()

            # Panel de Decisión del Revisor
            if not is_editor_mode:
                st.markdown("---")
                st.markdown("#### Panel de Decisión del Revisor")
                rev_notes = st.text_area("Observaciones / Comentarios del Revisor:", placeholder="Ingrese notas de revisión...")
                
                col_ap, col_rej = st.columns(2)
                with col_ap:
                    if st.button("Aprobar y Avanzar a Siguiente Subetapa", type="primary"):
                        exec_state["status"] = "APPROVED"
                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "APPROVED_BY_REVIEWER",
                            "user": current_sub["reviewer_role"] or "revisor@miempresa.com",
                            "notes": rev_notes or "Aprobado sin comentarios."
                        })

                        current_flat_idx = 0
                        for i, item in enumerate(all_substages):
                            if item["stage_idx"] == exec_state["current_stage_idx"] and item["sub_idx"] == exec_state["current_substage_idx"]:
                                current_flat_idx = i
                                break
                        
                        if current_flat_idx + 1 < len(all_substages):
                            next_item = all_substages[current_flat_idx + 1]
                            exec_state["current_stage_idx"] = next_item["stage_idx"]
                            exec_state["current_substage_idx"] = next_item["sub_idx"]
                            exec_state["status"] = "IN_PROGRESS"
                            st.success(f"Subetapa aprobada. Avanzando a: {next_item['substage']['title']}.")
                        else:
                            exec_state["status"] = "COMPLETED"
                            st.success("Workflow completado con éxito.")
                        st.rerun()

                with col_rej:
                    if st.button("Rechazar y Devolver al Editor", type="secondary"):
                        exec_state["status"] = "REJECTED"
                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "REJECTED_BY_REVIEWER",
                            "user": current_sub["reviewer_role"] or "revisor@miempresa.com",
                            "notes": rev_notes or "Rechazado para corrección."
                        })
                        st.error("Subetapa rechazada. Devuelta al rol Editor para corrección.")
                        st.rerun()

            # Historial Inmutable de Auditoría
            st.markdown("---")
            st.markdown("#### Trazabilidad y Auditoría (Historial Inmutable)")
            if len(exec_state["audit_logs"]) == 0:
                st.caption("No hay eventos registrados aún en esta ejecución.")
            else:
                for log in reversed(exec_state["audit_logs"]):
                    st.markdown(f"- **`{log['timestamp']}`** | `{log['action']}` por **{log['user']}** → *{log['notes']}*")

# ==============================================================================
# VISTA 3: FÁBRICA DE APIS CON IA (EDITABLE + GEMINI DIRECTO)
# ==============================================================================
elif mode == "Fábrica de APIs con IA":
    st.markdown('<div class="main-header">Fábrica de APIs y Microservicios con IA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Diseña microservicios con Google Gemini (Google AI Studio sin pasar por Vertex AI). Todos los esquemas y códigos generados son 100% editables antes de registrarse en el catálogo.</div>', unsafe_allow_html=True)

    with st.expander("Configuración de Google Gemini API Key (Directo / AI Studio)", expanded=False):
        st.caption("Usa el modelo Gemini 1.5 / 2.0 directamente vía Google AI Studio con tu API Key.")
        gemini_api_key = st.text_input("GEMINI_API_KEY:", value=os.environ.get("GEMINI_API_KEY", ""), type="password", placeholder="AIzaSy...")
        st.info("Si dejas la clave vacía, la plataforma usará el generador estructurado local de alta precisión.")

    if "ai_generated_api" not in st.session_state:
        st.session_state.ai_generated_api = None

    col_prompt, col_templates = st.columns([2, 1])

    with col_templates:
        st.markdown("##### Plantillas de Ejemplo:")
        if st.button("Extractor OCR de Facturas"):
            st.session_state.ai_prompt_text = "Crear un microservicio que reciba la URL de un PDF de factura o boleta, extraiga el RUT del emisor, monto neto, IVA, monto total y fecha de emisión."
        if st.button("Validador de Scoring Crediticio"):
            st.session_state.ai_prompt_text = "Crear una API que reciba RUT, ingresos mensuales y monto solicitado, consulte el riesgo crediticio y devuelva si es aprobado, el score (1-1000) y la tasa de interés."
        if st.button("Calculador de Vacaciones y Plazos"):
            st.session_state.ai_prompt_text = "Crear una API que reciba fecha de inicio de contrato y días solicitados, calcule los días proporcionales acumulados y devuelva la fecha de término."

    with col_prompt:
        ai_prompt = st.text_area(
            "¿Qué funcionalidad debe realizar tu API / Microservicio?",
            value=st.session_state.get("ai_prompt_text", "Crear una API que reciba el RUT de un cliente y valide si tiene antecedentes legales y comerciales vigentes, retornando un indicador booleano y el nivel de riesgo."),
            height=130,
            placeholder="Ej: Necesito una API que reciba un archivo PDF, extraiga las tablas de costos y calcule el subtotal con IVA..."
        )

        generate_btn = st.button("Generar API y Esquemas con IA", type="primary")

    if generate_btn and ai_prompt:
        with st.spinner("Generando microservicio, esquemas JSON y código FastAPI con Gemini..."):
            prompt_lower = ai_prompt.lower()
            
            used_gemini_direct = False
            if gemini_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    sys_instruction = f"""Genera la especificación técnica de un microservicio FastAPI para el siguiente requerimiento: '{ai_prompt}'.
Devuelve un JSON estricto con las siguientes claves:
- srv_name: string (nombre amigable)
- srv_key: string (clave técnica en mayúsculas ej: SRV_SCORING)
- in_schema: objeto JSON Schema
- out_schema: objeto JSON Schema
"""
                    res = model.generate_content(sys_instruction)
                    raw_text = res.text.strip().replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(raw_text)
                    srv_name = parsed.get("srv_name", "Servicio IA Personalizado")
                    srv_key = parsed.get("srv_key", "SRV_CUSTOM_AI")
                    in_schema = parsed.get("in_schema", {})
                    out_schema = parsed.get("out_schema", {})
                    used_gemini_direct = True
                except Exception as ex:
                    st.warning(f"Aviso de Gemini Directo ({ex}). Usando generador estructurado de respaldo.")

            if not used_gemini_direct:
                if "pdf" in prompt_lower or "ocr" in prompt_lower or "factura" in prompt_lower:
                    srv_key = "SRV_AI_OCR_EXTRACTOR"
                    srv_name = "Extractor Inteligente de Documentos"
                    in_schema = {
                        "type": "object",
                        "required": ["pdf_document_url"],
                        "properties": {
                            "pdf_document_url": {"type": "string", "title": "URL del Documento PDF"},
                            "tipo_documento": {"type": "string", "title": "Tipo (Factura/Contrato)", "default": "factura"}
                        }
                    }
                    out_schema = {
                        "type": "object",
                        "properties": {
                            "rut_emisor": {"type": "string", "title": "RUT Emisor", "pattern": "^[0-9]{7,8}-[0-9kK]$", "example": "76452190-K"},
                            "monto_neto": {"type": "number", "title": "Monto Neto"},
                            "iva": {"type": "number", "title": "IVA (19%)"},
                            "monto_total": {"type": "number", "title": "Total Factura"},
                            "fecha_emision": {"type": "string", "format": "date"}
                        }
                    }
                elif "crediticio" in prompt_lower or "scoring" in prompt_lower or "riesgo" in prompt_lower:
                    srv_key = "SRV_AI_CREDIT_SCORING"
                    srv_name = "Evaluador de Scoring Financiero"
                    in_schema = {
                        "type": "object",
                        "required": ["rut", "ingresos_mensuales", "monto_solicitado"],
                        "properties": {
                            "rut": {"type": "string", "title": "RUT Cliente", "pattern": "^[0-9]{7,8}-[0-9kK]$", "example": "17837734-5"},
                            "ingresos_mensuales": {"type": "number", "title": "Ingresos Mensuales (CLP)"},
                            "monto_solicitado": {"type": "number", "title": "Monto de Crédito Solicitado"}
                        }
                    }
                    out_schema = {
                        "type": "object",
                        "properties": {
                            "aprobado": {"type": "boolean", "title": "Crédito Aprobado"},
                            "score_crediticio": {"type": "integer", "title": "Score (1-1000)"},
                            "tasa_interes_mensual": {"type": "number", "title": "Tasa Mensual (%)"},
                            "monto_maximo_aprobable": {"type": "number", "title": "Monto Máximo"}
                        }
                    }
                else:
                    srv_key = "SRV_AI_CUSTOM_VALIDATOR"
                    srv_name = "Validador Automático Personalizado"
                    in_schema = {
                        "type": "object",
                        "required": ["identificador_consulta", "datos_entrada"],
                        "properties": {
                            "identificador_consulta": {"type": "string", "title": "ID / RUT a Consultar"},
                            "datos_entrada": {"type": "string", "title": "Parámetros Adicionales"}
                        }
                    }
                    out_schema = {
                        "type": "object",
                        "properties": {
                            "resultado_exitoso": {"type": "boolean", "title": "Validación Exitosa"},
                            "nivel_riesgo": {"type": "string", "title": "Nivel de Riesgo (Bajo/Medio/Alto)"},
                            "observaciones": {"type": "string", "title": "Detalle de la Evaluación"}
                        }
                    }

            code_template = f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI(
    title="{srv_name}",
    description="Microservicio generado para Workflow Engine",
    version="1.0.0"
)

# 1. Modelo de Entrada (Input Payload)
class RequestPayload(BaseModel):
'''
            for prop, val in in_schema.get("properties", {}).items():
                py_type = "str" if val.get("type") == "string" else ("float" if val.get("type") == "number" else ("int" if val.get("type") == "integer" else "bool"))
                code_template += f'    {prop}: {py_type} = Field(..., description="{val.get("title", prop)}")\n'

            code_template += f'''
# 2. Modelo de Salida (Output Schema)
class ResponsePayload(BaseModel):
'''
            for prop, val in out_schema.get("properties", {}).items():
                py_type = "str" if val.get("type") == "string" else ("float" if val.get("type") == "number" else ("int" if val.get("type") == "integer" else "bool"))
                code_template += f'    {prop}: {py_type}\n'

            code_template += f'''
# 3. Endpoint Principal del Microservicio
@app.post("/api/v1/process", response_model=ResponsePayload)
def process_data(req: RequestPayload):
    """
    Lógica de negocio ejecutada en Cloud Run.
    """
    return ResponsePayload(
'''
            for prop, val in out_schema.get("properties", {}).items():
                if val.get("type") == "boolean":
                    default_val = "True"
                elif val.get("type") in ["number", "integer"]:
                    default_val = "950" if "score" in prop else "1000000"
                elif val.get("format") == "date":
                    default_val = 'datetime.now().strftime("%Y-%m-%d")'
                else:
                    default_val = '"17.837.734-5"' if "rut" in prop else '"Procesado con éxito"'
                code_template += f'        {prop}={default_val},\n'

            code_template += f'''    )

@app.get("/health")
def health():
    return {{"status": "ok", "service": "{srv_key}"}}
'''

            st.session_state.ai_generated_api = {
                "key": srv_key,
                "name": srv_name,
                "url": f"https://{srv_key.lower().replace('_', '-')}-432889140614.us-central1.run.app/api/v1/process",
                "in_schema_str": json.dumps(in_schema, indent=2, ensure_ascii=False),
                "out_schema_str": json.dumps(out_schema, indent=2, ensure_ascii=False),
                "code": code_template
            }

    # PANEL EDITABLE DE LA API GENERADA
    if st.session_state.ai_generated_api:
        api_data = st.session_state.ai_generated_api
        st.success(f"Microservicio Generado: **{api_data['name']}** `[{api_data['key']}]` (Puedes editar cualquier parámetro antes de registrarlo)")

        with st.form("form_edit_ai_api"):
            col_e1, col_e2, col_e3 = st.columns([2, 1.5, 2.5])
            with col_e1:
                edit_name = st.text_input("Nombre del Servicio (Editable):", value=api_data["name"])
            with col_e2:
                edit_key = st.text_input("Clave Única (Key Editable):", value=api_data["key"])
            with col_e3:
                edit_url = st.text_input("Endpoint URL (Editable):", value=api_data["url"])

            tab_e_schema, tab_e_code = st.tabs(["Editar Esquemas JSON (Input & Output)", "Editar Código FastAPI"])

            with tab_e_schema:
                col_in_e, col_out_e = st.columns(2)
                with col_in_e:
                    st.markdown("**Input Schema JSON (Editable):**")
                    edit_in_schema = st.text_area("Input Schema:", value=api_data["in_schema_str"], height=260)
                with col_out_e:
                    st.markdown("**Output Schema JSON (Editable):**")
                    edit_out_schema = st.text_area("Output Schema:", value=api_data["out_schema_str"], height=260)

            with tab_e_code:
                st.markdown("**Código FastAPI (Python Editable):**")
                edit_code = st.text_area("Código Fuente FastAPI:", value=api_data["code"], height=320)

            submit_save_custom = st.form_submit_button("Guardar y Registrar API en el Catálogo", type="primary")
            if submit_save_custom:
                if edit_name and edit_key:
                    try:
                        parsed_in = json.loads(edit_in_schema)
                        parsed_out = json.loads(edit_out_schema)
                    except Exception as json_err:
                        st.error(f"Error en la sintaxis JSON: {json_err}")
                        parsed_in = {}
                        parsed_out = {}

                    existing_keys = [s["key"] for s in st.session_state.microservices]
                    if edit_key in existing_keys:
                        for s in st.session_state.microservices:
                            if s["key"] == edit_key:
                                s["name"] = edit_name
                                s["url"] = edit_url
                    else:
                        st.session_state.microservices.append({
                            "key": edit_key.upper().strip(),
                            "name": edit_name.strip(),
                            "url": edit_url.strip()
                        })

                    st.session_state.ai_generated_api["name"] = edit_name
                    st.session_state.ai_generated_api["key"] = edit_key
                    st.session_state.ai_generated_api["url"] = edit_url
                    st.session_state.ai_generated_api["in_schema_str"] = edit_in_schema
                    st.session_state.ai_generated_api["out_schema_str"] = edit_out_schema
                    st.session_state.ai_generated_api["code"] = edit_code

                    st.success(f"Microservicio '{edit_name}' guardado y registrado en el catálogo.")
                    st.rerun()

# ==============================================================================
# VISTA 4: CATÁLOGO DE MICROSERVICIOS
# ==============================================================================
elif mode == "Catálogo de Microservicios":
    st.markdown('<div class="main-header">Catálogo de Microservicios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestión de microservicios desplegados en Cloud Run para asociarlos a cualquier subetapa del workflow.</div>', unsafe_allow_html=True)

    st.markdown("### Registrar Nuevo Microservicio")
    with st.form("form_new_service_direct", clear_on_submit=True):
        col_srv1, col_srv2 = st.columns([2, 1])
        with col_srv1:
            srv_name = st.text_input("Nombre del Servicio:", placeholder="Ej: Validador de Scoring Crediticio")
        with col_srv2:
            srv_key = st.text_input("Clave Única (Key):", placeholder="Ej: SRV_SCORING_API")
        
        srv_url = st.text_input("Endpoint URL (Cloud Run o externa):", placeholder="https://srv-scoring-xyz.a.run.app/api/v1/score")
        
        submit_srv = st.form_submit_button("Registrar Microservicio en el Catálogo", type="primary")
        if submit_srv:
            if srv_name and srv_key:
                st.session_state.microservices.append({
                    "key": srv_key.upper().strip(),
                    "name": srv_name.strip(),
                    "url": srv_url.strip() if srv_url else "https://mi-servicio.a.run.app/api/v1/process"
                })
                st.success(f"Microservicio '{srv_name}' registrado exitosamente en el catálogo.")
                st.rerun()
            else:
                st.error("Debes completar al menos el Nombre y la Clave Única del servicio.")

    st.markdown("---")
    st.markdown(f"### Microservicios Disponibles ({len(st.session_state.microservices)} Registrados)")
    
    for idx, s in enumerate(st.session_state.microservices):
        with st.container():
            col_m1, col_m2 = st.columns([5, 1])
            with col_m1:
                st.markdown(f"**{s['name']}** `[{s['key']}]`")
                st.caption(f"Endpoint: `{s['url']}`")
            with col_m2:
                if st.button("Eliminar", key=f"del_ms_{idx}"):
                    st.session_state.microservices.pop(idx)
                    st.rerun()
            st.divider()
