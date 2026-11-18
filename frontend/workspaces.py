"""Usuarios (espacios de trabajo) de la app.

Cada usuario es una carpeta data/cases/<id>/ con sus ficheros:
    table.json, kanban.json, boxes.json   -> datos del plan (los usan table_store / kanban_store)
    chat.json                             -> conversación guardada
    summary.json                          -> lo que generó "Cargar plan": resumen ejecutivo, titular y primera acción
    profile.json                          -> ficha de datos del hogar (profile_store), que el Co-Pilot mantiene al día
    meta.json                             -> {display_name, base_case, copied_from, tutorial_done}

Los 4 casos de Sherpas (carpeta cases/) son usuarios de serie. Un usuario nuevo se crea
copiando los datos de otro (por ejemplo, la pareja de Timothy copia el plan de Timothy y lo
personaliza). Su `base_case` es el caso de Sherpas del que cuelga: el backend lo usa para leer
el informe y la persona del hogar.
"""
import json
import os
import re
import shutil
import time
import unicodedata
from functools import lru_cache
from pathlib import Path
import project_paths

ROOT = project_paths.ROOT
CASES_DIR = project_paths.CASES_DIR
DATA_DIR = project_paths.DATA_CASES_DIR      # el mismo sitio que usan table_store y kanban_store
DATA_FILES = ("table.json", "kanban.json", "boxes.json", "summary.json", "profile.json")
PLAN_FILES = ("table.json", "kanban.json", "boxes.json", "profile.json")   # lo que "Cargar plan" sobrescribe
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


# ---------------------------------------------------------------- utilidades
def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:40].strip("-")


def _dir(user_id: str) -> Path:
    if not _ID_RE.match(user_id or ""):
        raise ValueError(f"Identificador de usuario no válido: '{user_id}'.")
    return DATA_DIR / user_id


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


# ---------------------------------------------------------------- casos de Sherpas
@lru_cache(maxsize=1)
def base_cases() -> tuple[dict, ...]:
    """Los casos de la carpeta cases/: id, título, ciudad y score."""
    out = []
    if CASES_DIR.exists():
        for d in sorted(CASES_DIR.iterdir()):
            f = d / "financial-health.json"
            if not (d.is_dir() and f.exists()):
                continue
            try:
                fh = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            info = fh.get("case", {})
            adults = [m.get("first_name", "") for m in info.get("household", []) if m.get("role") != "child"]
            out.append({
                "id": d.name,
                "title": " & ".join(a for a in adults if a) or d.name,
                "city": info.get("city") or "",
                "score": int(fh.get("score", {}).get("published_score", 0) or 0),
            })
    return tuple(out)


def score_label(score: int) -> str:
    return "Crítico" if score < 40 else ("Atención" if score < 70 else "Óptimo")


# ---------------------------------------------------------------- meta
def read_meta(user_id: str) -> dict:
    try:
        return json.loads((_dir(user_id) / "meta.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_meta(user_id: str, **updates) -> dict:
    meta = {**read_meta(user_id), **updates}
    _atomic_write(_dir(user_id) / "meta.json", json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def base_case_of(user_id: str) -> str:
    return read_meta(user_id).get("base_case") or user_id


def tutorial_done(user_id: str) -> bool:
    return bool(read_meta(user_id).get("tutorial_done"))


def mark_tutorial_done(user_id: str) -> None:
    write_meta(user_id, tutorial_done=True)


# ---------------------------------------------------------------- resumen del plan
def save_plan_summary(user_id: str, init_response: dict) -> None:
    """Guarda lo que devuelve /api/cases/<id>/init y que el backend solo conserva en memoria:
    el resumen ejecutivo (hecho a partir de persona.md y del informe), el titular y la primera acción."""
    plan = init_response.get("master_plan") or {}
    data = {
        "executive_summary": init_response.get("executive_summary") or "",
        "headline": plan.get("headline") or init_response.get("headline") or "",
        "immediate_action": plan.get("immediate_action") or {},
        "tasks": [{"title": t.get("title", ""), "week": t.get("week"),
                   "impact": (t.get("impact") or {}).get("value", "")}
                  for t in plan.get("tasks", []) if isinstance(t, dict)],
        "saved_at": int(time.time()),
    }
    _atomic_write(_dir(user_id) / "summary.json", json.dumps(data, indent=2, ensure_ascii=False))


def backup_plan_files(user_id: str) -> Path | None:
    """Copia table/kanban/boxes/profile actuales a data/cases/<id>/backup-<fecha>/ antes de que "Cargar plan"
    los sobrescriba. Devuelve la carpeta, o None si no había nada que guardar."""
    files = [f for f in (_dir(user_id) / n for n in PLAN_FILES) if f.exists()]
    if not files:
        return None
    dest = _dir(user_id) / time.strftime("backup-%Y%m%d-%H%M%S")
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy2(f, dest / f.name)
    return dest


def load_plan_summary(user_id: str) -> dict | None:
    try:
        data = json.loads((_dir(user_id) / "summary.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if data.get("executive_summary") or data.get("headline") else None


# ---------------------------------------------------------------- usuarios
def list_users() -> list[dict]:
    """Casos de Sherpas + usuarios creados por copia. Cada uno: id, label, city, score, custom, base_case."""
    base = {c["id"]: c for c in base_cases()}
    users = [{
        "id": c["id"], "label": c["title"], "city": c["city"], "score": c["score"],
        "custom": False, "base_case": c["id"], "copied_from": None,
    } for c in base.values()]
    if DATA_DIR.exists():
        for d in sorted(DATA_DIR.iterdir()):
            if not d.is_dir() or d.name in base or not _ID_RE.match(d.name):
                continue
            meta = read_meta(d.name)
            if not meta.get("base_case"):
                continue                      # carpeta sin meta: no es un usuario creado por la app
            bc = base.get(meta["base_case"], {})
            users.append({
                "id": d.name, "label": meta.get("display_name") or d.name,
                "city": bc.get("city", ""), "score": bc.get("score", 0),
                "custom": True, "base_case": meta["base_case"], "copied_from": meta.get("copied_from"),
            })
    return users


def get_user(user_id: str) -> dict | None:
    return next((u for u in list_users() if u["id"] == user_id), None)


def create_user(display_name: str, copy_from: str) -> str:
    """Crea un usuario nuevo con una copia de los datos de `copy_from`. Devuelve su id."""
    display_name = (display_name or "").strip()
    new_id = slugify(display_name)
    if not new_id:
        raise ValueError("Escribe un nombre para el usuario nuevo.")
    src = get_user(copy_from)
    if not src:
        raise ValueError(f"No existe el usuario '{copy_from}' para copiar.")
    if get_user(new_id) or (DATA_DIR / new_id).exists():
        raise ValueError(f"Ya existe un usuario llamado '{new_id}'. Prueba con otro nombre.")

    dest = _dir(new_id)
    dest.mkdir(parents=True)
    try:
        for fname in DATA_FILES:
            f = _dir(copy_from) / fname
            if f.exists():
                shutil.copy2(f, dest / fname)
        write_meta(new_id, display_name=display_name, base_case=src["base_case"],
                   copied_from=copy_from, created_at=int(time.time()), tutorial_done=False)
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)   # no dejar un usuario a medias
        raise
    return new_id


def has_plan(user_id: str) -> bool:
    """True si el usuario ya tiene tabla o tareas guardadas."""
    return any((_dir(user_id) / f).exists() for f in ("table.json", "kanban.json"))


# ---------------------------------------------------------------- chat guardado
MAX_SAVED_MESSAGES = 200


def load_chat(user_id: str) -> list[dict]:
    try:
        data = json.loads((_dir(user_id) / "chat.json").read_text(encoding="utf-8"))
        return [m for m in data if isinstance(m, dict) and m.get("role") and "content" in m]
    except Exception:
        return []


def save_chat(user_id: str, messages: list[dict]) -> None:
    _atomic_write(_dir(user_id) / "chat.json",
                  json.dumps(messages[-MAX_SAVED_MESSAGES:], indent=2, ensure_ascii=False))
