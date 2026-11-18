"""Kanban storage: kanban.json

{"cards": [{"id": "a1b2c3", "title": "...", "short_description": "...", "detailed_description": "...", "category": "debt", "impact": "-$3,500", "week": 1, "steps": [...], "status": "todo", "content": "..."}, ...]}

status is one of STATUSES. The order of the list is the order inside each column.
The UI buttons and the MCP tools both call the functions below, so the logic lives here only once.
"""
import json
import os
import threading
import uuid
from pathlib import Path
import project_paths

BASE_DATA_DIR = project_paths.DATA_CASES_DIR
KANBAN_FILE = Path(os.environ.get("KANBAN_JSON", Path(__file__).with_name("kanban.json")))
_lock = threading.Lock()

# key (stored in the JSON) -> label (shown in the UI). Order = left to right.
STATUSES = {"todo": "To do", "in_process": "In process", "done": "Done"}


def set_case(case_id: str = "michael-carter") -> Path:
    global KANBAN_FILE
    custom = os.environ.get("KANBAN_JSON")
    if custom:
        KANBAN_FILE = Path(custom)
        return KANBAN_FILE
    target_dir = BASE_DATA_DIR / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "kanban.json"
    KANBAN_FILE = target_file

    # Auto-migracion si no existe kanban.json pero si boxes.json
    if not target_file.exists():
        boxes_file = target_dir / "boxes.json"
        if boxes_file.exists():
            try:
                raw_boxes = json.loads(boxes_file.read_text(encoding="utf-8"))
                boxes_list = raw_boxes.get("boxes", []) if isinstance(raw_boxes, dict) else raw_boxes
                cards = []
                for b in boxes_list:
                    cat = b.get("category", "general")
                    st = "in_process" if cat in ("immediate", "prioritaria", "alerta") else "todo"
                    impact_text = b.get("impact", "")
                    title = b.get("title", "Tarea").strip()
                    desc = b.get("description") or b.get("content") or ""
                    steps = b.get("steps") or []
                    cards.append({
                        "id": uuid.uuid4().hex[:6],
                        "title": title,
                        "short_description": desc[:120] if len(desc) > 120 else desc,
                        "detailed_description": desc,
                        "category": cat,
                        "impact": impact_text,
                        "week": b.get("week"),
                        "steps": steps,
                        "status": st,
                        "content": desc
                    })
                save({"cards": cards})
            except Exception:
                pass
    return target_file


def _clean_card(c: dict) -> dict:
    raw_title = str(c.get("title", "")).strip()
    if not raw_title:
        raise ValueError("Every card needs a title.")

    status = c.get("status", "todo")
    if status not in STATUSES:
        status = "todo"

    cid = str(c.get("id") or uuid.uuid4().hex[:6])

    # 1. Extraer impacto si viene prefijado entre corchetes: [+$500/mes] Titulo
    impact = str(c.get("impact", "")).strip()
    title = raw_title
    if title.startswith("[") and "]" in title:
        idx_close = title.index("]")
        bracket_txt = title[1:idx_close].strip()
        title = title[idx_close + 1:].strip()
        if not impact:
            impact = bracket_txt

    # 2. Pasos de ejecucion (steps)
    steps = []
    raw_steps = c.get("steps")
    if isinstance(raw_steps, list):
        steps = [str(s).strip() for s in raw_steps if str(s).strip()]

    raw_content = str(c.get("content") or c.get("description") or "").strip()

    # Si steps viene vacio pero hay lineas con * o - en content
    text_desc = raw_content
    if not steps and raw_content:
        lines = [line.strip() for line in raw_content.split("\n") if line.strip()]
        desc_lines = []
        for line in lines:
            if line.startswith(("* ", "- ", "• ")) or (len(line) > 2 and line[0].isdigit() and line[1] in (".", ")")):
                step_text = line.lstrip("*-•0123456789.) ").strip()
                if step_text:
                    steps.append(step_text)
            else:
                desc_lines.append(line)
        text_desc = "\n".join(desc_lines).strip()

    # 3. Descripciones breve y detallada
    short_desc = str(c.get("short_description", "")).strip()
    detailed_desc = str(c.get("detailed_description", "")).strip()

    if not short_desc:
        if text_desc:
            first_sentence = text_desc.split(".")[0].strip()
            short_desc = (first_sentence + ".") if first_sentence and not first_sentence.endswith(".") else first_sentence
            if len(short_desc) > 130:
                short_desc = short_desc[:127] + "..."
        else:
            short_desc = title

    if not detailed_desc:
        detailed_desc = text_desc if text_desc else short_desc

    # 4. Categoria
    category = str(c.get("category", "")).strip().lower()
    if not category or category == "general":
        lower_txt = f"{title} {raw_content} {impact}".lower()
        if any(w in lower_txt for w in ("deuda", "interes", "tarjeta", "amex", "credito", "prestamo")):
            category = "debt"
        elif any(w in lower_txt for w in ("seguro", "poliza", "cobertura", "responsabilidad", "vida")):
            category = "insurance"
        elif any(w in lower_txt for w in ("ahorro", "fondo", "emergencia", "401", "ira")):
            category = "savings"
        elif any(w in lower_txt for w in ("inversion", "cartera", "activo", "bolsa")):
            category = "investment"
        elif any(w in lower_txt for w in ("presupuesto", "gasto", "entretenimiento", "estilo")):
            category = "lifestyle"
        elif any(w in lower_txt for w in ("inmediat", "hoy", "urgente")):
            category = "immediate"
        elif any(w in lower_txt for w in ("meta", "objetivo", "vivienda", "casa")):
            category = "goal"
        else:
            category = "general"

    # 5. Semana
    raw_week = c.get("week")
    week = None
    if raw_week is not None and str(raw_week).strip():
        try:
            week = int(raw_week)
        except (ValueError, TypeError):
            week = None

    return {
        "id": cid,
        "title": title,
        "short_description": short_desc,
        "detailed_description": detailed_desc,
        "category": category,
        "impact": impact,
        "week": week,
        "steps": steps,
        "status": status,
        "content": raw_content or detailed_desc
    }


def clean(data: dict) -> dict:
    cards, seen = [], set()
    for raw_c in data.get("cards", []):
        cleaned = _clean_card(raw_c)
        cid = cleaned["id"]
        if cid in seen:
            cid = uuid.uuid4().hex[:6]
            cleaned["id"] = cid
        seen.add(cid)
        cards.append(cleaned)
    return {"cards": cards}


def load(case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    with _lock:
        if not KANBAN_FILE.exists():
            return {"cards": []}
        return clean(json.loads(KANBAN_FILE.read_text(encoding="utf-8")))


def save(data: dict, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = clean(data)
    with _lock:
        tmp = KANBAN_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, KANBAN_FILE)  # atomic swap
    return data


def version(case_id: str | None = None) -> int:
    """Changes whenever the file changes (used by the watcher)."""
    if case_id:
        set_case(case_id)
    return KANBAN_FILE.stat().st_mtime_ns if KANBAN_FILE.exists() else 0


# ---------------- operations (used by the UI and by the MCP tools) ----------------
def _find(data: dict, card_id: str) -> dict:
    for c in data["cards"]:
        if c["id"] == card_id:
            return c
    raise ValueError(f"No card with id '{card_id}'. Existing ids: {[c['id'] for c in data['cards']]}")


def add_card(
    title: str,
    content: str = "",
    status: str = "todo",
    short_description: str = "",
    detailed_description: str = "",
    category: str = "general",
    impact: str = "",
    week: int | None = None,
    steps: list[str] | None = None,
    case_id: str | None = None
) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    data["cards"].append({
        "title": title,
        "content": content,
        "status": status,
        "short_description": short_description,
        "detailed_description": detailed_description,
        "category": category,
        "impact": impact,
        "week": week,
        "steps": steps or []
    })
    return save(data)


def update_card(
    card_id: str,
    title: str | None = None,
    content: str | None = None,
    short_description: str | None = None,
    detailed_description: str | None = None,
    category: str | None = None,
    impact: str | None = None,
    week: int | None = None,
    steps: list[str] | None = None,
    status: str | None = None,
    case_id: str | None = None
) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    card = _find(data, card_id)
    if title is not None:
        card["title"] = title
    if content is not None:
        card["content"] = content
    if short_description is not None:
        card["short_description"] = short_description
    if detailed_description is not None:
        card["detailed_description"] = detailed_description
    if category is not None:
        card["category"] = category
    if impact is not None:
        card["impact"] = impact
    if week is not None:
        card["week"] = week
    if steps is not None:
        card["steps"] = steps
    if status is not None:
        card["status"] = status
    return save(data)


def move_card(card_id: str, status: str, case_id: str | None = None) -> dict:
    """Move a card to another column; it lands at the bottom of that column."""
    if case_id:
        set_case(case_id)
    if status not in STATUSES:
        raise ValueError(f"Invalid status '{status}'. Use one of {list(STATUSES)}.")
    data = load()
    card = _find(data, card_id)
    card["status"] = status
    data["cards"].remove(card)
    data["cards"].append(card)
    return save(data)


def arrange(layout: dict[str, list[str]], case_id: str | None = None) -> dict:
    """Save a drag-and-drop result: {status: [card ids in order]}.
    Refuses if the cards in `layout` aren't exactly the cards in the file
    (e.g. the AI added or deleted one meanwhile), so a stale screen can't overwrite it."""
    if case_id:
        set_case(case_id)
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


def delete_card(card_id: str, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    data["cards"].remove(_find(data, card_id))
    return save(data)
