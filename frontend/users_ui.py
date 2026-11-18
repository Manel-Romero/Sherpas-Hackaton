"""Pantalla de entrada, cambio de usuario y creación de usuarios copiando los datos de otro."""
import streamlit as st

from compat import stretch

import kanban_store as ks
import table_store as ts
import workspaces

# Claves de sesión que dependen del usuario activo: se borran al entrar o salir.
_PER_USER_KEYS = ("table_version", "df", "kanban_version", "last_nonce", "ask_talk_agent",
                  "is_streaming", "notify_changes", "notify_msg", "_chat_saved", "show_tutorial",
                  "auto_init_tried", "tut_step", "tts_open", "mic_gen", "_mic_hash",
                  "init_error", "want_plan_now", "tut_gate_shown")


def login(user_id: str) -> None:
    """Deja la sesión lista para `user_id` y vuelve a ejecutar la app."""
    ss = st.session_state
    for k in _PER_USER_KEYS:
        ss.pop(k, None)
    ss.user = user_id
    ss.case_id = user_id                          # kanban_ui y el backend trabajan con "case_id"
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
    """Formulario: nombre del usuario nuevo + de quién copiar los datos."""
    users = workspaces.list_users()
    ids = [u["id"] for u in users]
    labels = {u["id"]: u["label"] for u in users}
    index = ids.index(default_source) if default_source in ids else 0
    with st.form(f"new_user_{key}", clear_on_submit=False):
        name = st.text_input("Nombre del usuario nuevo", placeholder="Ej: Melanie")
        source = st.selectbox("Copiar los datos de", ids, index=index, format_func=labels.get)
        st.caption("Se copian la tabla y las tareas. El chat no se copia. "
                   "Después cada uno edita lo suyo sin afectar al otro.")
        if st.form_submit_button("Crear y entrar", **stretch(st.form_submit_button)):
            try:
                login(workspaces.create_user(name, source))
            except ValueError as e:
                st.error(str(e))


def login_screen() -> None:
    """Primera pantalla: elegir usuario o crear uno nuevo. Termina con st.stop()."""
    st.markdown('<div class="empty-title" style="margin-top:6vh">Sherpas Co-Pilot</div>'
                '<div class="empty-sub">Tu plan financiero, hecho para entenderlo y para actuar. '
                'Elige quién eres para continuar.</div>', unsafe_allow_html=True)

    users = workspaces.list_users()
    with st.container():
        st.markdown('<span class="marker empty-marker"></span>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, u in enumerate(users):
            detail = f"{u['city']} · " if u["city"] else ""
            label = f"{u['label']}  —  {detail}score {u['score']}/100"
            if u["custom"]:
                label += "  (copia)"
            if cols[i % 2].button(label, key=f"login_{u['id']}", **stretch(st.button)):
                login(u["id"])

    left, mid, right = st.columns([1, 2, 1])
    with mid:
        with st.expander("Crear un usuario nuevo copiando los datos de otro"):
            create_user_form(users[0]["id"] if users else None, key="login")
    st.stop()


def user_strip(user: dict | None) -> tuple[bool, bool]:
    """Franja superior con el usuario activo y sus acciones.
    Devuelve (pulsó Tutorial, pulsó Cargar plan)."""
    ss = st.session_state
    c_user, c_tut, c_plan, c_users = st.columns([4, 1.3, 1.5, 1.5])
    with c_user:
        if user:
            st.markdown(
                f"<div class='user-chip'><strong>{user['label']}</strong>"
                f"<span class='user-meta'>{user['city']} · score {user['score']}/100 "
                f"({workspaces.score_label(user['score'])})</span></div>",
                unsafe_allow_html=True)
    tut = c_tut.button("Tutorial", icon=":material/help:", **stretch(st.button))
    plan = c_plan.button("Cargar plan", icon=":material/play_arrow:", **stretch(st.button),
                         help="El Co-Pilot analiza tu caso y rellena el plan, la tabla y las tareas.")
    with c_users:
        with st.popover("Usuarios", icon=":material/group:", **stretch(st.popover)):
            if st.button("Cambiar de usuario", key="switch_user", **stretch(st.button)):
                logout()
            st.markdown("**Crear usuario copiando este**")
            create_user_form(ss.get("user"), key="strip")
    return tut, plan
