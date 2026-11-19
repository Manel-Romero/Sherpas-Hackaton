# Local storage for action boxes and legacy task compatibility
# Format: {"boxes": [{"title": "...", "content": "...", "category": "..."}, ...]}
import json
import os
import threading
from pathlib import Path

BASE_DATA_DIR = Path(__file__).resolve().parent / "data" / "cases"
_lock = threading.Lock()

def get_boxes_file(case_id: str = "michael-carter") -> Path:
    custom_path = os.environ.get("BOXES_JSON")
    if custom_path:
        return Path(custom_path)
    target_dir = BASE_DATA_DIR / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "boxes.json"

def clean(data: dict) -> dict:
    boxes, seen = [], set()
    for b in data.get("boxes", []):
        title = str(b.get("title", "")).strip()
        if not title:
            continue
        if title in seen:
            continue
        seen.add(title)
        
        category = str(b.get("category", "general")).strip()
        description = str(b.get("description") or b.get("content") or "").strip()
        impact = str(b.get("impact", "")).strip()
        
        raw_week = b.get("week")
        week = None
        if raw_week is not None and str(raw_week).strip():
            try:
                week = int(raw_week)
            except (ValueError, TypeError):
                week = None

        steps_raw = b.get("steps")
        if isinstance(steps_raw, list):
            steps = [str(s).strip() for s in steps_raw if str(s).strip()]
        elif isinstance(steps_raw, str) and " | " in steps_raw:
            steps = [s.strip() for s in steps_raw.split(" | ") if s.strip()]
        else:
            steps = []

        boxes.append({
            "title": title,
            "category": category,
            "description": description,
            "impact": impact,
            "week": week,
            "steps": steps,
            "content": description
        })
    return {"boxes": boxes}

def load(case_id: str = "michael-carter") -> dict:
    boxes_file = get_boxes_file(case_id)
    with _lock:
        if not boxes_file.exists():
            return {"boxes": []}
        return clean(json.loads(boxes_file.read_text(encoding="utf-8")))

def save(data: dict, case_id: str = "michael-carter") -> dict:
    boxes_file = get_boxes_file(case_id)
    data = clean(data)
    with _lock:
        tmp = boxes_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, boxes_file)
    return data

def add_box(
    title: str,
    content: str = "",
    category: str = "general",
    impact: str = "",
    week: int | None = None,
    steps: list[str] | None = None,
    case_id: str = "michael-carter"
) -> dict:
    data = load(case_id)
    data["boxes"] = [b for b in data["boxes"] if b["title"] != title]
    data["boxes"].append({
        "title": title,
        "category": category,
        "description": content,
        "content": content,
        "impact": impact,
        "week": week,
        "steps": steps or []
    })
    return save(data, case_id)

def remove_box(title: str, case_id: str = "michael-carter") -> dict:
    data = load(case_id)
    data["boxes"] = [b for b in data["boxes"] if b["title"] != title]
    return save(data, case_id)

def version(case_id: str = "michael-carter") -> int:
    boxes_file = get_boxes_file(case_id)
    return boxes_file.stat().st_mtime_ns if boxes_file.exists() else 0
