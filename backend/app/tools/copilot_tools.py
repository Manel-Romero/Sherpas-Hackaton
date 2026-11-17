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
    task_id: str,
    title: str = "",
    description: str = "",
    week: int = 1,
    impact_metric: str = "Ahorro",
    impact_value: str = "",
    config: RunnableConfig = None  # Inyectado automaticamente por LangChain en tiempo de ejecucion
) -> str:
    """Gestiona la lista de tareas pendientes del usuario (anadir, completar o eliminar una tarea)."""
    session = _get_session_from_config(config)
    
    if action == "add":
        new_task = TaskItem(
            id=task_id or f"task_{len(session.tasks) + 1}",
            title=title or "Nueva tarea recomendada",
            description=description,
            week=week,
            status="pending",
            impact=TaskImpact(metric=impact_metric, value=impact_value) if impact_value else None
        )
        session.add_task(new_task)
        return f"Tarea '{new_task.title}' anadida correctamente a la lista (Semana {week})."

    elif action == "complete":
        success = session.update_task_status(task_id, "completed")
        if success:
            return f"Tarea '{task_id}' marcada como completada con exito."
        return f"No se encontro la tarea '{task_id}' para marcarla como completada."

    elif action == "delete":
        success = session.remove_task(task_id)
        if success:
            return f"Tarea '{task_id}' eliminada de la lista."
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
                from frontend import table_store as ts
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
        from frontend import table_store as ts
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
    """Modifica o introduce un valor numerico en una celda de la hoja de calculo mensual (ej: fecha '2026-03', columna 'Gastos_Fijos', valor 17336)."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        from frontend import table_store as ts
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
    """Establece el valor numerico de una celda en la tabla mensual (fecha YYYY-MM, columna, valor)."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        from frontend import table_store as ts
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
        from frontend import table_store as ts
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
        from frontend import table_store as ts
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
        from frontend import table_store as ts
        ts.delete_row(date, case_id=case_id)
        return f"Fila del mes {date} eliminada de la tabla mensual."
    except Exception as e:
        return f"Error eliminando fila: {str(e)}"

@tool
def add_table_column(
    name: str,
    default: float = 0.0,
    config: RunnableConfig = None
) -> str:
    """Anade una nueva columna a la hoja de calculo mensual (ej: 'Fondo_Herencia', 'Amortizacion_Extra')."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        from frontend import table_store as ts
        ts.add_column(name, default, case_id=case_id)
        return f"Columna '{name}' anadida con exito a la tabla mensual."
    except Exception as e:
        return f"Error anadiendo columna: {str(e)}"

@tool
def add_column(
    name: str,
    default: float = 0.0,
    config: RunnableConfig = None
) -> str:
    """Anade una nueva columna numerica a la tabla mensual (alias de add_table_column)."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        from frontend import table_store as ts
        ts.add_column(name, default, case_id=case_id)
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
        from frontend import table_store as ts
        ts.delete_column(name, case_id=case_id)
        return f"Columna '{name}' eliminada de la tabla mensual."
    except Exception as e:
        return f"Error eliminando columna: {str(e)}"

@tool
def add_kanban_card(
    title: str,
    content: str = "",
    status: Literal["todo", "in_process", "done"] = "todo",
    config: RunnableConfig = None
) -> str:
    """Anade una nueva tarjeta directamente al tablero Kanban ('todo', 'in_process' o 'done')."""
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    try:
        import kanban_store as ks
        ks.set_case(case_id)
        card_res = ks.add_card(title=title, content=content, status=status, case_id=case_id)
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
        description: Explicacion accesible y empatica orientada a no expertos (sin jerga bancaria compleja)
        category: Categoria ('immediate', 'prioritaria', 'savings', 'investment', 'debt', 'insurance', 'lifestyle', 'alerta', 'goal', 'general')
        impact: Beneficio cuantificado conciso (ej: '+$500/mes', '-$2,000 en deuda', '+5 pts')
        week: Numero de semana asignada (1 a 4) si aplica
        steps: Lista de pasos directos a seguir para ejecutar la accion (ej: ['Llamar al banco', 'Ajustar cuota'])
    """
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id", "michael-carter")
    desc = description or content
    norm_cat = "immediate" if category == "prioritaria" else category
    try:
        from frontend import boxes_store as bs
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
                ks.update_card(existing[0]["id"], title=title, content=desc, case_id=case_id)
            else:
                initial_st = "in_process" if norm_cat in ("immediate", "alerta") else "todo"
                ks.add_card(title=title, content=desc, status=initial_st, case_id=case_id)
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
        from frontend import table_store as ts
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

ALL_COPILOT_TOOLS = [
    manage_task,
    update_dashboard_metric,
    display_chart,
    inspect_case_data,
    get_table,
    modify_table_cell,
    set_cell,
    set_cells,
    set_row,
    delete_row,
    add_table_column,
    add_column,
    delete_column,
    manage_box,
    add_kanban_card,
    move_kanban_card,
    delete_kanban_card,
    project_growth,
]
