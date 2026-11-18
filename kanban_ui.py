"""Tablero Kanban interactivo con modal emergente centrado en pantalla para el detalle,
sincronizacion reactiva con el Co-Pilot y notificaciones de cumplimiento o ajuste del plan.
"""
import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import kanban_store as ks

try:                                    # same embedded fonts as the rest of the app
    from frontend.style import FONT_CSS
except Exception:                       # pragma: no cover - fonts are optional
    FONT_CSS = ""

BOARD_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  /*FONTS*/
  :root {
    --surface: #151c19;
    --surface-2: #1d2622;
    --surface-3: #232d29;
    --border: rgba(222,236,228,0.11);
    --border-strong: rgba(222,236,228,0.26);
    --text: #eef3ef;
    --muted: #b6c3bb;
    --accent: #d6e6dc;
    --good: #86c9a4;
    --serif: "Newsreader", "Iowan Old Style", Georgia, serif;
    --sans: "Hanken Grotesk", -apple-system, "Segoe UI", system-ui, sans-serif;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    background: transparent;
    color: var(--text);
    font-family: var(--sans);
    font-feature-settings: "tnum" 1, "kern" 1;
  }
  .board { display: grid; gap: 14px; padding: 4px 2px 14px; align-items: start; }
  @media (max-width: 640px) { .board { grid-template-columns: 1fr !important; } }

  .column { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
  .header {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 2px 4px 10px; font-family: var(--serif); font-weight: 500; font-size: 1.15rem; letter-spacing: -0.01em;
  }
  .count { color: var(--muted); font-family: var(--sans); font-size: 0.85rem; font-weight: 500; }
  .body { min-height: 80px; border-radius: 8px; padding: 2px; }
  .body.over { outline: 1px dashed var(--accent); }

  /* Card: flat, one hairline. Only the border changes on hover. */
  .card {
    position: relative; background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px;
    padding: 12px 14px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.15s ease;
  }
  .card:hover { border-color: var(--border-strong); }
  .card.dragging { opacity: 0.35; cursor: grabbing; }

  .card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
  .badges-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; max-width: calc(100% - 28px); }
  .badge { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 500; line-height: 1.3; color: var(--muted); }
  /* The category is a coloured dot + its name (colour comes from CAT_STYLES) */
  .badge-category::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .badge-impact { color: var(--good); font-weight: 600; }
  .badge-week { color: var(--muted); }

  .x {
    width: 22px; height: 22px; border: none; border-radius: 4px; background: transparent; color: var(--muted);
    font-size: 18px; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0;
  }
  .x:hover { background: var(--surface-3); color: #e58a78; }

  .title { font-weight: 600; font-size: 0.98rem; color: var(--text); line-height: 1.35; margin-bottom: 6px; overflow-wrap: anywhere; }
  .short-desc { color: var(--muted); font-size: 0.86rem; line-height: 1.5; margin-bottom: 8px; overflow-wrap: anywhere; }

  .card-footer { display: flex; justify-content: flex-end; align-items: center; padding-top: 6px; }
  .modal-open-btn {
    background: transparent; border: none; color: var(--text); font-family: var(--sans); font-size: 0.82rem; font-weight: 600;
    padding: 2px 0; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--border-strong);
  }
  .modal-open-btn:hover { text-decoration-color: var(--text); }

  /* Detail dialog, centred on screen */
  .modal-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh;
    background: rgba(5, 8, 7, 0.78); z-index: 99999; display: none; align-items: center; justify-content: center;
    padding: 18px; box-sizing: border-box;
  }
  .modal-overlay.open { display: flex !important; }
  .modal-dialog {
    background: var(--surface); border: 1px solid var(--border-strong); border-radius: 10px; width: 100%; max-width: 580px;
    max-height: 88vh; overflow-y: auto; padding: 24px 28px; position: relative; box-sizing: border-box;
  }
  .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .modal-badges { display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }
  .modal-close-btn {
    width: 32px; height: 32px; border: 1px solid transparent; border-radius: 6px; background: transparent; color: var(--muted);
    font-size: 22px; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center;
  }
  .modal-close-btn:hover { background: var(--surface-2); border-color: var(--border); color: var(--text); }
  .modal-title { font-family: var(--serif); font-size: 1.7rem; font-weight: 500; letter-spacing: -0.015em; color: var(--text); line-height: 1.2; margin-bottom: 16px; overflow-wrap: anywhere; }
  .modal-section-box { border-left: 2px solid var(--border-strong); padding: 2px 0 2px 14px; margin-bottom: 16px; }
  .modal-subtitle { font-size: 0.85rem; font-weight: 600; color: var(--muted); margin-bottom: 6px; }
  .modal-short-desc { font-size: 0.95rem; color: var(--text); line-height: 1.5; }
  .modal-detailed-desc { font-size: 0.92rem; color: var(--text); line-height: 1.6; margin-bottom: 14px; white-space: pre-wrap; }
  .modal-steps-list { margin: 6px 0 16px 20px; padding: 0; }
  .modal-steps-list li { font-size: 0.9rem; color: var(--text); line-height: 1.55; margin-bottom: 6px; }
  .modal-meta-grid { display: flex; gap: 8px; flex-wrap: wrap; margin: 14px 0 18px; padding: 0; }
  .meta-pill { font-size: 0.8rem; border: 1px solid var(--border); border-radius: 6px; padding: 3px 8px; color: var(--muted); }
  .modal-actions { display: flex; gap: 10px; justify-content: flex-end; align-items: center; padding-top: 14px; border-top: 1px solid var(--border); flex-wrap: wrap; }
  .btn-action-primary, .btn-action-secondary, .btn-action-close {
    font-family: var(--sans); font-size: 0.88rem; padding: 8px 16px; border-radius: 6px; cursor: pointer; transition: background 0.15s ease, border-color 0.15s ease;
  }
  .btn-action-primary { background: var(--accent); color: #0e1311; font-weight: 600; border: 1px solid var(--accent); }
  .btn-action-primary:hover { background: #fff; border-color: #fff; }
  .btn-action-secondary { background: transparent; color: var(--text); font-weight: 500; border: 1px solid var(--border-strong); }
  .btn-action-secondary:hover { border-color: var(--text); }
  .btn-action-close { background: transparent; color: var(--muted); font-weight: 500; border: 1px solid var(--border); }
  .btn-action-close:hover { color: var(--text); border-color: var(--border-strong); }
</style>
</head>
<body>
<div id="board" class="board"></div>

<!-- Modal Centrado -->
<div id="taskModal" class="modal-overlay">
  <div class="modal-dialog">
    <div class="modal-header">
      <div class="modal-badges" id="modalBadges"></div>
      <button class="modal-close-btn" id="modalCloseBtn" title="Cerrar">×</button>
    </div>
    
    <div class="modal-title" id="modalTitle"></div>
    
    <div class="modal-section-box">
      <div class="modal-subtitle">Resumen</div>
      <div class="modal-short-desc" id="modalShortDesc"></div>
    </div>

    <div class="modal-body-section" id="modalDescSection">
      <div class="modal-subtitle">Explicación y contexto</div>
      <div class="modal-detailed-desc" id="modalDetailedDesc"></div>
    </div>

    <div class="modal-body-section" id="modalStepsSection">
      <div class="modal-subtitle">Pasos recomendados</div>
      <ol class="modal-steps-list" id="modalStepsList"></ol>
    </div>

    <div class="modal-meta-grid" id="modalMetaGrid"></div>

    <div class="modal-actions" id="modalActions">
      <button class="btn-action-secondary" id="modalMoveBtn">En proceso</button>
      <button class="btn-action-primary" id="modalCompleteBtn">Marcar como completada</button>
      <button class="btn-action-close" id="modalFooterCloseBtn">Cerrar</button>
    </div>
  </div>
</div>

<script>
const board = document.getElementById("board");
const modal = document.getElementById("taskModal");
let lastArgs = null, lastLayout = "", dragged = null, dropped = false, seq = 0;
let activeModalCard = null;

const CAT_STYLES = {
  debt:       { label: "Deuda",       color: "#e2b560" },
  savings:    { label: "Ahorro",      color: "#86c9a4" },
  investment: { label: "Inversión",   color: "#8fb7d4" },
  insurance:  { label: "Seguros",     color: "#7fc4c9" },
  lifestyle:  { label: "Presupuesto", color: "#b9a3d6" },
  immediate:  { label: "Prioritaria", color: "#eef3ef" },
  goal:       { label: "Meta",        color: "#9aa8e0" },
  alerta:     { label: "Alerta",      color: "#e58a78" },
  general:    { label: "General",     color: "#b6c3bb" }
};

function post(type, extra) {
  window.parent.postMessage(Object.assign({isStreamlitMessage: true, type: type}, extra), "*");
}
function setHeight() {
  setTimeout(() => {
    post("streamlit:setFrameHeight", {height: Math.max(board.scrollHeight + 30, 320)});
  }, 25);
}
function emit(value) {
  value.nonce = Date.now() + "-" + (++seq);
  post("streamlit:setComponentValue", {value: value, dataType: "json"});
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function layoutOf() {
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

function clearOver() {
  board.querySelectorAll(".body.over").forEach(b => b.classList.remove("over"));
}

function cardAfter(body, y) {
  let best = {offset: -Infinity, el: null};
  body.querySelectorAll(".card:not(.dragging)").forEach(c => {
    const box = c.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > best.offset) best = {offset: offset, el: c};
  });
  return best.el;
}

// Modal en el centro
function openCardModal(c) {
  activeModalCard = c;
  
  const catKey = (c.category || "general").toLowerCase();
  const catConf = CAT_STYLES[catKey] || CAT_STYLES.general;
  const badgesBox = document.getElementById("modalBadges");
  badgesBox.innerHTML = "";
  
  const catB = el("span", "badge badge-category", catConf.label);
  catB.style.color = catConf.color;
  badgesBox.append(catB);
  
  if (c.impact && c.impact.trim()) {
    badgesBox.append(el("span", "badge badge-impact", c.impact.trim()));
  }
  if (c.week) {
    badgesBox.append(el("span", "badge badge-week", "Semana " + c.week));
  }

  document.getElementById("modalTitle").textContent = c.title || "Tarea";

  const shortText = c.short_description || (c.content ? c.content.split("\n")[0] : "");
  document.getElementById("modalShortDesc").textContent = shortText || "Sin descripcion breve.";

  const fullDesc = c.detailed_description || c.content || shortText;
  document.getElementById("modalDetailedDesc").textContent = fullDesc;

  const stepsList = document.getElementById("modalStepsList");
  const stepsSec = document.getElementById("modalStepsSection");
  stepsList.innerHTML = "";
  if (Array.isArray(c.steps) && c.steps.length > 0) {
    stepsSec.style.display = "block";
    c.steps.forEach(s => stepsList.append(el("li", "", s)));
  } else {
    stepsSec.style.display = "none";
  }

  const metaGrid = document.getElementById("modalMetaGrid");
  metaGrid.innerHTML = "";
  metaGrid.append(el("span", "meta-pill", "Categoría: " + (catConf.label || c.category)));
  if (c.impact) metaGrid.append(el("span", "meta-pill", "Impacto estimado: " + c.impact));
  if (c.week) metaGrid.append(el("span", "meta-pill", "Semana asignada: " + c.week));
  const stLabel = (c.status === "done" ? "Completada" : (c.status === "in_process" ? "En proceso" : "Por hacer"));
  metaGrid.append(el("span", "meta-pill", "Columna actual: " + stLabel));

  const completeBtn = document.getElementById("modalCompleteBtn");
  const moveBtn = document.getElementById("modalMoveBtn");
  
  if (c.status === "done") {
    completeBtn.style.display = "none";
    moveBtn.textContent = "Mover a Por hacer";
    moveBtn.onclick = () => { moveCardModal(c.id, "todo"); };
  } else if (c.status === "in_process") {
    completeBtn.style.display = "inline-block";
    completeBtn.textContent = "Marcar como completada";
    completeBtn.onclick = () => { moveCardModal(c.id, "done"); };
    moveBtn.textContent = "Mover a Por hacer";
    moveBtn.onclick = () => { moveCardModal(c.id, "todo"); };
  } else {
    completeBtn.style.display = "inline-block";
    completeBtn.textContent = "Marcar como completada";
    completeBtn.onclick = () => { moveCardModal(c.id, "done"); };
    moveBtn.textContent = "Mover a En proceso";
    moveBtn.onclick = () => { moveCardModal(c.id, "in_process"); };
  }

  modal.classList.add("open");
}

function closeCardModal() {
  modal.classList.remove("open");
  activeModalCard = null;
}

function moveCardModal(cardId, targetStatus) {
  closeCardModal();
  const curLayout = layoutOf();
  for (const s in curLayout) {
    curLayout[s] = curLayout[s].filter(id => id !== cardId);
  }
  if (!curLayout[targetStatus]) curLayout[targetStatus] = [];
  curLayout[targetStatus].push(cardId);
  emit({type: "move", layout: curLayout});
}

document.getElementById("modalCloseBtn").addEventListener("click", closeCardModal);
document.getElementById("modalFooterCloseBtn").addEventListener("click", closeCardModal);
modal.addEventListener("click", ev => {
  if (ev.target === modal) closeCardModal();
});
window.addEventListener("keydown", ev => {
  if (ev.key === "Escape" && modal.classList.contains("open")) closeCardModal();
});

function makeCard(c) {
  const card = el("div", "card");
  card.draggable = true;
  card.dataset.id = c.id;

  // 1. Fila de badges superiores y boton eliminar
  const topRow = el("div", "card-top");
  const badgesRow = el("div", "badges-row");

  const catKey = (c.category || "general").toLowerCase();
  const catConf = CAT_STYLES[catKey] || CAT_STYLES.general;
  const catBadge = el("span", "badge badge-category", catConf.label);
  catBadge.style.color = catConf.color;
  badgesRow.append(catBadge);

  if (c.impact && c.impact.trim()) {
    const impBadge = el("span", "badge badge-impact", c.impact.trim());
    badgesRow.append(impBadge);
  }

  if (c.week) {
    const weekBadge = el("span", "badge badge-week", "Semana " + c.week);
    badgesRow.append(weekBadge);
  }

  const x = el("button", "x", "×");
  x.title = "Eliminar tarea";
  x.addEventListener("click", ev => {
    ev.stopPropagation();
    emit({type: "delete", id: c.id});
  });

  topRow.append(badgesRow, x);
  card.append(topRow);

  // 2. Titulo limpio
  const titleEl = el("div", "title", c.title || "Tarea");
  card.append(titleEl);

  // 3. Descripcion breve (poco texto en tarjeta)
  const shortText = c.short_description || (c.content ? c.content.split("\n")[0] : "");
  if (shortText) {
    const shortEl = el("div", "short-desc", shortText);
    card.append(shortEl);
  }

  // 4. Pie de tarjeta con boton Ver Detalle
  const footer = el("div", "card-footer");
  const modalBtn = el("button", "modal-open-btn", "Ver detalle");
  modalBtn.addEventListener("click", ev => {
    ev.stopPropagation();
    openCardModal(c);
  });
  footer.append(modalBtn);
  card.append(footer);

  // Clic en la tarjeta abre el modal en el centro
  card.addEventListener("click", ev => {
    if (ev.target.closest("button")) return;
    openCardModal(c);
  });

  // Arrastrar y soltar
  card.addEventListener("dragstart", ev => {
    dragged = card;
    dropped = false;
    card.classList.add("dragging");
    ev.dataTransfer.effectAllowed = "move";
    ev.dataTransfer.setData("text/plain", c.id);
  });

  card.addEventListener("dragend", () => {
    card.classList.remove("dragging");
    clearOver();
    if (!dropped) render(lastArgs);
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
      clearOver();
      body.classList.add("over");
      const after = cardAfter(body, ev.clientY);
      if (after) {
        if (after !== dragged.nextElementSibling || dragged.parentNode !== body) {
          body.insertBefore(dragged, after);
        }
      } else if (dragged.parentNode !== body || dragged !== body.lastElementChild) {
        body.appendChild(dragged);
      }
    });

    body.addEventListener("drop", ev => {
      ev.preventDefault();
      dropped = true;
      clearOver();
      updateCounts();
      setHeight();
      const now = JSON.stringify(layoutOf());
      if (now !== lastLayout) {
        lastLayout = now;
        emit({type: "move", layout: layoutOf()});
      }
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
""".replace("/*FONTS*/", FONT_CSS)

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


def notify_agent_of_kanban_change(
    action: str,
    card: dict,
    case_id: str = "michael-carter",
    session_id: str = "default"
):
    """Consulta al Co-Pilot cuando el usuario pide explicitamente hablar sobre un elemento añadido."""
    title = card.get("title", "Tarea")
    impact = card.get("impact", "")

    user_msg = (
        f"He añadido {title} al plan (impacto: {impact}). "
        f"Explicame con claridad como me recomiendas abordarla y que debo tener en cuenta."
    )
    st.toast(f"Consultando al Co-Pilot sobre '{title}'...", icon=":material/chat:")

    try:
        import httpx
        api_base = os.environ.get("API_BASE_URL", "http://localhost:8000")
        payload = {
            "message": user_msg,
            "case_id": case_id,
            "session_id": session_id,
        }
        # gpt-5-mini razona y puede usar herramientas: 30 s se quedaban cortos (el backend seguiría y cobraría igual)
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{api_base}/api/chat", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("reply", "")

                ss = st.session_state
                if "messages" not in ss:
                    ss.messages = []
                ss.messages.append({"role": "user", "content": user_msg})
                msg_obj = {"role": "assistant", "content": reply}
                if data.get("chart_to_render"):
                    msg_obj["chart"] = data["chart_to_render"]
                ss.messages.append(msg_obj)

                short_reply = reply[:140] + "..." if len(reply) > 140 else reply
                st.toast(f"Co-Pilot: {short_reply}", icon=":material/chat:")
    except Exception:
        pass


def _add_card():
    with st.popover("Añadir tarea", icon=":material/add:"):
        with st.form("add_card", clear_on_submit=True):
            title = st.text_input("Título de la tarea (acción concreta)")
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                category = st.selectbox(
                    "Categoría",
                    ["debt", "savings", "investment", "insurance", "lifestyle", "immediate", "general"],
                    format_func=lambda x: {
                        "debt": "Deuda",
                        "savings": "Ahorro",
                        "investment": "Inversión",
                        "insurance": "Seguros",
                        "lifestyle": "Presupuesto",
                        "immediate": "Prioritaria",
                        "general": "General"
                    }.get(x, x.capitalize())
                )
            with c_col2:
                status = st.selectbox("Columna", list(ks.STATUSES), format_func=ks.STATUSES.get)

            c_sub1, c_sub2 = st.columns(2)
            with c_sub1:
                impact = st.text_input("Impacto estimado (ej: -$3,500 o +$500/mes)", value="")
            with c_sub2:
                week = st.number_input("Semana (1 a 4)", min_value=1, max_value=4, value=1)

            short_desc = st.text_input("Descripción breve (una línea para la tarjeta)")
            detailed_desc = st.text_area("Descripción detallada y contexto")
            steps_text = st.text_area("Pasos recomendados (uno por linea)")

            if st.form_submit_button("Guardar tarea") and title.strip():
                try:
                    steps_list = [s.strip() for s in steps_text.split("\n") if s.strip()]
                    new_card = {
                        "title": title.strip(),
                        "content": detailed_desc.strip() or short_desc.strip(),
                        "status": status,
                        "short_description": short_desc.strip(),
                        "detailed_description": detailed_desc.strip(),
                        "category": category,
                        "impact": impact.strip(),
                        "week": int(week),
                        "steps": steps_list
                    }
                    ks.add_card(**new_card)
                    ss = st.session_state
                    ss.ask_talk_agent = {
                        "type": "task",
                        "title": title.strip(),
                        "impact": impact.strip(),
                        "category": category
                    }
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

def render():
    ss = st.session_state
    ss.board_rev = ss.get("board_rev", 0) + 1
    ss.kanban_version = ks.version()
    case_id = getattr(ss, "case_id", "michael-carter")
    session_id = getattr(ss, "session_id", "default")

    # Preguntar al usuario si quiere hablar con el agente tras anadir una tarea
    if "ask_talk_agent" in ss and ss.ask_talk_agent and ss.ask_talk_agent.get("type") == "task":
        item = ss.ask_talk_agent
        t_title = item.get("title", "")
        with st.container():
            c_info, c_action, c_close = st.columns([6, 3, 1])
            with c_info:
                st.info(f"Has añadido la tarea **'{t_title}'**. ¿Quieres hablar con el Co-Pilot sobre ella?")
            with c_action:
                if st.button("Hablar con el agente", icon=":material/chat:", key=f"talk_task_{t_title}"):
                    del ss.ask_talk_agent
                    notify_agent_of_kanban_change(
                        "add",
                        {"title": t_title, "impact": item.get("impact", "")},
                        case_id=case_id,
                        session_id=session_id
                    )
                    st.rerun()
            with c_close:
                if st.button("No", key=f"dismiss_task_{t_title}"):
                    del ss.ask_talk_agent
                    st.rerun()

    a, _ = st.columns([3, 6])
    with a:
        _add_card()

    current_data = ks.load()

    event = _board(
        cards=current_data["cards"],
        statuses=ks.STATUSES,
        rev=ss.board_rev,
        key="kanban",
        default=None,
    )

    if event and event.get("nonce") != ss.get("last_nonce"):
        ss.last_nonce = event["nonce"]
        try:
            if event["type"] == "delete":
                ks.delete_card(event["id"])
            elif event["type"] == "move":
                ks.arrange(event["layout"])
            ss.kanban_version = ks.version()
        except ValueError as e:
            st.toast(str(e))
        st.rerun()
