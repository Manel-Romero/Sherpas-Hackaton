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
from datetime import datetime
from pathlib import Path
import pandas as pd

BASE_DATA_DIR = Path(__file__).resolve().parent / "data" / "cases"
DATA_FILE = Path(os.environ.get("TABLE_JSON", Path(__file__).with_name("table.json")))
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_lock = threading.Lock()


def set_case(case_id: str = "michael-carter") -> Path:
    global DATA_FILE
    target_dir = BASE_DATA_DIR / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    DATA_FILE = target_dir / "table.json"
    return DATA_FILE


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
        columns = list(dict.fromkeys(columns))
    if "date" in columns:
        columns.remove("date")
    rows, seen = [], set()
    for r in data.get("rows", []):
        try:
            d = normalize_date(r.get("date", ""))
        except Exception:
            continue
        if d in seen:
            continue
        seen.add(d)
        rows.append({"date": d, **{c: to_number(r.get(c)) for c in columns}})
    rows.sort(key=lambda r: r["date"])
    return {"columns": columns, "rows": rows}


def load(case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    with _lock:
        if not DATA_FILE.exists():
            return {"columns": [], "rows": []}
        return clean(json.loads(DATA_FILE.read_text(encoding="utf-8")))


def save(data: dict, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = clean(data)
    with _lock:
        tmp = DATA_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, DATA_FILE)  # atomic: readers never see a half-written file
    return data


def version(case_id: str | None = None) -> int:
    """Changes whenever the file changes (used by the UI to detect AI edits)."""
    if case_id:
        set_case(case_id)
    return DATA_FILE.stat().st_mtime_ns if DATA_FILE.exists() else 0


def set_cell(date: str, column: str, value: float, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    d = normalize_date(date)
    if column not in data["columns"]:
        data["columns"].append(column)

    row_found = False
    for r in data["rows"]:
        if r["date"] == d:
            r[column] = to_number(value)
            row_found = True
            break

    if not row_found:
        new_row = {"date": d, **{c: 0.0 for c in data["columns"]}}
        new_row[column] = to_number(value)
        data["rows"].append(new_row)

    return save(data)


def set_cells(updates: list[dict], case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    rows = {r["date"]: r for r in data["rows"]}
    for u in updates:
        d = normalize_date(u["date"])
        col = u["column"]
        if col not in data["columns"]:
            data["columns"].append(col)
        row = rows.setdefault(d, {"date": d, **{c: 0.0 for c in data["columns"]}})
        row[col] = to_number(u["value"])
    data["rows"] = list(rows.values())
    return save(data)


def set_row(date: str, values: dict[str, float], case_id: str | None = None) -> dict:
    return set_cells([{"date": date, "column": c, "value": v} for c, v in values.items()], case_id=case_id)


def delete_row(date: str, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    d = normalize_date(date)
    data["rows"] = [r for r in data["rows"] if r["date"] != d]
    return save(data)


def add_column(name: str, default: float = 0.0, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    if name not in data["columns"]:
        data["columns"].append(name)
        for r in data["rows"]:
            if name not in r:
                r[name] = default
        return save(data)
    return data


def delete_column(name: str, case_id: str | None = None) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    if name in data["columns"]:
        data["columns"].remove(name)
        for r in data["rows"]:
            r.pop(name, None)
        return save(data)
    return data


def initialize_default_table(
    case_id: str,
    monthly_income: float,
    monthly_expenses: float,
    total_debt: float,
    net_worth: float
) -> dict:
    set_case(case_id)
    columns = ["Ingresos", "Gastos_Fijos", "Ahorro_Libre", "Deuda_Pendiente", "Patrimonio"]
    now = datetime.now()
    rows = []

    monthly_cashflow = monthly_income - monthly_expenses
    current_net_worth = net_worth
    current_debt = total_debt

    for i in range(-2, 10):  # 2 meses pasados + 10 meses de proyeccion futura
        year = now.year + (now.month + i - 1) // 12
        month = (now.month + i - 1) % 12 + 1
        date_str = f"{year:04d}-{month:02d}"

        if i < 0:
            row_income = monthly_income
            row_expenses = monthly_expenses
        else:
            row_income = monthly_income
            row_expenses = monthly_expenses
            current_net_worth += max(monthly_cashflow, 0)
            current_debt = max(0, current_debt - 250)

        rows.append({
            "date": date_str,
            "Ingresos": round(row_income, 2),
            "Gastos_Fijos": round(row_expenses, 2),
            "Ahorro_Libre": round(row_income - row_expenses, 2),
            "Deuda_Pendiente": round(current_debt, 2),
            "Patrimonio": round(current_net_worth, 2)
        })

    return save({"columns": columns, "rows": rows})


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


def next_month(date: str) -> str:
    y, m = map(int, date.split("-"))
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}"


def default_month(data: dict) -> str:
    """Month for a new row: the one after the last row, or this month if the table is empty."""
    if data.get("rows"):
        return next_month(data["rows"][-1]["date"])  # rows are always sorted
    return datetime.now().strftime("%Y-%m")


