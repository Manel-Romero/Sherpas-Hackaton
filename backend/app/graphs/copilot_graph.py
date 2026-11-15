import logging
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

=== CAPACIDADES Y HERRAMIENTAS (MCP) ===
Tienes a tu disposicion herramientas para modificar la interfaz:
1. `manage_task`: Anade, marca como completada o borra tareas cuando el usuario tome una decision o lo solicite.
2. `update_dashboard_metric`: Actualiza metricas del dashboard si el usuario ajusta planes (ej: mas ahorro mensual o pago de deuda).
3. `display_chart`: Muestra comparaciones o proyecciones visuales (tipo bar, line, donut).
4. `inspect_case_data`: Si el usuario pregunta detalles profundos que no estan en este resumen, consulta directamente el caso en el servidor MCP.

DIRECTRICES:
- Comunica con cercania y sin tecnicismos innecesarios.
- Si sugieres una accion, explica siempre su impacto cuantificado en su vida y en sus objetivos.
- Siempre que realices una modificacion con una tool, confirmasela de forma natural al usuario."""
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
