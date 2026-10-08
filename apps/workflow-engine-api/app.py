import streamlit as st
import json
import uuid
from datetime import datetime, date

# Configuración de Página
st.set_page_config(
    page_title="Workflow Studio | Python Cloud Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialización del Estado de la Aplicación (Session State)
if "workflow" not in st.session_state:
    st.session_state.workflow = {
        "id": "wf-custom-01",
        "name": "Workflow de Servicios a Medida",
        "tenant": "MI_EMPRESA",
        "code": "WF_CUSTOM",
        "stages": [] # Inicia 100% en blanco
    }

if "microservices" not in st.session_state:
    st.session_state.microservices = [
        {
            "key": "SRV_DATE_CALCULATOR",
            "name": "Calculador de Días Hábiles",
            "url": "https://srv-date-calculator-xyz.a.run.app/api/v1/calculate"
        },
        {
            "key": "SRV_PDF_READER",
            "name": "Extractor OCR de PDFs",
            "url": "https://srv-pdf-reader-xyz.a.run.app/api/v1/extract"
        },
        {
            "key": "SRV_DOC_GENERATOR",
            "name": "Generador de Contratos PDF",
            "url": "https://srv-doc-gen-xyz.a.run.app/api/v1/generate"
        }
    ]

if "execution" not in st.session_state:
    st.session_state.execution = {
        "code": f"EXEC-{datetime.utcnow().year}-00001",
        "status": "NOT_STARTED", # NOT_STARTED, IN_PROGRESS, IN_REVIEW, COMPLETED
        "current_stage_idx": 0,
        "current_substage_idx": 0,
        "iteration": 1,
        "form_data": {},
        "context_data": {},
        "audit_logs": []
    }

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .stage-card {
        background-color: #f8fafc;
        border: 2px solid #cbd5e1;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .substage-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Barra Lateral
st.sidebar.markdown("### ⚡ Workflow Studio")
st.sidebar.caption(f"Tenant: **{st.session_state.workflow['tenant']}**")

mode = st.sidebar.radio(
    "Selecciona la Vista:",
    [
        "🛠️ Diseñador de Workflows",
        "🚀 Portal de Ejecución (Runtime)",
        "🤖 Generador de APIs con IA",
        "🔌 Catálogo de Microservicios"
    ],
    index=0
)

st.sidebar.divider()
if st.sidebar.button("🗑️ Vaciar / Reiniciar Todo"):
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
if mode == "🛠️ Diseñador de Workflows":
    st.markdown('<div class="main-header">🛠️ Diseñador de Workflows y Subetapas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Crea y estructura las etapas, agrega subetapas, define sus campos dinámicos y asigna roles de Google Workspace.</div>', unsafe_allow_html=True)

    col_name, col_code = st.columns([3, 1])
    with col_name:
        st.session_state.workflow["name"] = st.text_input("Nombre del Workflow:", value=st.session_state.workflow["name"])
    with col_code:
        st.session_state.workflow["code"] = st.text_input("Código Técnico:", value=st.session_state.workflow["code"])

    st.divider()

    # Formulario para Crear Nueva Etapa
    with st.expander("➕ **Crear Nueva Etapa**", expanded=len(st.session_state.workflow["stages"]) == 0):
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
                        "substages": [] # Inicia 100% vacía, sin subetapas por defecto
                    }
                    st.session_state.workflow["stages"].append(new_stage)
                    st.success(f"Etapa '{stage_title}' creada exitosamente.")
                    st.rerun()
                else:
                    st.error("Debes ingresar el nombre de la etapa.")

    # Listado de Etapas Creadas
    if len(st.session_state.workflow["stages"]) == 0:
        st.info("🎨 El workflow está vacío. Haz clic arriba en **'+ Crear Nueva Etapa'** para comenzar.")
    else:
        st.markdown(f"#### 📋 Estructura del Flujo ({len(st.session_state.workflow['stages'])} Etapas configuradas)")
        
        for s_idx, stage in enumerate(st.session_state.workflow["stages"]):
            with st.container():
                st.markdown(f"---")
                col_st_title, col_st_del = st.columns([5, 1])
                with col_st_title:
                    st.markdown(f"### 🏷️ Etapa {s_idx + 1}: **{stage['title']}** `[{stage['key']}]`")
                with col_st_del:
                    if st.button(f"🗑️ Eliminar Etapa", key=f"del_stage_{stage['id']}"):
                        st.session_state.workflow["stages"].pop(s_idx)
                        st.rerun()

                # Subetapas dentro de esta Etapa
                if len(stage["substages"]) == 0:
                    st.warning(f"⚠️ Esta etapa no tiene subetapas. Agrega una a continuación.")
                else:
                    for sub_idx, substage in enumerate(stage["substages"]):
                        with st.expander(f"🔹 **Subetapa {s_idx + 1}.{sub_idx + 1}: {substage['title']}** `[{substage['key']}]` — ({len(substage['fields'])} campos)", expanded=True):
                            col_sub_info, col_sub_actions = st.columns([3, 1])
                            
                            with col_sub_info:
                                st.write(f"**Rol Editor:** `{substage['editor_role'] or 'No asignado'}` | **Rol Revisor:** `{substage['reviewer_role'] or 'No asignado'}`")
                                st.write(f"**Servicio:** `{substage['service_key'] or 'Manual (Formulario)'}`")

                            with col_sub_actions:
                                col_c1, col_c2 = st.columns(2)
                                with col_c1:
                                    if st.button("📋 Clonar", key=f"clone_sub_{substage['id']}"):
                                        cloned_sub = json.loads(json.dumps(substage))
                                        cloned_sub["id"] = str(uuid.uuid4())
                                        cloned_sub["title"] = f"{substage['title']} (Copia)"
                                        cloned_sub["key"] = f"{substage['key']}_COPY"
                                        stage["substages"].append(cloned_sub)
                                        st.success(f"Subetapa clonada.")
                                        st.rerun()
                                with col_c2:
                                    if st.button("🗑️ Borrar", key=f"del_sub_{substage['id']}"):
                                        stage["substages"].pop(sub_idx)
                                        st.rerun()

                            # Configuración de Roles y Microservicio para esta Subetapa
                            st.markdown("##### ⚙️ Configuración de Roles y Microservicio")
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

                            # Constructor de Campos Dinámicos (Schema Builder)
                            st.markdown("##### 📝 Constructor de Campos del Formulario (Input Schema)")
                            
                            # Mostrar tabla de campos existentes
                            if len(substage["fields"]) > 0:
                                for f_idx, field in enumerate(substage["fields"]):
                                    col_f_name, col_f_title, col_f_type, col_f_req, col_f_del = st.columns([2, 2, 1.5, 1, 0.5])
                                    with col_f_name:
                                        st.code(field["name"])
                                    with col_f_title:
                                        st.write(f"**{field['title']}**")
                                    with col_f_type:
                                        st.badge = field["type"]
                                        st.caption(f"Tipo: `{field['type']}`")
                                    with col_f_req:
                                        st.write("Obligatorio" if field["required"] else "Opcional")
                                    with col_f_del:
                                        if st.button("❌", key=f"del_f_{substage['id']}_{field['id']}"):
                                            substage["fields"].pop(f_idx)
                                            st.rerun()
                            else:
                                st.caption("No hay campos configurados en esta subetapa. Agrega campos con el botón de abajo.")

                            # Formulario para Agregar Campo
                            with st.form(f"form_add_field_{substage['id']}", clear_on_submit=True):
                                st.markdown("**+ Agregar Nuevo Campo:**")
                                col_cf1, col_cf2, col_cf3, col_cf4 = st.columns([2, 2, 1.5, 1])
                                with col_cf1:
                                    f_title = st.text_input("Título / Etiqueta:", placeholder="Ej: RUT del Proveedor", key=f"ft_{substage['id']}")
                                with col_cf2:
                                    f_name = st.text_input("Nombre Técnico (JSON Key):", placeholder="Ej: rut_proveedor", key=f"fn_{substage['id']}")
                                with col_cf3:
                                    f_type = st.selectbox("Tipo de Dato:", ["Texto", "Número", "Fecha", "Booleano", "Archivo / PDF"], key=f"fty_{substage['id']}")
                                with col_cf4:
                                    st.write("")
                                    st.write("")
                                    f_req = st.checkbox("Obligatorio", value=True, key=f"fr_{substage['id']}")

                                submit_field = st.form_submit_button("+ Guardar Campo", type="secondary")
                                if submit_field:
                                    if f_title:
                                        type_mapping = {
                                            "Texto": "string",
                                            "Número": "number",
                                            "Fecha": "date",
                                            "Booleano": "boolean",
                                            "Archivo / PDF": "file"
                                        }
                                        new_field = {
                                            "id": str(uuid.uuid4()),
                                            "title": f_title,
                                            "name": f_name if f_name else f_title.lower().replace(" ", "_"),
                                            "type": type_mapping[f_type],
                                            "required": f_req
                                        }
                                        substage["fields"].append(new_field)
                                        st.success(f"Campo '{f_title}' agregado.")
                                        st.rerun()
                                    else:
                                        st.error("Debes ingresar la etiqueta del campo.")

                # Formulario para Agregar Subetapa a esta Etapa
                with st.expander(f"➕ **Agregar Subetapa a la Etapa {s_idx + 1}: {stage['title']}**"):
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

                        submit_sub = st.form_submit_button("+ Crear Subetapa", type="primary")
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
elif mode == "🚀 Portal de Ejecución (Runtime)":
    st.markdown('<div class="main-header">🚀 Portal Operativo de Ejecución</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Simula el ingreso de datos, revisión/aprobación por roles, disparo de microservicios y botón Volver.</div>', unsafe_allow_html=True)

    if len(st.session_state.workflow["stages"]) == 0:
        st.warning("⚠️ No hay etapas creadas en el workflow. Ve al 'Diseñador de Workflows' y crea al menos una etapa con subetapas.")
    else:
        stages = st.session_state.workflow["stages"]
        
        # Validar si hay subetapas
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
            st.warning("⚠️ Las etapas creadas no contienen subetapas. Agrega subetapas en el Diseñador.")
        else:
            # Barra Superior de Ejecución
            exec_state = st.session_state.execution
            col_ex1, col_ex2, col_ex3 = st.columns([2, 2, 1])
            with col_ex1:
                st.info(f"🔑 **Clave de Ejecución:** `{exec_state['code']}`")
            with col_ex2:
                status_colors = {
                    "NOT_STARTED": "⚪ No Iniciada",
                    "IN_PROGRESS": "🔵 En Edición",
                    "IN_REVIEW": "🟡 En Revisión",
                    "COMPLETED": "🟢 Completada"
                }
                st.info(f"📊 **Estado:** {status_colors.get(exec_state['status'], exec_state['status'])} | **Iteración:** `{exec_state['iteration']}`")
            with col_ex3:
                # Botón Volver / Rollback
                can_rollback = not (exec_state["current_stage_idx"] == 0 and exec_state["current_substage_idx"] == 0)
                if st.button("⏪ Volver (Rollback)", disabled=not can_rollback, type="secondary"):
                    if can_rollback:
                        # Retroceder al paso anterior
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
                        
                        # Log de Auditoría
                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "ROLLBACK_TRIGGERED",
                            "user": "operador@miempresa.com",
                            "notes": f"Retroceso a {prev_item['substage']['title']} (Iteración {exec_state['iteration']})"
                        })
                        st.warning(f"⏪ Retroceso aplicado hacia: {prev_item['substage']['title']} (Iteración {exec_state['iteration']})")
                        st.rerun()

            # Obtener subetapa activa
            current_stage = stages[exec_state["current_stage_idx"]]
            current_sub = current_stage["substages"][exec_state["current_substage_idx"]]

            st.markdown(f"### 📍 Etapa Activa: **{current_stage['title']}** ➔ Subetapa: **{current_sub['title']}**")
            
            # Selector de Simulación de Rol
            role_mode = st.radio(
                "Simular Acción como Rol:",
                [f"✏️ Editor ({current_sub['editor_role'] or 'operaciones@miempresa.com'})", 
                 f"🛡️ Revisor ({current_sub['reviewer_role'] or 'supervisores@miempresa.com'})"],
                horizontal=True
            )
            is_editor_mode = "Editor" in role_mode

            st.divider()

            # Formulario Dinámico de la Subetapa
            st.markdown("#### 📝 Formulario de Entrada (Generado Dinámicamente)")
            
            if len(current_sub["fields"]) == 0:
                st.caption("Esta subetapa no tiene campos configurados.")
            else:
                with st.form("runtime_dynamic_form"):
                    form_inputs = {}
                    for field in current_sub["fields"]:
                        f_key = f"input_{field['name']}"
                        prev_val = exec_state["form_data"].get(field["name"], None)

                        if field["type"] == "string":
                            form_inputs[field["name"]] = st.text_input(
                                f"{field['title']} {'*' if field['required'] else ''}",
                                value=prev_val or "",
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
                            form_inputs[field["name"]] = "archivo_subido.pdf"
                            st.file_uploader(f"Subir {field['title']}", disabled=not is_editor_mode)

                    # Si tiene microservicio asociado
                    if current_sub["service_key"]:
                        st.info(f"⚡ **Microservicio Conectado:** `{current_sub['service_key']}` (Se ejecutará al enviar)")

                    # Botón de Guardar para el Editor
                    if is_editor_mode:
                        submit_data = st.form_submit_button("💾 Guardar y Enviar a Revisión", type="primary")
                        if submit_data:
                            exec_state["form_data"].update(form_inputs)
                            exec_state["status"] = "IN_REVIEW"
                            exec_state["audit_logs"].append({
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "action": "SUBMITTED_FOR_REVIEW",
                                "user": current_sub["editor_role"] or "editor@miempresa.com",
                                "notes": f"Datos ingresados: {json.dumps(form_inputs)}"
                            })
                            st.success("✅ Formulario enviado con éxito. Estado actualizado a: **EN REVISIÓN**.")
                            st.rerun()

            # Panel de Decisión del Revisor
            if not is_editor_mode:
                st.markdown("---")
                st.markdown("#### 🛡️ Panel de Decisión del Revisor")
                rev_notes = st.text_area("Observaciones / Comentarios del Revisor:", placeholder="Ingrese notas de revisión...")
                
                col_ap, col_rej = st.columns(2)
                with col_ap:
                    if st.button("✅ Aprobar y Avanzar a Siguiente Subetapa", type="primary"):
                        exec_state["status"] = "APPROVED"
                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "APPROVED_BY_REVIEWER",
                            "user": current_sub["reviewer_role"] or "revisor@miempresa.com",
                            "notes": rev_notes or "Aprobado sin comentarios."
                        })

                        # Avanzar al siguiente paso si existe
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
                            st.success(f"🎉 Subetapa aprobada. Avanzando a: **{next_item['substage']['title']}**.")
                        else:
                            exec_state["status"] = "COMPLETED"
                            st.balloons()
                            st.success("🏁 ¡Workflow completado con éxito!")
                        st.rerun()

                with col_rej:
                    if st.button("❌ Rechazar y Devolver al Editor", type="secondary"):
                        exec_state["status"] = "REJECTED"
                        exec_state["audit_logs"].append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "action": "REJECTED_BY_REVIEWER",
                            "user": current_sub["reviewer_role"] or "revisor@miempresa.com",
                            "notes": rev_notes or "Rechazado para corrección."
                        })
                        st.error(f"⚠️ Subetapa rechazada. Devuelta al rol Editor para corrección.")
                        st.rerun()

            # Historial Inmutable de Auditoría
            st.markdown("---")
            st.markdown("#### 📜 Trazabilidad y Auditoría (Historial Inmutable)")
            if len(exec_state["audit_logs"]) == 0:
                st.caption("No hay eventos registrados aún en esta ejecución.")
            else:
                for log in reversed(exec_state["audit_logs"]):
                    st.markdown(f"- **`{log['timestamp']}`** | `{log['action']}` por **{log['user']}** ➔ *{log['notes']}*")

# ==============================================================================
# VISTA 3: GENERADOR DE APIS Y MICROSERVICIOS CON IA
# ==============================================================================
elif mode == "🤖 Generador de APIs con IA":
    st.markdown('<div class="main-header">🤖 Generador de APIs y Microservicios con IA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Describe en lenguaje natural la funcionalidad que necesitas y la IA construirá automáticamente el microservicio, sus esquemas JSON (Input/Output) y el código FastAPI para Cloud Run.</div>', unsafe_allow_html=True)

    if "ai_generated_api" not in st.session_state:
        st.session_state.ai_generated_api = None

    col_prompt, col_templates = st.columns([2, 1])

    with col_templates:
        st.markdown("##### 💡 Plantillas de Ejemplo:")
        if st.button("📄 Extractor OCR de Facturas"):
            st.session_state.ai_prompt_text = "Crear un microservicio que reciba la URL de un PDF de factura o boleta, extraiga el RUT del emisor, monto neto, IVA, monto total y fecha de emisión."
        if st.button("💰 Validador de Scoring Crediticio"):
            st.session_state.ai_prompt_text = "Crear una API que reciba RUT, ingresos mensuales y monto solicitado, consulte el riesgo crediticio y devuelva si es aprobado, el score (1-1000) y la tasa de interés."
        if st.button("📅 Calculador de Vacaciones y Plazos"):
            st.session_state.ai_prompt_text = "Crear una API que reciba fecha de inicio de contrato y días solicitados, calcule los días proporcionales acumulados y devuelva la fecha de término."

    with col_prompt:
        ai_prompt = st.text_area(
            "¿Qué funcionalidad debe realizar tu API / Microservicio?",
            value=st.session_state.get("ai_prompt_text", "Crear una API que reciba el RUT de un cliente y valide si tiene antecedentes legales y comerciales vigentes, retornando un indicador booleano y el nivel de riesgo."),
            height=130,
            placeholder="Ej: Necesito una API que reciba un archivo PDF, extraiga las tablas de costos y calcule el subtotal con IVA..."
        )

        generate_btn = st.button("✨ Generar API y Esquemas con IA", type="primary")

    if generate_btn and ai_prompt:
        with st.spinner("🤖 La IA está diseñando la API, generando modelos Pydantic, esquemas JSON y código FastAPI..."):
            # Generación inteligente estructurada
            prompt_lower = ai_prompt.lower()
            
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
                        "rut_emisor": {"type": "string", "title": "RUT Emisor"},
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
                        "rut": {"type": "string", "title": "RUT Cliente"},
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
    description="Microservicio generado automáticamente por IA para Workflow Engine",
    version="1.0.0"
)

# 1. Modelo de Entrada (Input Payload)
class RequestPayload(BaseModel):
'''
            for prop, val in in_schema["properties"].items():
                py_type = "str" if val.get("type") == "string" else ("float" if val.get("type") == "number" else ("int" if val.get("type") == "integer" else "bool"))
                code_template += f'    {prop}: {py_type} = Field(..., description="{val.get("title", prop)}")\n'

            code_template += f'''
# 2. Modelo de Salida (Output Schema)
class ResponsePayload(BaseModel):
'''
            for prop, val in out_schema["properties"].items():
                py_type = "str" if val.get("type") == "string" else ("float" if val.get("type") == "number" else ("int" if val.get("type") == "integer" else "bool"))
                code_template += f'    {prop}: {py_type}\n'

            code_template += f'''
# 3. Endpoint Principal del Microservicio
@app.post("/api/v1/process", response_model=ResponsePayload)
def process_data(req: RequestPayload):
    """
    Lógica de negocio ejecutada en Cloud Run.
    """
    # Lógica procesada
    return ResponsePayload(
'''
            for prop, val in out_schema["properties"].items():
                if val.get("type") == "boolean":
                    default_val = "True"
                elif val.get("type") in ["number", "integer"]:
                    default_val = "950" if "score" in prop else "1000000"
                elif val.get("format") == "date":
                    default_val = 'datetime.now().strftime("%Y-%m-%d")'
                else:
                    default_val = '"76.452.190-K"' if "rut" in prop else '"Procesado con éxito"'
                code_template += f'        {prop}={default_val},\n'

            code_template += f'''    )

@app.get("/health")
def health():
    return {{"status": "ok", "service": "{srv_key}"}}
'''

            st.session_state.ai_generated_api = {
                "key": srv_key,
                "name": srv_name,
                "url": f"https://{srv_key.lower().replace('_', '-')}-xyz.a.run.app/api/v1/process",
                "in_schema": in_schema,
                "out_schema": out_schema,
                "code": code_template
            }

    # Mostrar Resultados Generados por la IA
    if st.session_state.ai_generated_api:
        api_data = st.session_state.ai_generated_api
        st.success(f"🎉 **Microservicio Diseñado:** `{api_data['name']}` `[{api_data['key']}]`")

        tab_schemas, tab_code, tab_save = st.tabs(["📋 Esquemas JSON (Input/Output)", "🐍 Código Python FastAPI", "🚀 Registrar en Catálogo"])

        with tab_schemas:
            col_in, col_out = st.columns(2)
            with col_in:
                st.markdown("**Input Schema (Datos que requiere):**")
                st.json(api_data["in_schema"])
            with col_out:
                st.markdown("**Output Schema (Datos que devuelve al Workflow):**")
                st.json(api_data["out_schema"])

        with tab_code:
            st.markdown("**Código del Microservicio listo para desplegar en Cloud Run:**")
            st.code(api_data["code"], language="python")

        with tab_save:
            st.markdown("##### 🚀 Registrar este Microservicio en el Catálogo de Workflows")
            st.write(f"Al registrarlo, quedará disponible de inmediato en cualquier subetapa del Diseñador de Workflows.")
            
            col_reg1, col_reg2 = st.columns([3, 1])
            with col_reg1:
                st.text_input("Endpoint URL:", value=api_data["url"], key="reg_api_url")
            with col_reg2:
                st.write("")
                st.write("")
                if st.button("➕ Guardar en Catálogo", type="primary"):
                    # Evitar duplicados
                    existing_keys = [s["key"] for s in st.session_state.microservices]
                    if api_data["key"] not in existing_keys:
                        st.session_state.microservices.append({
                            "key": api_data["key"],
                            "name": api_data["name"],
                            "url": api_data["url"]
                        })
                    st.success(f"✅ ¡Microservicio '{api_data['name']}' registrado en el catálogo!")
                    st.balloons()

# ==============================================================================
# VISTA 4: CATÁLOGO DE MICROSERVICIOS
# ==============================================================================
elif mode == "🔌 Catálogo de Microservicios":
    st.markdown('<div class="main-header">🔌 Catálogo y Fábrica de Microservicios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestiona los microservicios disponibles en Cloud Run para asociarlos a cualquier subetapa.</div>', unsafe_allow_html=True)

    with st.expander("➕ **Registrar Nuevo Microservicio Manualmente**", expanded=False):
        with st.form("form_new_service", clear_on_submit=True):
            col_srv1, col_srv2 = st.columns([2, 1])
            with col_srv1:
                srv_name = st.text_input("Nombre del Servicio:", placeholder="Ej: Validador de Scoring Crediticio")
            with col_srv2:
                srv_key = st.text_input("Clave Única (Key):", placeholder="Ej: SRV_SCORING_API")
            
            srv_url = st.text_input("Endpoint URL (Cloud Run):", placeholder="https://srv-scoring-xyz.a.run.app/api/v1/score")
            
            submit_srv = st.form_submit_button("+ Registrar en Catálogo", type="primary")
            if submit_srv:
                if srv_name and srv_key:
                    st.session_state.microservices.append({
                        "key": srv_key.upper(),
                        "name": srv_name,
                        "url": srv_url
                    })
                    st.success(f"Microservicio '{srv_name}' registrado exitosamente.")
                    st.rerun()
                else:
                    st.error("Debes completar el nombre y la clave del servicio.")

    st.markdown("#### 📦 Microservicios Registrados en el Sistema:")
    for s in st.session_state.microservices:
        with st.container():
            st.markdown(f"- ⚡ **{s['name']}** `[{s['key']}]` ➔ `{s['url']}`")

