"""Tutorial de bienvenida: un diálogo de varios pasos que se abre la primera vez que
un usuario entra, y que se puede volver a abrir con el botón "Tutorial".

Los pasos salen de personalize.steps(): usan el resumen y el plan que generó "Cargar plan" para ese
usuario (data/cases/<id>/summary.json) y su persona. Cada paso se puede escuchar con el botón Escuchar."""
import streamlit as st

from compat import stretch

import personalize
import voice_ui
import workspaces

def _needs_plan(user_id: str) -> bool:
    """True si el usuario tiene un caso del que generar plan pero todavía no lo ha generado."""
    return personalize.profile(user_id)["has_data"] and workspaces.load_plan_summary(user_id) is None


def _gate() -> None:
    """Sin plan no hay tutorial: el tutorial se construye con el resumen y el plan que genera la IA,
    así que aquí se ofrece generarlo (y reintentarlo si falló) en vez de mostrar una versión sin IA."""
    ss = st.session_state
    st.markdown("## Primero, tu plan")
    st.markdown("Este tutorial se construye con tu resumen y tu plan de acción, y todavía no están generados. "
                "El Co-Pilot los prepara en aproximadamente un minuto y después el tutorial se abre con tus datos.")
    err = ss.get("init_error")
    if err:
        st.warning(f"No se ha podido generar el plan: {err}\n\n"
                   "Comprueba que el backend está arrancado y que el archivo `.env` tiene `TEAM_KEY` y `MCP_TOKEN` "
                   "(el token caduca cada 72 h).")
    if st.button("Reintentar" if err else "Generar mi plan", key="tut_gen", type="primary",
                 icon=":material/auto_awesome:", **stretch(st.button)):
        ss.show_tutorial = True              # al terminar de generar, el tutorial se abre solo
        ss.want_plan_now = True
        st.rerun()                           # rerun completo: cierra el diálogo y deja ver el progreso


@st.dialog("Tutorial")
def _dialog() -> None:
    ss = st.session_state
    if _needs_plan(ss.get("user")):
        _gate()
        return
    steps = personalize.steps(ss.get("user"))
    step = min(max(ss.get("tut_step", 0), 0), len(steps) - 1)
    s = steps[step]
    last = step == len(steps) - 1

    st.progress((step + 1) / len(steps), text=f"Paso {step + 1} de {len(steps)}")
    st.markdown(f"## {s['title']}")
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
    Se marca como visto al abrirlo con el plan ya generado: si lo cierran con la X no vuelve a salir solo.
    Sin plan solo se ofrece generarlo (no cuenta como visto), y como mucho una vez por sesión."""
    ss = st.session_state
    asked = ss.pop("show_tutorial", False)
    if not (asked or not workspaces.tutorial_done(user_id)):
        return
    if _needs_plan(user_id):
        if asked or not ss.get("tut_gate_shown"):
            ss.tut_gate_shown = True
            ss.tut_step = 0
            _dialog()
        return
    workspaces.mark_tutorial_done(user_id)
    ss.tut_step = 0
    _dialog()
