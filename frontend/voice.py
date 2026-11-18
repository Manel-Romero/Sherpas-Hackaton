"""Voz: texto a voz y voz a texto con ElevenLabs, a través del proxy del hackathon.

    POST {LLM_PROXY_URL}/audio/speech          (modelo eleven-flash-v2.5)  -> audio mp3
    POST {LLM_PROXY_URL}/audio/transcriptions  (modelo scribe-v2)          -> {"text": "..."}

Cuidado con el presupuesto: ElevenLabs es compartido y a cada equipo le tocan unos 1,40 $ en total
(~35.000 caracteres con eleven-flash-v2.5). Por eso:
  - el audio solo se genera cuando el usuario pulsa el botón (nunca solo),
  - todo audio generado se guarda en data/audio_cache/ y no se vuelve a pagar,
  - los textos largos se recortan (MAX_CHARS) y el botón avisa del coste estimado.
"""
import hashlib
import re
from pathlib import Path

import httpx

import envconfig
import project_paths

CACHE_DIR = project_paths.AUDIO_CACHE_DIR
MAX_CHARS = 1200
PRICE_PER_1K = {"eleven-flash-v2.5": 0.04, "eleven-multilingual-v2": 0.08, "eleven-v3": 0.08}
TIMEOUT = 60.0
_TRANSPORT = None          # solo para tests: un httpx.MockTransport


# ---------------------------------------------------------------- configuración
def _cfg() -> dict:
    return {
        "url": envconfig.get("LLM_PROXY_URL", "https://llm-hackathon.sherpaswealth.com/v1").rstrip("/"),
        "key": envconfig.get("TEAM_KEY", ""),
        "tts_model": envconfig.get("TTS_MODEL", "eleven-flash-v2.5"),
        "voice": envconfig.get("TTS_VOICE", "alloy"),
        "stt_model": envconfig.get("STT_MODEL", "scribe-v2"),
    }


def enabled() -> bool:
    """Hay una clave de equipo real configurada (y la voz no está apagada con VOICE_ENABLED=0)."""
    key = _cfg()["key"]
    off = envconfig.get("VOICE_ENABLED", "1").lower() in ("0", "false", "no")
    return bool(key) and not key.startswith("your-") and not off


# ---------------------------------------------------------------- texto
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF️‍]")


def clean_for_speech(text: str) -> str:
    """Quita el formato Markdown, enlaces y emojis, que sonarían raro leídos en voz alta."""
    t = str(text or "")
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"^\s*[-*•]\s+", "", t, flags=re.M)
    t = re.sub(r"(\*\*|__|\*|_|`|~~)", "", t)
    t = _EMOJI.sub("", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", ". ", t)
    t = re.sub(r"\s*\n\s*", ". ", t)
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    t = re.sub(r"\.\s*\.", ".", t)
    return t.strip()


def prepare(text: str, max_chars: int = MAX_CHARS) -> tuple[str, bool]:
    """Texto listo para leer y si se ha recortado (se corta al final de una frase)."""
    t = clean_for_speech(text)
    if len(t) <= max_chars:
        return t, False
    cut = t[:max_chars]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return (cut[: end + 1] if end > max_chars * 0.5 else cut).strip(), True


def estimate_cost(text: str) -> float:
    spoken, _ = prepare(text)
    return len(spoken) / 1000 * PRICE_PER_1K.get(_cfg()["tts_model"], 0.08)


# ---------------------------------------------------------------- caché en disco
def _path(spoken: str) -> Path:
    c = _cfg()
    h = hashlib.sha1(f"{c['tts_model']}|{c['voice']}|{spoken}".encode("utf-8")).hexdigest()[:24]
    return CACHE_DIR / f"{h}.mp3"


def is_cached(text: str) -> bool:
    spoken, _ = prepare(text)
    return bool(spoken) and _path(spoken).exists()


# ---------------------------------------------------------------- llamadas al proxy
def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, transport=_TRANSPORT)


def _explain(resp: httpx.Response) -> str:
    code = resp.status_code
    body = resp.text[:200].replace("\n", " ")
    if code == 429:
        return "Demasiadas peticiones seguidas al servicio de voz. Espera unos segundos y vuelve a intentarlo."
    if code in (402, 403):
        return ("El servicio de voz ha rechazado la petición, probablemente porque se ha agotado el "
                f"presupuesto de ElevenLabs del equipo. ({code}: {body})")
    if code == 401:
        return "La clave del equipo (TEAM_KEY) no es válida para el servicio de voz."
    return f"El servicio de voz respondió {code}: {body}"


def speak(text: str) -> tuple[bytes | None, str | None]:
    """Devuelve (audio mp3, error). Usa la caché; solo paga si el texto no se había leído antes."""
    spoken, truncated = prepare(text)
    if not spoken:
        return None, "No hay texto que leer."
    path = _path(spoken)
    if path.exists():
        return path.read_bytes(), None
    if not enabled():
        return None, "La voz no está configurada: falta TEAM_KEY en el archivo .env."

    c = _cfg()
    try:
        with _client() as cli:
            r = cli.post(f"{c['url']}/audio/speech",
                         headers={"Authorization": f"Bearer {c['key']}"},
                         json={"model": c["tts_model"], "input": spoken, "voice": c["voice"],
                               "response_format": "mp3"})
    except httpx.HTTPError as e:
        return None, f"No se pudo conectar con el servicio de voz: {e}"
    if r.status_code != 200:
        return None, _explain(r)
    if not r.content or "json" in r.headers.get("content-type", ""):
        return None, f"El servicio de voz no devolvió audio: {r.text[:200]}"

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(r.content)
    tmp.replace(path)
    return r.content, None


def transcribe(audio: bytes, filename: str = "voz.wav", language: str | None = "es") -> tuple[str | None, str | None]:
    """Voz a texto con scribe-v2. Devuelve (texto, error)."""
    if not audio:
        return None, "No se ha grabado nada."
    if not enabled():
        return None, "La voz no está configurada: falta TEAM_KEY en el archivo .env."
    c = _cfg()
    data = {"model": c["stt_model"]}
    if language:
        data["language"] = language
    try:
        with _client() as cli:
            r = cli.post(f"{c['url']}/audio/transcriptions",
                         headers={"Authorization": f"Bearer {c['key']}"},
                         data=data, files={"file": (filename, audio, "audio/wav")})
    except httpx.HTTPError as e:
        return None, f"No se pudo conectar con el servicio de voz: {e}"
    if r.status_code != 200:
        return None, _explain(r)
    try:
        text = (r.json().get("text") or "").strip()
    except ValueError:
        return None, "Respuesta de transcripción no válida."
    return (text, None) if text else (None, "No se entendió nada. Prueba a hablar más cerca del micrófono.")
