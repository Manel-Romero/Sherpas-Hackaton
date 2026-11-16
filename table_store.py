"""Shared storage layer: both the Streamlit app and the MCP server use this.

JSON format:
{
  "columns": ["Revenue", "Costs"],
  "rows": [{"date": "2026-01", "Revenue": 100, "Costs": 50}, ...]
}
Dates are monthly strings ("YYYY-MM"); every other value is a number.
"""
import json
import os
import re
import threading
from pathlib import Path
import pandas as pd

DATA_FILE = Path(os.environ.get("TABLE_JSON", Path(__file__).with_name("table.json")))
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_lock = threading.Lock()


def normalize_date(value) -> str:
    """Accept '2026-03' or '2026-03-15' and return '2026-03'."""
    s = str(value).strip()[:7]
    if not DATE_RE.match(s):
        raise ValueError(f"Invalid month '{value}'. Use YYYY-MM, e.g. 2026-03.")
    return s


def to_number(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Value '{value}' is not numeric.")


def clean(data: dict) -> dict:
    """Validate, enforce numeric cells, unique + sorted dates."""
    columns = list(data.get("columns", []))
    if len(set(columns)) != len(columns):
        raise ValueError("Duplicate column names.")
    if "date" in columns:
        raise ValueError("'date' is reserved for the first column.")
    rows, seen = [], set()
    for r in data.get("rows", []):
        d = normalize_date(r["date"])
        if d in seen:
            raise ValueError(f"Duplicate month {d}.")
        seen.add(d)
        rows.append({"date": d, **{c: to_number(r.get(c)) for c in columns}})
    rows.sort(key=lambda r: r["date"])
    return {"columns": columns, "rows": rows}


def load() -> dict:
    with _lock:
        if not DATA_FILE.exists():
            return {"columns": [], "rows": []}
        return clean(json.loads(DATA_FILE.read_text(encoding="utf-8")))


def save(data: dict) -> dict:
    data = clean(data)
    with _lock:
        tmp = DATA_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, DATA_FILE)  # atomic: readers never see a half-written file
    return data


def version() -> int:
    """Changes whenever the file changes (used by the UI to detect AI edits)."""
    return DATA_FILE.stat().st_mtime_ns if DATA_FILE.exists() else 0


# ---------- DataFrame helpers for the UI ----------
def to_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame(data["rows"], columns=["date", *data["columns"]])


def from_df(df: pd.DataFrame, columns: list[str]) -> dict:
    rows = []
    for rec in df.to_dict("records"):
        if rec.get("date") is None or str(rec["date"]).strip() in ("", "nan", "None"):
            continue  # blank row the user hasn't filled in yet
        rows.append(rec)
    return clean({"columns": columns, "rows": rows})

from datetime import datetime

def next_month(date: str) -> str:
    y, m = map(int, date.split("-"))
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}"

def default_month(data: dict) -> str:
    """Month for a new row: the one after the last row, or this month if the table is empty."""
    if data["rows"]:
        return next_month(data["rows"][-1]["date"])   # rows are always sorted
    return datetime.now().strftime("%Y-%m")

