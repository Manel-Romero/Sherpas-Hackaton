"""Lee la configuración del frontend: variables de entorno y, si no están, el `.env` de la raíz
(el mismo fichero que usa el backend). Así el frontend no necesita nada más para hablar con el proxy."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_cache: dict | None = None


def _read_dotenv() -> dict:
    out = {}
    f = ROOT / ".env"
    if not f.exists():
        return out
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def get(key: str, default: str = "") -> str:
    """Variable de entorno > .env > valor por defecto."""
    global _cache
    if key in os.environ and os.environ[key] != "":
        return os.environ[key]
    if _cache is None:
        _cache = _read_dotenv()
    return _cache.get(key) or default


def reload() -> None:
    """Vuelve a leer el .env (útil en tests)."""
    global _cache
    _cache = None
