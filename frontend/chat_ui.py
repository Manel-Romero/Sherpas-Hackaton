"""Chat con el Co-Pilot (backend FastAPI, respuesta en streaming SSE).

En app.py:
    prompt = chat_ui.input_box()          # arriba del todo; la barra se ancla abajo
    ...
    with chat_tab:
        chat_ui.render(prompt)            # historial, estado vacío con sugerencias y streaming
"""
import json
import os

import httpx
import streamlit as st

from compat import stretch

import dashboard_ui
import workspaces

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

SUGGESTIONS = [
    ("🚨 Gasto imprevisto de 2.000 $",
     "He tenido un gasto imprevisto de 2.000 $. Ajusta mi tabla para absorberlo y dime cómo afecta a mi plan."),
    ("🔍 Explícame mi score",
     "Explícame mi score de salud financiera y cuál es mi principal cuello de botella, sin tecnicismos."),
    ("💰 Me dan un bonus de 15.000 $",
     "Voy a recibir un bonus de 15.000 $. ¿Qué hago con él? Aplica los cambios que recomiendes en mi tabla."),
    ("📊 Gráfico de mis gastos",
     "Muéstrame un gráfico con la distribución de mis ingresos y gastos mensuales actuales."),
]


def input_box() -> str | None:
    return st.chat_input("Pregunta lo que quieras sobre tu plan…")


def persist() -> None:
    """Guarda la conversación en disco si ha cambiado (así sigue ahí cuando vuelves otro día)."""
    ss = st.session_state
    user, msgs = ss.get("user"), ss.get("messages", [])
    if user and ss.get("_chat_saved") != (user, len(msgs)):
        workspaces.save_chat(user, msgs)
        ss._chat_saved = (user, len(msgs))


def _empty_state():
    """Título y sugerencias (usan los estilos .empty-title / .empty-sub / .empty-marker)."""
    box = st.empty()
    chosen = None
    with box.container():
        st.markdown('<div class="empty-title">¿Qué quieres saber de tu plan?</div>'
                    '<div class="empty-sub">Pregunta con tus palabras o empieza con una de estas ideas.</div>',
                    unsafe_allow_html=True)
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
        box.empty()                                  # quitar el estado vacío en cuanto hay mensaje
    ss.messages.append({"role": "user", "content": active})
    with st.chat_message("user"):
        st.markdown(active)
    _stream_reply(active)


def _stream_reply(prompt: str) -> None:
    ss = st.session_state
    text, chart, diffs, changed = "", None, [], False

    with st.chat_message("assistant"):
        slot = st.empty()
        slot.markdown("*Pensando…*")
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
                        raise RuntimeError(f"El servidor respondió {resp.status_code}: {resp.text[:300]}")
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
                            note = f"*⚡ Aplicando cambios ({ev.get('tool', 'herramienta')})…*"
                            slot.markdown(f"{text}\n\n{note}" if text else note)
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
                slot.warning("El Co-Pilot no devolvió respuesta. Inténtalo de nuevo.")
        except httpx.ConnectError:
            slot.error(f"No puedo conectar con el backend en {API_BASE_URL}. "
                       "¿Está arrancado? (`uvicorn backend.app.main:app --port 8000`)")
            return
        except Exception as e:
            slot.error(f"Fallo al hablar con el Co-Pilot: {e}")
            return
        finally:
            ss.is_streaming = False

    persist()
    if changed:
        ss.notify_msg = "; ".join(dict.fromkeys(d for d in diffs if d)) or "Cambios aplicados"
        ss.notify_changes = True
        ss.pop("table_version", None)                # fuerza a recargar la tabla desde el fichero
    st.rerun()
