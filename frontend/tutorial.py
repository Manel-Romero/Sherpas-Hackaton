"""Tutorial de bienvenida: un diálogo de varios pasos que se abre la primera vez que
un usuario entra, y que se puede volver a abrir con el botón "Tutorial".

Los pasos salen de personalize.steps(): usan el resumen y el plan que generó "Cargar plan" para ese
usuario (data/cases/<id>/summary.json) y su persona. Cada paso se puede escuchar con el botón 🔊."""
import streamlit as st

from compat import stretch

import personalize
import voice_ui
import workspaces

@st.dialog("Tutorial")
def _dialog() -> None:
    ss = st.session_state
    steps = personalize.steps(ss.get("user"))
    step = min(max(ss.get("tut_step", 0), 0), len(steps) - 1)
    s = steps[step]
    last = step == len(steps) - 1

    st.progress((step + 1) / len(steps), text=f"Paso {step + 1} de {len(steps)}")
    st.markdown(f"## {s['icon']} {s['title']}")
    st.markdown(s["body"])
    if s.get("more"):
        with st.expander("Ver el resumen completo"):
            st.markdown(s["more"])
    voice_ui.speak_button(f"{s['title']}. {s.get('speech') or s['body']}", key=f"tut{step}")

    c_skip, c_back, c_next = st.columns(3)
    with c_skip:
        if not last and st.button("Saltar", key="tut_skip", **stretch(st.button)):
            st.rerun()                       # rerun completo: cierra el diálogo
    with c_back:
        if step > 0 and st.button("← Atrás", key="tut_back", **stretch(st.button)):
            ss.tut_step = step - 1
            st.rerun(scope="fragment")       # solo redibuja el diálogo
    with c_next:
        if last:
            if st.button("Empezar", key="tut_done", **stretch(st.button)):
                st.rerun()
        elif st.button("Siguiente →", key="tut_next", **stretch(st.button)):
            ss.tut_step = step + 1
            st.rerun(scope="fragment")


def request(user_id: str) -> None:
    """Pide abrir el tutorial en la próxima ejecución (lo usa el botón de la barra superior)."""
    st.session_state.show_tutorial = True


def maybe_show(user_id: str) -> None:
    """Llamar una vez por ejecución. Abre el diálogo si se ha pedido o si es la primera vez.
    Se marca como visto al abrirlo: si lo cierran con la X no vuelve a salir solo."""
    ss = st.session_state
    first_time = not workspaces.tutorial_done(user_id)
    if ss.pop("show_tutorial", False) or first_time:
        workspaces.mark_tutorial_done(user_id)
        ss.tut_step = 0
        _dialog()
