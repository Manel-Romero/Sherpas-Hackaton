"""Drag-and-drop kanban board with an ✕ on every card.

The board itself is a tiny custom Streamlit component: kanban_frontend/index.html,
which this file creates by itself from BOARD_HTML
(plain HTML + JS, embedded below as BOARD_HTML). It sends two kinds of events back to Python:
  {"type": "move",   "layout": {status: [card ids]}}   (a card was dragged)
  {"type": "delete", "id": "..."}                      (the ✕ was clicked)

In app.py, inside the first tab:
    import kanban_ui
    with kanban:
        kanban_ui.render()
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import kanban_store as ks

BOARD_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  /* Change the colors here (they match style.py) */
  :root {
    --surface: #111318; --surface-2: #181b23;
    --border: rgba(255,255,255,0.08); --border-strong: rgba(255,255,255,0.16);
    --text: #f4f5f7; --muted: rgba(244,245,247,0.62); --accent: #4f8cff;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; background: transparent; color: var(--text);
               font-family: -apple-system, "Segoe UI", system-ui, sans-serif; }
  .board { display: grid; gap: 14px; padding: 4px 2px 8px; align-items: start; }
  @media (max-width: 640px) { .board { grid-template-columns: 1fr !important; } }
  .column { background: var(--surface); border: 1px solid var(--border);
            border-radius: 16px; padding: 12px; }
  .header { display: flex; justify-content: space-between; font-weight: 600; padding: 2px 4px 10px; }
  .count { color: var(--muted); font-weight: 500; }
  .body { min-height: 80px; border-radius: 10px; padding: 2px; }   /* empty columns stay droppable */
  .body.over { outline: 1px dashed var(--accent); }
  .card { position: relative; background: var(--surface-2); border: 1px solid var(--border);
          border-radius: 12px; padding: 12px 14px; margin-bottom: 8px; cursor: grab; }
  .card:hover { border-color: var(--border-strong); }
  .card.dragging { opacity: 0.35; }
  .title { font-weight: 600; padding-right: 26px; overflow-wrap: anywhere; }
  .content { color: var(--muted); font-size: 0.9rem; line-height: 1.5; margin-top: 6px;
             white-space: pre-wrap; overflow-wrap: anywhere; }
  .x { position: absolute; top: 8px; right: 8px; width: 24px; height: 24px; border: none;
       border-radius: 8px; background: transparent; color: var(--muted); font-size: 13px; cursor: pointer; }
  .x:hover { background: rgba(255,255,255,0.1); color: var(--text); }
</style>
</head>
<body>
<div id="board" class="board"></div>
<script>
const board = document.getElementById("board");
let lastArgs = null, lastLayout = "", dragged = null, dropped = false, seq = 0;

// ---- talking to Streamlit (the plain component protocol, no library needed) ----
function post(type, extra) {
  window.parent.postMessage(Object.assign({isStreamlitMessage: true, type: type}, extra), "*");
}
function setHeight() { post("streamlit:setFrameHeight", {height: board.scrollHeight + 16}); }
function emit(value) {                       // nonce makes every event unique
  value.nonce = Date.now() + "-" + (++seq);
  post("streamlit:setComponentValue", {value: value, dataType: "json"});
}

// ---- helpers ----
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;   // textContent: card text can never run as HTML
  return e;
}
function layoutOf() {                        // {status: [card ids in order]} read from the screen
  const out = {};
  board.querySelectorAll(".column").forEach(col => {
    out[col.dataset.status] = [...col.querySelectorAll(".card")].map(c => c.dataset.id);
  });
  return out;
}
function updateCounts() {
  board.querySelectorAll(".column").forEach(col => {
    col.querySelector(".count").textContent = col.querySelectorAll(".card").length;
  });
}
function clearOver() { board.querySelectorAll(".body.over").forEach(b => b.classList.remove("over")); }
function cardAfter(body, y) {                // the card just below the mouse (null = end of column)
  let best = {offset: -Infinity, el: null};
  body.querySelectorAll(".card:not(.dragging)").forEach(c => {
    const box = c.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > best.offset) best = {offset: offset, el: c};
  });
  return best.el;
}

function makeCard(c) {
  const card = el("div", "card");
  card.draggable = true;
  card.dataset.id = c.id;
  const x = el("button", "x", "✕");
  x.title = "Delete card";
  x.addEventListener("click", ev => { ev.stopPropagation(); emit({type: "delete", id: c.id}); });
  card.append(x, el("div", "title", c.title));
  if (c.content) card.append(el("div", "content", c.content));

  card.addEventListener("dragstart", ev => {
    dragged = card; dropped = false;
    card.classList.add("dragging");
    ev.dataTransfer.effectAllowed = "move";
    ev.dataTransfer.setData("text/plain", c.id);      // Firefox needs some data to start a drag
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("dragging");
    clearOver();
    if (!dropped) render(lastArgs);                    // cancelled drag: put everything back
    dragged = null;
  });
  return card;
}

function render(args) {
  lastArgs = args;
  const statuses = Object.entries(args.statuses);
  board.innerHTML = "";
  board.style.gridTemplateColumns = "repeat(" + statuses.length + ", 1fr)";
  for (const [key, label] of statuses) {
    const col = el("div", "column");
    col.dataset.status = key;
    const header = el("div", "header");
    header.append(el("span", "", label), el("span", "count", "0"));
    const body = el("div", "body");

    body.addEventListener("dragover", ev => {
      if (!dragged) return;
      ev.preventDefault();
      clearOver(); body.classList.add("over");
      const after = cardAfter(body, ev.clientY);
      if (after) { if (after !== dragged.nextElementSibling || dragged.parentNode !== body) body.insertBefore(dragged, after); }
      else if (dragged.parentNode !== body || dragged !== body.lastElementChild) body.appendChild(dragged);
    });
    body.addEventListener("drop", ev => {
      ev.preventDefault();
      dropped = true; clearOver(); updateCounts(); setHeight();
      const now = JSON.stringify(layoutOf());
      if (now !== lastLayout) { lastLayout = now; emit({type: "move", layout: layoutOf()}); }
    });

    args.cards.filter(c => c.status === key).forEach(c => body.append(makeCard(c)));
    col.append(header, body);
    board.append(col);
  }
  updateCounts();
  lastLayout = JSON.stringify(layoutOf());
  setHeight();
}

window.addEventListener("message", ev => {
  if (ev.data && ev.data.type === "streamlit:render") render(ev.data.args);
});
window.addEventListener("resize", setHeight);
post("streamlit:componentReady", {apiVersion: 1});
</script>
</body>
</html>
"""

# The board's HTML lives in this file (see BOARD_HTML below) and is written to a folder
# next to this module at startup, so there is nothing else to copy around.
_FRONTEND = Path(__file__).with_name("kanban_frontend")

def changed() -> bool:
    return ks.version() != st.session_state.kanban_version


def _write_frontend() -> None:
    _FRONTEND.mkdir(exist_ok=True)
    target = _FRONTEND / "index.html"
    if not target.exists() or target.read_text(encoding="utf-8") != BOARD_HTML:
        target.write_text(BOARD_HTML, encoding="utf-8")


_write_frontend()
_board = components.declare_component("kanban_board", path=str(_FRONTEND))


def _add_card():
    with st.popover("➕ Add card"):
        with st.form("add_card", clear_on_submit=True):
            title = st.text_input("Title")
            content = st.text_area("Description")
            status = st.selectbox("Column", list(ks.STATUSES), format_func=ks.STATUSES.get)
            if st.form_submit_button("Add") and title.strip():
                try:
                    ks.add_card(title, content, status)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

def render():
    ss = st.session_state
    ss.board_rev = ss.get("board_rev", 0) + 1     # changes every run -> the board redraws from the file
    ss.kanban_version = ks.version()              # the watcher compares against this

    a, _ = st.columns([2, 7])
    with a:
        _add_card()

    event = _board(
        cards=ks.load()["cards"],
        statuses=ks.STATUSES,
        rev=ss.board_rev,
        key="kanban",
        default=None,
    )

    # The component keeps returning its LAST event on every rerun,
    # so each event is handled only once (they carry a unique nonce).
    if event and event.get("nonce") != ss.get("last_nonce"):
        ss.last_nonce = event["nonce"]
        try:
            if event["type"] == "delete":
                ks.delete_card(event["id"])
            elif event["type"] == "move":
                ks.arrange(event["layout"])
            ss.kanban_version = ks.version()      # our own save: the watcher stays quiet
        except ValueError as e:
            st.toast(str(e))                      # e.g. the AI changed the board meanwhile
        st.rerun()                                # redraw the board from the file
