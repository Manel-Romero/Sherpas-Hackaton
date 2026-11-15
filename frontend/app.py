import os
import sys
import json
from pathlib import Path

# Asegurar que el directorio raiz del proyecto este siempre en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    from frontend.style import style
    from frontend import table_store as ts
    from frontend import boxes_store as bs
except ImportError:
    from style import style
    import table_store as ts
    import boxes_store as bs


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
if "messages" not in ss:
    ss.messages = []
if "cases_list" not in ss:
    ss.cases_list = []
if "editor_gen" not in ss:
    ss.editor_gen = 0
if "table_version" not in ss:
    ss.table_version = 0
if "boxes_version" not in ss:
    ss.boxes_version = 0
if "df" not in ss:
    ss.df = ts.to_df(ts.load(ss.case_id))
if "boxes" not in ss:
    ss.boxes = bs.load(ss.case_id).get("boxes", [])

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
            r = httpx.post(f"{API_BASE_URL}/api/cases/{case_id}/init", json={}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                mp = data.get("master_plan", {})
                ss.messages = [
                    {
                        "role": "assistant",
                        "content": f"¡Hola! He analizado tu perfil financiero completo de Sherpas. {mp.get('headline', '')}.\n\nTu accion inmediata para hoy es: **{mp.get('immediate_action', {}).get('title', '')}**. ¿En que puedo ayudarte?"
                    }
                ]
                # Recargar tabla y cajas
                ss.df = ts.to_df(ts.load(case_id))
                ss.boxes = bs.load(case_id).get("boxes", [])
                ss.table_version = ts.version(case_id)
                ss.boxes_version = bs.version(case_id)
                ss.editor_gen += 1
                st.success("Plan maestro inicializado con exito")
                st.rerun()
            else:
                st.error(f"Fallo al inicializar: {r.text}")
        except Exception as e:
            st.error(f"Error conectando con el backend: {e}")

if not ss.cases_list:
    fetch_cases()

# Sincronizar versiones de ficheros locales si cambiaron
if ts.version(ss.case_id) != ss.table_version:
    ss.table_version = ts.version(ss.case_id)
    ss.df = ts.to_df(ts.load(ss.case_id))
    ss.editor_gen += 1

if bs.version(ss.case_id) != ss.boxes_version:
    ss.boxes_version = bs.version(ss.case_id)
    ss.boxes = bs.load(ss.case_id).get("boxes", [])

# =============================================================================
# CABECERA SUPERIOR: SELECTOR Y CARGA DE PLAN
# =============================================================================
case_map = {c["id"]: f"{c.get('title', c['id'])} ({c.get('city', '')}) - Score: {c.get('score', 0)}" for c in ss.cases_list}
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
        ss.messages = []
        ss.df = ts.to_df(ts.load(selected_case))
        ss.boxes = bs.load(selected_case).get("boxes", [])
        ss.table_version = ts.version(selected_case)
        ss.boxes_version = bs.version(selected_case)
        ss.editor_gen += 1
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
def render_box(title: str, content: str, category: str = "general"):
    """Dibuja una tarjeta con diseno adaptable."""
    with st.container():
        st.markdown('<span class="box-marker"></span>', unsafe_allow_html=True)
        head, btn = st.columns([20, 1])
        
        is_immediate = category == "immediate" or title.startswith("⚡")
        if is_immediate:
            head.markdown('<span class="immediate-badge">⚡ Accion Prioritaria (Hoy)</span>', unsafe_allow_html=True)
            
        head.subheader(title)
        btn.button(
            "✕",
            key=f"remove_{ss.case_id}_{title}",
            on_click=bs.remove_box,
            args=(title, ss.case_id),
        )
        st.markdown(content.replace("\n", "  \n"))

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
tab_vertical, tab_table, tab_chat = st.tabs(["Vertical", "Table", "Chat"])

# --- Tab 1: Vertical (Cajas y tareas) ---
with tab_vertical:
    boxes = ss.boxes
    if not boxes:
        st.info("No hay tarjetas activas. Pulsa 'Cargar / Reiniciar Plan' para generar la sintesis del caso.")
    else:
        for b in boxes:
            render_box(b.get("title", ""), b.get("content", "Vacio"), b.get("category", "general"))

# --- Tab 2: Table (Hoja de calculo mensual) ---
with tab_table:
    current_table = ts.load(ss.case_id)
    rows = current_table.get("rows", [])
    cols = current_table.get("columns", [])

    # Resumen superior de KPIs
    if rows:
        latest_row = rows[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='kpi-pill'>Mes activo: <strong>{latest_row.get('date', 'N/A')}</strong></div>", unsafe_allow_html=True)
        if "Patrimonio" in latest_row:
            c2.markdown(f"<div class='kpi-pill'>Patrimonio: <strong>${latest_row['Patrimonio']:,.0f}</strong></div>", unsafe_allow_html=True)
        if "Ingresos" in latest_row and "Gastos_Fijos" in latest_row:
            cf = latest_row["Ingresos"] - latest_row["Gastos_Fijos"]
            c3.markdown(f"<div class='kpi-pill'>Ahorro mensual: <strong>${cf:,.0f}</strong></div>", unsafe_allow_html=True)
        if "Deuda_Pendiente" in latest_row:
            c4.markdown(f"<div class='kpi-pill'>Deuda viva: <strong>${latest_row['Deuda_Pendiente']:,.0f}</strong></div>", unsafe_allow_html=True)

    add_column_popover()

    columns_in_df = list(ss.df.columns[1:])
    config = {
        "date": st.column_config.TextColumn(
            "Mes (YYYY-MM)",
            required=True,
            default=ts.default_month(current_table),
        )
    }
    for c in columns_in_df:
        config[c] = st.column_config.NumberColumn(c, format="$%.2f")

    edited = st.data_editor(
        ss.df,
        key=f"editor-{ss.editor_gen}-{ss.case_id}",
        num_rows="dynamic",
        column_config=config,
        hide_index=True,
    )

    try:
        new_data = ts.from_df(edited, columns_in_df)
        if new_data != current_table:
            row_added = len(new_data["rows"]) > len(current_table["rows"])
            ts.save(new_data, case_id=ss.case_id)
            ss.table_version = ts.version(ss.case_id)
            if row_added:
                ss.df = ts.to_df(new_data)
                ss.editor_gen += 1
                st.rerun()
    except ValueError as e:
        st.error(str(e))

# --- Tab 3: Chat (Co-Pilot Conversacional en Streaming) ---
with tab_chat:
    # Chips de preguntas rapidas recomendadas para la presentacion
    st.write("**Preguntas de prueba rapida para la demo:**")
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    chip_text = None
    with c_btn1:
        if st.button("🚨 Tuve un accidente (-2.000 €)", use_container_width=True):
            chip_text = "He tenido un accidente imprevisto y he tenido que desembolsar 2.000 €. Ajusta mi tabla para absorber el gasto y dime como afecta a mi plan."
    with c_btn2:
        if st.button("🔍 Explica mi score bajo", use_container_width=True):
            chip_text = "¿Por que mi score es tan bajo y cual es mi cuello de botella principal segun mi informe?"
    with c_btn3:
        if st.button("💰 Bonus de 15.000 $", use_container_width=True):
            chip_text = "Voy a recibir un bonus de 15.000 $. En lugar de gastarlo, amortiza la deuda de la tarjeta en la tabla y destina el resto a mi colchon de seguridad."

    # Historial de mensajes
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

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

            try:
                with httpx.Client(timeout=60.0) as client:
                    with client.stream(
                        "POST",
                        f"{API_BASE_URL}/api/chat/stream",
                        json={"message": active_prompt, "case_id": ss.case_id}
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
                                if ev_type == "delta":
                                    delta = event.get("delta", "")
                                    full_response += delta
                                    placeholder.markdown(full_response + "▌")
                                elif ev_type == "tool_start":
                                    tools_used.append(event.get("tool", "tool"))
                            except json.JSONDecodeError:
                                continue

                placeholder.markdown(full_response)
                ss.messages.append({"role": "assistant", "content": full_response})

                # Si el modelo ejecuto herramientas que modificaron tabla o cajas, recargar
                if tools_used or ts.version(ss.case_id) != ss.table_version or bs.version(ss.case_id) != ss.boxes_version:
                    ss.table_version = ts.version(ss.case_id)
                    ss.boxes_version = bs.version(ss.case_id)
                    ss.df = ts.to_df(ts.load(ss.case_id))
                    ss.boxes = bs.load(ss.case_id).get("boxes", [])
                    ss.editor_gen += 1
                    st.rerun()

            except Exception as e:
                placeholder.error(f"Fallo en la comunicacion con el Co-Pilot: {e}")

    # JavaScript auto-scroll para que el chat baje automaticamente
    components.html(
        """
        <script>
        const main = window.parent.document.querySelector('[data-testid="stMain"]');
        if (main) main.scrollTo({top: main.scrollHeight, behavior: 'smooth'});
        </script>
        """,
        height=0
    )

# =============================================================================
# WATCHER EN SEGUNDO PLANO
# =============================================================================
@st.fragment(run_every=1)
def watcher():
    if ts.version(ss.case_id) != ss.table_version or bs.version(ss.case_id) != ss.boxes_version:
        st.rerun()

watcher()
