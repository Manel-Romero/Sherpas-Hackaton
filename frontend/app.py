import os
import sys
import json
import time
import re
from pathlib import Path

# Asegurar que el directorio raiz del proyecto este siempre en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from style import style
    import table_store as ts
    import kanban_store as ks
    import kanban_ui
    import table_ui
    from frontend import boxes_store as bs
except ImportError:
    from frontend.style import style
    from frontend import table_store as ts
    import kanban_store as ks
    import kanban_ui
    import table_ui
    from frontend import boxes_store as bs


# Configuracion de pagina completa en modo ancho
st.set_page_config(page_title="Sherpas Wealth Co-Pilot", page_icon="🧭", layout="wide")

# Inyeccion de estilos CSS personalizados (Tema oscuro fintech)
st.markdown(style, unsafe_allow_html=True)

# Estilos adicionales para cabecera y tarjetas destacadas
st.markdown("""
<style>
    .top-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: var(--surface);
        padding: 10px 16px;
        border-radius: 12px;
        border: 1px solid var(--border);
        margin-bottom: 16px;
    }
    .immediate-badge {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 6px;
        display: inline-block;
    }
    .kpi-pill {
        background: var(--surface-2);
        padding: 6px 14px;
        border-radius: 8px;
        border: 1px solid var(--border);
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

# =============================================================================
# ESTADO DE SESION
# =============================================================================
ss = st.session_state

if "case_id" not in ss:
    ss.case_id = "michael-carter"
if "session_id" not in ss:
    ss.session_id = f"sess_{ss.case_id}"
if "messages" not in ss:
    ss.messages = []
if "cases_list" not in ss:
    ss.cases_list = []
if "notify_changes" not in ss:
    ss.notify_changes = False
if "notify_msg" not in ss:
    ss.notify_msg = ""

# Notificacion emergente toast si hubo cambios aplicados
if ss.notify_changes:
    st.toast(f"Cambios aplicados: {ss.notify_msg}", icon="✅")
    ss.notify_changes = False

ts.set_case(ss.case_id)
ks.set_case(ss.case_id)
table_ui.refresh()

# =============================================================================
# COMUNICACION CON BACKEND FASTAPI
# =============================================================================
def fetch_cases():
    try:
        r = httpx.get(f"{API_BASE_URL}/api/cases", timeout=5)
        if r.status_code == 200:
            ss.cases_list = r.json()
    except Exception:
        ss.cases_list = [
            {"id": "michael-carter", "title": "Michael Carter", "city": "Austin", "score": 26},
            {"id": "daniel-emily-johnson", "title": "Daniel & Emily", "city": "Denver", "score": 52},
            {"id": "samantha-lewis", "title": "Samantha Lewis", "city": "Miami", "score": 82},
            {"id": "timothy-melanie-weah", "title": "Timothy & Melanie", "city": "San Francisco", "score": 60}
        ]

def initialize_case_plan(case_id: str):
    with st.spinner("Analizando perfil con el modelo de razonamiento y poblando proyecciones..."):
        try:
            r = httpx.post(f"{API_BASE_URL}/api/cases/{case_id}/init", json={"session_id": ss.session_id}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                mp = data.get("master_plan", {})
                ss.session_id = f"sess_{case_id}_{int(time.time())}"
                ss.messages = [
                    {
                        "role": "assistant",
                        "content": f"¡Hola! He analizado tu perfil financiero completo de Sherpas. {mp.get('headline', '')}.\n\nTu accion inmediata para hoy es: **{mp.get('immediate_action', {}).get('title', '')}**. ¿En que puedo ayudarte?"
                    }
                ]
                ts.set_case(case_id)
                ks.set_case(case_id)
                table_ui.refresh()
                st.success("Plan maestro inicializado con exito")
                st.rerun()
            else:
                st.error(f"Fallo al inicializar: {r.text}")
        except Exception as e:
            st.error(f"Error conectando con el backend: {e}")

if not ss.cases_list:
    fetch_cases()

# =============================================================================
# CABECERA SUPERIOR: SELECTOR Y CARGA DE PLAN
# =============================================================================
def format_case_label(c):
    title = c.get('title', c['id'])
    city = c.get('city', '')
    score = c.get('score', 0)
    if city and f"({city})" in title:
        return f"{title} - Score: {score}/100"
    elif city:
        return f"{title} ({city}) - Score: {score}/100"
    return f"{title} - Score: {score}/100"

case_map = {c["id"]: format_case_label(c) for c in ss.cases_list}
active_meta = next((c for c in ss.cases_list if c["id"] == ss.case_id), {})

head_col1, head_col2, head_col3 = st.columns([4, 2, 4])
with head_col1:
    selected_case = st.selectbox(
        "Cliente:",
        options=list(case_map.keys()),
        format_func=lambda x: case_map.get(x, x),
        index=list(case_map.keys()).index(ss.case_id) if ss.case_id in case_map else 0,
        label_visibility="collapsed"
    )
    if selected_case != ss.case_id:
        ss.case_id = selected_case
        ss.session_id = f"sess_{selected_case}"
        ss.messages = []
        ts.set_case(selected_case)
        ks.set_case(selected_case)
        table_ui.refresh()
        st.rerun()

with head_col2:
    if st.button("🚀 Cargar / Reiniciar Plan", use_container_width=True):
        initialize_case_plan(ss.case_id)

with head_col3:
    score_val = active_meta.get("score", 0)
    score_status = "Critico" if score_val < 40 else ("Atencion" if score_val < 70 else "Optimo")
    st.markdown(
        f"<div style='text-align: right; font-size: 0.95rem; padding-top: 6px;'>"
        f"Score: <strong>{score_val}/100</strong> <span style='color: {'#ef4444' if score_val < 40 else '#3b82f6'};'>({score_status})</span> | "
        f"Hogar: <strong>{active_meta.get('city', '')}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )

# =============================================================================
# COMPONENTES DE CAJA Y TABLA
# =============================================================================
CATEGORY_CONFIG = {
    "investment": {"label": "Inversion", "color": "#3b82f6", "bg": "rgba(59, 130, 246, 0.12)", "border": "rgba(59, 130, 246, 0.28)", "icon": "📈"},
    "savings": {"label": "Ahorro", "color": "#10b981", "bg": "rgba(16, 185, 129, 0.12)", "border": "rgba(16, 185, 129, 0.28)", "icon": "💰"},
    "debt": {"label": "Deuda", "color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.12)", "border": "rgba(245, 158, 11, 0.28)", "icon": "💳"},
    "insurance": {"label": "Seguros", "color": "#06b6d4", "bg": "rgba(6, 182, 212, 0.12)", "border": "rgba(6, 182, 212, 0.28)", "icon": "🛡️"},
    "lifestyle": {"label": "Presupuesto", "color": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.12)", "border": "rgba(139, 92, 246, 0.28)", "icon": "🌱"},
    "immediate": {"label": "Accion Prioritaria (Hoy)", "color": "#22c55e", "bg": "rgba(34, 197, 94, 0.15)", "border": "rgba(34, 197, 94, 0.35)", "icon": "⚡"},
    "prioritaria": {"label": "Accion Prioritaria (Hoy)", "color": "#22c55e", "bg": "rgba(34, 197, 94, 0.15)", "border": "rgba(34, 197, 94, 0.35)", "icon": "⚡"},
    "goal": {"label": "Objetivo Maestro", "color": "#818cf8", "bg": "rgba(99, 102, 241, 0.12)", "border": "rgba(99, 102, 241, 0.28)", "icon": "🎯"},
    "alerta": {"label": "Contingencia", "color": "#ef4444", "bg": "rgba(239, 68, 68, 0.12)", "border": "rgba(239, 68, 68, 0.28)", "icon": "🚨"},
}

def render_box(box_data: dict | str, content: str = "", category: str = "general"):
    """Renderiza una tarjeta estructurada directamente desde los campos nativos JSON."""
    if isinstance(box_data, dict):
        box_title = (box_data.get("title") or "").strip()
        cat = (box_data.get("category") or "general").strip().lower()
        description = (box_data.get("description") or box_data.get("content") or "").strip()
        impact = (box_data.get("impact") or "").strip()
        raw_week = box_data.get("week")
        steps = box_data.get("steps") or []
    else:
        box_title = str(box_data).strip()
        cat = (category or "general").strip().lower()
        description = (content or "").strip()
        impact = ""
        raw_week = None
        steps = []

    week_str = f"Semana {raw_week}" if raw_week is not None and str(raw_week).strip() else ""
    if isinstance(steps, str):
        steps = [s.strip() for s in steps.split("\n") if s.strip()]

    cfg = CATEGORY_CONFIG.get(cat, {
        "label": cat.capitalize(),
        "color": "#94a3b8",
        "bg": "rgba(148, 163, 184, 0.12)",
        "border": "rgba(148, 163, 184, 0.25)",
        "icon": "📌"
    })

    with st.container():
        st.markdown('<span class="box-marker"></span>', unsafe_allow_html=True)

        # 1. Caso especial: Objetivo Maestro (Hero Card)
        if cat == "goal":
            c_left, c_right = st.columns([22, 1])
            with c_left:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(79, 140, 255, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%);
                            border: 1px solid rgba(79, 140, 255, 0.3); border-radius: 14px; padding: 16px 20px; margin-bottom: 8px;">
                    <div style="font-size: 0.76rem; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;">
                        🎯 Objetivo Maestro del Plan
                    </div>
                    <div style="font-size: 1.18rem; font-weight: 600; color: #f4f5f7; line-height: 1.4;">
                        {description or box_title}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c_right:
                st.button("✕", key=f"remove_{ss.case_id}_{box_title}", on_click=bs.remove_box, args=(box_title, ss.case_id))
            return

        # 2. Tarjetas de Accion y Tareas
        c_head, c_btn = st.columns([22, 1])
        with c_head:
            badges_html = []
            # Badge de categoria
            badges_html.append(
                f'<span style="background: {cfg["bg"]}; color: {cfg["color"]}; border: 1px solid {cfg["border"]}; '
                f'padding: 3px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">'
                f'{cfg["icon"]} {cfg["label"]}</span>'
            )
            # Badge de semana si existe
            if week_str:
                badges_html.append(
                    f'<span style="background: var(--surface-2); color: var(--muted); border: 1px solid var(--border); '
                    f'padding: 3px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 500;">'
                    f'📅 {week_str}</span>'
                )
            # Badge de impacto financiero si existe
            if impact:
                badges_html.append(
                    f'<span style="background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); '
                    f'padding: 3px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 600;">'
                    f'✨ {impact}</span>'
                )

            st.markdown(f'<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap;">{" ".join(badges_html)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size: 1.08rem; font-weight: 600; color: #f4f5f7; margin-bottom: 8px;">{box_title}</div>', unsafe_allow_html=True)

        with c_btn:
            st.button("✕", key=f"remove_{ss.case_id}_{box_title}", on_click=bs.remove_box, args=(box_title, ss.case_id))

        # Descripcion accesible (si no es identica al titulo)
        if description and description != box_title:
            st.markdown(f'<div style="color: var(--muted); font-size: 0.92rem; line-height: 1.5; margin-bottom: 8px;">{description}</div>', unsafe_allow_html=True)

        # Pasos secuenciales limpios
        if steps:
            steps_html = "".join([
                f'<li style="color: var(--text); margin-bottom: 6px; font-size: 0.92rem; line-height: 1.45;">{s}</li>'
                for s in steps
            ])
            st.markdown(f'<ol style="margin: 0 0 10px 18px; padding: 0;">{steps_html}</ol>', unsafe_allow_html=True)

def render_chart(chart: dict):
    """Renderiza graficos interactivos generados por el Co-Pilot o la tabla."""
    if not chart:
        return
    c_type = chart.get("type", "bar")
    title = chart.get("title", "")
    labels = chart.get("labels") or chart.get("categories") or []
    values = chart.get("values") or []

    if not labels or not values:
        return

    fig = go.Figure()
    if c_type == "bar":
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker_color="#4f8cff",
            text=[f"${v:,.0f}" if isinstance(v, (int, float)) and v >= 100 else str(v) for v in values],
            textposition="auto"
        ))
    elif c_type == "line":
        fig.add_trace(go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers",
            line=dict(color="#4f8cff", width=3),
            marker=dict(size=8, color="#22c55e")
        ))
    elif c_type in ("donut", "pie"):
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.45 if c_type == "donut" else 0.0,
            marker=dict(colors=[
                "#4f8cff", "#22c55e", "#f59e0b", "#ec4899", "#a855f7",
                "#06b6d4", "#14b8a6", "#eab308", "#6366f1", "#f97316"
            ]),
            textinfo="label+percent",
            hoverinfo="label+value+percent",
            textposition="inside"
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="#f4f5f7", size=15)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f4f5f7", family="Inter"),
        margin=dict(l=15, r=15, t=35, b=15),
        height=320,
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
    )
    st.plotly_chart(fig, use_container_width=True)

def add_column_popover():
    with st.popover("➕ Anadir Columna"):
        with st.form(f"add_col_{ss.case_id}", clear_on_submit=True):
            name = st.text_input("Nombre de la columna (ej: Fondo_Estudios)")
            default = st.number_input("Valor por defecto", value=0.0)
            if st.form_submit_button("Guardar") and name.strip():
                try:
                    ts.add_column(name.strip(), default, case_id=ss.case_id)
                    ss.table_version = ts.version(ss.case_id)
                    ss.df = ts.to_df(ts.load(ss.case_id))
                    ss.editor_gen += 1
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

# =============================================================================
# LAS TRES MODALIDADES (TABS)
# =============================================================================
tab_vertical, tab_table, tab_chat = st.tabs(["📋 Plan de Accion", "📊 Proyeccion & Datos", "💬 Chat Co-Pilot"])

# --- Tab 1: Vertical (Tablero Kanban interactivo) ---
with tab_vertical:
    kanban_ui.render()

# --- Tab 2: Table (Hoja de calculo mensual y graficos) ---
with tab_table:
    current_table = ts.load(ss.case_id)
    rows = current_table.get("rows", [])
    cols = current_table.get("columns", [])

    # Resumen superior de KPIs
    if rows:
        current_month = time.strftime("%Y-%m")
        active_row = next((r for r in rows if r.get("date") == current_month), rows[0])
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='kpi-pill'>Mes activo: <strong>{active_row.get('date', 'N/A')}</strong></div>", unsafe_allow_html=True)
        if "Patrimonio" in active_row:
            c2.markdown(f"<div class='kpi-pill'>Patrimonio: <strong>${active_row['Patrimonio']:,.0f}</strong></div>", unsafe_allow_html=True)
        if "Ingresos" in active_row and "Gastos_Fijos" in active_row:
            cf = active_row["Ingresos"] - active_row["Gastos_Fijos"]
            c3.markdown(f"<div class='kpi-pill'>Flujo libre: <strong>${cf:,.0f}</strong></div>", unsafe_allow_html=True)
        if "Deuda_Pendiente" in active_row:
            c4.markdown(f"<div class='kpi-pill'>Deuda viva: <strong>${active_row['Deuda_Pendiente']:,.0f}</strong></div>", unsafe_allow_html=True)

    # Grafico interactivo de evolucion temporal (Patrimonio, Deuda, Ahorro)
    if "df" in ss and not ss.df.empty and len(ss.df) > 1:
        with st.expander("📈 Proyeccion Financiera a 12 Meses (Plan Sherpas Wealth)", expanded=True):
            st.caption("Evolucion proyectada al cumplir el plan de accion: crecimiento de patrimonio neto (linea azul), amortizacion progresiva de deuda (linea roja punteada) y ahorro libre mensual generado (barras verdes). Reacciona en tiempo real a cualquier cambio en la tabla inferior o imprevisto gestionado por el Co-Pilot.")
            fig_proj = go.Figure()
            df_plot = ss.df
            if "Patrimonio" in df_plot.columns:
                fig_proj.add_trace(go.Scatter(
                    x=df_plot["date"], y=df_plot["Patrimonio"],
                    name="Patrimonio Neto", mode="lines+markers",
                    line=dict(color="#4f8cff", width=3),
                    marker=dict(size=6)
                ))
            if "Deuda_Pendiente" in df_plot.columns:
                fig_proj.add_trace(go.Scatter(
                    x=df_plot["date"], y=df_plot["Deuda_Pendiente"],
                    name="Deuda Pendiente", mode="lines+markers",
                    line=dict(color="#ef4444", width=2, dash="dot"),
                    marker=dict(size=6)
                ))
            if "Ahorro_Libre" in df_plot.columns:
                fig_proj.add_trace(go.Bar(
                    x=df_plot["date"], y=df_plot["Ahorro_Libre"],
                    name="Ahorro Mensual",
                    marker_color="rgba(34, 197, 94, 0.45)"
                ))
            fig_proj.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f4f5f7", family="Inter"),
                margin=dict(l=10, r=10, t=25, b=10),
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", tickprefix="$"),
            )
            st.plotly_chart(fig_proj, use_container_width=True)

    table_ui.render()

# --- Tab 3: Chat (Co-Pilot Conversacional en Streaming) ---
with tab_chat:
    # Chips de preguntas rapidas recomendadas para la presentacion
    st.write("**Preguntas de prueba rapida para la demo:**")
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    chip_text = None
    with c_btn1:
        if st.button("🚨 Gasto imprevisto (-2.000 $)", use_container_width=True):
            chip_text = "He tenido un accidente imprevisto y he tenido que desembolsar 2.000 $. Ajusta mi tabla para absorber el gasto y dime como afecta a mi plan."
    with c_btn2:
        if st.button("🔍 Diagnostico y score", use_container_width=True):
            chip_text = "Analiza mi score de salud financiera y explicame cual es mi cuello de botella principal segun mi informe."
    with c_btn3:
        if st.button("💰 Bonus de 15.000 $", use_container_width=True):
            chip_text = "Voy a recibir un bonus de 15.000 $. En lugar de gastarlo, amortiza la deuda de la tarjeta en la tabla y destina el resto a mi colchon de seguridad."
    with c_btn4:
        if st.button("📊 Comparativa visual", use_container_width=True):
            chip_text = "Muestrame un grafico comparativo con la distribucion de mis ingresos y gastos mensuales actuales."

    # Historial de mensajes
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("chart"):
                render_chart(m["chart"])

# =============================================================================
# CHAT INPUT Y STREAMING SSE
# =============================================================================
prompt_input = st.chat_input("Escribe tu consulta al Co-Pilot...")
active_prompt = chip_text or prompt_input

if active_prompt:
    ss.messages.append({"role": "user", "content": active_prompt})
    with tab_chat:
        with st.chat_message("user"):
            st.markdown(active_prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            tools_used = []
            applied_diffs = []
            changes_applied_flag = False
            received_chart = None

            ss.is_streaming = True
            try:
                # Preparar historial previo de conversacion (excluyendo el mensaje que se acaba de anadir)
                history_payload = [
                    {"role": m["role"], "content": m["content"]}
                    for m in ss.messages[:-1]
                ]
                payload = {
                    "message": active_prompt,
                    "case_id": ss.case_id,
                    "session_id": ss.session_id,
                    "history": history_payload
                }
                with httpx.Client(timeout=90.0) as client:
                    with client.stream(
                        "POST",
                        f"{API_BASE_URL}/api/chat/stream",
                        json=payload
                    ) as response:
                        for line in response.iter_lines():
                            if not line.startswith("data: "):
                                continue
                            raw_event = line[6:].strip()
                            if not raw_event:
                                continue
                            try:
                                event = json.loads(raw_event)
                                ev_type = event.get("type")
                                if ev_type in ("token", "delta"):
                                    delta = event.get("content") or event.get("delta", "")
                                    full_response += delta
                                    placeholder.markdown(full_response + "▌")
                                elif ev_type == "tool_start":
                                    tool_name = event.get("tool", "herramienta")
                                    tools_used.append(tool_name)
                                    status_info = f"\n\n*⚡ Ejecutando accion MCP: {tool_name}...*"
                                    placeholder.markdown((full_response + status_info) if full_response else f"*⚡ Ejecutando accion MCP: {tool_name}...*")
                                elif ev_type == "tool_end":
                                    tool_name = event.get("tool", "herramienta")
                                    is_mod = event.get("modified", False)
                                    t_diff = event.get("diff", "")
                                    if is_mod:
                                        changes_applied_flag = True
                                        if t_diff:
                                            applied_diffs.append(t_diff)
                                        else:
                                            applied_diffs.append(tool_name)
                                    placeholder.markdown(full_response + "▌" if full_response else "*Procesando respuesta...*")
                                elif ev_type == "state":
                                    state_reply = event.get("full_reply", "")
                                    if state_reply and not full_response:
                                        full_response = state_reply
                                    chart_data = event.get("chart_to_render")
                                    if chart_data:
                                        received_chart = chart_data
                                    if event.get("changes_applied"):
                                        changes_applied_flag = True
                                        if event.get("applied_summary"):
                                            applied_diffs.append(event.get("applied_summary"))
                                elif ev_type == "error":
                                    err_detail = event.get("detail", "Error en el servidor")
                                    placeholder.error(f"Error en el servidor: {err_detail}")
                            except json.JSONDecodeError:
                                continue

                if full_response:
                    placeholder.markdown(full_response)
                    if received_chart:
                        render_chart(received_chart)
                    msg_payload = {"role": "assistant", "content": full_response}
                    if received_chart:
                        msg_payload["chart"] = received_chart
                    ss.messages.append(msg_payload)
                else:
                    placeholder.warning("El Co-Pilot no emitio respuesta de texto.")

                if changes_applied_flag:
                    summary_msg = "; ".join(dict.fromkeys(applied_diffs)) or "Cambios aplicados con exito"
                    ss.notify_changes = True
                    ss.notify_msg = summary_msg
                    st.toast(f"Cambios aplicados: {summary_msg}", icon="✅")

                # Sincronizar estado interno de tabla y cajas para que las otras pestanas se actualicen
                ss.table_version = ts.version(ss.case_id)
                ss.boxes_version = bs.version(ss.case_id)
                ss.df = ts.to_df(ts.load(ss.case_id))
                ss.boxes = bs.load(ss.case_id).get("boxes", [])
                ss.editor_gen += 1
                st.rerun()

            except Exception as e:
                placeholder.error(f"Fallo en la comunicacion con el Co-Pilot: {e}")
            finally:
                ss.is_streaming = False

    # JavaScript auto-scroll para que el chat baje automaticamente
    st.html(
        """
        <script>
        const main = document.querySelector('[data-testid="stMain"]');
        if (main) main.scrollTo({top: main.scrollHeight, behavior: 'smooth'});
        </script>
        """,
        unsafe_allow_javascript=True
    )

# =============================================================================
# WATCHER EN SEGUNDO PLANO
# =============================================================================
@st.fragment(run_every=1)
def watcher():
    # Evitar recargas si hay una consulta de chat procesandose
    if ss.get("is_streaming", False):
        return
    if table_ui.changed() or kanban_ui.changed():
        st.toast("Cambios aplicados", icon="🔄")
        st.rerun()

watcher()
