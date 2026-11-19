import json
from datetime import datetime
from typing import Literal, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from backend.app.services.session_store import session_store, SessionData
from backend.app.services.case_repository import case_repo
from backend.app.models.plan import TaskItem, TaskImpact

def _get_session_from_config(config: RunnableConfig) -> SessionData:
    # Extrae de forma segura la sesion actual a partir de la configuracion de ejecucion inyectada
    configurable = config.get("configurable", {}) if config else {}
    session_id = configurable.get("session_id", "default")
    case_id = configurable.get("case_id", "michael-carter")
    return session_store.get_or_create(session_id, case_id)

@tool
def manage_task(
    action: Literal["add", "complete", "delete"],
    task_id: str = "",
    title: str = "",
    description: str = "",
    short_description: str = "",
    detailed_description: str = "",
    category: Literal["debt", "savings", "investment", "insurance", "lifestyle", "immediate", "goal", "general"] = "savings",
    week: int = 1,
    impact_metric: str = "Ahorro",
    impact_value: str = "",
    steps: Optional[list[str]] = None,
    config: RunnableConfig = None
) -> str:
    """Gestiona la lista de tareas y tarjetas del tablero Kanban del usuario (anadir, completar o eliminar una accion)."""
    session = _get_session_from_config(config)
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    
    if action == "add":
        new_task = TaskItem(
            id=task_id or f"task_{len(session.tasks) + 1}",
            title=title or "Nueva tarea recomendada",
            short_description=short_description or (description[:120] if len(description) > 120 else description),
            detailed_description=detailed_description or description,
            description=description,
            week=week,
            category=category,
            status="pending",
            impact=TaskImpact(metric=impact_metric, value=impact_value) if impact_value else None,
            steps=steps or []
        )
        session.add_task(new_task)
        # Sincronizar en el tablero Kanban en disco
        try:
            import kanban_store as ks
            ks.set_case(case_id)
            desc_val = detailed_description or description
            s_desc_val = short_description or (desc_val[:120] if len(desc_val) > 120 else desc_val)
            ks.add_card(
                title=title or "Nueva tarea recomendada",
                content=desc_val,
                status="todo",
                short_description=s_desc_val,
                detailed_description=desc_val,
                category=category,
                impact=impact_value,
                week=week,
                steps=steps or [],
                case_id=case_id
            )
        except Exception:
            pass
        return f"Tarea '{new_task.title}' anadida correctamente al roadmap y tablero Kanban (Semana {week})."

    elif action == "complete":
        success_session = session.update_task_status(task_id, "completed")
        success_kanban = False
        try:
            import kanban_store as ks
            ks.set_case(case_id)
            kb_data = ks.load(case_id)
            target_id = None
            for c in kb_data.get("cards", []):
                cid = c.get("id", "")
                ctitle = c.get("title", "")
                if cid == task_id or (task_id and task_id.lower() in ctitle.lower()) or (title and title.lower() in ctitle.lower()):
                    target_id = cid
                    break
            if target_id:
                ks.move_card(target_id, "done", case_id=case_id)
                success_kanban = True
        except Exception:
            pass

        if success_session or success_kanban:
            return f"Tarea '{task_id or title}' marcada como completada ('done') en el roadmap y tablero Kanban."
        return f"No se encontro la tarea '{task_id}' para marcarla como completada."

    elif action == "delete":
        success_session = session.remove_task(task_id)
        success_kanban = False
        try:
            import kanban_store as ks
            ks.set_case(case_id)
            kb_data = ks.load(case_id)
            for c in kb_data.get("cards", []):
                cid = c.get("id", "")
                ctitle = c.get("title", "")
                if cid == task_id or (task_id and task_id.lower() in ctitle.lower()) or (title and title.lower() in ctitle.lower()):
                    ks.delete_card(cid, case_id=case_id)
                    success_kanban = True
                    break
        except Exception:
            pass

        if success_session or success_kanban:
            return f"Tarea '{task_id}' eliminada del roadmap y tablero Kanban."
        return f"No se encontro la tarea '{task_id}' para eliminar."

    return f"Accion '{action}' no reconocida."

@tool
def update_dashboard_metric(
    key: str,
    value: float,
    reason: str = "",
    config: RunnableConfig = None
) -> str:
    """Actualiza una metrica o celda clave del dashboard financiero (ej: monthly_income / ingreso_mensual, monthly_expenses / gastos, net_worth / patrimonio_neto, etc.)."""
    session = _get_session_from_config(config)
    success = session.update_dashboard_metric(key, value, reason)
    if success:
        configurable = config.get("configurable", {}) if config else {}
        case_id = configurable.get("case_id", "michael-carter")
        norm_key = session._normalize_metric_key(key)
        # Sincronizar tambien con la tabla de proyeccion si es ingreso o gasto
        if norm_key in ("monthly_income", "monthly_expenses"):
            try:
                import table_store as ts
                data = ts.load(case_id=case_id)
                col_name = "Ingresos" if norm_key == "monthly_income" else "Gastos_Fijos"
                if col_name in data.get("columns", []):
                    for r in data.get("rows", []):
                        r[col_name] = float(value)
                        if "Ingresos" in r and "Gastos_Fijos" in r:
                            r["Ahorro_Libre"] = round(r["Ingresos"] - r["Gastos_Fijos"], 2)
                    ts.save(data, case_id=case_id)
            except Exception:
                pass
        return f"Metrica '{key}' actualizada a {value} con exito en el dashboard."
    return f"No se pudo actualizar la metrica '{key}'."

@tool
def display_chart(
    chart_type: Literal["bar", "line", "donut"],
    title: str,
    categories: Optional[list[str]] = None,
    values: Optional[list[float]] = None,
    labels: Optional[list[str]] = None,
    config: RunnableConfig = None  # Inyectado automaticamente por LangChain en tiempo de ejecucion
) -> str:
    """Solicita a la interfaz mostrar un grafico interactivo (barras, lineas o donut) con proyecciones o desgloses.
    
    Args:
        chart_type: 'bar', 'line' o 'donut'
        title: Titulo descriptivo del grafico
        categories: Lista de categorias o etiquetas (ej: ['Gastos Esenciales', 'Alquiler', 'Deudas'])
        values: Lista de valores numericos correspondientes (ej: [5500, 2800, 950])
        labels: Alias alternativo de categories
    """
    session = _get_session_from_config(config)
    cat_list = categories if categories is not None else (labels if labels is not None else [])
    val_list = values if values is not None else []
    chart_payload = {
        "type": chart_type,
        "title": title,
        "labels": cat_list,
        "categories": cat_list,
        "values": val_list
    }
    session.pending_charts.append(chart_payload)
    return f"Grafico '{title}' ({chart_type}) enviado para visualizacion en el frontend."

@tool
async def inspect_case_data(
    part: Literal["financial-health", "investment-analysis", "persona"],
    section: str = "",
    config: RunnableConfig = None  # Inyectado automaticamente por LangChain en tiempo de ejecucion
) -> str:
    """Consulta en profundidad secciones detalladas del caso a traves del servidor MCP sin saturar el contexto general."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")

    try:
        data = await case_repo.get_case_section(case_id, part, section if section else None)
        if isinstance(data, str):
            return data[:3000]
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        return formatted[:3000]
    except Exception as e:
        return f"Error consultando datos de {part} / {section} en servidor MCP: {str(e)}"

@tool
def get_table(
    config: RunnableConfig = None
) -> str:
    """Devuelve la tabla mensual completa con sus columnas y filas actuales (formato JSON)."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        data = ts.load(case_id=case_id)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error leyendo tabla mensual: {str(e)}"

@tool
def modify_table_cell(
    date: str,
    column: str,
    value: float,
    config: RunnableConfig = None
) -> str:
    """Modifica o introduce un valor numerico en una celda de la hoja de calculo mensual.
    
    IMPORTANTE SOBRE COLUMNAS:
    - 'Gastos_Fijos': Gastos mensuales de vida y cuotas (ej: 9306). Si sube un gasto o cuota, modificalo aqui.
    - 'Deuda_Pendiente': SALDO TOTAL VIVO acumulado de deuda (ej: 28500), NO es una cuota mensual. Si el cliente amortiza 400$, la deuda baja a 28100$.
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        # Salvaguarda: si se confunde cuota mensual con saldo total de deuda
        if column == "Deuda_Pendiente" and 0 < value < 2000:
            cur = ts.load(case_id=case_id)
            for r in cur.get("rows", []):
                if r.get("date") == date and float(r.get("Deuda_Pendiente", 0)) > 10000:
                    old_debt = float(r["Deuda_Pendiente"])
                    value = max(0.0, round(old_debt - value, 2))
                    break
        ts.set_cell(date, column, value, case_id=case_id)
        return f"Celda ({date}, {column}) actualizada a {value} en la tabla mensual del cliente."
    except Exception as e:
        return f"Error al modificar celda: {str(e)}"

@tool
def set_cell(
    date: str,
    column: str,
    value: float,
    config: RunnableConfig = None
) -> str:
    """Establece el valor numerico de una celda en la tabla mensual (fecha YYYY-MM, columna, valor).
    
    IMPORTANTE SOBRE COLUMNAS:
    - 'Gastos_Fijos': Gastos mensuales de vida y cuotas (ej: 9306).
    - 'Deuda_Pendiente': SALDO TOTAL VIVO acumulado de deuda (ej: 28500), NO es una cuota mensual.
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        # Salvaguarda: si se confunde cuota mensual con saldo total de deuda
        if column == "Deuda_Pendiente" and 0 < value < 2000:
            cur = ts.load(case_id=case_id)
            for r in cur.get("rows", []):
                if r.get("date") == date and float(r.get("Deuda_Pendiente", 0)) > 10000:
                    old_debt = float(r["Deuda_Pendiente"])
                    value = max(0.0, round(old_debt - value, 2))
                    break
        ts.set_cell(date, column, value, case_id=case_id)
        return f"Celda ({date}, {column}) actualizada a {value} en la tabla mensual del cliente."
    except Exception as e:
        return f"Error al modificar celda: {str(e)}"

@tool
def set_cells(
    updates: list[dict],
    config: RunnableConfig = None
) -> str:
    """Modifica multiples celdas de la tabla a la vez. Cada actualizacion: {'date': 'YYYY-MM', 'column': str, 'value': float}."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        ts.set_cells(updates, case_id=case_id)
        return f"{len(updates)} celdas actualizadas con exito en la tabla mensual."
    except Exception as e:
        return f"Error actualizando celdas: {str(e)}"

@tool
def set_row(
    date: str,
    values: dict[str, float],
    config: RunnableConfig = None
) -> str:
    """Crea o actualiza una fila mensual completa con un diccionario de columna -> valor."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        ts.set_row(date, values, case_id=case_id)
        return f"Fila del mes {date} actualizada con exito en la tabla mensual."
    except Exception as e:
        return f"Error actualizando fila: {str(e)}"

@tool
def delete_row(
    date: str,
    config: RunnableConfig = None
) -> str:
    """Elimina una fila mensual completa de la tabla por su fecha (YYYY-MM)."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        ts.delete_row(date, case_id=case_id)
        return f"Fila del mes {date} eliminada de la tabla mensual."
    except Exception as e:
        return f"Error eliminando fila: {str(e)}"

@tool
def set_cell_formula(
    date: str,
    column: str,
    formula: str,
    config: RunnableConfig = None
) -> str:
    """Evalua y asigna una formula o funcion estilo Excel a una celda especifica (ej: formula='prev * 1.10', 'Ingresos * 0.20', '15000 + 2000')."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        data = ts.set_cell_formula(date, column, formula, case_id=case_id)
        res_val = 0.0
        for r in data.get("rows", []):
            if r.get("date") == ts.normalize_date(date):
                res_val = r.get(column, 0.0)
                break
        return f"Celda ({date}, {column}) calculada con formula '{formula}' -> {res_val} con exito."
    except Exception as e:
        return f"Error evaluando celda con formula: {str(e)}"

@tool
def apply_column_formula(
    column: str,
    formula: str,
    start_date: Optional[str] = None,
    initial_value: Optional[float] = None,
    config: RunnableConfig = None
) -> str:
    """Aplica una formula o funcion estilo Excel a una columna a traves de los meses (ej: formula='prev * 1.10' para interes compuesto, 'Ingresos - Gastos_Fijos' para balance, 'Ingresos * 0.15' para ahorro, 'max(0, prev - 500)' para amortizacion).

    Variables disponibles en la formula:
      - Nombres de columnas de la fila (ej: Ingresos, Gastos_Fijos, etc.)
      - prev: valor de la celda en la fila anterior (o initial_value)
      - t: paso temporal (0, 1, 2, ...) desde el inicio
      - row_index: indice absoluto de la fila
      - date: fecha YYYY-MM
      - value: valor actual de la celda
      - Funciones matematicas: min, max, round, abs, pow, sum, sqrt
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    session = _get_session_from_config(config)

    try:
        import table_store as ts
        tb_data = ts.apply_column_formula(
            column=column,
            formula=formula,
            start_date=start_date,
            initial_value=initial_value,
            case_id=case_id
        )
        rows = tb_data.get("rows", [])

        norm_col = session._normalize_metric_key(column)
        if norm_col in ("monthly_income", "monthly_expenses") and rows:
            start_idx = 0
            if start_date:
                norm_sd = ts.normalize_date(start_date)
                for i, r in enumerate(rows):
                    if r.get("date") == norm_sd:
                        start_idx = i
                        break
            else:
                now_m = datetime.now().strftime("%Y-%m")
                for i, r in enumerate(rows):
                    if r.get("date") == now_m:
                        start_idx = i
                        break
            first_val = float(rows[start_idx].get(column, 0.0))
            session.update_dashboard_metric(norm_col, first_val, reason=f"Formula en columna {column}: {formula}")

        chart_cats = [r["date"] for r in rows if column in r]
        chart_vals = [float(r[column]) for r in rows if column in r]
        session.pending_charts.append({
            "type": "line",
            "title": f"Proyeccion de {column} (Formula: {formula})",
            "labels": chart_cats,
            "categories": chart_cats,
            "values": chart_vals
        })

        preview = [f"{r['date']}: ${float(r[column]):,.2f}" for r in rows[:4] if column in r]
        return f"Formula '{formula}' aplicada a columna '{column}' en {len(rows)} meses. Primeros meses: {', '.join(preview)}..."
    except Exception as e:
        return f"Error aplicando formula en columna: {str(e)}"

@tool
def register_loan_and_amortization(
    debt_name: str,
    principal: float,
    start_date: str,
    target_payoff_date: str,
    monthly_payment: Optional[float] = None,
    config: RunnableConfig = None
) -> str:
    """Registra y planifica la amortizacion de un prestamo o deuda en el dashboard y tabla mensual.
    
    Inicia la deuda exactamente en el mes especificado (sin alterar meses pasados),
    calcula la cuota fija mensual requerida para extinguirla, reduce la deuda mes a mes
    hasta dejarla a cero en la fecha objetivo, y actualiza las metricas y graficos correspondientes.
    
    Args:
        debt_name: Nombre o concepto del prestamo o deuda (ej: 'Prestamo Imprevisto').
        principal: Importe total del prestamo o deuda (ej: 20000.0).
        start_date: Mes de inicio en formato YYYY-MM (ej: '2026-11'). Meses anteriores no se tocan.
        target_payoff_date: Mes objetivo para que la deuda llegue a 0 en formato YYYY-MM (ej: '2027-03').
        monthly_payment: Opcional. Cuota fija mensual. Si no se pasa, se calcula dividiendo el principal entre los meses hasta el objetivo.
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    session = _get_session_from_config(config)

    try:
        import table_store as ts
        data = ts.load(case_id=case_id)
        rows = data.get("rows", [])
        if not rows:
            return "Error: la tabla mensual no tiene filas disponibles."

        norm_start = ts.normalize_date(start_date)
        norm_target = ts.normalize_date(target_payoff_date)

        sy, sm = int(norm_start.split("-")[0]), int(norm_start.split("-")[1])
        ty, tm = int(norm_target.split("-")[0]), int(norm_target.split("-")[1])
        num_months = (ty - sy) * 12 + (tm - sm) + 1
        if num_months <= 0:
            return f"Error: la fecha objetivo ({target_payoff_date}) debe ser posterior o igual a la de inicio ({start_date})."

        quota = float(monthly_payment) if (monthly_payment and monthly_payment > 0) else round(float(principal) / num_months, 2)

        existing_dates = [r.get("date") for r in rows]
        last_date = existing_dates[-1] if existing_dates else norm_start
        ly, lm = int(last_date.split("-")[0]), int(last_date.split("-")[1])
        while (ly < ty) or (ly == ty and lm < tm):
            lm += 1
            if lm > 12:
                lm = 1
                ly += 1
            ts.add_next_month(case_id=case_id)
            data = ts.load(case_id=case_id)
            rows = data.get("rows", [])

        rem = float(principal)
        chart_labels = []
        chart_values = []

        for r in rows:
            d = r.get("date")
            chart_labels.append(d)
            if d < norm_start:
                chart_values.append(float(r.get("Deuda_Pendiente", 0.0)))
            elif d <= norm_target:
                rem = max(0.0, round(rem - quota, 2))
                if d == norm_target:
                    rem = 0.0
                r["Deuda_Pendiente"] = rem
                chart_values.append(rem)
            else:
                r["Deuda_Pendiente"] = 0.0
                chart_values.append(0.0)

        ts.save(data, case_id=case_id)
        session.update_dashboard_metric("debt_balance", float(principal), reason=f"Inicio prestamo {debt_name}")

        session.pending_charts.append({
            "type": "line",
            "title": f"Amortizacion {debt_name}: Cuota ${quota:,.2f}/mes hasta {norm_target}",
            "labels": chart_labels,
            "categories": chart_labels,
            "values": chart_values
        })

        return (
            f"Prestamo '{debt_name}' de ${principal:,.2f} registrado con exito.\n"
            f"- Periodo: {norm_start} a {norm_target} ({num_months} meses)\n"
            f"- Cuota fija de amortizacion: ${quota:,.2f}/mes\n"
            f"- Saldo extinguido a $0.00 en {norm_target}\n"
            f"- Meses anteriores a {norm_start} conservados intactos sin deuda ficticia."
        )
    except Exception as e:
        return f"Error registrando prestamo y amortizacion: {str(e)}"

@tool
def evaluate_formula(
    expression: str,
    variables: Optional[dict[str, float]] = None,
    config: RunnableConfig = None
) -> str:
    """Calcula y evalua cualquier formula o expresion matematica/financiera estilo Excel (ej: '15000 * (1.10 ** 12)', 'PV * (1 + 0.07)**10', etc.)."""
    try:
        import table_store as ts
        ctx = dict(variables or {})
        result = ts.evaluate_formula(expression, ctx)
        return f"Resultado de '{expression}': {result:,.2f}"
    except Exception as e:
        return f"Error calculando expresion '{expression}': {str(e)}"

@tool
def spreadsheet_aggregate(
    column: str,
    operation: Literal["sum", "average", "min", "max", "growth_rate"] = "sum",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """Calcula operaciones de agregacion estilo Excel (sum, average, min, max, growth_rate) sobre una columna de la tabla mensual."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        res = ts.spreadsheet_aggregate(column, operation, start_date, end_date, case_id=case_id)
        return f"Agregacion {operation.upper()} en columna '{column}': {res:,.2f}"
    except Exception as e:
        return f"Error calculando agregacion: {str(e)}"

@tool
def add_table_column(
    name: str,
    default: float = 0.0,
    formula: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """Anade una nueva columna a la hoja de calculo mensual (ej: 'Fondo_Herencia', 'Amortizacion_Extra', 'Ahorro_Vacaciones'). Si se proporciona formula, calcula los valores en toda la tabla."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        ts.add_column(name, default, formula=formula, case_id=case_id)
        if formula:
            return f"Columna '{name}' anadida y calculada con formula '{formula}' en la tabla mensual."
        return f"Columna '{name}' anadida con exito a la tabla mensual."
    except Exception as e:
        return f"Error anadiendo columna: {str(e)}"

@tool
def add_column(
    name: str,
    default: float = 0.0,
    formula: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """Anade una nueva columna numerica a la tabla mensual con valor por defecto o formula estilo Excel (alias de add_table_column)."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        ts.add_column(name, default, formula=formula, case_id=case_id)
        if formula:
            return f"Columna '{name}' anadida y calculada con formula '{formula}' en la tabla mensual."
        return f"Columna '{name}' anadida con exito a la tabla mensual."
    except Exception as e:
        return f"Error anadiendo columna: {str(e)}"

@tool
def delete_column(
    name: str,
    config: RunnableConfig = None
) -> str:
    """Elimina una columna de la tabla mensual."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import table_store as ts
        ts.delete_column(name, case_id=case_id)
        return f"Columna '{name}' eliminada de la tabla mensual."
    except Exception as e:
        return f"Error eliminando columna: {str(e)}"

@tool
def add_kanban_card(
    title: str,
    content: str = "",
    status: Literal["todo", "in_process", "done"] = "todo",
    short_description: str = "",
    detailed_description: str = "",
    category: Literal["debt", "savings", "investment", "insurance", "lifestyle", "immediate", "goal", "general"] = "general",
    impact: str = "",
    week: Optional[int] = None,
    steps: Optional[list[str]] = None,
    config: RunnableConfig = None
) -> str:
    """Anade una nueva tarjeta estructurada directamente al tablero Kanban ('todo', 'in_process' o 'done')."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import kanban_store as ks
        ks.set_case(case_id)
        ks.add_card(
            title=title,
            content=content or detailed_description or short_description,
            status=status,
            short_description=short_description,
            detailed_description=detailed_description or content,
            category=category,
            impact=impact,
            week=week,
            steps=steps or [],
            case_id=case_id
        )
        return f"Tarjeta '{title}' anadida a la columna '{status}' en el tablero Kanban."
    except Exception as e:
        return f"Error anadiendo tarjeta al tablero Kanban: {str(e)}"

@tool
def delete_kanban_card(
    card_title_or_id: str,
    config: RunnableConfig = None
) -> str:
    """Elimina una tarjeta del tablero Kanban por su ID o parte de su titulo."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import kanban_store as ks
        ks.set_case(case_id)
        data = ks.load(case_id)
        target_id = None
        for c in data.get("cards", []):
            if c["id"] == card_title_or_id or card_title_or_id.lower() in c["title"].lower():
                target_id = c["id"]
                break
        if not target_id:
            return f"No se encontro ninguna tarjeta con titulo o id '{card_title_or_id}'."
        ks.delete_card(target_id, case_id=case_id)
        return f"Tarjeta '{target_id}' eliminada del tablero Kanban."
    except Exception as e:
        return f"Error eliminando tarjeta del tablero: {str(e)}"

@tool
def manage_box(
    action: Literal["add", "update", "delete"],
    title: str,
    description: str = "",
    content: str = "",
    short_description: str = "",
    detailed_description: str = "",
    category: Literal["immediate", "prioritaria", "savings", "investment", "debt", "insurance", "lifestyle", "alerta", "goal", "general"] = "general",
    impact: str = "",
    week: Optional[int] = None,
    steps: Optional[list[str]] = None,
    config: RunnableConfig = None
) -> str:
    """Gestiona tarjetas en el panel de accion con campos estructurados nativos.
    
    Args:
        action: 'add', 'update' o 'delete'
        title: Titulo conciso y claro de la accion (sin corchetes de categoria ni emojis, ej: 'Apertura de cuenta HSA')
        description: Explicacion accesible y empatica orientada a no expertos
        short_description: Descripcion breve de 1 linea para la vista previa
        detailed_description: Explicacion extendida con contexto financiero
        category: Categoria ('immediate', 'prioritaria', 'savings', 'investment', 'debt', 'insurance', 'lifestyle', 'alerta', 'goal', 'general')
        impact: Beneficio cuantificado conciso (ej: '+$500/mes', '-$2,000 en deuda', '+5 pts')
        week: Numero de semana asignada (1 a 4) si aplica
        steps: Lista de pasos directos a seguir para ejecutar la accion
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    desc = detailed_description or description or content
    s_desc = short_description or (desc[:120] if len(desc) > 120 else desc)
    norm_cat = "immediate" if category == "prioritaria" else category
    try:
        import boxes_store as bs
        import kanban_store as ks
        ks.set_case(case_id)
        if action in ("add", "update"):
            bs.add_box(
                title=title,
                content=desc,
                category=norm_cat,
                impact=impact,
                week=week,
                steps=steps,
                case_id=case_id
            )
            # Sincronizar con tablero Kanban
            kb_data = ks.load(case_id)
            existing = [c for c in kb_data.get("cards", []) if c.get("title") == title]
            if existing:
                ks.update_card(
                    existing[0]["id"],
                    title=title,
                    content=desc,
                    short_description=s_desc,
                    detailed_description=desc,
                    category=norm_cat,
                    impact=impact,
                    week=week,
                    steps=steps or [],
                    case_id=case_id
                )
            else:
                initial_st = "in_process" if norm_cat in ("immediate", "alerta") else "todo"
                ks.add_card(
                    title=title,
                    content=desc,
                    status=initial_st,
                    short_description=s_desc,
                    detailed_description=desc,
                    category=norm_cat,
                    impact=impact,
                    week=week,
                    steps=steps or [],
                    case_id=case_id
                )
            return f"Tarjeta '{title}' guardada en el panel vertical."
        elif action == "delete":
            bs.remove_box(title, case_id=case_id)
            kb_data = ks.load(case_id)
            for c in kb_data.get("cards", []):
                if c.get("title") == title:
                    ks.delete_card(c["id"], case_id=case_id)
            return f"Tarjeta '{title}' eliminada del panel vertical."
        return f"Accion '{action}' no reconocida."
    except Exception as e:
        return f"Error gestionando tarjeta: {str(e)}"

@tool
def move_kanban_card(
    card_title_or_id: str,
    status: Literal["todo", "in_process", "done"],
    config: RunnableConfig = None
) -> str:
    """Mueve una tarjeta en el tablero Kanban a una columna especifica ('todo', 'in_process', 'done').
    
    Args:
        card_title_or_id: ID de la tarjeta o titulo (ej: 'Revisar presupuesto')
        status: Columna destino ('todo', 'in_process' o 'done')
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import kanban_store as ks
        ks.set_case(case_id)
        data = ks.load(case_id)
        target_id = None
        for c in data.get("cards", []):
            if c["id"] == card_title_or_id or card_title_or_id.lower() in c["title"].lower():
                target_id = c["id"]
                break
        if not target_id:
            return f"No se encontro ninguna tarjeta con titulo o id '{card_title_or_id}'."
        ks.move_card(target_id, status, case_id=case_id)
        return f"Tarjeta '{target_id}' movida a la columna '{status}' en el tablero Kanban."
    except Exception as e:
        return f"Error moviendo tarjeta en el tablero: {str(e)}"

@tool
def project_growth(
    column: str,
    rate_pct: float,
    compounding: bool = True,
    start_date: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """Aplica una proyeccion de crecimiento mensual (lineal o compuesto) a una columna de la tabla mensual en todos los meses registrados.
    
    Args:
        column: Nombre de la columna (ej: 'Ingresos', 'Gastos_Fijos', 'Ahorro_Libre').
        rate_pct: Porcentaje mensual de crecimiento (ej: 10.0 para un 10% cada mes).
        compounding: True para crecimiento compuesto mes a mes (ej: mes2 = mes1 * (1 + rate/100)), False para lineal.
        start_date: Fecha de inicio opcional ('YYYY-MM'). Si se omite, inicia desde el mes en curso o primer mes futuro.
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    session = _get_session_from_config(config)

    try:
        import table_store as ts
        tb_data = ts.load(case_id=case_id)
        cols = list(tb_data.get("columns", []))
        rows = tb_data.get("rows", [])

        if column not in cols:
            cols.append(column)
            for r in rows:
                if column not in r:
                    r[column] = 0.0

        if not rows:
            return f"No hay filas registradas en la tabla para proyectar {column}."

        start_idx = 0
        if start_date:
            for i, r in enumerate(rows):
                if r.get("date") == start_date:
                    start_idx = i
                    break
        else:
            now_m = datetime.now().strftime("%Y-%m")
            for i, r in enumerate(rows):
                if r.get("date") == now_m:
                    start_idx = i
                    break

        multiplier = 1.0 + (rate_pct / 100.0)
        base_val = 0.0
        if start_idx > 0 and column in rows[start_idx - 1]:
            base_val = float(rows[start_idx - 1][column])
        if base_val <= 0.0 and column in rows[start_idx]:
            base_val = float(rows[start_idx][column])
        if base_val <= 0.0 and session.dashboard:
            base_val = session.dashboard.monthly_income if column == "Ingresos" else session.dashboard.monthly_expenses
        if base_val <= 0.0:
            base_val = 15000.0

        current_val = base_val
        summary_items = []
        chart_cats = []
        chart_vals = []

        for i in range(start_idx, len(rows)):
            step = i - start_idx + 1
            if compounding:
                current_val = round(base_val * (multiplier ** step), 2)
            else:
                current_val = round(base_val * (1.0 + (rate_pct / 100.0) * step), 2)

            r_date = rows[i]["date"]
            rows[i][column] = current_val
            summary_items.append(f"{r_date}: ${current_val:,.2f}")
            chart_cats.append(r_date)
            chart_vals.append(current_val)

        tb_data["columns"] = cols
        tb_data["rows"] = rows
        ts.save(tb_data, case_id=case_id)

        norm_col = session._normalize_metric_key(column)
        if norm_col in ("monthly_income", "monthly_expenses"):
            first_val = float(rows[start_idx][column])
            session.update_dashboard_metric(norm_col, first_val, reason=f"Proyeccion de {column} (+{rate_pct}% mensual {'compuesto' if compounding else 'lineal'})")

        chart_title = f"Proyeccion de {column} (+{rate_pct}% mensual {'compuesto' if compounding else 'lineal'})"
        session.pending_charts.append({
            "type": "line",
            "title": chart_title,
            "labels": chart_cats,
            "categories": chart_cats,
            "values": chart_vals
        })

        comp_str = "compuesto" if compounding else "lineal"
        return (
            f"Proyeccion de {column} aplicada con exito (+{rate_pct}% mensual {comp_str}) en {len(chart_cats)} meses. "
            f"Primeros meses: {', '.join(summary_items[:4])}..."
        )
    except Exception as e:
        return f"Error aplicando proyeccion de crecimiento en tabla: {str(e)}"

@tool
def simulate_scenario(
    scenario_name: str,
    monthly_income_delta: float = 0.0,
    monthly_expense_delta: float = 0.0,
    emergency_expense: float = 0.0,
    one_off_bonus: float = 0.0,
    debt_extra_payment: float = 0.0,
    lump_sum_debt_payment: float = 0.0,
    house_downpayment: float = 0.0,
    house_purchase_month: Optional[str] = None,
    horizon_months: int = 24,
    config: RunnableConfig = None
) -> str:
    """Ejecuta una simulacion matematica What-If (ingresos, gastos, imprevistos, bonus, compra de vivienda) y prepara graficos comparativos interactivos."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    session = _get_session_from_config(config)

    from backend.app.services.simulation_engine import ScenarioParams, run_scenario_simulation

    income = 15000.0
    expenses = 9000.0
    debt = 25000.0
    net_worth = 200000.0
    score = 50

    if session.dashboard:
        db = session.dashboard
        income = db.monthly_income
        expenses = db.monthly_expenses
        debt = db.total_liabilities
        net_worth = db.net_worth
        score = db.health_score

    params = ScenarioParams(
        monthly_income_delta=monthly_income_delta,
        monthly_expense_delta=monthly_expense_delta,
        emergency_expense=emergency_expense,
        one_off_bonus=one_off_bonus,
        debt_extra_payment=debt_extra_payment,
        lump_sum_debt_payment=lump_sum_debt_payment,
        house_downpayment=house_downpayment,
        house_purchase_month=house_purchase_month,
        horizon_months=horizon_months
    )

    try:
        res = run_scenario_simulation(
            case_id=case_id,
            base_income=income,
            base_expenses=expenses,
            base_debt=debt,
            base_net_worth=net_worth,
            base_score=score,
            params=params,
            scenario_name=scenario_name
        )

        chart_months = [pt.month for pt in res.timeline]
        chart_nw = [pt.net_worth for pt in res.timeline]
        session.pending_charts.append({
            "type": "line",
            "title": f"Simulacion: {scenario_name} (Score Proyectado: {res.projected_score}/100, delta: {res.score_delta:+d})",
            "labels": chart_months,
            "categories": chart_months,
            "values": chart_nw
        })

        return (
            f"Simulacion '{scenario_name}' completada con exito.\n"
            f"- Veredicto: {res.verdict}\n"
            f"- Score proyectado: {res.projected_score}/100 (Variacion: {res.score_delta:+d} pts)\n"
            f"- Patrimonio neto a 12 meses: ${res.net_worth_12m:,.0f} (Delta: ${res.net_worth_delta_12m:+,.0f})\n"
            f"- Hitos: {'; '.join(res.milestones) if res.milestones else 'Evolucion sostenida sin quiebres de liquidez'}"
        )
    except Exception as e:
        return f"Error ejecutando simulacion: {str(e)}"

@tool
async def generate_advisor_report_tool(
    config: RunnableConfig = None
) -> str:
    """Genera la ficha ejecutiva de sintesis para preparar la reunion de asesoria con Sherpas Wealth."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    session_id = configurable.get("session_id", "default")
    from backend.app.services.report_generator import generate_client_handover_report
    try:
        rep = await generate_client_handover_report(case_id, session_id)
        return (
            f"Ficha de acompanamiento generada para {rep['title']}.\n"
            f"Score actual: {rep['score']}/100 ({rep['band']}).\n"
            f"Preguntas clave preparadas para el asesor:\n" +
            "\n".join([f"- {q}" for q in rep.get("advisor_questions", [])])
        )
    except Exception as e:
        return f"Error generando ficha de acompanamiento: {str(e)}"

@tool
def financial_calculator(
    operation: Literal[
        "loan_amortization",
        "compound_future_value",
        "retirement_runway",
        "debt_avalanche_vs_snowball",
        "tax_savings_estimate"
    ],
    principal: float = 0.0,
    annual_rate_pct: float = 0.0,
    years: float = 0.0,
    monthly_contribution: float = 0.0,
    annual_spending: float = 0.0,
    inflation_rate_pct: float = 0.0,
    marginal_tax_rate_pct: float = 0.0,
    debts: Optional[list[dict]] = None,
    config: RunnableConfig = None
) -> str:
    """Calculadora financiera de proposito general para modelar cualquier operacion matematica con rigor.
    Operaciones:
      - 'loan_amortization': Cuota mensual, coste total en intereses y tiempo de amortizacion.
      - 'compound_future_value': Crecimiento compuesto con aportaciones regulares (401k, 529, fondos).
      - 'retirement_runway': Ano exacto de agotamiento de fondos bajo una tasa de gasto e inflacion dada (detecta desacumulaciones criticas).
      - 'debt_avalanche_vs_snowball': Comparativa de ahorro en intereses entre metodo avalancha (mayor interes primero) vs bola de nieve (menor saldo primero).
      - 'tax_savings_estimate': Ahorro fiscal directo derivado de aportaciones deducibles (HSA, IRA tradicional, 401k).
    """
    try:
        if operation == "loan_amortization":
            p = max(0.0, principal)
            r = (annual_rate_pct / 100.0) / 12.0
            n = int(years * 12) if years > 0 else 12
            if r > 0 and n > 0:
                payment = p * (r * ((1.0 + r) ** n)) / (((1.0 + r) ** n) - 1.0)
            else:
                payment = p / max(1, n)
            total_paid = payment * n
            total_interest = total_paid - p
            return (
                f"Amortizacion de prestamo (${p:,.0f} al {annual_rate_pct:.2f}% en {years} anos):\n"
                f"- Cuota mensual estimada: ${payment:,.2f}/mes\n"
                f"- Intereses totales pagados: ${total_interest:,.2f}\n"
                f"- Desembolso total: ${total_paid:,.2f}"
            )

        elif operation == "compound_future_value":
            p = max(0.0, principal)
            pmt = max(0.0, monthly_contribution)
            r = (annual_rate_pct / 100.0) / 12.0
            n = int(years * 12) if years > 0 else 12
            if r > 0:
                fv_principal = p * ((1.0 + r) ** n)
                fv_pmt = pmt * (((1.0 + r) ** n) - 1.0) / r
            else:
                fv_principal = p
                fv_pmt = pmt * n
            fv_total = fv_principal + fv_pmt
            total_invested = p + (pmt * n)
            interest_earned = fv_total - total_invested
            return (
                f"Valor Futuro Compuesto (${p:,.0f} inicial + ${pmt:,.0f}/mes al {annual_rate_pct:.1f}% en {years} anos):\n"
                f"- Capital final acumulado: ${fv_total:,.2f}\n"
                f"- Total aportado: ${total_invested:,.2f}\n"
                f"- Intereses generados por interes compuesto: ${interest_earned:,.2f}"
            )

        elif operation == "retirement_runway":
            balance = max(0.0, principal)
            spend = max(0.0, annual_spending)
            r = annual_rate_pct / 100.0
            inf = inflation_rate_pct / 100.0
            curr_year = datetime.now().year
            sim_years = 0
            while balance > 0 and sim_years < 60:
                balance = (balance - spend) * (1.0 + r)
                spend = spend * (1.0 + inf)
                sim_years += 1

            swr = (annual_spending / max(1.0, principal)) * 100.0
            if sim_years >= 60:
                return (
                    f"Analisis de Sostenibilidad de Jubilacion:\n"
                    f"- Tasa de retiro inicial: {swr:.2f}%\n"
                    f"- La cartera es perpetuamente sostenible (+60 anos sin agotamiento)."
                )
            else:
                depletion_year = curr_year + sim_years
                return (
                    f"Alerta de Agotamiento de Fondos (Precipicio de Jubilacion):\n"
                    f"- Tasa de retiro actual: {swr:.2f}%\n"
                    f"- Los fondos se agotan en {sim_years} anos (Ano estimado: {depletion_year}).\n"
                    f"- Causa: Gasto anual supera la tasa segura de retiro recomendada del 4%."
                )

        elif operation == "debt_avalanche_vs_snowball":
            debt_list = debts or [
                {"name": "Tarjeta Credito", "balance": 3500.0, "rate": 24.9},
                {"name": "Prestamo", "balance": 15000.0, "rate": 5.5}
            ]
            avalanche_order = sorted(debt_list, key=lambda d: d.get("rate", 0), reverse=True)
            snowball_order = sorted(debt_list, key=lambda d: d.get("balance", 0))
            return (
                f"Comparativa de Estrategias de Amortizacion de Deuda:\n"
                f"1. Metodo Avalancha (Prioridad matematico-financiera por mayor TAE):\n"
                f"   Orden recomendado: {', '.join([d['name'] + ' (' + str(d['rate']) + '% TAE)' for d in avalanche_order])}.\n"
                f"   Ventaja: Ahorra el maximo de intereses financieros.\n"
                f"2. Metodo Bola de Nieve (Prioridad psicologica por menor saldo):\n"
                f"   Orden: {', '.join([d['name'] + ' ($' + str(d['balance']) + ')' for d in snowball_order])}.\n"
                f"   Ventaja: Victorias tempranas rapidas para aliviar el estres emocional."
            )

        elif operation == "tax_savings_estimate":
            contrib = max(0.0, principal if principal > 0 else monthly_contribution * 12)
            tax_rate = marginal_tax_rate_pct / 100.0 if marginal_tax_rate_pct > 0 else 0.24
            savings = contrib * tax_rate
            return (
                f"Estimacion de Ventaja y Ahorro Fiscal:\n"
                f"- Aportacion deducible anual: ${contrib:,.2f}\n"
                f"- Tipo marginal estimado: {tax_rate * 100:.1f}%\n"
                f"- Ahorro directo en IRPF / Taxes: ${savings:,.2f} al ano (${savings / 12:,.2f}/mes)."
            )

        return f"Operacion '{operation}' no reconocida."
    except Exception as e:
        return f"Error en calculo financiero: {str(e)}"

@tool
async def search_case_details(
    query: str,
    config: RunnableConfig = None
) -> str:
    """Busca en profundidad en todo el expediente del cliente (persona.md, informe de salud financiera, cartera y analisis de inversiones). Devuelve las secciones mas relevantes que coincidan con la busqueda."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        raw_case = await case_repo.get_case(case_id)
        q = query.lower().strip()
        matched_chunks = []

        # Buscar en persona.md
        if raw_case.persona_markdown:
            paras = raw_case.persona_markdown.split("\n\n")
            for p in paras:
                if q in p.lower():
                    matched_chunks.append(f"[Persona.md]\n{p.strip()[:600]}")
                    if len(matched_chunks) >= 3:
                        break

        # Buscar en salud financiera
        fh_str = json.dumps(raw_case.financial_health, ensure_ascii=False)
        if q in fh_str.lower() and len(matched_chunks) < 3:
            # Extraer bloque
            idx = fh_str.lower().find(q)
            start = max(0, idx - 150)
            end = min(len(fh_str), idx + 350)
            matched_chunks.append(f"[Salud Financiera]\n...{fh_str[start:end]}...")

        # Buscar en analisis de inversiones
        ia_str = json.dumps(raw_case.investment_analysis, ensure_ascii=False)
        if q in ia_str.lower() and len(matched_chunks) < 3:
            idx = ia_str.lower().find(q)
            start = max(0, idx - 150)
            end = min(len(ia_str), idx + 350)
            matched_chunks.append(f"[Inversiones]\n...{ia_str[start:end]}...")

        if not matched_chunks:
            return f"No se encontraron coincidencias exactas para '{query}' en el expediente de {case_id}."
        return "\n\n---\n\n".join(matched_chunks)
    except Exception as e:
        return f"Error buscando en expediente: {str(e)}"

ALL_COPILOT_TOOLS = [
    manage_task,
    update_dashboard_metric,
    display_chart,
    inspect_case_data,
    get_table,
    modify_table_cell,
    set_cell,
    set_cells,
    set_cell_formula,
    apply_column_formula,
    set_row,
    delete_row,
    add_table_column,
    add_column,
    delete_column,
    evaluate_formula,
    spreadsheet_aggregate,
    manage_box,
    add_kanban_card,
    move_kanban_card,
    delete_kanban_card,
    project_growth,
    register_loan_and_amortization,
    simulate_scenario,
    generate_advisor_report_tool,
    financial_calculator,
    search_case_details,
]
