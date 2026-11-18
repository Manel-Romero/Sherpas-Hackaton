"""Tutorial de bienvenida: un diálogo de varios pasos que se abre la primera vez que
un usuario entra, y que se puede volver a abrir con el botón "Tutorial"."""
import streamlit as st

from compat import stretch

import workspaces

STEPS = [
    {
        "icon": "👋",
        "title": "Bienvenido a tu plan",
        "body": (
            "Aquí tu plan financiero deja de ser un documento largo y se convierte en algo que "
            "puedes **mover, probar y preguntar**. En un minuto te enseñamos las tres pestañas."
        ),
    },
    {
        "icon": "📋",
        "title": "Plan de acción",
        "body": (
            "Es un tablero con las tareas del plan, empezando por la acción más urgente.\n\n"
            "- **Arrastra** una tarjeta entre *To do*, *In process* y *Done*.\n"
            "- **Haz clic** en una tarjeta para ver el detalle y los pasos.\n"
            "- Usa **➕ Añadir tarea** para crear la tuya. La ✕ la borra."
        ),
    },
    {
        "icon": "📊",
        "title": "Proyección y datos",
        "body": (
            "Arriba ves tus cifras clave y cómo evoluciona tu patrimonio mes a mes.\n\n"
            "- **Edita cualquier celda** de la tabla y el gráfico se actualiza.\n"
            "- Añade una fila para un mes nuevo o una **columna** para seguir otra cifra.\n"
            "- Todo se guarda solo."
        ),
    },
    {
        "icon": "💬",
        "title": "Chat con el Co-Pilot",
        "body": (
            "Pregunta lo que no entiendas, con tus palabras. El Co-Pilot conoce tu caso y puede "
            "**cambiar la tabla y las tareas por ti**.\n\n"
            "Prueba con: *«Me han dado un bonus de 15.000 $, ¿qué hago con él?»* o "
            "*«Muéstrame un gráfico de mis gastos»*."
        ),
    },
    {
        "icon": "👥",
        "title": "¿Vais en pareja?",
        "body": (
            "Cada persona puede tener **su propio usuario**. Desde el botón **👥 Usuarios** "
            "crea uno nuevo **copiando los datos de otro**: empieza igual que el original y "
            "después lo personalizas sin tocar el de tu pareja.\n\n"
            "Si el plan aún está vacío, pulsa **🚀 Cargar plan** para que el Co-Pilot lo genere."
        ),
    },
]


@st.dialog("Tutorial")
def _dialog() -> None:
    ss = st.session_state
    step = min(max(ss.get("tut_step", 0), 0), len(STEPS) - 1)
    s = STEPS[step]
    last = step == len(STEPS) - 1

    st.progress((step + 1) / len(STEPS), text=f"Paso {step + 1} de {len(STEPS)}")
    st.markdown(f"## {s['icon']} {s['title']}")
    st.markdown(s["body"])

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
