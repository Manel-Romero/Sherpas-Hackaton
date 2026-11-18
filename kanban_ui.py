"""Tablero Kanban interactivo con modal emergente centrado en pantalla para el detalle,
sincronizacion reactiva con el Co-Pilot y notificaciones de cumplimiento o ajuste del plan.
"""
import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import kanban_store as ks

BOARD_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap');

  :root {
    --bg: #04070d;
    --surface: #0a0f18;
    --surface-2: #0e1626;
    --surface-3: #141f36;
    --border: rgba(255,255,255,0.08);
    --border-strong: rgba(69, 101, 214, 0.28);
    --text: #f8fafc;
    --muted: #94a3b8;
    --accent: #4565d6;
    --accent-light: #6586fc;
    --green-bg: rgba(16, 185, 129, 0.12);
    --green-border: rgba(16, 185, 129, 0.32);
    --green-text: #34d399;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    background: transparent;
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;
  }
  .board {
    display: grid;
    gap: 14px;
    padding: 4px 2px 14px;
    align-items: start;
  }
  @media (max-width: 640px) {
    .board { grid-template-columns: 1fr !important; }
  }
  .column {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 14px;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    padding: 2px 4px 10px;
    font-size: 0.94rem;
  }
  .count {
    color: var(--muted);
    font-size: 0.8rem;
    font-weight: 600;
    background: var(--surface-2);
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--border);
  }
  .body {
    min-height: 80px;
    border-radius: 10px;
    padding: 2px;
  }
  .body.over {
    outline: 1px dashed var(--accent);
  }

  /* Tarjeta estructurada en columna */
  .card {
    position: relative;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.14s ease;
  }
  .card:hover {
    border-color: var(--border-strong);
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
    transform: translateY(-1px);
  }
  .card.dragging {
    opacity: 0.35;
    cursor: grabbing;
  }

  /* Fila superior de badges y boton eliminar */
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }
  .badges-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
    max-width: calc(100% - 28px);
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    line-height: 1.3;
  }
  .badge-category {
    border: 1px solid transparent;
  }
  .badge-impact {
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    color: var(--green-text);
  }
  .badge-week {
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--border);
    color: var(--muted);
  }

  .x {
    width: 22px;
    height: 22px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--muted);
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }
  .x:hover {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  /* Titulo y texto breve en la tarjeta */
  .title {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 0.94rem;
    color: #f8fafc;
    line-height: 1.35;
    margin-bottom: 6px;
    overflow-wrap: anywhere;
  }
  .short-desc {
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.45;
    margin-bottom: 8px;
    overflow-wrap: anywhere;
  }

  /* Pie de tarjeta con boton ver detalle */
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
  .modal-open-btn {
    background: rgba(69, 101, 214, 0.12);
    border: 1px solid rgba(69, 101, 214, 0.25);
    color: #93c5fd;
    font-size: 0.76rem;
    font-weight: 600;
    border-radius: 6px;
    padding: 4px 10px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .modal-open-btn:hover {
    background: rgba(69, 101, 214, 0.25);
    border-color: var(--accent);
    color: #fff;
  }

  /* MODAL CENTRADO EN LA PANTALLA */
  .modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    width: 100vw; height: 100vh;
    background: rgba(4, 7, 13, 0.82);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    z-index: 99999;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 18px;
    box-sizing: border-box;
  }
  .modal-overlay.open {
    display: flex !important;
  }
  .modal-dialog {
    background: #0a0f18;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 18px;
    width: 100%;
    max-width: 580px;
    max-height: 88vh;
    overflow-y: auto;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.85), 0 0 1px 1px rgba(255, 255, 255, 0.08);
    padding: 24px 28px;
    position: relative;
    box-sizing: border-box;
    animation: modalPop 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  }
  @keyframes modalPop {
    from { transform: scale(0.92) translateY(8px); opacity: 0; }
    to { transform: scale(1) translateY(0); opacity: 1; }
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  .modal-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
  }
  .modal-close-btn {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.08);
    color: var(--muted);
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }
  .modal-close-btn:hover {
    background: rgba(239, 68, 68, 0.25);
    color: #ef4444;
  }
  .modal-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.35;
    margin-bottom: 14px;
    overflow-wrap: anywhere;
  }
  .modal-section-box {
    background: rgba(69, 101, 214, 0.08);
    border: 1px solid rgba(69, 101, 214, 0.22);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 14px;
  }
  .modal-subtitle {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--muted);
    letter-spacing: 0.05em;
    margin-bottom: 6px;
  }
  .modal-short-desc {
    font-size: 0.9rem;
    color: #f8fafc;
    line-height: 1.45;
  }
  .modal-detailed-desc {
    font-size: 0.88rem;
    color: #e2e8f0;
    line-height: 1.55;
    margin-bottom: 14px;
    white-space: pre-wrap;
  }
  .modal-steps-list {
    margin: 6px 0 16px 20px;
    padding: 0;
  }
  .modal-steps-list li {
    font-size: 0.86rem;
    color: var(--text);
    line-height: 1.5;
    margin-bottom: 6px;
  }
  .modal-meta-grid {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 14px 0 18px;
    padding: 10px 12px;
    background: var(--surface-3);
    border: 1px solid var(--border);
    border-radius: 10px;
  }
  .meta-pill {
    font-size: 0.74rem;
    background: rgba(0,0,0,0.3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 8px;
    color: var(--muted);
  }
  .modal-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    align-items: center;
    padding-top: 14px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    flex-wrap: wrap;
  }
  .btn-action-primary {
    background: #10b981;
    color: #ffffff;
    font-weight: 700;
    font-size: 0.84rem;
    padding: 8px 16px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-action-primary:hover {
    background: #059669;
    color: #fff;
  }
  .btn-action-secondary {
    background: rgba(69, 101, 214, 0.18);
    color: #93c5fd;
    font-weight: 600;
    font-size: 0.84rem;
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid rgba(69, 101, 214, 0.35);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-action-secondary:hover {
    background: rgba(69, 101, 214, 0.3);
    color: #fff;
  }
  .btn-action-close {
    background: rgba(255, 255, 255, 0.06);
    color: var(--muted);
    font-weight: 500;
    font-size: 0.84rem;
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-action-close:hover {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text);
  }
</style>
</head>
<body>
<div id="board" class="board"></div>

<!-- Modal Centrado -->
<div id="taskModal" class="modal-overlay">
  <div class="modal-dialog">
    <div class="modal-header">
      <div class="modal-badges" id="modalBadges"></div>
      <button class="modal-close-btn" id="modalCloseBtn" title="Cerrar">✕</button>
    </div>
    
    <div class="modal-title" id="modalTitle"></div>
    
    <div class="modal-section-box">
      <div class="modal-subtitle">RESUMEN EJECUTIVO (BREVE)</div>
      <div class="modal-short-desc" id="modalShortDesc"></div>
    </div>

    <div class="modal-body-section" id="modalDescSection">
      <div class="modal-subtitle">EXPLICACION Y CONTEXTO FINANCIERO EXTENDIDO</div>
      <div class="modal-detailed-desc" id="modalDetailedDesc"></div>
    </div>

    <div class="modal-body-section" id="modalStepsSection">
      <div class="modal-subtitle">PASOS RECOMENDADOS DE EJECUCION</div>
      <ol class="modal-steps-list" id="modalStepsList"></ol>
    </div>

    <div class="modal-meta-grid" id="modalMetaGrid"></div>

    <div class="modal-actions" id="modalActions">
      <button class="btn-action-secondary" id="modalMoveBtn">🚀 En proceso</button>
      <button class="btn-action-primary" id="modalCompleteBtn">✅ Marcar como Completada</button>
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
  debt: { label: "Deuda", icon: "💳", color: "#f87171", bg: "rgba(239, 68, 68, 0.12)", border: "rgba(239, 68, 68, 0.28)" },
  savings: { label: "Ahorro", icon: "💰", color: "#34d399", bg: "rgba(16, 185, 129, 0.12)", border: "rgba(16, 185, 129, 0.28)" },
  investment: { label: "Inversion", icon: "📈", color: "#60a5fa", bg: "rgba(59, 130, 246, 0.12)", border: "rgba(59, 130, 246, 0.28)" },
  insurance: { label: "Seguros", icon: "🛡️", color: "#38bdf8", bg: "rgba(6, 182, 212, 0.12)", border: "rgba(6, 182, 212, 0.28)" },
  lifestyle: { label: "Presupuesto", icon: "🌱", color: "#a78bfa", bg: "rgba(139, 92, 246, 0.12)", border: "rgba(139, 92, 246, 0.28)" },
  immediate: { label: "Prioritaria", icon: "⚡", color: "#34d399", bg: "rgba(16, 185, 129, 0.15)", border: "rgba(16, 185, 129, 0.35)" },
  goal: { label: "Meta", icon: "🎯", color: "#818cf8", bg: "rgba(99, 102, 241, 0.15)", border: "rgba(99, 102, 241, 0.35)" },
  alerta: { label: "Alerta", icon: "🚨", color: "#f87171", bg: "rgba(239, 68, 68, 0.15)", border: "rgba(239, 68, 68, 0.35)" },
  general: { label: "General", icon: "📌", color: "#94a3b8", bg: "rgba(148, 163, 184, 0.12)", border: "rgba(148, 163, 184, 0.25)" }
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
  
  const catB = el("span", "badge badge-category", catConf.icon + " " + catConf.label);
  catB.style.color = catConf.color;
  catB.style.backgroundColor = catConf.bg;
  catB.style.borderColor = catConf.border;
  badgesBox.append(catB);
  
  if (c.impact && c.impact.trim()) {
    badgesBox.append(el("span", "badge badge-impact", "✨ " + c.impact.trim()));
  }
  if (c.week) {
    badgesBox.append(el("span", "badge badge-week", "📅 Semana " + c.week));
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
  metaGrid.append(el("span", "meta-pill", "Categoria: " + (catConf.label || c.category)));
  if (c.impact) metaGrid.append(el("span", "meta-pill", "Impacto estimado: " + c.impact));
  if (c.week) metaGrid.append(el("span", "meta-pill", "Semana asignada: " + c.week));
  const stLabel = (c.status === "done" ? "Completada" : (c.status === "in_process" ? "En proceso" : "Por hacer"));
  metaGrid.append(el("span", "meta-pill", "Columna actual: " + stLabel));

  const completeBtn = document.getElementById("modalCompleteBtn");
  const moveBtn = document.getElementById("modalMoveBtn");
  
  if (c.status === "done") {
    completeBtn.style.display = "none";
    moveBtn.textContent = "↩️ Mover a Por Hacer";
    moveBtn.onclick = () => { moveCardModal(c.id, "todo"); };
  } else if (c.status === "in_process") {
    completeBtn.style.display = "inline-block";
    completeBtn.textContent = "✅ Marcar como Completada";
    completeBtn.onclick = () => { moveCardModal(c.id, "done"); };
    moveBtn.textContent = "↩️ Mover a Por Hacer";
    moveBtn.onclick = () => { moveCardModal(c.id, "todo"); };
  } else {
    completeBtn.style.display = "inline-block";
    completeBtn.textContent = "✅ Marcar como Completada";
    completeBtn.onclick = () => { moveCardModal(c.id, "done"); };
    moveBtn.textContent = "🚀 Mover a En Proceso";
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
  const catBadge = el("span", "badge badge-category", catConf.icon + " " + catConf.label);
  catBadge.style.color = catConf.color;
  catBadge.style.backgroundColor = catConf.bg;
  catBadge.style.borderColor = catConf.border;
  badgesRow.append(catBadge);

  if (c.impact && c.impact.trim()) {
    const impBadge = el("span", "badge badge-impact", "✨ " + c.impact.trim());
    badgesRow.append(impBadge);
  }

  if (c.week) {
    const weekBadge = el("span", "badge badge-week", "📅 Sem. " + c.week);
    badgesRow.append(weekBadge);
  }

  const x = el("button", "x", "✕");
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
  const modalBtn = el("button", "modal-open-btn", "🔍 Ver detalle");
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
"""

_FRONTEND = Path(__file__).with_name("kanban_frontend")

def changed() -> bool:
    ss = st.session_state
    case_id = getattr(ss, "case_id", "michael-carter")
    if "kanban_version" not in ss:
        return False
    return ks.version(case_id) != ss.kanban_version


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
    """Consulta al Co-Pilot cuando el usuario pide explicitamente hablar sobre un elemento anadido."""
    title = card.get("title", "Tarea")
    impact = card.get("impact", "")

    user_msg = (
        f"He anadido {title} al plan (impacto: {impact}). "
        f"Explicame con claridad como me recomiendas abordarla y que debo tener en cuenta."
    )
    st.toast(f"Consultando al Co-Pilot sobre '{title}'...", icon="💬")

    try:
        import httpx
        api_base = os.environ.get("API_BASE_URL", "http://localhost:8000")
        payload = {
            "message": user_msg,
            "case_id": case_id,
            "session_id": session_id,
        }
        with httpx.Client(timeout=30.0) as client:
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
                st.toast(f"💬 Co-Pilot: {short_reply}", icon="💡")
    except Exception:
        pass


def _add_card():
    with st.popover("➕ Anadir tarea estructurada"):
        with st.form("add_card", clear_on_submit=True):
            title = st.text_input("Titulo de la tarea (accion concreta)")
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                category = st.selectbox(
                    "Categoria",
                    ["debt", "savings", "investment", "insurance", "lifestyle", "immediate", "general"],
                    format_func=lambda x: {
                        "debt": "💳 Deuda",
                        "savings": "💰 Ahorro",
                        "investment": "📈 Inversion",
                        "insurance": "🛡️ Seguros",
                        "lifestyle": "🌱 Presupuesto",
                        "immediate": "⚡ Prioritaria",
                        "general": "📌 General"
                    }.get(x, x.capitalize())
                )
            with c_col2:
                status = st.selectbox("Columna", list(ks.STATUSES), format_func=ks.STATUSES.get)

            c_sub1, c_sub2 = st.columns(2)
            with c_sub1:
                impact = st.text_input("Impacto estimado (ej: -$3,500 o +$500/mes)", value="")
            with c_sub2:
                week = st.number_input("Semana (1 a 4)", min_value=1, max_value=4, value=1)

            short_desc = st.text_input("Descripcion breve (1 linea para la vista principal)")
            detailed_desc = st.text_area("Descripcion detallada y contexto (visible en modal centrado)")
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
    case_id = getattr(ss, "case_id", "michael-carter")
    session_id = getattr(ss, "session_id", "default")
    ss.kanban_version = ks.version(case_id)

    # Preguntar al usuario si quiere hablar con el agente tras anadir una tarea
    if "ask_talk_agent" in ss and ss.ask_talk_agent and ss.ask_talk_agent.get("type") == "task":
        item = ss.ask_talk_agent
        t_title = item.get("title", "")
        with st.container():
            c_info, c_action, c_close = st.columns([6, 3, 1])
            with c_info:
                st.info(f"Has anadido la tarea **'{t_title}'**. ¿Quieres hablar con el Co-Pilot sobre ella?")
            with c_action:
                if st.button("💬 Hablar con el agente", key=f"talk_task_{t_title}"):
                    del ss.ask_talk_agent
                    notify_agent_of_kanban_change(
                        "add",
                        {"title": t_title, "impact": item.get("impact", "")},
                        case_id=case_id,
                        session_id=session_id
                    )
                    st.rerun()
            with c_close:
                if st.button("✕ No", key=f"dismiss_task_{t_title}"):
                    del ss.ask_talk_agent
                    st.rerun()

    a, _ = st.columns([3, 6])
    with a:
        _add_card()

    current_data = ks.load(case_id)

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
                ks.delete_card(event["id"], case_id=case_id)
            elif event["type"] == "move":
                ks.arrange(event["layout"], case_id=case_id)
            ss.kanban_version = ks.version(case_id)
        except ValueError as e:
            st.toast(str(e))
        st.rerun()
