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
import math
import threading
from datetime import datetime
from pathlib import Path
import pandas as pd
import project_paths

BASE_DATA_DIR = project_paths.DATA_CASES_DIR
DATA_FILE = Path(os.environ.get("TABLE_JSON", Path(__file__).with_name("table.json")))
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_lock = threading.Lock()

SAFE_FUNCTIONS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "pow": pow,
    "sum": sum,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
}


def evaluate_formula(formula: str, context: dict) -> float:
    """Evalua una formula matematica o expresion estilo Excel de forma segura."""
    cleaned = formula.strip()
    if cleaned.startswith("="):
        cleaned = cleaned[1:].strip()

    scope = {"__builtins__": None, **SAFE_FUNCTIONS, **context}
    try:
        res = eval(cleaned, scope)
        return float(res)
    except Exception as e:
        raise ValueError(f"Error evaluando formula '{formula}': {str(e)}")


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


def recalculate_projections(data: dict) -> dict:
    """Recalcula dinamicamente Ahorro_Libre y Patrimonio a partir de Ingresos y Gastos_Fijos."""
    columns = list(data.get("columns", []))
    rows = data.get("rows", [])
    if not rows:
        return data

    has_inc = "Ingresos" in columns
    has_exp = "Gastos_Fijos" in columns

    if has_inc and has_exp:
        if "Ahorro_Libre" not in columns:
            columns.append("Ahorro_Libre")

        has_nw = "Patrimonio" in columns
        base_nw = to_number(rows[0].get("Patrimonio", 0.0)) if has_nw else 0.0

        for idx, r in enumerate(rows):
            inc = to_number(r.get("Ingresos", 0.0))
            exp = to_number(r.get("Gastos_Fijos", 0.0))
            free_savings = round(inc - exp, 2)
            r["Ahorro_Libre"] = free_savings

            if has_nw:
                if idx == 0:
                    base_nw = to_number(r.get("Patrimonio", base_nw))
                else:
                    base_nw = round(base_nw + max(0.0, free_savings), 2)
                    r["Patrimonio"] = base_nw

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
    data = recalculate_projections(clean(data))
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


def add_column(
    name: str,
    default: float = 0.0,
    formula: str | None = None,
    case_id: str | None = None
) -> dict:
    if case_id:
        set_case(case_id)
    data = load()
    if name not in data["columns"]:
        data["columns"].append(name)
        for r in data["rows"]:
            if name not in r:
                r[name] = default
        data = save(data)
    if formula:
        return apply_column_formula(name, formula, case_id=case_id)
    return data


def apply_column_formula(
    column: str,
    formula: str,
    start_date: str | None = None,
    initial_value: float | None = None,
    case_id: str | None = None
) -> dict:
    """Aplica una formula estilo Excel a una columna a lo largo de las filas mensuales.

    Variables en cada fila:
      - Nombres de columnas existentes (ej: Ingresos, Gastos_Fijos, etc.)
      - prev: valor de la celda en la fila anterior (o initial_value para la primera fila)
      - t: paso temporal relativo (0, 1, 2, ...) desde start_date
      - row_index: indice absoluto de la fila
      - date: mes YYYY-MM
      - value: valor actual de la celda
      - Funciones matematicas: min, max, round, abs, pow, sum, sqrt
    """
    if case_id:
        set_case(case_id)
    data = load()
    if column not in data["columns"]:
        data["columns"].append(column)

    rows = data.get("rows", [])
    if not rows:
        return data

    start_idx = 0
    if start_date:
        if str(start_date).lower().strip() in ("current", "now", "presente"):
            now_m = datetime.now().strftime("%Y-%m")
            for i, r in enumerate(rows):
                if r.get("date") == now_m:
                    start_idx = i
                    break
        else:
            norm_sd = normalize_date(start_date)
            for i, r in enumerate(rows):
                if r.get("date") == norm_sd:
                    start_idx = i
                    break

    prev_val = 0.0
    if initial_value is not None:
        prev_val = float(initial_value)
    elif start_idx > 0 and column in rows[start_idx - 1]:
        prev_val = to_number(rows[start_idx - 1][column])
    elif column in rows[start_idx]:
        prev_val = to_number(rows[start_idx][column])

    for i in range(start_idx, len(rows)):
        r = rows[i]
        t_step = i - start_idx
        current_cell_val = to_number(r.get(column, 0.0))

        ctx = {
            "prev": prev_val,
            "t": t_step,
            "row_index": i,
            "date": r.get("date", ""),
            "value": current_cell_val,
        }
        for c in data["columns"]:
            c_val = to_number(r.get(c, 0.0))
            ctx[c] = c_val
            ctx[c.lower()] = c_val
            clean_col = re.sub(r"[^a-zA-Z0-9_]", "_", c.strip())
            ctx[clean_col] = c_val
            ctx[clean_col.lower()] = c_val

        eval_res = evaluate_formula(formula, ctx)
        new_val = round(eval_res, 2)
        r[column] = new_val
        prev_val = new_val

    return save(data)


def set_cell_formula(date: str, column: str, formula: str, case_id: str | None = None) -> dict:
    """Evalua y asigna una formula a una celda especifica (date, column)."""
    if case_id:
        set_case(case_id)
    data = load()
    d = normalize_date(date)
    if column not in data["columns"]:
        data["columns"].append(column)

    row_target = None
    target_idx = 0
    for idx, r in enumerate(data["rows"]):
        if r["date"] == d:
            row_target = r
            target_idx = idx
            break

    if row_target is None:
        row_target = {"date": d, **{c: 0.0 for c in data["columns"]}}
        data["rows"].append(row_target)
        data["rows"].sort(key=lambda x: x["date"])
        target_idx = data["rows"].index(row_target)

    prev_val = 0.0
    if target_idx > 0:
        prev_row = data["rows"][target_idx - 1]
        prev_val = to_number(prev_row.get(column, 0.0))

    ctx = {
        "prev": prev_val,
        "t": 0,
        "row_index": target_idx,
        "date": d,
        "value": to_number(row_target.get(column, 0.0)),
    }
    for c in data["columns"]:
        c_val = to_number(row_target.get(c, 0.0))
        ctx[c] = c_val
        ctx[c.lower()] = c_val
        clean_col = re.sub(r"[^a-zA-Z0-9_]", "_", c.strip())
        ctx[clean_col] = c_val
        ctx[clean_col.lower()] = c_val

    new_val = round(evaluate_formula(formula, ctx), 2)
    row_target[column] = new_val
    return save(data)


def spreadsheet_aggregate(
    column: str,
    operation: str = "sum",
    start_date: str | None = None,
    end_date: str | None = None,
    case_id: str | None = None
) -> float:
    """Calcula agregaciones estilo Excel (sum, average, min, max, growth_rate) sobre una columna."""
    if case_id:
        set_case(case_id)
    data = load()
    if column not in data.get("columns", []):
        raise ValueError(f"Columna '{column}' no encontrada en la tabla.")

    rows = data.get("rows", [])
    if start_date:
        sd = normalize_date(start_date)
        rows = [r for r in rows if r.get("date", "") >= sd]
    if end_date:
        ed = normalize_date(end_date)
        rows = [r for r in rows if r.get("date", "") <= ed]

    values = [to_number(r.get(column, 0.0)) for r in rows]
    if not values:
        return 0.0

    op = operation.lower().strip()
    if op in ("sum", "suma", "total"):
        return round(sum(values), 2)
    elif op in ("average", "avg", "mean", "promedio"):
        return round(sum(values) / len(values), 2)
    elif op in ("min", "minimo"):
        return round(min(values), 2)
    elif op in ("max", "maximo"):
        return round(max(values), 2)
    elif op in ("growth_rate", "crecimiento"):
        if values[0] != 0:
            return round(((values[-1] - values[0]) / abs(values[0])) * 100.0, 2)
        return 0.0
    else:
        raise ValueError(f"Operacion desconocida: {operation}. Usa sum, average, min, max o growth_rate.")


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


