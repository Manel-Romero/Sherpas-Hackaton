# Pantalla de entrada, cambio de usuario y creacion de usuarios copiando datos.
import streamlit as st

from compat import stretch

import kanban_store as ks
import table_store as ts
import workspaces

# Claves de sesion dependientes del usuario activo
_PER_USER_KEYS = ("table_version", "df", "kanban_version", "last_nonce", "ask_talk_agent",
                  "is_streaming", "notify_changes", "notify_msg", "_chat_saved", "show_tutorial")


def login(user_id: str) -> None:
    """Deja la sesion lista para user_id y recarga la aplicacion."""
    ss = st.session_state
    for k in _PER_USER_KEYS:
        ss.pop(k, None)
    ss.user = user_id
    ss.case_id = user_id
    ss.session_id = f"sess_{user_id}"
    ss.messages = workspaces.load_chat(user_id)
    ss.editor_gen = ss.get("editor_gen", 0) + 1
    ts.set_case(user_id)
    ks.set_case(user_id)
    st.rerun()


def logout() -> None:
    ss = st.session_state
    for k in _PER_USER_KEYS + ("user", "case_id", "session_id", "messages"):
        ss.pop(k, None)
    st.rerun()


def create_user_form(default_source: str | None, key: str) -> None:
    """Formulario: nombre del usuario nuevo + caso fuente para copiar datos."""
    users = workspaces.list_users()
    ids = [u["id"] for u in users]
    labels = {u["id"]: u["label"] for u in users}
    index = ids.index(default_source) if default_source in ids else 0
    with st.form(f"new_user_{key}", clear_on_submit=False):
        name = st.text_input("Nombre del nuevo cliente o escenario", placeholder="Ej: Escenario Compra Vivienda")
        source = st.selectbox("Copiar datos iniciales de:", ids, index=index, format_func=labels.get)
        st.caption("Se clonan la tabla y tareas del plan. El historial de chat empieza limpio.")
        if st.form_submit_button("Crear y acceder", **stretch(st.form_submit_button)):
            try:
                login(workspaces.create_user(name, source))
            except ValueError as e:
                st.error(str(e))


def login_screen() -> None:
    """Primera pantalla de seleccion de cliente o creacion. Termina con st.stop()."""
    st.markdown(
        '<div style="text-align: center; margin-top: 5vh; margin-bottom: 28px;">'
        '<div style="font-family: \'Poppins\', sans-serif; font-size: 2.2rem; font-weight: 800; letter-spacing: 0.04em; color: #ffffff;">'
        'SHERPAS <span style="color: #6586fc;">WEALTH</span></div>'
        '<div style="color: var(--muted); font-size: 1.05rem; margin-top: 6px;">'
        'Plataforma de Finanzas Generativas para Gestion Patrimonial</div>'
        '<div style="color: var(--muted); font-size: 0.86rem; margin-top: 4px;">'
        'Selecciona un expediente de cliente para acceder al panel</div>'
        '</div>',
        unsafe_allow_html=True
    )

    users = workspaces.list_users()
    with st.container():
        st.markdown('<span class="marker empty-marker"></span>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, u in enumerate(users):
            detail = f"{u['city']} · " if u["city"] else ""
            score = u.get("score", 0)
            score_cls = "Optimo" if score >= 70 else ("Atencion" if score >= 40 else "Critico")
            label = f"{u['label']} — {detail}Score {score}/100 ({score_cls})"
            if u["custom"]:
                label = "👤 " + label
            if cols[i % 2].button(label, key=f"login_{u['id']}", **stretch(st.button)):
                login(u["id"])

    left, mid, right = st.columns([1, 2, 1])
    with mid:
        with st.expander("➕ Crear nuevo escenario clonando un cliente"):
            create_user_form(users[0]["id"] if users else None, key="login")
    st.stop()


def user_strip(user: dict | None) -> tuple[bool, bool]:
    """Franja superior de cliente activo y acciones rapidas.
    Devuelve (pulso Tutorial, pulso Cargar plan)."""
    ss = st.session_state
    c_user, c_tut, c_plan, c_users = st.columns([5, 1.2, 1.4, 1.4])
    with c_user:
        if user:
            score = user.get("score", 0)
            score_cls = "score-glow-pill" if score >= 70 else ("score-glow-pill-amber" if score >= 40 else "score-glow-pill-red")
            score_txt = workspaces.score_label(score)
            city_str = f" · 📍 {user['city']}" if user.get("city") else ""
            st.markdown(
                f"<div class='user-chip'>"
                f"<span style='font-family:Poppins, sans-serif; font-weight:700; font-size:1.05rem; color:#f8fafc;'>{user['label']}</span>"
                f"<span class='{score_cls}'>Score {score}/100 · {score_txt}</span>"
                f"<span class='user-meta'>{city_str}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    tut = c_tut.button("❔ Tutorial", **stretch(st.button))
    plan = c_plan.button("🚀 Cargar plan", **stretch(st.button),
                         help="El Co-Pilot analiza el caso y genera el plan, la tabla y las tareas.")
    with c_users:
        with st.popover("👥 Clientes", **stretch(st.popover)):
            if st.button("Cambiar de cliente", key="switch_user", **stretch(st.button)):
                logout()
            st.markdown("**Crear escenario clonando este**")
            create_user_form(ss.get("user"), key="strip")
    return tut, plan
