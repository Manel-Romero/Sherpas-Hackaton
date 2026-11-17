"""Kanban storage: kanban.json

{"cards": [{"id": "a1b2c3", "title": "...", "content": "...", "status": "todo"}, ...]}

status is one of STATUSES. The order of the list is the order inside each column.
The UI buttons and the MCP tools both call the functions below, so the logic lives here only once.
"""
import json
import os
import threading
import uuid
from pathlib import Path

KANBAN_FILE = Path(os.environ.get("KANBAN_JSON", Path(__file__).with_name("kanban.json")))
_lock = threading.Lock()

# key (stored in the JSON) -> label (shown in the UI). Order = left to right.
STATUSES = {"todo": "To do", "in_process": "In process", "done": "Done"}


def clean(data: dict) -> dict:
    cards, seen = [], set()
    for c in data.get("cards", []):
        title = str(c.get("title", "")).strip()
        if not title:
            raise ValueError("Every card needs a title.")
        status = c.get("status", "todo")
        if status not in STATUSES:
            raise ValueError(f"Invalid status '{status}'. Use one of {list(STATUSES)}.")
        cid = str(c.get("id") or uuid.uuid4().hex[:6])   # new cards get an id here
        if cid in seen:
            raise ValueError(f"Duplicate id '{cid}'.")
        seen.add(cid)
        cards.append({"id": cid, "title": title,
                      "content": str(c.get("content", "")).strip(), "status": status})
    return {"cards": cards}


def load() -> dict:
    with _lock:
        if not KANBAN_FILE.exists():
            return {"cards": []}
        return clean(json.loads(KANBAN_FILE.read_text(encoding="utf-8")))


def save(data: dict) -> dict:
    data = clean(data)
    with _lock:
        tmp = KANBAN_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, KANBAN_FILE)  # atomic swap
    return data


def version() -> int:
    """Changes whenever the file changes (used by the watcher)."""
    return KANBAN_FILE.stat().st_mtime_ns if KANBAN_FILE.exists() else 0


# ---------------- operations (used by the UI and by the MCP tools) ----------------
def _find(data: dict, card_id: str) -> dict:
    for c in data["cards"]:
        if c["id"] == card_id:
            return c
    raise ValueError(f"No card with id '{card_id}'. Existing ids: {[c['id'] for c in data['cards']]}")


def add_card(title: str, content: str = "", status: str = "todo") -> dict:
    data = load()
    data["cards"].append({"title": title, "content": content, "status": status})
    return save(data)


def update_card(card_id: str, title: str | None = None, content: str | None = None) -> dict:
    data = load()
    card = _find(data, card_id)
    if title is not None:
        card["title"] = title
    if content is not None:
        card["content"] = content
    return save(data)


def move_card(card_id: str, status: str) -> dict:
    """Move a card to another column; it lands at the bottom of that column."""
    if status not in STATUSES:
        raise ValueError(f"Invalid status '{status}'. Use one of {list(STATUSES)}.")
    data = load()
    card = _find(data, card_id)
    card["status"] = status
    data["cards"].remove(card)
    data["cards"].append(card)
    return save(data)


def arrange(layout: dict[str, list[str]]) -> dict:
    """Save a drag-and-drop result: {status: [card ids in order]}.
    Refuses if the cards in `layout` aren't exactly the cards in the file
    (e.g. the AI added or deleted one meanwhile), so a stale screen can't overwrite it."""
    data = load()
    by_id = {c["id"]: c for c in data["cards"]}
    ids = [i for column in layout.values() for i in column]
    if sorted(ids) != sorted(by_id):
        raise ValueError("The board changed while you were moving a card. Refreshing...")
    cards = []
    for status in STATUSES:
        for cid in layout.get(status, []):
            by_id[cid]["status"] = status
            cards.append(by_id[cid])
    return save({"cards": cards})


def delete_card(card_id: str) -> dict:
    data = load()
    data["cards"].remove(_find(data, card_id))
    return save(data)
