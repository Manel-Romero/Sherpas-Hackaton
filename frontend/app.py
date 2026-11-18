# Sherpas Wealth Co-Pilot: Frontend Streamlit
import os
import sys
import time
from pathlib import Path

# Configuracion de rutas
FRONTEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FRONTEND_DIR.parent
for p in (str(FRONTEND_DIR), str(PROJECT_ROOT)):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

import httpx
import streamlit as st
from streamlit import config as _st_config

# Tema oscuro corporativo forzado desde el codigo (Sherpas Wealth official palette)
for _key, _val in {
    "base": "dark",
    "primaryColor": "#4565d6",
    "backgroundColor": "#04070d",
    "secondaryBackgroundColor": "#0a0f18",
    "textColor": "#f8fafc"
}.items():
    _st_config.set_option(f"theme.{_key}", _val)

import chat_ui
import dashboard_ui
import kanban_store as ks
import kanban_ui
import table_store as ts
import table_ui
import tutorial
import users_ui
import workspaces
from style import style

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Sherpas Wealth | Generative Finance", page_icon="🧭", layout="wide")
st.markdown(style, unsafe_allow_html=True)

ss = st.session_state

# ---- Entrada: seleccion de cliente obligatorio ----
if not ss.get("user") or workspaces.get_user(ss.user) is None:
    ss.pop("user", None)
    users_ui.login_screen()

user = workspaces.get_user(ss.user)

# Asignar caso activo a los almacenes
ts.set_case(ss.user)
ks.set_case(ss.user)
table_ui.refresh()

if ss.pop("notify_changes", False):
    st.toast(f"Cambios aplicados: {ss.get('notify_msg', '')}", icon="✅")


def initialize_plan() -> None:
    """Solicita al backend analizar el caso y generar plan maestro, proyecciones y tareas."""
    with st.spinner("El Co-Pilot esta analizando el perfil financiero completo y generando el plan maestro..."):
        try:
            r = httpx.post(f"{API_BASE_URL}/api/cases/{ss.case_id}/init",
                           json={"session_id": ss.session_id}, timeout=180)
        except httpx.ConnectError:
            st.error(f"No se puede conectar con el backend en {API_BASE_URL}. "
                     "Asegurate de que este iniciado.")
            return
        except Exception as e:
            st.error(f"Error al llamar al backend: {e}")
            return
    if r.status_code != 200:
        st.error(f"No se pudo cargar el plan: {r.text[:300]}")
        return
    plan = r.json().get("master_plan", {})
    action = plan.get("immediate_action", {}).get("title", "")
    ss.messages = [{
        "role": "assistant",
        "content": f"¡Hola! He analizado tu perfil financiero de Sherpas. {plan.get('headline', '')}\n\n"
                   f"Tu primera accion prioritaria para hoy es: **{action}**. ¿En que puedo ayudarte?",
    }]
    ss.session_id = f"sess_{ss.case_id}_{int(time.time())}"
    ss.pop("table_version", None)
    chat_ui.persist()
    st.rerun()


# ---- Franja de cliente superior y tutorial ----
want_tutorial, want_plan = users_ui.user_strip(user)
if want_tutorial:
    tutorial.request(ss.user)
if want_plan:
    initialize_plan()
tutorial.maybe_show(ss.user)

# ---- Entrada de chat (anclada abajo, visible unicamente en la pestana de Chat) ----
prompt = chat_ui.input_box()

# ---- Las tres modalidades de trabajo ----
tab_plan, tab_data, tab_chat = st.tabs(["📋 Plan de accion", "📊 Proyeccion & datos", "💬 Chat Co-Pilot"])

with tab_plan:
    dashboard_ui.render_plan_progress()
    kanban_ui.render()

with tab_data:
    summary = st.container()
    table_ui.render()
    with summary:
        table = ts.load()
        dashboard_ui.render_kpis(table)
        dashboard_ui.render_projection(ts.to_df(table))
        dashboard_ui.render_distribution(table)

with tab_chat:
    chat_ui.render(prompt)

chat_ui.persist()


# ---- Vigilante en segundo plano para sincronizar cambios externos ----
@st.fragment(run_every=1)
def watcher():
    if ss.get("is_streaming"):
        return
    if table_ui.changed() or kanban_ui.changed():
        st.toast("Plan actualizado", icon="🔄")
        st.rerun()


watcher()
