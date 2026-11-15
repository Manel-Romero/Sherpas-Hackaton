# Almacenamiento local de la hoja de calculo financiera mensual
# Formato: {"columns": ["Ingresos", "Gastos", ...], "rows": [{"date": "2026-01", ...}]}
import json
import os
import re
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_lock = threading.Lock()

def get_table_file(case_id: str = "michael-carter") -> Path:
    # Ruta del archivo de tabla mensual aislado por caso
    custom_path = os.environ.get("TABLE_JSON")
    if custom_path:
        return Path(custom_path)
    target_dir = BASE_DATA_DIR / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "table.json"

def normalize_date(value) -> str:
    s = str(value).strip()[:7]
    if not DATE_RE.match(s):
        raise ValueError(f"Mes invalido '{value}'. Usa formato YYYY-MM (ej: 2026-03).")
    return s

def to_number(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"El valor '{value}' no es numerico.")

def clean(data: dict) -> dict:
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

def load(case_id: str = "michael-carter") -> dict:
    table_file = get_table_file(case_id)
    with _lock:
        if not table_file.exists():
            return {"columns": [], "rows": []}
        return clean(json.loads(table_file.read_text(encoding="utf-8")))

def save(data: dict, case_id: str = "michael-carter") -> dict:
    table_file = get_table_file(case_id)
    data = clean(data)
    with _lock:
        tmp = table_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, table_file)
    return data

def version(case_id: str = "michael-carter") -> int:
    table_file = get_table_file(case_id)
    return table_file.stat().st_mtime_ns if table_file.exists() else 0

def set_cell(date: str, column: str, value: float, case_id: str = "michael-carter") -> dict:
    data = load(case_id)
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
    
    return save(data, case_id)

def add_column(name: str, default: float = 0.0, case_id: str = "michael-carter") -> dict:
    data = load(case_id)
    if name not in data["columns"]:
        data["columns"].append(name)
        for r in data["rows"]:
            if name not in r:
                r[name] = default
        return save(data, case_id)
    return data

def initialize_default_table(
    case_id: str,
    monthly_income: float,
    monthly_expenses: float,
    total_debt: float,
    net_worth: float
) -> dict:
    # Genera proyeccion inicial de 12 meses para el cliente basada en sus datos reales
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
            current_debt = max(0, current_debt - 250)  # Reduccion progresiva estimada
            
        rows.append({
            "date": date_str,
            "Ingresos": round(row_income, 2),
            "Gastos_Fijos": round(row_expenses, 2),
            "Ahorro_Libre": round(row_income - row_expenses, 2),
            "Deuda_Pendiente": round(current_debt, 2),
            "Patrimonio": round(current_net_worth, 2)
        })
        
    return save({"columns": columns, "rows": rows}, case_id)

def to_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame(data.get("rows", []), columns=["date", *data.get("columns", [])])

def from_df(df: pd.DataFrame, columns: list[str]) -> dict:
    rows = []
    for rec in df.to_dict("records"):
        if rec.get("date") is None or str(rec["date"]).strip() in ("", "nan", "None"):
            continue
        rows.append(rec)
    return clean({"columns": columns, "rows": rows})

def next_month(date: str) -> str:
    y, m = map(int, date.split("-"))
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}"

def default_month(data: dict) -> str:
    if data.get("rows"):
        return next_month(data["rows"][-1]["date"])
    return datetime.now().strftime("%Y-%m")

