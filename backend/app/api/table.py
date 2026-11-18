"""API endpoints for interactive financial projection spreadsheet.
"""
from typing import Optional, Any, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import table_store as ts

router = APIRouter(prefix="/cases/{case_id}/table", tags=["Projection Table"])


class SetCellRequest(BaseModel):
    date: str
    column: str
    value: Union[float, int, str]


class AddColumnRequest(BaseModel):
    name: str
    default_value: float = 0.0


class SetFormulaRequest(BaseModel):
    column: str
    formula: str


@router.get("")
def get_table(case_id: str):
    """Devuelve las columnas y filas de la proyeccion financiera mensual."""
    try:
        ts.set_case(case_id)
        data = ts.load(case_id)
        if not data.get("rows"):
            data = ts.initialize_default_table(
                case_id=case_id,
                monthly_income=15000.0,
                monthly_expenses=9306.0,
                total_debt=28500.0,
                net_worth=218500.0
            )
        return {
            "case_id": case_id,
            "version": ts.version(case_id),
            "columns": data.get("columns", []),
            "rows": data.get("rows", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando tabla: {str(e)}")


@router.post("/cell")
def update_cell(case_id: str, req: SetCellRequest):
    """Actualiza el valor o formula de una celda en la tabla."""
    try:
        ts.set_case(case_id)
        if isinstance(req.value, str) and req.value.startswith("="):
            res = ts.set_cell_formula(req.date, req.column, req.value, case_id=case_id)
        else:
            try:
                num_val = float(req.value)
            except (ValueError, TypeError):
                num_val = 0.0
            res = ts.set_cell(req.date, req.column, num_val, case_id=case_id)

        # Recalcular proyecciones automaticas sobre los datos cargados
        current_data = ts.load(case_id)
        recalculated = ts.recalculate_projections(current_data)
        ts.save(recalculated, case_id=case_id)

        updated_data = ts.load(case_id)
        return {
            "success": True,
            "updated": res,
            "version": ts.version(case_id),
            "rows": updated_data.get("rows", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando celda: {str(e)}")


@router.post("/column")
def add_column(case_id: str, req: AddColumnRequest):
    """Anade una nueva columna a la hoja de calculo."""
    try:
        ts.set_case(case_id)
        res = ts.add_column(req.name.strip(), default=req.default_value, case_id=case_id)
        updated_data = ts.load(case_id)
        return {
            "success": True,
            "columns": updated_data.get("columns", []),
            "version": ts.version(case_id)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error anadiendo columna: {str(e)}")


@router.post("/next-month")
def add_next_month(case_id: str):
    """Anade una nueva fila proyectada para el siguiente mes consecutivo."""
    try:
        ts.set_case(case_id)
        data = ts.load(case_id)
        rows = data.get("rows", [])
        if not rows:
            raise HTTPException(status_code=400, detail="No hay filas previas en la tabla")

        last_row = rows[-1]
        next_m = ts.default_month(data)

        # Copiar valores base del ultimo mes proyectado
        new_row_vals = {k: v for k, v in last_row.items() if k != "date"}
        ts.set_row(next_m, new_row_vals, case_id=case_id)

        current_data = ts.load(case_id)
        recalculated = ts.recalculate_projections(current_data)
        ts.save(recalculated, case_id=case_id)

        updated_data = ts.load(case_id)
        return {
            "success": True,
            "new_month": next_m,
            "version": ts.version(case_id),
            "rows": updated_data.get("rows", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error anadiendo siguiente mes: {str(e)}")


@router.delete("/column/{col_name}")
def delete_column(case_id: str, col_name: str):
    """Elimina una columna de la hoja de calculo."""
    try:
        ts.set_case(case_id)
        res = ts.delete_column(col_name, case_id=case_id)
        updated_data = ts.load(case_id)
        return {
            "success": True,
            "columns": updated_data.get("columns", []),
            "version": ts.version(case_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando columna: {str(e)}")


@router.get("/summary")
def get_table_summary(case_id: str):
    """Calcula metricas agregadas y KPIs para el dashboard."""
    try:
        ts.set_case(case_id)
        data = ts.load(case_id)
        rows = data.get("rows", [])
        if not rows:
            return {
                "active_month": "N/A",
                "net_worth": 0.0,
                "monthly_income": 0.0,
                "monthly_expenses": 0.0,
                "free_cash_flow": 0.0,
                "debt_balance": 0.0
            }

        first_row = rows[0]
        income = float(first_row.get("Ingresos", 0.0))
        expenses = float(first_row.get("Gastos_Fijos", 0.0)) + float(first_row.get("Gastos_Variables", 0.0))
        debt = float(first_row.get("Deuda_Pendiente", 0.0))
        net_worth = float(first_row.get("Patrimonio", 0.0))
        free_cf = income - expenses

        return {
            "active_month": first_row.get("date", "N/A"),
            "net_worth": net_worth,
            "monthly_income": income,
            "monthly_expenses": expenses,
            "free_cash_flow": free_cf,
            "debt_balance": debt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")
