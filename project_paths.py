"""Rutas del proyecto en un solo sitio. El backend, el frontend y los almacenes de datos importan de aquí
en vez de calcular cada uno su `Path(__file__).parent...`."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "cases"                       # los 4 casos de Sherpas (solo lectura)
DATA_DIR = ROOT / "data"
DATA_CASES_DIR = DATA_DIR / "cases"              # una carpeta por usuario: tabla, tareas, chat, resumen...
LOGS_DIR = DATA_DIR / "logs"
AUDIO_CACHE_DIR = DATA_DIR / "audio_cache"       # voz ya generada (no se vuelve a pagar)
