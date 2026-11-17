import streamlit as st
from pathlib import Path
from style import style
import table_store as ts
import kanban_store as ks
import chat_store as cs

import kanban_ui
import table_ui
"""import chat_ui"""

# "wide" lets the content (and our full-width top bar) use the whole screen.
st.set_page_config(page_title="Layouts", layout="wide")
#Style
st.markdown(style,unsafe_allow_html=True)

def require_login() -> str:
    if user := st.session_state.get("user"):
        folder = Path("data") / user
        folder.mkdir(parents=True, exist_ok=True)
        ts.DATA_FILE = folder / "table.json"
        ks.KANBAN_FILE = folder / "kanban.json"
        cs.CHAT_FILE = folder / "chat.json"
        return st.session_state.user
    st.title("Login")
    with st.form("login"):
        username = st.text_input("User")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log in"):
                st.session_state.user = username.strip().lower()
                st.rerun()
    st.stop()          # nothing below runs until someone is logged in

require_login()

ss = st.session_state

table_ui.refresh()
      
# =============================================================================
# THE THREE MODES (TABS)
# =============================================================================

kanban, table, chat = st.tabs(["Kanban", "Table", "Chat"])

with kanban:
    kanban_ui.render()

# --- Chat mode: the full conversation so far ---
"""with chat:
    chat_ui.render_history()
chat_ui.handle_input(chat)   # top level, outside the tabs, replacing the old `if prompt := st.chat_input(...)` block
"""
# ---- Table: drawn once per real change ----
with table:
    table_ui.render()

# =============================================================================
# WATCHER: cheap check, full rerun only if the file changed ----
# =============================================================================

@st.fragment(run_every=1)
def watcher():
    if table_ui.changed() or kanban_ui.changed():
        st.rerun()

watcher()