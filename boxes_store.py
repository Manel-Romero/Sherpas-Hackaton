"""Storage for the boxes (title + content). Same idea as table_store.py.

boxes.json format:
{"boxes": [{"title": "...", "content": "..."}, ...]}
Titles must be unique (the AI and the UI refer to a box by its title).
"""
import json
import os
import threading
from pathlib import Path

BOXES_FILE = Path(os.environ.get("BOXES_JSON", Path(__file__).with_name("boxes.json")))
_lock = threading.Lock()


def clean(data: dict) -> dict:
    boxes, seen = [], set()
    for b in data.get("boxes", []):
        title = str(b.get("title", "")).strip()
        content = str(b.get("content", "")).strip()
        if not title:
            raise ValueError("Every box needs a title.")
        if title in seen:
            raise ValueError(f"Duplicate title '{title}'.")
        seen.add(title)
        boxes.append({"title": title, "content": content})
    return {"boxes": boxes}

def load() -> dict:
    with _lock:
        if not BOXES_FILE.exists():
            return {"boxes": []}
        return clean(json.loads(BOXES_FILE.read_text(encoding="utf-8")))

def save(data: dict) -> dict:
    data = clean(data)
    with _lock:
        tmp = BOXES_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, BOXES_FILE)  # atomic swap
    return data

def version() -> int:
    """Changes whenever the file changes (used by the watcher)."""
    return BOXES_FILE.stat().st_mtime_ns if BOXES_FILE.exists() else 0