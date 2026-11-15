import logging
from datetime import datetime
from typing import Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from backend.app.config import settings
from backend.app.graphs.state import CopilotState
from backend.app.services.session_store import session_store
from backend.app.services.llm_factory import get_chat_llm
from backend.app.tools.copilot_tools import ALL_COPILOT_TOOLS

logger = logging.getLogger(__name__)

def build_system_prompt(session_id: str, case_id: str) -> str:
    # Construye el prompt de sistema dinamicamente con el estado actual
    session = session_store.get_or_create(session_id, case_id)
    
    summary = session.summary_executive or f"Caso activo: {case_id}."
    
    # Resumen del dashboard financiero
    if session.dashboard:
        db = session.dashboard
        dashboard_summary = (
            f"Health Score: {db.health_score}/100 | "
            f"Patrimonio Neto: ${db.net_worth:,.0f} | "
            f"Total Activos: ${db.total_assets:,.0f} | "
            f"Total Deudas: ${db.total_liabilities:,.0f} | "
            f"Ingreso Mensual: ${db.monthly_income:,.0f} | "
            f"Gastos Mensuales: ${db.monthly_expenses:,.0f} | "
            f"Cashflow Libre: ${db.monthly_free_cashflow:,.0f}"
        )
    else:
        dashboard_summary = "Dashboard aun no inicializado."

    # Resumen de la lista de tareas
    if session.tasks:
        tasks_lines = [
            f"- [{t.status.upper()}] {t.id}: {t.title} (Semana {t.week}) -> Impacto: {t.impact.value if t.impact else 'N/A'}"
            for t in session.tasks
        ]
        tasks_summary = "\n".join(tasks_lines)
    else:
        tasks_summary = "No hay tareas activas en este momento."

    prompt = f"""Eres el Asesor Financiero Co-Pilot de Sherpas Wealth, guiando a la familia en tiempo real.
Tu mision es acompanar al usuario con empatia, responder sus preguntas con rigor, motivarle a actuar y mantener sincronizada la interfaz.

=== RESUMEN EJECUTIVO Y PERFIL DEL CASO ===
{summary}

=== ESTADO ACTUAL DEL DASHBOARD FINANCIERO ===
{dashboard_summary}

=== LISTA DE TAREAS ACTUAL ===
{tasks_summary}

=== FECHA Y MES DE REFERENCIA ===
Mes actual de la sesion: {datetime.now().strftime("%Y-%m")}

=== CAPACIDADES Y HERRAMIENTAS ===
Tienes a tu disposicion herramientas para sincronizar la interfaz en tiempo real:
1. `modify_table_cell`: Modifica celdas de la hoja de calculo mensual (date YYYY-MM, column, value). Ej: para reflejar un gasto extraordinario o imprevisto en el mes actual.
2. `add_table_column`: Anade una nueva columna a la tabla si el usuario introduce un nuevo concepto financiero.
3. `manage_box`: Crea, actualiza o elimina tarjetas visuales en el panel vertical de la interfaz (action='add', title, content, category='prioritaria'|'alerta'|'general').
4. `manage_task`: Gestiona la lista de tareas pendientes (anadir, completar, borrar).
5. `update_dashboard_metric`: Actualiza metricas globales del dashboard guardando el valor previo.
6. `display_chart`: Muestra graficos interactivos (bar, line, donut).
7. `inspect_case_data`: Consulta detalles profundos del caso en el servidor MCP oficial de Sherpas.

DIRECTRICES OPERATIVAS:
- Comunica con empatia, cercania y rigor financiero sin tecnicismos innecesarios.
- PROACTIVIDAD INMEDIATA: Si el usuario te informa de un imprevisto, gasto o accidente ocurrido (ej: 'he tenido un accidente y he tenido que desembolsar 2k €' o 'tuve que pagar una averia'), NUNCA pidas permiso ni preguntes si quiere que lo anadas. DEBES INVOCAR DIRECTAMENTE las herramientas pertinentes en esta misma ejecucion:
  a) Usa `manage_box` para registrar una tarjeta visible de contingencia con el detalle del impacto y plan de accion.
  b) Usa `modify_table_cell` para ajustar los gastos o ahorro del mes actual en la tabla.
  c) Si procede, usa `update_dashboard_metric` o `manage_task`.
- Despues de ejecutar las herramientas, en tu mensaje confirma de forma calida lo que acabas de actualizar en la interfaz, interesate por su bienestar y demuestra como el plan maestro absorbe el bache sin desviarse de los objetivos patrimoniales a largo plazo.
- Responde siempre en castellano sin acentos."""
    return prompt

async def agent_node(state: CopilotState, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
    # Nodo del agente: extrae contexto de config de forma aislada y ejecuta el modelo
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id") or state.get("case_id", "michael-carter")
    session_id = configurable.get("session_id") or state.get("session_id", "default")

    system_prompt = build_system_prompt(session_id, case_id)
    raw_messages = state.get("messages", [])

    # Filtrar mensajes de sistema previos e inyectar el prompt actualizado al inicio
    conversation = [m for m in raw_messages if not isinstance(m, SystemMessage)]
    messages = [SystemMessage(content=system_prompt)] + conversation

    llm = get_chat_llm(streaming=True)
    llm_with_tools = llm.bind_tools(ALL_COPILOT_TOOLS)
    response = await llm_with_tools.ainvoke(messages, config=config)
    return {"messages": [response]}

# Definicion del grafo ciclico ReAct con ToolNode nativo
copilot_builder = StateGraph(CopilotState)
copilot_builder.add_node("agent", agent_node)
copilot_builder.add_node("tools", ToolNode(ALL_COPILOT_TOOLS))

copilot_builder.add_edge(START, "agent")
# Si el agente emitio llamadas a herramientas vamos a tools. Si termino, vamos a END.
copilot_builder.add_conditional_edges("agent", tools_condition, ["tools", END])
# Desde tools volvemos ciclicamente a agent para razonar sobre los resultados
copilot_builder.add_edge("tools", "agent")

copilot_graph = copilot_builder.compile()
