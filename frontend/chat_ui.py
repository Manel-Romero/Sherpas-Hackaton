# Chat con el Co-Pilot (backend FastAPI, respuesta en streaming SSE).
import json
import os

import httpx
import streamlit as st

from compat import stretch

import dashboard_ui
import workspaces

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

SUGGESTIONS = [
    ("🚨 Gasto imprevisto de $2,000",
     "He tenido un gasto imprevisto de $2,000. Ajusta mi tabla para absorberlo y explicame como afecta a mi plan."),
    ("🔍 Explicame mi score financiero",
     "Explicame mi score de salud financiera y cual es mi principal cuello de botella patrimonial."),
    ("💰 Bonus extraordinario de $15,000",
     "Voy a recibir un bonus de $15,000. ¿Como me recomiendas asignarlo? Aplica los cambios que consideres en mi tabla."),
    ("📊 Grafico de balance y gastos",
     "Muestrame un grafico comparativo con la distribucion de mis ingresos y gastos mensuales actuales."),
]


def input_box() -> str | None:
    return st.chat_input("Consulta cualquier aspecto de tu plan al Co-Pilot...")


def persist() -> None:
    """Guarda la conversacion en disco si ha cambiado para mantener persistencia."""
    ss = st.session_state
    user, msgs = ss.get("user"), ss.get("messages", [])
    if user and ss.get("_chat_saved") != (user, len(msgs)):
        workspaces.save_chat(user, msgs)
        ss._chat_saved = (user, len(msgs))


def _empty_state():
    """Cabecera y chips de sugerencias adaptados al diseno de Sherpas."""
    box = st.empty()
    chosen = None
    with box.container():
        st.markdown(
            '<div class="empty-title" style="font-family: \'Poppins\', sans-serif; font-size: 1.85rem; font-weight: 700; color: #ffffff;">'
            '¿En que puedo ayudarte hoy?</div>'
            '<div class="empty-sub" style="color: var(--muted); margin-bottom: 24px;">'
            'Pregunta en lenguaje natural o selecciona una de estas consultas rapidas:</div>',
            unsafe_allow_html=True
        )
        with st.container():
            st.markdown('<span class="marker empty-marker"></span>', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, (label, text) in enumerate(SUGGESTIONS):
                if cols[i % 2].button(label, key=f"chip_{i}", **stretch(st.button)):
                    chosen = text
    return box, chosen


def render(prompt: str | None) -> None:
    ss = st.session_state
    ss.setdefault("messages", [])
    st.markdown('<span class="marker chat-marker"></span>', unsafe_allow_html=True)

    chip = None
    if not ss.messages:
        box, chip = _empty_state()
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("chart"):
                dashboard_ui.render_chart(m["chart"])

    active = prompt or chip
    if not active:
        return
    if not ss.messages:
        box.empty()
    ss.messages.append({"role": "user", "content": active})
    with st.chat_message("user"):
        st.markdown(active)
    _stream_reply(active)


def _stream_reply(prompt: str) -> None:
    ss = st.session_state
    text, chart, diffs, changed = "", None, [], False

    with st.chat_message("assistant"):
        slot = st.empty()
        slot.markdown("*Razonando respuesta...*")
        ss.is_streaming = True
        try:
            payload = {
                "message": prompt,
                "case_id": ss.case_id,
                "session_id": ss.session_id,
                "history": [{"role": m["role"], "content": m["content"]} for m in ss.messages[:-1]],
            }
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", f"{API_BASE_URL}/api/chat/stream", json=payload) as resp:
                    if resp.status_code != 200:
                        resp.read()
                        raise RuntimeError(f"El servidor respondio {resp.status_code}: {resp.text[:300]}")
                    for line in resp.iter_lines():
                        if not line.startswith("data: "):
                            continue
                        try:
                            ev = json.loads(line[6:].strip())
                        except json.JSONDecodeError:
                            continue
                        kind = ev.get("type")
                        if kind in ("token", "delta"):
                            text += ev.get("content") or ev.get("delta", "")
                            slot.markdown(text + "▌")
                        elif kind == "tool_start":
                            tool_name = ev.get("tool", "herramienta")
                            note = f"\n\n*⚡ Ejecutando accion MCP: `{tool_name}`...*"
                            slot.markdown(f"{text}{note}" if text else note)
                        elif kind == "tool_end" and ev.get("modified"):
                            changed = True
                            diffs.append(ev.get("diff") or ev.get("tool", ""))
                        elif kind == "state":
                            if ev.get("full_reply") and not text:
                                text = ev["full_reply"]
                            chart = ev.get("chart_to_render") or chart
                            if ev.get("changes_applied"):
                                changed = True
                                if ev.get("applied_summary"):
                                    diffs.append(ev["applied_summary"])
                        elif kind == "error":
                            slot.error(f"Error del servidor: {ev.get('detail', 'desconocido')}")

            if text:
                slot.markdown(text)
                if chart:
                    dashboard_ui.render_chart(chart)
                ss.messages.append({"role": "assistant", "content": text, **({"chart": chart} if chart else {})})
            else:
                slot.warning("El Co-Pilot no devolvio respuesta. Intentalo de nuevo.")
        except httpx.ConnectError:
            slot.error(f"No se puede conectar con el backend en {API_BASE_URL}. "
                       "Comprueba que este arrancado.")
            return
        except Exception as e:
            slot.error(f"Fallo al conectar con el Co-Pilot: {e}")
            return
        finally:
            ss.is_streaming = False

    persist()
    if changed:
        ss.notify_msg = "; ".join(dict.fromkeys(d for d in diffs if d)) or "Cambios aplicados"
        ss.notify_changes = True
        ss.pop("table_version", None)
    st.rerun()
