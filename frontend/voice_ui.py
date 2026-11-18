"""Botones de voz para Streamlit: 🔊 escuchar un texto y 🎤 hacer una pregunta hablando.

El audio solo se genera al pulsar (cuesta dinero del presupuesto compartido de ElevenLabs) y queda en
data/audio_cache/, así que oírlo una segunda vez es gratis. Si no hay TEAM_KEY, no se muestra nada de voz.
"""
import hashlib

import streamlit as st

from compat import stretch

import voice


def available() -> bool:
    return voice.enabled()


def mic_available() -> bool:
    return voice.enabled() and hasattr(st, "audio_input")


@st.fragment
def speak_button(text: str, key: str, label: str = "🔊 Escuchar") -> None:
    """Botón que lee `text` en voz alta. Es un fragmento: al pulsarlo solo se redibuja él."""
    if not voice.enabled() or not voice.clean_for_speech(text):
        return
    ss = st.session_state
    opened = ss.setdefault("tts_open", [])
    k = f"{key}_{hashlib.sha1(str(text).encode('utf-8')).hexdigest()[:8]}"     # si cambia el texto, es otro audio
    cached = voice.is_cached(text)
    help_txt = "Ya generado: gratis." if cached else (
        f"Primera vez: ~{voice.estimate_cost(text):.3f} $ del presupuesto de ElevenLabs. Después es gratis.")
    clicked = st.button(label + (" ✓" if cached else ""), key=f"tts_btn_{k}", help=help_txt)
    if clicked and k not in opened:
        opened.append(k)
    if k in opened:
        with st.spinner("Generando voz…"):
            audio, err = voice.speak(text)
        if err:
            opened.remove(k)
            st.warning(err)
        else:
            _, truncated = voice.prepare(text)
            try:
                st.audio(audio, format="audio/mp3", autoplay=clicked)  # solo suena solo al pulsar
            except TypeError:                                          # Streamlit antiguo sin autoplay
                st.audio(audio, format="audio/mp3")
            if truncated:
                st.caption("Se lee el principio del texto (límite de voz).")


def mic_prompt() -> str | None:
    """🎤 Pregunta hablando. Devuelve el texto transcrito la primera vez que se graba un audio nuevo."""
    if not mic_available():
        return None
    ss = st.session_state
    gen = ss.setdefault("mic_gen", 0)
    with st.popover("🎤 Preguntar con la voz", **stretch(st.popover)):
        st.caption("Graba tu pregunta, para y se envía sola. Se transcribe con ElevenLabs (scribe-v2).")
        clip = st.audio_input("Grabar", key=f"mic_{gen}", label_visibility="collapsed")
    if clip is None:
        return None
    data = clip.getvalue()
    h = hashlib.sha1(data).hexdigest()
    if ss.get("_mic_hash") == h:
        return None
    ss._mic_hash = h
    ss.mic_gen = gen + 1                              # el siguiente rerun muestra el grabador vacío
    with st.spinner("Transcribiendo…"):
        text, err = voice.transcribe(data)
    if err:
        st.warning(err)
        return None
    return text
