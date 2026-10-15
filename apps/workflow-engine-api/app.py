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
            "Portal del Cliente (Ejecutar Trámite)",
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
            "Portal del Cliente (Vista Previa)"
        ]
    },
    "ADMIN": {
        "label": "Administrador (Studio Completo)",
        "email": "admin@miempresa.com",
        "name": "Administrador del Sistema",
        "role_badge": "ADMINISTRADOR",
        "allowed_views": [
            "Portal del Cliente (Front-End)",
            "Bandeja de Operaciones (Revisión)",
            "Diseñador de Workflows",
            "Fábrica de APIs con IA",
            "Catálogo de Microservicios"
        ]
    }
}

if "auth_user_key" not in st.session_state:
    st.session_state.auth_user_key = "CLIENTE"

st.sidebar.markdown("### Perfil de Acceso")
selected_role_key = st.sidebar.selectbox(
    "Acceder como:",
    options=["CLIENTE", "OPERADOR", "ADMIN"],
    format_func=lambda k: f"{'👤' if k=='CLIENTE' else ('🛡️' if k=='OPERADOR' else '⚙️')} {ROLES_DEF[k]['label']}",
    index=["CLIENTE", "OPERADOR", "ADMIN"].index(st.session_state.auth_user_key),
    help="Cambia entre el Portal del Cliente, Bandeja de Operaciones o Consola de Administración"
)
st.session_state.auth_user_key = selected_role_key
current_user = ROLES_DEF[selected_role_key]

st.sidebar.caption(f"**Usuario:** `{current_user['name']}`  \n**Email:** `{current_user['email']}`")
st.sidebar.divider()

views_for_role = current_user["allowed_views"]
if "active_view" not in st.session_state or st.session_state.active_view not in views_for_role:
    st.session_state.active_view = views_for_role[0]

mode = st.sidebar.radio(
    "Navegación:",
    views_for_role,
    index=views_for_role.index(st.session_state.active_view) if st.session_state.active_view in views_for_role else 0
)
st.session_state.active_view = mode

# Opciones de administración adicionales en la barra lateral si es Admin
if selected_role_key == "ADMIN":
    st.sidebar.divider()
    st.sidebar.markdown(f"**Microservicios en Catálogo:** `{len(st.session_state.microservices)}`")
    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("Cargar Ejemplo", help="Cargar flujo de ejemplo"):
            st.session_state.workflow["stages"] = json.loads(json.dumps(EXAMPLE_STAGES))
            st.session_state.selected_stage_idx = 0
            st.session_state.execution["status"] = "NOT_STARTED"
            st.session_state.execution["current_stage_idx"] = 0
            st.session_state.execution["current_substage_idx"] = 0
            st.session_state.execution["form_data"] = {}
            st.success("Ejemplo cargado.")
            st.rerun()

    with col_btn2:
        if st.button("Vaciar Todo", help="Dejar el flujo en blanco"):
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

# ==============================================================================
# GENERADOR DE DIAGRAMA SVG CON CONECTORES REALES Y PLANO NAVEGABLE
# ==============================================================================
def generate_pipeline_svg(stages, selected_idx):
    if not stages:
        return "", 400, 150
    steps = []
    for s_idx, stg in enumerate(stages):
        is_parallel = (stg.get("mode") == "PARALLEL")
        if is_parallel and len(steps) > 0 and steps[-1]["type"] == "PARALLEL":
            steps[-1]["stages"].append((s_idx, stg))
        else:
            steps.append({
                "type": "PARALLEL" if is_parallel else "SERIES",
                "stages": [(s_idx, stg)]
            })

    card_w = 205
    card_h = 86
    start_end_w = 78
    start_end_h = 56
    gap_x = 65
    gap_y = 20

    max_branches = max([len(st["stages"]) for st in steps] or [1])
    total_h = max(190, max_branches * card_h + (max_branches - 1) * gap_y + 80)
    center_y = total_h / 2

    # Posiciones X de columnas
    col_x = [30]  # INICIO
    curr_x = 30 + start_end_w + gap_x
    for st in steps:
        col_x.append(curr_x)
        curr_x += card_w + gap_x
    fin_x = curr_x
    total_w = fin_x + start_end_w + 40

    col_nodes = []

    # 1. NODO INICIO
    inicio_y = center_y - start_end_h / 2
    col_nodes.append([{
        "type": "START",
        "x": col_x[0],
        "y": inicio_y,
        "w": start_end_w,
        "h": start_end_h,
        "in_x": col_x[0],
        "in_y": center_y,
        "out_x": col_x[0] + start_end_w,
        "out_y": center_y,
    }])

    # 2. NODOS DE ETAPAS
    for col_idx, step in enumerate(steps):
        k = len(step["stages"])
        block_h = k * card_h + (k - 1) * gap_y
        start_y = center_y - block_h / 2
        nodes_in_col = []
        for b_idx, (s_idx, stg) in enumerate(step["stages"]):
            ny = start_y + b_idx * (card_h + gap_y)
            nx = col_x[col_idx + 1]
            nodes_in_col.append({
                "type": "STAGE",
                "stage_idx": s_idx,
                "stage": stg,
                "x": nx,
                "y": ny,
                "w": card_w,
                "h": card_h,
                "in_x": nx,
                "in_y": ny + card_h / 2,
                "out_x": nx + card_w,
                "out_y": ny + card_h / 2,
                "is_selected": (s_idx == selected_idx)
            })
        col_nodes.append(nodes_in_col)

    # 3. NODO FIN
    fin_y = center_y - start_end_h / 2
    col_nodes.append([{
        "type": "END",
        "x": fin_x,
        "y": fin_y,
        "w": start_end_w,
        "h": start_end_h,
        "in_x": fin_x,
        "in_y": center_y,
        "out_x": fin_x + start_end_w,
        "out_y": center_y
    }])

    # GENERAR SVG
    svg_parts = [
        f'<svg width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui, -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; user-select:none; display:block;">',
        '<defs>',
        '  <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b" />',
        '  </marker>',
        '  <marker id="arrow-blue" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0284c7" />',
        '  </marker>',
        '  <filter id="shadow-active" x="-10%" y="-10%" width="130%" height="130%">',
        '    <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#2563eb" flood-opacity="0.35" />',
        '  </filter>',
        '  <filter id="shadow-card" x="-10%" y="-10%" width="120%" height="120%">',
        '    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.06" />',
        '  </filter>',
        '  <pattern id="grid-dots" width="20" height="20" patternUnits="userSpaceOnUse">',
        '    <circle cx="2" cy="2" r="1" fill="#cbd5e1" opacity="0.65" />',
        '  </pattern>',
        '</defs>',
        f'<rect width="{total_w}" height="{total_h}" fill="url(#grid-dots)" rx="8" />'
    ]

    # DIBUJAR CONECTORES ENTRE COLUMNAS CONSECUTIVAS
    for c in range(len(col_nodes) - 1):
        from_nodes = col_nodes[c]
        to_nodes = col_nodes[c + 1]

        if len(from_nodes) == 1 and len(to_nodes) == 1:
            fn = from_nodes[0]
            tn = to_nodes[0]
            if abs(fn["out_y"] - tn["in_y"]) < 2:
                svg_parts.append(f'<line x1="{fn["out_x"]}" y1="{fn["out_y"]}" x2="{tn["in_x"]}" y2="{tn["in_y"]}" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)" />')
            else:
                dx = (tn["in_x"] - fn["out_x"]) / 2
                svg_parts.append(f'<path d="M {fn["out_x"]} {fn["out_y"]} C {fn["out_x"] + dx} {fn["out_y"]}, {tn["in_x"] - dx} {tn["in_y"]}, {tn["in_x"]} {tn["in_y"]}" stroke="#64748b" stroke-width="2.5" fill="none" marker-end="url(#arrow)" />')

        elif len(from_nodes) == 1 and len(to_nodes) > 1:
            # Bifurcación en paralelo (Fork)
            fn = from_nodes[0]
            for tn in to_nodes:
                dx = (tn["in_x"] - fn["out_x"]) * 0.55
                svg_parts.append(f'<path d="M {fn["out_x"]} {fn["out_y"]} C {fn["out_x"] + dx} {fn["out_y"]}, {tn["in_x"] - dx} {tn["in_y"]}, {tn["in_x"]} {tn["in_y"]}" stroke="#0284c7" stroke-width="2.5" fill="none" marker-end="url(#arrow-blue)" />')

        elif len(from_nodes) > 1 and len(to_nodes) == 1:
            # Convergencia de paralelo a serie (Join)
            tn = to_nodes[0]
            for fn in from_nodes:
                dx = (tn["in_x"] - fn["out_x"]) * 0.55
                svg_parts.append(f'<path d="M {fn["out_x"]} {fn["out_y"]} C {fn["out_x"] + dx} {fn["out_y"]}, {tn["in_x"] - dx} {tn["in_y"]}, {tn["in_x"]} {tn["in_y"]}" stroke="#0284c7" stroke-width="2.5" fill="none" marker-end="url(#arrow-blue)" />')

        else:
            # Conexión múltiple
            for fn in from_nodes:
                for tn in to_nodes:
                    dx = (tn["in_x"] - fn["out_x"]) * 0.55
                    svg_parts.append(f'<path d="M {fn["out_x"]} {fn["out_y"]} C {fn["out_x"] + dx} {fn["out_y"]}, {tn["in_x"] - dx} {tn["in_y"]}, {tn["in_x"]} {tn["in_y"]}" stroke="#0284c7" stroke-width="1.8" stroke-dasharray="4" fill="none" marker-end="url(#arrow-blue)" />')

    # DIBUJAR NODOS
    for col in col_nodes:
        for node in col:
            ntype = node["type"]
            nx, ny, nw, nh = node["x"], node["y"], node["w"], node["h"]

            if ntype == "START":
                svg_parts.append(
                    f'<g>'
                    f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="10" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" filter="url(#shadow-card)" />'
                    f'<text x="{nx + nw/2}" y="{ny + 24}" font-size="11" font-weight="700" fill="#0f172a" text-anchor="middle">INICIO</text>'
                    f'<text x="{nx + nw/2}" y="{ny + 41}" font-size="9.5" fill="#64748b" text-anchor="middle">Disparo</text>'
                    f'</g>'
                )
            elif ntype == "END":
                svg_parts.append(
                    f'<g>'
                    f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="10" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" filter="url(#shadow-card)" />'
                    f'<text x="{nx + nw/2}" y="{ny + 24}" font-size="11" font-weight="700" fill="#0f172a" text-anchor="middle">FIN</text>'
                    f'<text x="{nx + nw/2}" y="{ny + 41}" font-size="9.5" fill="#64748b" text-anchor="middle">Cierre</text>'
                    f'</g>'
                )
            elif ntype == "STAGE":
                s_idx = node["stage_idx"]
                stg = node["stage"]
                is_sel = node["is_selected"]
                is_par = (stg.get("mode") == "PARALLEL")

                bg_fill = "#eff6ff" if is_sel else ("#f0f9ff" if is_par else "#ffffff")
                border_color = "#2563eb" if is_sel else ("#0284c7" if is_par else "#cbd5e1")
                border_width = "2.5" if is_sel else "1.5"
                filter_attr = 'filter="url(#shadow-active)"' if is_sel else 'filter="url(#shadow-card)"'

                title_safe = html.escape(stg["title"])
                if len(title_safe) > 22:
                    title_safe = title_safe[:20] + "..."

                sub_cnt = len(stg["substages"])
                srv_keys = [s["service_key"] for s in stg["substages"] if s.get("service_key")]
                sub_label = f"{sub_cnt} Subetapa{'s' if sub_cnt != 1 else ''}"
                srv_label = f"Srv: {srv_keys[0]}" if len(srv_keys) == 1 else (f"{len(srv_keys)} Servicios" if len(srv_keys) > 1 else "Manual")

                if is_par:
                    track_txt = html.escape(stg.get("track", "Paralelo"))
                    badge_bg = "#e0f2fe"
                    badge_fg = "#0369a1"
                    badge_label = f"PARALELO: {track_txt}"
                else:
                    badge_bg = "#f1f5f9"
                    badge_fg = "#475569"
                    badge_label = "SERIE"

                if len(badge_label) > 18:
                    badge_label = badge_label[:16] + ".."

                sel_indicator = ""
                if is_sel:
                    sel_indicator = (
                        f'<rect x="{nx + nw - 75}" y="{ny + 8}" width="68" height="17" rx="4" fill="#2563eb" />'
                        f'<text x="{nx + nw - 41}" y="{ny + 20}" font-size="8.5" font-weight="700" fill="#ffffff" text-anchor="middle">EDITANDO</text>'
                    )

                svg_parts.append(
                    f'<a href="?select_stage={s_idx}" target="_parent" style="text-decoration:none; cursor:pointer;">'
                    f'<g class="stage-card">'
                    f'<rect class="card-bg" x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="10" fill="{bg_fill}" stroke="{border_color}" stroke-width="{border_width}" {filter_attr} />'
                    f'<rect x="{nx + 8}" y="{ny + 8}" width="88" height="17" rx="4" fill="{badge_bg}" />'
                    f'<text x="{nx + 12}" y="{ny + 20}" font-size="8.5" font-weight="700" fill="{badge_fg}">{badge_label}</text>'
                    f'{sel_indicator}'
                    f'<text x="{nx + 10}" y="{ny + 44}" font-size="12" font-weight="700" fill="#0f172a">{title_safe}</text>'
                    f'<text x="{nx + 10}" y="{ny + 60}" font-size="9.5" fill="#64748b">{sub_label} • {srv_label}</text>'
                    f'<text x="{nx + 10}" y="{ny + 74}" font-size="8" fill="#2563eb" font-weight="600">Pincha para editar ↓</text>'
                    f'</g>'
                    f'</a>'
                )

    svg_parts.append('</svg>')
    return "".join(svg_parts), total_w, total_h

# ==============================================================================
# VISTA 1: DISEÑADOR VISUAL E INTERACTIVO (FOCUSED INSPECTOR)
# ==============================================================================
if mode == "Diseñador de Workflows":
    st.markdown('<div class="main-header">Diseñador de Workflows</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Selecciona cualquier etapa del diagrama para modificarla directamente en el panel inferior.</div>', unsafe_allow_html=True)

    col_name, col_code = st.columns([3, 1])
    with col_name:
        st.session_state.workflow["name"] = st.text_input("Nombre del Workflow:", value=st.session_state.workflow["name"])
    with col_code:
        st.session_state.workflow["code"] = st.text_input("Código Técnico:", value=st.session_state.workflow["code"])

    stages = st.session_state.workflow["stages"]

    # Sincronizar selección desde click en diagrama SVG (query param 'select_stage')
    if "select_stage" in st.query_params:
        try:
            target_idx = int(st.query_params["select_stage"])
            if 0 <= target_idx < len(stages):
                st.session_state.selected_stage_idx = target_idx
        except Exception:
            pass

    # Validar índice activo
    if len(stages) > 0:
        if st.session_state.selected_stage_idx >= len(stages):
            st.session_state.selected_stage_idx = max(0, len(stages) - 1)
        active_stage = stages[st.session_state.selected_stage_idx]
    else:
        active_stage = None

    st.markdown("---")

    # Botones superiores de adición
    col_hdr1, col_hdr2, col_hdr3 = st.columns([4.5, 2.5, 2.5])
    with col_hdr1:
        st.markdown("### Diagrama del Flujo (Pipeline Conectado)")
        st.caption("Desplázate horizontalmente por el plano para recorrer el flujo. Haz clic sobre cualquier cuadro para editarlo.")
    with col_hdr2:
        if st.button("+ Agregar Etapa en Serie", type="secondary", use_container_width=True):
            new_s = {
                "id": str(uuid.uuid4()),
                "title": f"Etapa {len(stages) + 1}",
                "key": f"ETAPA_{len(stages) + 1}",
                "mode": "SERIES",
                "track": "Principal",
                "substages": []
            }
            stages.append(new_s)
            st.session_state.selected_stage_idx = len(stages) - 1
            st.rerun()
    with col_hdr3:
        btn_par_disabled = (len(stages) == 0)
        if st.button("+ Añadir Paralelo (bajo nodo actual)", type="secondary", disabled=btn_par_disabled, use_container_width=True, help="Agrega un único bloque concurrente directamente bajo la etapa seleccionada"):
            curr_idx = st.session_state.selected_stage_idx
            curr_stg = stages[curr_idx]

            if curr_stg.get("mode") != "PARALLEL":
                curr_stg["mode"] = "PARALLEL"
                if not curr_stg.get("track") or curr_stg["track"] == "Principal":
                    curr_stg["track"] = "Track A"
                next_letter = "Track B"
                insert_pos = curr_idx + 1
            else:
                blk_start = curr_idx
                while blk_start > 0 and stages[blk_start - 1].get("mode") == "PARALLEL":
                    blk_start -= 1
                blk_end = curr_idx
                while blk_end < len(stages) - 1 and stages[blk_end + 1].get("mode") == "PARALLEL":
                    blk_end += 1
                num_in_blk = blk_end - blk_start + 1
                next_letter = f"Track {chr(ord('A') + num_in_blk)}" if num_in_blk < 26 else f"Track {num_in_blk + 1}"
                insert_pos = blk_end + 1

            new_branch = {
                "id": str(uuid.uuid4()),
                "title": f"{next_letter} - Nueva Rama",
                "key": f"ETAPA_PAR_{next_letter.replace(' ', '_').upper()}_{len(stages) + 1}",
                "mode": "PARALLEL",
                "track": next_letter,
                "substages": []
            }
            stages.insert(insert_pos, new_branch)
            st.session_state.selected_stage_idx = insert_pos
            st.rerun()

    # RENDER DEL PLANO NAVEGABLE CON CONECTORES
    if len(stages) == 0:
        st.info("El flujo está vacío. Agrega una etapa con los botones superiores o carga el ejemplo desde la barra lateral.")
    else:
        svg_content, total_w, total_h = generate_pipeline_svg(stages, st.session_state.selected_stage_idx)

        # Contenedor iframe interactivo: renderiza SVG sin sanitización y con scroll horizontal libre
        iframe_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 6px;
    background: transparent;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow-x: auto;
    overflow-y: hidden;
  }}
  .canvas-wrapper {{
    min-width: {total_w}px;
    width: {total_w}px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .stage-card:hover .card-bg {{
    stroke: #2563eb !important;
    stroke-width: 2.8px !important;
  }}
</style>
</head>
<body>
  <div class="canvas-wrapper">
    {svg_content}
  </div>
</body>
</html>"""
        components.html(iframe_doc, height=int(total_h + 45), scrolling=True)

        # NAVEGACIÓN Y ACCIONES RÁPIDAS DE ETAPAS
        st.write("**Navegación de Etapas (selecciona para editar):**")
        pill_cols = st.columns(min(len(stages), 7))
        for p_idx, s_item in enumerate(stages):
            is_active = (p_idx == st.session_state.selected_stage_idx)
            with pill_cols[p_idx % len(pill_cols)]:
                tag = f"[{s_item.get('track', 'P')}] " if s_item.get("mode") == "PARALLEL" else ""
                short_title = s_item['title'][:13] + '..' if len(s_item['title']) > 14 else s_item['title']
                btn_label = f"★ {p_idx+1}. {tag}{short_title}" if is_active else f"{p_idx+1}. {tag}{short_title}"
                if st.button(btn_label, key=f"nav_pill_{s_item['id']}", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state.selected_stage_idx = p_idx
                    st.rerun()

        # Acciones de la etapa activa
        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns([3, 2.5, 1.5, 1.5, 2])
        with col_act1:
            btn_add_par_lbl = f"+ Rama Paralela bajo '{active_stage['title'][:13]}..'" if len(active_stage['title']) > 13 else f"+ Rama Paralela bajo '{active_stage['title']}'"
            if st.button(btn_add_par_lbl, key="btn_act_add_par", use_container_width=True, help="Agrega un único bloque bajo esta etapa en el mismo grupo paralelo"):
                curr_idx = st.session_state.selected_stage_idx
                curr_stg = stages[curr_idx]
                if curr_stg.get("mode") != "PARALLEL":
                    curr_stg["mode"] = "PARALLEL"
                    if not curr_stg.get("track") or curr_stg["track"] == "Principal":
                        curr_stg["track"] = "Track A"
                    next_letter = "Track B"
                    insert_pos = curr_idx + 1
                else:
                    blk_start = curr_idx
                    while blk_start > 0 and stages[blk_start - 1].get("mode") == "PARALLEL":
                        blk_start -= 1
                    blk_end = curr_idx
                    while blk_end < len(stages) - 1 and stages[blk_end + 1].get("mode") == "PARALLEL":
                        blk_end += 1
                    num_in_blk = blk_end - blk_start + 1
                    next_letter = f"Track {chr(ord('A') + num_in_blk)}" if num_in_blk < 26 else f"Track {num_in_blk + 1}"
                    insert_pos = blk_end + 1

                new_branch = {
                    "id": str(uuid.uuid4()),
                    "title": f"{next_letter} - Nueva Rama",
                    "key": f"ETAPA_PAR_{next_letter.replace(' ', '_').upper()}_{len(stages) + 1}",
                    "mode": "PARALLEL",
                    "track": next_letter,
                    "substages": []
                }
                stages.insert(insert_pos, new_branch)
                st.session_state.selected_stage_idx = insert_pos
                st.rerun()

        with col_act2:
            if st.button("+ Insertar Serie después", key="btn_act_add_ser", use_container_width=True):
                new_s = {
                    "id": str(uuid.uuid4()),
                    "title": f"Etapa {len(stages) + 1}",
                    "key": f"ETAPA_{len(stages) + 1}",
                    "mode": "SERIES",
                    "track": "Principal",
                    "substages": []
                }
                stages.insert(st.session_state.selected_stage_idx + 1, new_s)
                st.session_state.selected_stage_idx += 1
                st.rerun()

        with col_act3:
            if st.button("← Mover antes", key="btn_act_mov_l", disabled=(st.session_state.selected_stage_idx == 0), use_container_width=True):
                idx = st.session_state.selected_stage_idx
                stages[idx], stages[idx - 1] = stages[idx - 1], stages[idx]
                st.session_state.selected_stage_idx = idx - 1
                st.rerun()

        with col_act4:
            if st.button("→ Mover después", key="btn_act_mov_r", disabled=(st.session_state.selected_stage_idx == len(stages) - 1), use_container_width=True):
                idx = st.session_state.selected_stage_idx
                stages[idx], stages[idx + 1] = stages[idx + 1], stages[idx]
                st.session_state.selected_stage_idx = idx + 1
                st.rerun()

        with col_act5:
            if st.button("Eliminar Etapa", key="btn_act_del", use_container_width=True):
                stages.pop(st.session_state.selected_stage_idx)
                st.session_state.selected_stage_idx = max(0, st.session_state.selected_stage_idx - 1)
                st.rerun()

        # ==============================================================================
        # BANNER DE EDICIÓN ACTIVA Y PANEL ENFOCADO DE LA ETAPA SELECCIONADA
        # ==============================================================================
        st.markdown("---")
        active_stage = stages[st.session_state.selected_stage_idx]

        banner_html = (
            f'<div id="stage-editor" style="background:linear-gradient(135deg, #1e3a8a, #2563eb); '
            f'border-radius:10px; padding:14px 20px; color:white; display:flex; justify-content:space-between; '
            f'align-items:center; box-shadow:0 4px 6px -1px rgba(37, 99, 235, 0.25); margin:10px 0 18px 0;">'
            f'<div>'
            f'<div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em; opacity:0.85;">Panel de Edición Activo</div>'
            f'<div style="font-size:19px; font-weight:700; margin-top:2px;">{active_stage["title"]} '
            f'<span style="font-size:13px; font-weight:500; opacity:0.9;">({active_stage.get("mode", "SERIES")} • {active_stage.get("track", "Principal")})</span></div>'
            f'</div>'
            f'<div style="background:rgba(255,255,255,0.2); border-radius:6px; padding:6px 14px; font-size:13px; font-weight:600;">'
            f'Etapa {st.session_state.selected_stage_idx + 1} de {len(stages)}'
            f'</div>'
            f'</div>'
        )
        if hasattr(st, "html"):
            st.html(banner_html)
        else:
            clean_banner = "\n".join(l.strip() for l in banner_html.splitlines() if l.strip())
            st.markdown(clean_banner, unsafe_allow_html=True)

        col_st_title, col_st_key, col_st_mode, col_st_track = st.columns([3, 2, 2, 2])
        with col_st_title:
            active_stage["title"] = st.text_input("Nombre de la Etapa:", value=active_stage["title"], key=f"inp_stg_title_{active_stage['id']}")
        with col_st_key:
            active_stage["key"] = st.text_input("Clave Técnica:", value=active_stage["key"], key=f"inp_stg_key_{active_stage['id']}")
        with col_st_mode:
            current_mode_idx = 0 if active_stage.get("mode") == "SERIES" else 1
            sel_mode = st.selectbox("Modo de Ejecución:", ["Serie (Secuencial)", "Paralelo (Bifurcación)"], index=current_mode_idx, key=f"inp_stg_mode_{active_stage['id']}")
            new_mode = "SERIES" if "Serie" in sel_mode else "PARALLEL"
            if new_mode != active_stage.get("mode"):
                active_stage["mode"] = new_mode
                if new_mode == "PARALLEL" and active_stage.get("track") == "Principal":
                    active_stage["track"] = "Track A"
                elif new_mode == "SERIES":
                    active_stage["track"] = "Principal"
                st.rerun()
        with col_st_track:
            if active_stage.get("mode") == "PARALLEL":
                active_stage["track"] = st.text_input("Nombre del Track:", value=active_stage.get("track", "Track A"), key=f"inp_stg_track_{active_stage['id']}")
            else:
                active_stage["track"] = "Principal"
                st.text_input("Track:", value="Principal (Serie)", disabled=True)

        # SUBETAPAS DE LA ETAPA SELECCIONADA
        st.markdown("#### Subetapas")
        if len(active_stage["substages"]) == 0:
            st.caption("Esta etapa aún no tiene subetapas. Agrega una subetapa con el formulario inferior.")
        else:
            for sub_idx, substage in enumerate(active_stage["substages"]):
                srv_tag = f" | Servicio: {substage['service_key']}" if substage.get("service_key") else " | Manual"
                with st.expander(f"Subetapa {sub_idx + 1}: {substage['title']} [{substage['key']}]{srv_tag} — ({len(substage['fields'])} campos)", expanded=True):
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
                            if st.button("Subir", key=f"btn_sub_up_{substage['id']}", disabled=(sub_idx == 0)):
                                active_stage["substages"][sub_idx], active_stage["substages"][sub_idx - 1] = active_stage["substages"][sub_idx - 1], active_stage["substages"][sub_idx]
                                st.rerun()
                        with col_c2:
                            if st.button("Bajar", key=f"btn_sub_dn_{substage['id']}", disabled=(sub_idx == len(active_stage["substages"]) - 1)):
                                active_stage["substages"][sub_idx], active_stage["substages"][sub_idx + 1] = active_stage["substages"][sub_idx + 1], active_stage["substages"][sub_idx]
                                st.rerun()
                        with col_c3:
                            if st.button("Clonar", key=f"btn_sub_cl_{substage['id']}"):
                                cloned_sub = json.loads(json.dumps(substage))
                                cloned_sub["id"] = str(uuid.uuid4())
                                cloned_sub["title"] = f"{substage['title']} (Copia)"
                                cloned_sub["key"] = f"{substage['key']}_COPY"
                                active_stage["substages"].append(cloned_sub)
                                st.rerun()
                        with col_c4:
                            if st.button("Borrar", key=f"btn_sub_dl_{substage['id']}"):
                                active_stage["substages"].pop(sub_idx)
                                st.rerun()

                    # Configuración de Roles y Microservicio para esta Subetapa
                    st.markdown("##### Configuración de Roles y Microservicio")
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
                            key=f"srv_{substage['id']}"
                        )
                        substage["service_key"] = "" if selected_srv == "(Manual / Formulario)" else selected_srv

                    # Constructor de Campos Dinámicos
                    st.markdown("##### Campos del Formulario (Input Schema)")
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
                        st.caption("No hay campos configurados en esta subetapa.")

                    # Formulario para Agregar Campo
                    with st.form(f"form_add_field_{substage['id']}", clear_on_submit=True):
                        st.markdown("**Agregar Nuevo Campo:**")
                        col_cf1, col_cf2 = st.columns([2, 2])
                        with col_cf1:
                            f_title = st.text_input("Título / Etiqueta:", placeholder="Ej: RUT del Solicitante", key=f"ft_{substage['id']}")
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

                        col_mask1, col_mask2 = st.columns(2)
                        with col_mask1:
                            f_placeholder_input = st.text_input("Guía visual / Placeholder:", placeholder="Ej: _ _ _ _ _ _ _ _ - _", key=f"fph_{substage['id']}")
                        with col_mask2:
                            f_mask_regex = st.text_input("Patrón / Regex (opcional):", placeholder="Ej: ^[0-9]{7,8}-[0-9kK]$", key=f"fmsk_{substage['id']}")

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
                                st.success(f"Campo '{f_title}' agregado.")
                                st.rerun()
                            else:
                                st.error("Debes ingresar la etiqueta del campo.")

        # Formulario para Agregar Subetapa a la Etapa Activa
        with st.expander(f"+ Agregar Nueva Subetapa a '{active_stage['title']}'"):
            with st.form(f"form_new_sub_{active_stage['id']}", clear_on_submit=True):
                col_sub1, col_sub2 = st.columns([3, 1])
                with col_sub1:
                    new_sub_title = st.text_input("Nombre de la Subetapa:", placeholder="Ej: Carga de Documentación")
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
                        active_stage["substages"].append(new_sub)
                        st.success(f"Subetapa '{new_sub_title}' creada.")
                        st.rerun()
                    else:
                        st.error("Debes ingresar el nombre de la subetapa.")

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
            
            st.info("💡 **Información para el Operador:** Para evaluar y aprobar esta solicitud, cambia el selector de perfil a **'Operador / Revisor Interno'** en la barra lateral izquierda.")

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
