import streamlit as st
import streamlit.components.v1 as components
import json
import uuid
import os
import html
from datetime import datetime, date

# Configuración de Página
st.set_page_config(
    page_title="Workflow Studio | Cloud Engine",
    layout="wide",
    initial_sidebar_state="collapsed"
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
# DATOS DE EJEMPLO (SERIE Y PARALELO + MICROSERVICIOS)
# ==============================================================================
EXAMPLE_STAGES = [
    {
        "id": "stg-01",
        "title": "Admisión y Validación de Identidad",
        "key": "ETAPA_ADMISION",
        "mode": "SERIES",
        "track": "Principal",
        "substages": [
            {
                "id": "sub-1-1",
                "title": "Ingreso de Datos y RUT",
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
                "title": "Cálculo de Plazos",
                "key": "SUB_CALC_DIAS",
                "editor_role": "operaciones@miempresa.com",
                "reviewer_role": "jefe.operaciones@miempresa.com",
                "service_key": "SRV_DATE_CALCULATOR",
                "fields": [
                    {
                        "id": "f-1-2-1",
                        "title": "Fecha de Inicio",
                        "name": "fecha_inicio",
                        "type": "date",
                        "required": True
                    },
                    {
                        "id": "f-1-2-2",
                        "title": "Días Hábiles",
                        "name": "dias_habiles",
                        "type": "number",
                        "required": True
                    }
                ]
            }
        ]
    },
    {
        "id": "stg-02a",
        "title": "Evaluación Técnica (OCR)",
        "key": "ETAPA_OCR_TECNICA",
        "mode": "PARALLEL",
        "track": "Track A (Técnico)",
        "substages": [
            {
                "id": "sub-2-1",
                "title": "Extracción OCR de Documentos",
                "key": "SUB_OCR_EXTRACT",
                "editor_role": "analista.tecnico@miempresa.com",
                "reviewer_role": "supervisor.tecnico@miempresa.com",
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
            }
        ]
    },
    {
        "id": "stg-02b",
        "title": "Evaluación Financiera (Scoring)",
        "key": "ETAPA_SCORING_FINANCIERO",
        "mode": "PARALLEL",
        "track": "Track B (Financiero)",
        "substages": [
            {
                "id": "sub-2-2",
                "title": "Scoring Crediticio",
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
                        "title": "Ingresos Mensuales (CLP)",
                        "name": "ingresos_mensuales",
                        "type": "number",
                        "required": True
                    }
                ]
            }
        ]
    },
    {
        "id": "stg-03",
        "title": "Aprobación y Contrato",
        "key": "ETAPA_APROBACION_LEGAL",
        "mode": "SERIES",
        "track": "Principal",
        "substages": [
            {
                "id": "sub-3-1",
                "title": "Generación de Contrato",
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
                "title": "Firma Electrónica",
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
        "name": "Workflow de Admisión y Evaluación",
        "tenant": "MI_EMPRESA",
        "code": "WF_ONBOARDING",
        "stages": json.loads(json.dumps(EXAMPLE_STAGES))
    }

if "selected_stage_idx" not in st.session_state:
    st.session_state.selected_stage_idx = 0

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
    /* 1. Ocultar barra lateral de Streamlit por completo para máxima amplitud */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* 2. Maximizar el ancho y optimizar paddings */
    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    .main-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.82rem;
        color: #64748b;
        margin-bottom: 1rem;
    }

    /* 3. Estilo de Pestañas / Barra Horizontal para st.radio */
    div[data-testid="stRadio"] {
        margin-bottom: 8px !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        align-items: center !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #475569 !important;
        cursor: pointer !important;
        transition: all 0.15s ease-in-out !important;
        margin-bottom: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"],
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: #0f172a !important;
        color: #ffffff !important;
        border-color: #0f172a !important;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.15) !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) * {
        color: #ffffff !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# STEPPER VISUAL SENCILLO PARA EL PORTAL DEL CLIENTE (FRONT-END)
# ==============================================================================
def render_client_stepper(stages, current_stage_idx, current_status):
    if not stages:
        return ""
    
    total = len(stages)
    items_html = []
    
    for idx, stg in enumerate(stages):
        is_completed = (current_status == "COMPLETED") or (idx < current_stage_idx)
        is_active = (current_status != "COMPLETED") and (idx == current_stage_idx)
        
        if is_completed:
            circle_bg = "#10b981"
            circle_color = "#ffffff"
            circle_icon = "✓"
            text_color = "#0f172a"
            badge_text = "Completado"
            badge_bg = "#dcfce7"
            badge_fg = "#166534"
        elif is_active:
            circle_bg = "#2563eb"
            circle_color = "#ffffff"
            circle_icon = str(idx + 1)
            text_color = "#1d4ed8"
            badge_text = "Paso Actual"
            badge_bg = "#dbeafe"
            badge_fg = "#1e40af"
        else:
            circle_bg = "#e2e8f0"
            circle_color = "#64748b"
            circle_icon = str(idx + 1)
            text_color = "#94a3b8"
            badge_text = "Pendiente"
            badge_bg = "#f1f5f9"
            badge_fg = "#64748b"

        title = stg["title"]
        if len(title) > 22:
            title = title[:20] + ".."

        item = (
            f'<div style="flex:1; text-align:center; position:relative; min-width:130px; padding:0 8px;">'
            f'<div style="width:36px; height:36px; border-radius:50%; background:{circle_bg}; color:{circle_color}; '
            f'display:flex; align-items:center; justify-content:center; margin:0 auto 8px auto; '
            f'font-weight:700; font-size:14px; box-shadow:0 2px 4px rgba(0,0,0,0.08);">{circle_icon}</div>'
            f'<div style="font-size:12px; font-weight:{"700" if is_active else "600"}; color:{text_color}; '
            f'line-height:1.25; margin-bottom:5px;">{title}</div>'
            f'<span style="font-size:9.5px; font-weight:700; background:{badge_bg}; color:{badge_fg}; '
            f'padding:2px 8px; border-radius:10px; display:inline-block;">{badge_text}</span>'
            f'</div>'
        )
        items_html.append(item)

    stepper_html = (
        f'<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:18px 12px; '
        f'margin:10px 0 20px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03); overflow-x:auto;">'
        f'<div style="display:flex; align-items:flex-start; justify-content:space-between; min-width:550px;">'
        f'{"".join(items_html)}'
        f'</div>'
        f'</div>'
    )
    return stepper_html

# ==============================================================================
# AUTENTICACIÓN Y GESTIÓN DE ROLES (RBAC)
# ==============================================================================
ROLES_DEF = {
    "CLIENTE": {
        "label": "Cliente Final (Solicitante)",
        "email": "cliente@usuario.cl",
        "name": "Juan Pérez González",
        "role_badge": "CLIENTE",
        "allowed_views": [
            "Portal del Cliente (Front-End)",
            "Seguimiento de Mi Solicitud"
        ]
    },
    "OPERADOR": {
        "label": "Operador / Revisor Interno",
        "email": "operaciones@miempresa.com",
        "name": "Carolina Soto (Operaciones)",
        "role_badge": "OPERADOR",
        "allowed_views": [
            "Bandeja de Operaciones (Revisión)",
            "Portal del Cliente (Front-End)"
        ]
    },
    "ADMIN": {
        "label": "Administrador (Studio Completo)",
        "email": "admin@miempresa.com",
        "name": "Administrador del Sistema",
        "role_badge": "ADMINISTRADOR",
        "allowed_views": [
            "Diseñador de Workflows (Studio)",
            "Portal de Ejecución (Runtime)",
            "Portal del Cliente (Front-End)",
            "Bandeja de Operaciones (Revisión)",
            "Fábrica de APIs con IA",
            "Catálogo de Microservicios"
        ]
    }
}

if "auth_user_key" not in st.session_state:
    st.session_state.auth_user_key = "ADMIN"

# ==============================================================================
# BARRA DE TAREAS SUPERIOR HORIZONTAL (HEADER Y NAVEGACIÓN)
# ==============================================================================
with st.container():
    col_brand, col_role, col_user, col_actions = st.columns([2.8, 2.6, 3.0, 2.2])

    with col_brand:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:8px; padding-top:2px;">
            <div style="background:#0f172a; color:#38bdf8; width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:16px;">⚡</div>
            <div>
                <div style="font-size:14.5px; font-weight:700; color:#0f172a; line-height:1.2;">Workflow Studio</div>
                <div style="font-size:10.5px; color:#64748b;">Cloud Engine • Empresa Demo</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_role:
        selected_role_key = st.selectbox(
            "Perfil de Acceso:",
            options=["ADMIN", "CLIENTE", "OPERADOR"],
            format_func=lambda k: f"{'⚙️' if k=='ADMIN' else ('👤' if k=='CLIENTE' else '🛡️')} {ROLES_DEF[k]['label']}",
            index=["ADMIN", "CLIENTE", "OPERADOR"].index(st.session_state.auth_user_key),
            help="Cambia entre la Consola de Administración, Portal del Cliente o Bandeja de Operaciones",
            label_visibility="collapsed"
        )
        st.session_state.auth_user_key = selected_role_key
        current_user = ROLES_DEF[selected_role_key]

    with col_user:
        badge_bg = '#f1f5f9' if selected_role_key=='ADMIN' else ('#dbeafe' if selected_role_key=='CLIENTE' else '#fef3c7')
        badge_fg = '#0f172a' if selected_role_key=='ADMIN' else ('#1e40af' if selected_role_key=='CLIENTE' else '#92400e')
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:flex-end; gap:8px; padding-top:4px;">
            <div style="text-align:right;">
                <div style="font-size:12px; font-weight:700; color:#1e293b;">{current_user['name']}</div>
                <div style="font-size:10.5px; color:#64748b;">{current_user['email']}</div>
            </div>
            <span style="background:{badge_bg}; color:{badge_fg}; font-size:10.5px; font-weight:700; padding:3px 8px; border-radius:6px; border:1px solid #cbd5e1;">
                {current_user['role_badge']}
            </span>
            <span style="background:#e0f2fe; color:#0369a1; font-size:10.5px; font-weight:700; padding:3px 8px; border-radius:6px; border:1px solid #bae6fd;">
                APIs: {len(st.session_state.microservices)}
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col_actions:
        if selected_role_key == "ADMIN":
            ca1, ca2 = st.columns(2)
            with ca1:
                if st.button("Cargar Ejemplo", help="Cargar flujo de ejemplo", key="btn_load_example_top", use_container_width=True):
                    st.session_state.workflow["stages"] = json.loads(json.dumps(EXAMPLE_STAGES))
                    st.session_state.selected_stage_idx = 0
                    st.session_state.execution["status"] = "NOT_STARTED"
                    st.session_state.execution["current_stage_idx"] = 0
                    st.session_state.execution["current_substage_idx"] = 0
                    st.session_state.execution["form_data"] = {}
                    st.success("Ejemplo cargado.")
                    st.rerun()
            with ca2:
                if st.button("Vaciar Todo", help="Dejar el flujo en blanco", key="btn_clear_all_top", use_container_width=True):
                    st.session_state.workflow["stages"] = []
                    st.session_state.selected_stage_idx = 0
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

    # Fila 2: Barra de navegación horizontal por pestañas
    views_for_role = current_user["allowed_views"]
    if "active_view" not in st.session_state or st.session_state.active_view not in views_for_role:
        st.session_state.active_view = views_for_role[0]

    mode = st.radio(
        "Navegación:",
        options=views_for_role,
        index=views_for_role.index(st.session_state.active_view),
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.active_view = mode

# ==============================================================================
# VISTA 1: DISEÑADOR DE WORKFLOWS (STUDIO VISUAL INTERACTIVO)
# ==============================================================================
if mode == "Diseñador de Workflows (Studio)":
    studio_path = os.path.join(os.path.dirname(__file__), "static_studio.html")
    if os.path.exists(studio_path):
        with open(studio_path, "r", encoding="utf-8") as f:
            studio_html = f.read()
        components.html(studio_html, height=920, scrolling=False)
    else:
        st.error("No se encontró el archivo compilado `static_studio.html`.")

# ==============================================================================
# VISTA 2: PORTAL DE EJECUCIÓN (RUNTIME)
# ==============================================================================
elif mode == "Portal de Ejecución (Runtime)":
    st.markdown('<div class="main-header">Portal Operativo de Ejecución</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ejecución del flujo en serie o paralelo, revisión por roles, invocación de microservicios y auditoría inmutable.</div>', unsafe_allow_html=True)

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
                    "stage_mode": stg.get("mode", "SERIES"),
                    "stage_track": stg.get("track", "Principal"),
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
            mode_badge = f"[{current_stage.get('mode', 'SERIES')} - {current_stage.get('track', 'Principal')}]"

            st.markdown(f"### Paso Actual: **{current_stage['title']}** `{mode_badge}` → Subetapa: **{current_sub['title']}**")
            
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

# ==============================================================================
# VISTA: PORTAL DEL CLIENTE (FRONT-END SENCILLO)
# ==============================================================================
elif mode in ["Portal del Cliente (Ejecutar Trámite)", "Portal del Cliente (Front-End)", "Portal del Cliente (Vista Previa)"]:
    exec_state = st.session_state.execution
    stages = st.session_state.workflow["stages"]

    header_html = (
        f'<div style="background:linear-gradient(135deg, #0f172a, #1e293b); border-radius:12px; padding:22px 26px; color:white; margin-bottom:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div>'
        f'<span style="background:#2563eb; color:white; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; padding:3px 8px; border-radius:4px;">Portal de Autoservicio Digital</span>'
        f'<h2 style="margin:8px 0 4px 0; color:white; font-size:1.5rem; font-weight:700;">{st.session_state.workflow["name"]}</h2>'
        f'<p style="margin:0; font-size:13px; color:#94a3b8;">Completa la información solicitada en cada paso. Tu avance se procesa en tiempo real.</p>'
        f'</div>'
        f'<div style="text-align:right; background:rgba(255,255,255,0.06); padding:8px 16px; border-radius:8px; border:1px solid rgba(255,255,255,0.12);">'
        f'<div style="font-size:10px; color:#94a3b8; text-transform:uppercase;">N° de Trámite</div>'
        f'<div style="font-size:16px; font-weight:700; color:#60a5fa;">{exec_state["code"]}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    if hasattr(st, "html"):
        st.html(header_html)
    else:
        st.markdown(header_html, unsafe_allow_html=True)

    if not stages:
        st.info("El flujo aún no tiene etapas configuradas. Un administrador debe diseñar el workflow primero.")
    else:
        # STEPPER VISUAL SENCILLO
        stepper_html = render_client_stepper(stages, exec_state["current_stage_idx"], exec_state["status"])
        if hasattr(st, "html"):
            st.html(stepper_html)
        else:
            st.markdown(stepper_html, unsafe_allow_html=True)

        # Barra de progreso
        if exec_state["status"] == "COMPLETED":
            pct = 1.0
        else:
            pct = min(1.0, max(0.05, (exec_state["current_stage_idx"]) / max(1, len(stages))))
        st.progress(pct, text=f"Progreso del trámite: {int(pct * 100)}%")

        # CASO 1: COMPLETADO
        if exec_state["status"] == "COMPLETED":
            st.markdown("""
            <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:12px; padding:36px 24px; text-align:center; margin:20px 0;">
                <div style="font-size:48px; margin-bottom:8px;">🎉</div>
                <h2 style="color:#166534; margin:0 0 8px 0;">¡Trámite Completado con Éxito!</h2>
                <p style="color:#374151; font-size:14px; max-width:550px; margin:0 auto 16px auto;">
                    Tu solicitud ha sido aprobada y procesada satisfactoriamente en todas sus etapas.
                </p>
            </div>
            """, unsafe_allow_html=True)
            col_c1, col_c2 = st.columns([1.2, 0.8])
            with col_c1:
                st.markdown("#### Datos de la Solicitud Finalizada:")
                for k, v in exec_state["form_data"].items():
                    st.write(f"- **{k.replace('_', ' ').capitalize()}:** `{v}`")
            with col_c2:
                st.markdown("#### Comprobante Oficial:")
                st.info(f"**Código de Ticket:** `{exec_state['code']}`  \n**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n**Resolución:** Aprobado")
                if st.button("Iniciar un Nuevo Trámite", type="primary", use_container_width=True):
                    st.session_state.execution = {
                        "code": f"EXEC-{datetime.utcnow().year}-{uuid.uuid4().hex[:5].upper()}",
                        "status": "NOT_STARTED",
                        "current_stage_idx": 0,
                        "current_substage_idx": 0,
                        "iteration": 1,
                        "form_data": {},
                        "context_data": {},
                        "audit_logs": []
                    }
                    st.rerun()

        # CASO 2: EN REVISIÓN POR OPERACIONES
        elif exec_state["status"] == "IN_REVIEW":
            current_stage = stages[exec_state["current_stage_idx"]]
            st.markdown(f"""
            <div style="background:#eff6ff; border:1.5px solid #bfdbfe; border-radius:12px; padding:36px 20px; text-align:center; margin:20px 0;">
                <div style="font-size:44px; margin-bottom:10px;">📋</div>
                <h3 style="color:#1e3a8a; margin:0 0 8px 0;">¡Antecedentes Recibidos con Éxito!</h3>
                <p style="color:#475569; font-size:14px; max-width:560px; margin:0 auto 16px auto;">
                    Hemos recibido correctamente tus datos correspondientes a <b>{current_stage['title']}</b>. Nuestro equipo de Operaciones está validando la información ingresada.
                </p>
                <div style="display:inline-block; background:#ffffff; border:1.5px solid #93c5fd; border-radius:24px; padding:8px 22px; font-size:13.5px; font-weight:700; color:#0284c7;">
                    Estado: En Revisión por Supervisor
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 **Información para el Operador:** Para evaluar y aprobar esta solicitud, cambia el selector de perfil a **'Operador / Revisor Interno'** en la barra de tareas superior.")

        # CASO 3: EN EDICIÓN POR EL CLIENTE
        else:
            current_stage = stages[exec_state["current_stage_idx"]]
            sub_list = current_stage.get("substages", [])
            
            if not sub_list:
                st.info(f"El paso '{current_stage['title']}' no requiere datos adicionales del cliente.")
                if st.button("Continuar →", type="primary"):
                    if exec_state["current_stage_idx"] + 1 < len(stages):
                        exec_state["current_stage_idx"] += 1
                        exec_state["current_substage_idx"] = 0
                    else:
                        exec_state["status"] = "COMPLETED"
                    st.rerun()
            else:
                current_sub = sub_list[min(exec_state["current_substage_idx"], len(sub_list) - 1)]

                if exec_state["status"] == "REJECTED":
                    last_log = exec_state["audit_logs"][-1] if exec_state["audit_logs"] else {}
                    obs = last_log.get("notes", "Por favor revisa y actualiza los antecedentes solicitados.")
                    st.warning(f"⚠️ **Observación del Revisor:** {obs}  \nPor favor corrige los datos a continuación y vuelve a enviar.")

                st.markdown(f"### {current_stage['title']}")
                st.caption(f"Paso {exec_state['current_stage_idx'] + 1} de {len(stages)} — {current_sub['title']}")

                with st.form(f"form_client_step_{current_stage['id']}_{current_sub['id']}"):
                    form_answers = {}
                    for field in current_sub["fields"]:
                        f_name = field["name"]
                        f_title = field["title"]
                        f_type = field.get("type", "string")
                        f_format = field.get("format", "none")
                        prev_val = exec_state["form_data"].get(f_name, "")

                        if f_format == "rut":
                            raw_val = st.text_input(f"{f_title} (* Obligatorio)" if field.get("required") else f_title, value=prev_val, placeholder="17837734-5", help="Ingresa tu RUT (ej: 17837734-5 o 178377345)")
                            norm_rut = format_chilean_rut(raw_val)
                            if norm_rut:
                                is_v, msg = validate_chilean_rut(norm_rut)
                                if is_v:
                                    st.caption(f"✓ Formato válido: `{norm_rut}`")
                                else:
                                    st.caption(f"⚠️ {msg}")
                            form_answers[f_name] = norm_rut
                        elif f_format == "email":
                            form_answers[f_name] = st.text_input(f"{f_title} (* Obligatorio)" if field.get("required") else f_title, value=prev_val, placeholder="nombre@correo.com")
                        elif f_format == "phone":
                            raw_ph = st.text_input(f"{f_title} (* Obligatorio)" if field.get("required") else f_title, value=prev_val, placeholder="+56 9 1234 5678")
                            form_answers[f_name] = format_phone_number(raw_ph)
                        elif f_type in ["date"]:
                            form_answers[f_name] = str(st.date_input(f_title, value=date.today()))
                        elif f_type in ["number", "integer"]:
                            form_answers[f_name] = st.number_input(f_title, value=float(prev_val) if prev_val else 0.0)
                        elif f_type in ["boolean"]:
                            form_answers[f_name] = st.checkbox(f_title, value=bool(prev_val))
                        elif f_type in ["file", "pdf"]:
                            uploaded = st.file_uploader(f"Adjuntar {f_title} (PDF o imagen):", type=["pdf", "png", "jpg", "jpeg"])
                            if uploaded:
                                form_answers[f_name] = f"archivo_{uploaded.name}"
                                st.caption(f"✓ Documento adjuntado: `{uploaded.name}` ({uploaded.size // 1024} KB)")
                            else:
                                form_answers[f_name] = prev_val or "documento_adjunto.pdf"
                        else:
                            form_answers[f_name] = st.text_input(f"{f_title} (* Obligatorio)" if field.get("required") else f_title, value=prev_val, placeholder=field.get("placeholder", ""))

                    submitted = st.form_submit_button("Continuar al Siguiente Paso →", type="primary", use_container_width=True)
                    if submitted:
                        exec_state["form_data"].update(form_answers)
                        
                        if current_sub.get("service_key"):
                            srv_key = current_sub["service_key"]
                            exec_state["audit_logs"].append({
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "action": f"MICROSERVICE_EXECUTED: {srv_key}",
                                "user": "Sistema",
                                "notes": f"Ejecutado automáticamente para {current_sub['title']}"
                            })

                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "SUBMITTED_BY_CLIENT",
                            "user": current_user["email"],
                            "notes": f"Datos ingresados en {current_stage['title']}"
                        })

                        if current_sub.get("reviewer_role"):
                            exec_state["status"] = "IN_REVIEW"
                        else:
                            if exec_state["current_substage_idx"] + 1 < len(sub_list):
                                exec_state["current_substage_idx"] += 1
                                exec_state["status"] = "IN_PROGRESS"
                            elif exec_state["current_stage_idx"] + 1 < len(stages):
                                exec_state["current_stage_idx"] += 1
                                exec_state["current_substage_idx"] = 0
                                exec_state["status"] = "IN_PROGRESS"
                            else:
                                exec_state["status"] = "COMPLETED"

                        st.rerun()

# ==============================================================================
# VISTA: SEGUIMIENTO DE MI SOLICITUD (CLIENTE)
# ==============================================================================
elif mode in ["Seguimiento de Mi Solicitud", "Seguimiento de Mi Trámite"]:
    exec_state = st.session_state.execution
    stages = st.session_state.workflow["stages"]

    st.markdown('<div class="main-header">Seguimiento de Mi Solicitud</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Consulta en tiempo real el avance y las resoluciones de tu trámite digital.</div>', unsafe_allow_html=True)

    col_tk1, col_tk2 = st.columns([3, 1])
    with col_tk1:
        st.text_input("Número de Trámite o Ticket:", value=exec_state["code"], disabled=True)
    with col_tk2:
        status_badges = {
            "NOT_STARTED": "⏳ No Iniciada",
            "IN_PROGRESS": "📝 En Edición",
            "IN_REVIEW": "🔍 En Revisión por Operaciones",
            "REJECTED": "⚠️ Requiere Corrección",
            "COMPLETED": "✅ Aprobada y Finalizada"
        }
        st.write("**Estado Actual:**")
        st.info(status_badges.get(exec_state["status"], exec_state["status"]))

    stepper_html = render_client_stepper(stages, exec_state["current_stage_idx"], exec_state["status"])
    if hasattr(st, "html"):
        st.html(stepper_html)
    else:
        st.markdown(stepper_html, unsafe_allow_html=True)

    st.markdown("#### Historial de Eventos:")
    if not exec_state["audit_logs"]:
        st.caption("No hay eventos registrados aún.")
    else:
        for log in reversed(exec_state["audit_logs"]):
            st.markdown(f"- **`{log['timestamp']}`** | `{log['action']}` → *{log['notes']}*")

# ==============================================================================
# VISTA: BANDEJA DE OPERACIONES (OPERADOR / REVISOR INTERNO)
# ==============================================================================
elif mode in ["Bandeja de Operaciones (Revisión)", "Bandeja de Operaciones"]:
    exec_state = st.session_state.execution
    stages = st.session_state.workflow["stages"]

    st.markdown('<div class="main-header">Bandeja de Operaciones y Aprobaciones</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestión de solicitudes recibidas, validación de antecedentes y resoluciones de aprobación o rechazo.</div>', unsafe_allow_html=True)

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Trámites Activos", "1 Caso", delta="En curso")
    with col_m2:
        is_pending_review = (exec_state["status"] == "IN_REVIEW")
        st.metric("Pendientes de Revisión", "1 Pendiente" if is_pending_review else "0 Pendientes")
    with col_m3:
        is_done = (exec_state["status"] == "COMPLETED")
        st.metric("Completados / Aprobados", "1 Caso" if is_done else "0 Casos")

    st.markdown("---")
    st.markdown(f"### Solicitud Activa: `{exec_state['code']}`")
    
    if not stages:
        st.info("No hay workflow configurado.")
    else:
        current_stage = stages[exec_state["current_stage_idx"]]
        sub_list = current_stage.get("substages", [])
        current_sub = sub_list[min(exec_state["current_substage_idx"], len(sub_list) - 1)] if sub_list else None

        col_st1, col_st2 = st.columns([2, 1])
        with col_st1:
            st.write(f"**Etapa Actual:** `{current_stage['title']}` | **Subetapa:** `{current_sub['title'] if current_sub else 'N/A'}`")
            st.write(f"**Estado de la Solicitud:** `{exec_state['status']}`")
        with col_st2:
            if current_sub and current_sub.get("service_key"):
                st.success(f"Microservicio: `{current_sub['service_key']}`")

        st.markdown("#### Datos Enviados por el Cliente:")
        if not exec_state["form_data"]:
            st.caption("El cliente aún no ha enviado antecedentes para esta solicitud.")
        else:
            col_d1, col_d2 = st.columns(2)
            items = list(exec_state["form_data"].items())
            mid = (len(items) + 1) // 2
            with col_d1:
                for k, v in items[:mid]:
                    st.write(f"**{k.replace('_', ' ').title()}:** `{v}`")
            with col_d2:
                for k, v in items[mid:]:
                    st.write(f"**{k.replace('_', ' ').title()}:** `{v}`")

        # PANEL DE APROBACIÓN / RESOLUCIÓN
        st.markdown("---")
        st.markdown("#### Resolución de Operaciones")

        if exec_state["status"] != "IN_REVIEW":
            if exec_state["status"] == "COMPLETED":
                st.success("✅ Esta solicitud ya fue aprobada y completada.")
            else:
                st.info(f"Esta solicitud está en estado `{exec_state['status']}`. Esperando envío del cliente para revisión.")
        else:
            rev_notes = st.text_area("Observaciones del Revisor:", placeholder="Escribe observaciones para el cliente o registro de auditoría...", key="op_notes")
            col_ap, col_rej = st.columns(2)
            with col_ap:
                if st.button("✓ Aprobar y Avanzar Trámite", type="primary", use_container_width=True):
                    exec_state["audit_logs"].append({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "action": "APPROVED_BY_OPERATOR",
                        "user": current_user["email"],
                        "notes": rev_notes or "Aprobado conforme por el operador"
                    })

                    # Avanzar a siguiente subetapa o etapa
                    if exec_state["current_substage_idx"] + 1 < len(sub_list):
                        exec_state["current_substage_idx"] += 1
                        exec_state["status"] = "IN_PROGRESS"
                    elif exec_state["current_stage_idx"] + 1 < len(stages):
                        exec_state["current_stage_idx"] += 1
                        exec_state["current_substage_idx"] = 0
                        exec_state["status"] = "IN_PROGRESS"
                    else:
                        exec_state["status"] = "COMPLETED"

                    st.success("Solicitud aprobada con éxito.")
                    st.rerun()

            with col_rej:
                if st.button("✗ Devolver al Cliente para Corrección", type="secondary", use_container_width=True):
                    exec_state["status"] = "REJECTED"
                    exec_state["audit_logs"].append({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "action": "RETURNED_BY_OPERATOR",
                        "user": current_user["email"],
                        "notes": rev_notes or "Se requieren correcciones de antecedentes"
                    })
                    st.warning("Solicitud devuelta al cliente con observaciones.")
                    st.rerun()

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
