import json
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
    config: RunnableConfig = None  # Inyectado automaticamente por LangChain en tiempo de ejecucion
) -> str:
    """Actualiza una metrica o celda clave del dashboard financiero (ej: net_worth, total_debt, monthly_savings, etc.)."""
    session = _get_session_from_config(config)
    success = session.update_dashboard_metric(key, value, reason)
    if success:
        return f"Metrica '{key}' actualizada a {value}. Motivo: {reason}"
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
            return f"Tarjeta '{title}' guardada en el panel vertical."
        elif action == "delete":
            bs.remove_box(title, case_id=case_id)
            return f"Tarjeta '{title}' eliminada del panel vertical."
        return f"Accion '{action}' no reconocida."
    except Exception as e:
        return f"Error gestionando tarjeta: {str(e)}"

ALL_COPILOT_TOOLS = [
    manage_task,
    update_dashboard_metric,
    display_chart,
    inspect_case_data,
    modify_table_cell,
    add_table_column,
    manage_box,
]
