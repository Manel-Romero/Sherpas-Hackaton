import streamlit as st
import streamlit.components.v1 as components  # needed for the auto-scroll script
from style import style
import table_store as ts
import kanban_store as ks
from pathlib import Path
import kanban_ui
import table_ui

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

# =============================================================================
# 2. STATE
# =============================================================================
# Streamlit re-runs this whole file every time you click something. Anything
# that must be remembered between runs has to live in ss.

# Boxes currently visible. Created only on the first run, so removing a box
# isn't undone by the next rerun.

ss = st.session_state
# Chat history: a list of {"role": "user" | "assistant", "content": "..."}
if "messages" not in ss:
    ss.messages = []

table_ui.refresh()
      
# =============================================================================
# THE THREE MODES (TABS)
# =============================================================================

kanban, table, chat = st.tabs(["Kanban", "Table", "Chat"])

with kanban:
    kanban_ui.render()

# --- Chat mode: the full conversation so far ---
with chat:
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

# ---- Table: drawn once per real change ----
with table:
    table_ui.render()
# =============================================================================
# CHAT INPUT
# =============================================================================
# st.chat_input is called here, OUTSIDE the tabs, because Streamlit only pins
# it to the bottom of the screen when it isn't inside a tab or column. The CSS
# above hides it unless the Chat tab is active.
#
# The new messages are stored BEFORE the tabs are drawn (below), so they show
# up immediately and we don't need st.rerun().

new_message = False   # becomes True only on the run where something was sent
if prompt := st.chat_input("Type a message..."):
    with chat:
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            st.write_stream(f"Dijiste {prompt}")
        
# =============================================================================
# AUTO-SCROLL
# =============================================================================
# Streamlit doesn't scroll down by itself. After a message is sent, we run a
# tiny JavaScript snippet that scrolls the page to the bottom. It runs twice
# (after 100 ms and 500 ms) to make sure the new message has been drawn first.

if new_message:
    components.html(
        """
        <script>
        const go = () => {
            // components.html lives in an iframe, so we reach the real page via window.parent
            const main = window.parent.document.querySelector('[data-testid="stMain"]');
            if (main) main.scrollTo({top: main.scrollHeight});
        };
        setTimeout(go, 100);
        setTimeout(go, 500);
        </script>
        """,
        height=0,  # invisible: it only exists to run the script
    )


# =============================================================================
# WATCHER: cheap check, full rerun only if the file changed ----
# =============================================================================

@st.fragment(run_every=1)
def watcher():
    if table_ui.changed() or kanban_ui.changed():
        st.rerun()

watcher()