import os
import json
import httpx
import streamlit as st
import plotly.graph_objects as go

# Configuracion de pagina en modo ancho
st.set_page_config(
    page_title="Sherpas Wealth Co-Pilot",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

# Estilos CSS sutiles para look fintech
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .immediate-action-box {
        background-color: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .badge-priority {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Inicializacion de variables de sesion
if "case_id" not in st.session_state:
    st.session_state.case_id = "michael-carter"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dashboard" not in st.session_state:
    st.session_state.dashboard = None
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "master_plan" not in st.session_state:
    st.session_state.master_plan = None
if "cases_list" not in st.session_state:
    st.session_state.cases_list = []
if "chart_data" not in st.session_state:
    st.session_state.chart_data = None

# Funciones de consulta a la API backend
def fetch_cases():
    try:
        r = httpx.get(f"{API_BASE_URL}/api/cases", timeout=10)
        if r.status_code == 200:
            st.session_state.cases_list = r.json()
    except Exception as e:
        st.sidebar.error(f"Error conectando al backend: {e}")

def sync_dashboard_and_tasks(case_id: str):
    try:
        r_dash = httpx.get(f"{API_BASE_URL}/api/cases/{case_id}/dashboard", timeout=10)
        if r_dash.status_code == 200:
            st.session_state.dashboard = r_dash.json()

        r_tasks = httpx.get(f"{API_BASE_URL}/api/cases/{case_id}/tasks", timeout=10)
        if r_tasks.status_code == 200:
            st.session_state.tasks = r_tasks.json()
    except Exception as e:
        st.error(f"Error sincronizando datos: {e}")

def initialize_case_plan(case_id: str, query: str = ""):
    with st.spinner("Analizando caso con modelo de razonamiento y generando plan maestro..."):
        try:
            payload = {"user_query": query or "Disena el plan inicial de choque"}
            r = httpx.post(f"{API_BASE_URL}/api/cases/{case_id}/init", json=payload, timeout=60)
            if r.status_code == 200:
                data = r.json()
                st.session_state.master_plan = data.get("master_plan")
                st.session_state.tasks = data.get("tasks", [])
                st.session_state.dashboard = data.get("dashboard")
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": f"¡Hola! He analizado tu perfil financiero completo. {data.get('master_plan', {}).get('headline', '')}. ¿En que te gustaria enfocarte hoy?"
                    }
                ]
                st.success("Plan maestro inicializado con exito")
            else:
                st.error(f"Fallo al inicializar: {r.text}")
        except Exception as e:
            st.error(f"Error de conexion al inicializar: {e}")

def update_task_status(case_id: str, task_id: str, current_status: str):
    new_status = "completed" if current_status != "completed" else "pending"
    try:
        r = httpx.patch(
            f"{API_BASE_URL}/api/cases/{case_id}/tasks/{task_id}",
            json={"status": new_status},
            timeout=10
        )
        if r.status_code == 200:
            sync_dashboard_and_tasks(case_id)
            st.rerun()
    except Exception as e:
        st.error(f"Error actualizando tarea: {e}")

# Cargar lista de casos si aun no esta disponible
if not st.session_state.cases_list:
    fetch_cases()

# BARRA LATERAL: Selector de caso e informacion
with st.sidebar:
    st.title("🧭 Sherpas Wealth")
    st.caption("Co-Pilot Financiero Interactivo")

    case_options = {c["id"]: f"{c['title']} (Score: {c.get('score', 0)})" for c in st.session_state.cases_list}
    if not case_options:
        case_options = {"michael-carter": "Michael Carter (Austin) - Score: 26"}

    selected_id = st.selectbox(
        "Seleccionar Cliente:",
        options=list(case_options.keys()),
        format_func=lambda x: case_options.get(x, x),
        index=list(case_options.keys()).index(st.session_state.case_id) if st.session_state.case_id in case_options else 0
    )

    if selected_id != st.session_state.case_id:
        st.session_state.case_id = selected_id
        st.session_state.master_plan = None
        st.session_state.messages = []
        sync_dashboard_and_tasks(selected_id)
        st.rerun()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Cargar Plan", use_container_width=True):
            initialize_case_plan(st.session_state.case_id)
            st.rerun()
    with col_btn2:
        if st.button("🔄 Refrescar", use_container_width=True):
            sync_dashboard_and_tasks(st.session_state.case_id)
            st.rerun()

    st.divider()

    # Informacion resumida del hogar
    current_case_meta = next((c for c in st.session_state.cases_list if c["id"] == st.session_state.case_id), None)
    if current_case_meta:
        st.subheader("Datos del Hogar")
        st.write(f"**Ciudad:** {current_case_meta.get('city', 'N/A')}")
        st.write(f"**Score Publicado:** {current_case_meta.get('score', 0)} / 100")
        hh = current_case_meta.get("household", [])
        if hh:
            st.write("**Integrantes:**")
            for m in hh:
                st.caption(f"- {m.get('first_name')} ({m.get('role')}, {m.get('age', 'N/A')} anos)")

# Sincronizar datos si no estan cargados
if not st.session_state.dashboard:
    sync_dashboard_and_tasks(st.session_state.case_id)

# LAYOUT PRINCIPAL: 3 PANELES SINCRONIZADOS
col_dash, col_tasks, col_chat = st.columns([3.8, 3.2, 3.0], gap="medium")

# ==========================================
# PANEL 1: DASHBOARD FINANCIERO
# ==========================================
with col_dash:
    st.subheader("📊 Dashboard Financiero")
    
    db = st.session_state.dashboard
    if db:
        # Metricas superiores principales
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(
                label="Health Score",
                value=f"{db.get('health_score', 0)} / 100",
                delta="Critico" if db.get('health_score', 0) < 40 else "Estable"
            )
        with col_m2:
            nw = db.get("net_worth", 0)
            nw_prev = db.get("metrics", {}).get("net_worth", {}).get("previous_value")
            delta_nw = f"{(nw - nw_prev):+,.0f}" if nw_prev is not None else None
            st.metric(
                label="Patrimonio Neto",
                value=f"${nw:,.0f}",
                delta=delta_nw
            )
        with col_m3:
            cf = db.get("monthly_free_cashflow", 0)
            st.metric(
                label="Cashflow Libre",
                value=f"${cf:,.0f}/mes",
                delta="Superavit" if cf >= 0 else "Deficit",
                delta_color="normal" if cf >= 0 else "inverse"
            )

        st.divider()

        # Desglose de ingresos y gastos
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            st.metric(label="Ingresos Mensuales", value=f"${db.get('monthly_income', 0):,.0f}")
        with col_sub2:
            st.metric(label="Gastos Mensuales", value=f"${db.get('monthly_expenses', 0):,.0f}")

        # Tarjetas adicionales generadas por el Co-Pilot
        metrics_dict = db.get("metrics", {})
        custom_metrics = {k: v for k, v in metrics_dict.items() if k not in ["health_score", "net_worth", "monthly_income", "monthly_expenses", "monthly_cashflow"]}
        if custom_metrics:
            st.write("**Metricas Ajustadas por el Co-Pilot:**")
            for k, m in custom_metrics.items():
                st.info(f"**{m.get('label', k)}:** {m.get('formatted_value', m.get('value'))} | *{m.get('note', '')}*")

        # Visualizacion de graficos interactivos si existen
        chart = st.session_state.chart_data
        if chart:
            st.write(f"**{chart.get('title', 'Proyeccion Grafica')}**")
            c_type = chart.get("type", "bar")
            labels = chart.get("labels", [])
            values = chart.get("values", [])
            
            if c_type == "bar":
                fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color="#0ea5e9")])
            elif c_type == "donut":
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5)])
            else:
                fig = go.Figure(data=[go.Scatter(x=labels, y=values, mode="lines+markers", line=dict(color="#0ea5e9"))])
            
            fig.update_layout(margin=dict(l=10, r=10, t=25, b=10), height=240)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Haz clic en 'Cargar Plan' para generar el analisis inicial del cliente.")

# ==========================================
# PANEL 2: PLAN DE ACCION Y TAREAS
# ==========================================
with col_tasks:
    st.subheader("📋 Plan de Accion")
    
    mp = st.session_state.master_plan
    tasks = st.session_state.tasks

    if mp and mp.get("immediate_action"):
        act = mp["immediate_action"]
        st.markdown(f"""
        <div class="immediate-action-box">
            <strong>⚡ Accion Inmediata (Hoy):</strong> {act.get('title', '')}<br/>
            <small style="color: #15803d;">Impacto: {act.get('expected_impact', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    if tasks:
        completed_count = sum(1 for t in tasks if t.get("status") == "completed")
        progress_pct = completed_count / len(tasks) if tasks else 0
        st.progress(progress_pct, text=f"Progreso del plan: {completed_count}/{len(tasks)} completadas ({int(progress_pct*100)}%)")

        st.write("**Lista de Tareas:**")
        for t in tasks:
            t_id = t.get("id", "")
            t_title = t.get("title", "")
            t_status = t.get("status", "pending")
            t_cat = t.get("category", "general").upper()
            t_week = t.get("week", 1)
            is_done = t_status == "completed"

            col_chk, col_txt = st.columns([0.15, 0.85])
            with col_chk:
                checked = st.checkbox("", value=is_done, key=f"chk_{t_id}")
                if checked != is_done:
                    update_task_status(st.session_state.case_id, t_id, t_status)

            with col_txt:
                strike_start = "~~" if is_done else ""
                strike_end = "~~" if is_done else ""
                st.markdown(f"{strike_start}**[{t_cat}]** {t_title} *(Semana {t_week})*{strike_end}")
                if t.get("impact"):
                    imp = t["impact"]
                    st.caption(f"Impacto: {imp.get('value', '')} ({imp.get('metric', '')})")
    else:
        st.info("Sin tareas activas. Inicia el plan para desplegar el roadmap.")

# ==========================================
# PANEL 3: CHAT CO-PILOT INTERACTIVO
# ==========================================
with col_chat:
    st.subheader("💬 Co-Pilot Chat")

    # Chips de preguntas rapidas
    col_chip1, col_chip2 = st.columns(2)
    chip_prompt = None
    with col_chip1:
        if st.button("🔍 Explicar mi score", use_container_width=True):
            chip_prompt = "Por que mi score es tan bajo y cual es mi cuello de botella principal?"
    with col_chip2:
        if st.button("💰 Simular colchon", use_container_width=True):
            chip_prompt = "Usa update_dashboard_metric para aumentar mi colchon a 4 meses y anade la tarea."

    # Historial de chat
    chat_container = st.container(height=420)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.write(m["content"])

    # Entrada de texto del usuario
    user_input = st.chat_input("Escribe a tu asesor co-pilot...")
    prompt_to_send = chip_prompt or user_input

    if prompt_to_send:
        # 1. Registrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt_to_send})
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt_to_send)

        # 2. Llamada interactiva al backend via streaming SSE
        with chat_container:
            with st.chat_message("assistant"):
                text_placeholder = st.empty()
                full_response = ""
                tools_called = []

                try:
                    with httpx.Client(timeout=60.0) as client:
                        with client.stream(
                            "POST",
                            f"{API_BASE_URL}/api/chat/stream",
                            json={"message": prompt_to_send, "case_id": st.session_state.case_id}
                        ) as response:
                            for line in response.iter_lines():
                                if not line.startswith("data: "):
                                    continue
                                raw_event = line[6:].strip()
                                if not raw_event:
                                    continue
                                try:
                                    event = json.loads(raw_event)
                                    e_type = event.get("type")

                                    if e_type == "delta":
                                        chunk = event.get("delta", "")
                                        full_response += chunk
                                        text_placeholder.markdown(full_response + "▌")

                                    elif e_type == "tool_start":
                                        t_name = event.get("tool", "herramienta")
                                        tools_called.append(t_name)

                                    elif e_type == "state_update":
                                        # Captura de graficos generados
                                        if event.get("chart"):
                                            st.session_state.chart_data = event["chart"]

                                except json.JSONDecodeError:
                                    continue

                    text_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                    # Si se invocaron herramientas, sincronizar dashboard y tareas
                    if tools_called:
                        sync_dashboard_and_tasks(st.session_state.case_id)
                        st.rerun()

                except Exception as e:
                    st.error(f"Error en la comunicacion con el Co-Pilot: {e}")
