"""Sherpas Wealth Co-Pilot: frontend de Streamlit.

Arrancar (con el backend ya en marcha, ver QUICKSTART.md):
    streamlit run frontend/app.py

Módulos de esta carpeta:
    users_ui.py       entrada, cambio de usuario y clonado de usuarios
    workspaces.py     usuarios en disco (data/cases/<id>/)
    tutorial.py       tutorial de bienvenida
    dashboard_ui.py   KPIs, gráficos y progreso
    chat_ui.py        chat con el Co-Pilot (SSE)
Del directorio raíz: table_store/table_ui (tabla), kanban_store/kanban_ui (tablero).
"""
import os
import sys
import time
from pathlib import Path

# La raíz del proyecto primero (table_store, kanban_ui...), y esta carpeta para los módulos nuevos.
FRONTEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FRONTEND_DIR.parent
for p in (str(FRONTEND_DIR), str(PROJECT_ROOT)):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

import httpx
import streamlit as st
from streamlit import config as _st_config

# Tema oscuro forzado desde el código: así no depende de .streamlit/config.toml ni de desde qué
# carpeta se lance la app (sin esto, la tabla y los menús salen en blanco en equipos con modo claro).
for _key, _val in {"base": "dark", "primaryColor": "#86c9a4", "backgroundColor": "#0e1311",
                   "secondaryBackgroundColor": "#151c19", "textColor": "#eef3ef"}.items():
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

st.set_page_config(page_title="Sherpas Co-Pilot", page_icon=":material/landscape:", layout="wide")
st.markdown(style, unsafe_allow_html=True)

ss = st.session_state

# ---- Entrada: sin usuario no se ejecuta nada más ----
if not ss.get("user") or workspaces.get_user(ss.user) is None:
    ss.pop("user", None)
    users_ui.login_screen()

user = workspaces.get_user(ss.user)

# Esta ejecución trabaja con los ficheros de este usuario
ts.set_case(ss.user)
ks.set_case(ss.user)
table_ui.refresh()

if ss.pop("notify_changes", False):
    st.toast(f"Cambios aplicados: {ss.get('notify_msg', '')}", icon=":material/check_circle:")


def initialize_plan(auto: bool = False) -> None:
    """Pide al backend que analice el caso y genere plan, tabla y tareas. Guarda también el resumen.
    `auto=True`: es la carga automática de la primera entrada (si falla, no se reintenta en esta sesión)."""
    if auto:
        ss.auto_init_tried = True
    msg = ("Preparando tu plan a medida: el Co-Pilot lee tu informe y tu perfil… (puede tardar un minuto)"
           if auto else "El Co-Pilot está analizando tu caso y preparando el plan… (puede tardar un minuto)")
    with st.spinner(msg):
        workspaces.backup_plan_files(ss.user)       # init sobrescribe tabla y tareas: guardamos copia
        try:
            r = httpx.post(f"{API_BASE_URL}/api/cases/{ss.case_id}/init",
                           json={"session_id": ss.session_id}, timeout=180)
        except httpx.ConnectError:
            st.error(f"No puedo conectar con el backend en {API_BASE_URL}. "
                     "Arráncalo con `uvicorn backend.app.main:app --port 8000`.")
            return
        except Exception as e:
            st.error(f"Error al llamar al backend: {e}")
            return
    if r.status_code != 200:
        st.error(f"No se pudo cargar el plan: {r.text[:300]}")
        return
    workspaces.save_plan_summary(ss.user, r.json())     # el backend solo lo guarda en memoria: lo guardamos en data/
    plan = r.json().get("master_plan", {})
    action = plan.get("immediate_action", {}).get("title", "")
    if not (auto and ss.get("messages")):               # la carga automática no borra una conversación previa
        ss.messages = [{
            "role": "assistant",
            "content": f"¡Hola! He analizado tu caso. {plan.get('headline', '')}\n\n"
                       f"Tu primera acción, para hoy: **{action}**. ¿Quieres que te la explique?",
        }]
    ss.session_id = f"sess_{ss.case_id}_{int(time.time())}"
    ss.pop("table_version", None)
    chat_ui.persist()
    st.rerun()


# ---- Franja de usuario + tutorial ----
want_tutorial, want_plan = users_ui.user_strip(user)
if want_tutorial:
    tutorial.request(ss.user)
if want_plan:
    initialize_plan()
elif not ss.get("auto_init_tried") and workspaces.load_plan_summary(ss.user) is None:
    initialize_plan(auto=True)      # primera entrada: genera el plan y el resumen antes del tutorial
tutorial.maybe_show(ss.user)

# ---- Barra de chat (se ancla abajo; el CSS solo la muestra en la pestaña Chat) ----
prompt = chat_ui.input_box()

# ---- Las tres pestañas ----
tab_plan, tab_data, tab_chat = st.tabs(["Plan de acción", "Proyección y datos", "Chat Co-Pilot"])

with tab_plan:
    dashboard_ui.render_plan_progress()
    kanban_ui.render()

with tab_data:
    summary = st.container()          # se rellena después de la tabla, para reflejar lo que acabas de editar
    table_ui.render()
    with summary:
        table = ts.load()
        dashboard_ui.render_kpis(table)
        dashboard_ui.render_projection(ts.to_df(table))
        dashboard_ui.render_distribution(table)

with tab_chat:
    chat_ui.render(prompt)

chat_ui.persist()


# ---- Vigilante: si un fichero cambia desde fuera (el Co-Pilot), se redibuja ----
@st.fragment(run_every=1)
def watcher():
    if ss.get("is_streaming"):
        return
    if table_ui.changed() or kanban_ui.changed():
        st.toast("Plan actualizado", icon=":material/sync:")
        st.rerun()


watcher()
