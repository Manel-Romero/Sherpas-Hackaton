import streamlit as st
import streamlit.components.v1 as components  # needed for the auto-scroll script
from style import style
import table_store as ts
import boxes_store as bs



# "wide" lets the content (and our full-width top bar) use the whole screen.
st.set_page_config(page_title="Layouts", layout="wide")
#Style
st.markdown(style,unsafe_allow_html=True)

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

if "table_version" not in ss or ts.version() != ss.table_version:
    ss.table_version = ts.version()
    ss.df = ts.to_df(ts.load())
    ss.editor_gen = ss.get("editor_gen", 0) + 1   # new key -> editor resets
    
if "boxes_version" not in ss or bs.version() != ss.boxes_version:
    ss.boxes_version = bs.version()
    ss.boxes = bs.load()["boxes"]

# =============================================================================
# 3. COMPONENTS
# =============================================================================

def box(title: str, content: str = "Vacío"):
    """Draw one box."""
    with st.container():
        # Invisible marker: the CSS above looks for it to know "this container
        # is a box" and gives it the card style.
        st.markdown('<span class="box-marker"></span>', unsafe_allow_html=True)

        # Two columns: wide one for the title, narrow one for the button
        head, btn = st.columns([20, 1])
        head.subheader(title)
        btn.button(
            "✕",
            key=f"remove_{title}",     # each button needs a unique key
            on_click=remove_box,       # runs remove_box(...) when clicked
            args=(title,),             # ...with this box's title
        )

        st.write(content)     # <- put your own content here

def remove_box(title: str):
    data = bs.load()
    data["boxes"] = [b for b in data["boxes"] if b["title"] != title]
    bs.save(data)

def add_column():
    with st.popover("➕ Add column"):
        with st.form("add_col", clear_on_submit=True):
            name = st.text_input("Column name")
            default = st.number_input("Default value", value=0.0)
            if st.form_submit_button("Add") and name.strip():
                try:
                    table = ts.load()
                    table["columns"].append(name.strip())
                    for r in table["rows"]:
                        r[name.strip()] = default
                    ts.save(table)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        
# =============================================================================
# THE THREE MODES (TABS)
# =============================================================================

vertical, table, chat = st.tabs(["Vertical","Table", "Chat"])

# --- Vertical mode: the boxes, stacked ---
with vertical:
    for b in ss.boxes:
        box(b["title"], b["content"] or "Vacío")

# --- Chat mode: the full conversation so far ---
with chat:
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

# ---- Table: drawn once per real change ----
with table:
    add_column()

    columns = list(st.session_state.df.columns[1:])
    config = {"date": st.column_config.TextColumn(
        "Month (YYYY-MM)",
        required=True,
        default=ts.default_month(ts.load()),   # <- new rows start with the next month
    )}
    for c in columns:
        config[c] = st.column_config.NumberColumn(c)
    
    edited = st.data_editor(
        st.session_state.df,
        key=f"editor-{st.session_state.editor_gen}",
        num_rows="dynamic",
        column_config=config,
        hide_index=True,
    )

    try:
        new = ts.from_df(edited, columns)
        current = ts.load()
        if new != current:
            row_added = len(new["rows"]) > len(current["rows"])
            ts.save(new)
            st.session_state.table_version = ts.version()   # our own save
            if row_added:
                # Rebuild the base table and reset the editor, so the NEXT new row
                # gets the next month instead of repeating this one
                st.session_state.df = ts.to_df(new)
                st.session_state.editor_gen += 1
                st.rerun()
    except ValueError as e:
        st.error(str(e))


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
    if ts.version() != ss.table_version or bs.version() != ss.boxes_version:
        st.rerun()  # reruns the whole app, which reloads the table

watcher()