import json
import logging
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from backend.app.config import settings
from backend.app.graphs.state import CaseInitState
from backend.app.models.plan import MasterPlan, WeeklyRoadmap, TaskItem, TaskImpact, ImmediateAction
from backend.app.models.dashboard import DashboardState, DashboardMetric
from backend.app.services.case_repository import case_repo
from backend.app.services.session_store import session_store
from backend.app.services.llm_factory import get_reasoning_llm

logger = logging.getLogger(__name__)

class SynthesizedCaseOutput(BaseModel):
    # Estructura tipada generada por el modelo de razonamiento maestro
    executive_summary: str = Field(
        description="Resumen cognitivo y financiero (1500-2000 tokens) que incluye salud financiera, tensiones emocionales y alertas criticas. Se muestra al usuario, asi que va en segunda persona y en lenguaje llano; el primer parrafo (3-4 frases) debe poder leerse solo."
    )
    headline: str = Field(description="Titular motivador que resume el objetivo principal del caso")
    immediate_action_title: str = Field(description="La accion mas urgente que debe hacer hoy")
    immediate_action_reason: str = Field(description="Por que esta accion desbloquea su situacion")
    immediate_action_steps: list[str] = Field(description="Pasos exactos en 3 minutos")
    immediate_action_impact: str = Field(description="Impacto cuantificado y emocional")
    
    tasks: list[TaskItem] = Field(description="Lista de 4 a 6 tareas concretas para el frontend")
    weekly_roadmaps: list[WeeklyRoadmap] = Field(description="Guia de 3 a 4 semanas para estructurar la ejecucion")
    
    net_worth: float = Field(description="Patrimonio neto actual aproximado")
    total_assets: float = Field(description="Total de activos")
    total_liabilities: float = Field(description="Total de deudas")
    monthly_income: float = Field(description="Ingreso mensual neto")
    monthly_expenses: float = Field(description="Gastos mensuales")

async def load_case_node(state: CaseInitState) -> CaseInitState:
    # Carga los datos del caso directamente desde el servidor MCP
    case_id = state.get("case_id", "michael-carter")
    try:
        raw_case = await case_repo.get_case(case_id)
        return {"raw_case": raw_case}
    except Exception as e:
        logger.error(f"Error cargando caso {case_id} desde servidor MCP: {e}")
        return {"error": f"No se pudo cargar el caso '{case_id}' desde el servidor MCP: {str(e)}"}

async def synthesize_case_node(state: CaseInitState) -> CaseInitState:
    # Invoca al modelo LLM para generar el plan, resumen y tareas iniciales
    if state.get("error"):
        return state

    raw_case = state.get("raw_case")
    if not raw_case:
        return {"error": "No se encontraron los datos del caso para inicializar."}

    case_id = raw_case.id
    user_query = state.get("user_query") or "Disena el plan de choque financiero y emocional para esta familia."

    # Datos extraidos del caso
    fh = raw_case.financial_health
    score = fh.get("score", {})
    score_published = score.get("published_score", 0)
    top_moves = score.get("top_moves", [])
    profile = fh.get("profile", {})
    persona_md = raw_case.persona_markdown

    system_prompt = """Eres el Agente Maestro de Sherpas Wealth, un asesor financiero de elite que traduce planes complejos en planes de accion inmediatos y empaticos.
Tu objetivo es analizar el caso completo (JSONs de salud financiera + markdown de perfil psicologico persona.md) y producir:
1. Un RESUMEN EJECUTIVO condensado (perfil emocional, tensiones D0 a D6, cuello de botella financiero, score).
2. Un PLAN DE ACCION con accion inmediata (lo primero que deben hacer hoy) y un roadmap semana a semana.
3. Una lista de TAREAS concretas con IMPACTO cuantitativo (ej: +$350/mes, -$18k deuda) y beneficio emocional.
4. Estimacion de metricas clave para el Dashboard (patrimonio, deudas, ingresos, gastos).

REGLAS DE SHERPAS:
- NUNCA inventes numeros. Usa exclusivamente los datos del caso.
- Empatia y respeto: Si la persona tiene panico o score bajo (ej. 26), no juzgues ni uses tono paternalista; dale una victoria rapida y tratalo como un adulto inteligente sin hacerle sentir culpable ni abrumado.
- Lenguaje accesible: Redacta los titulares, motivos y tareas en un lenguaje claro, terrenal y comprensible para no expertos, evitando tecnicismos financieros innecesarios.
- El RESUMEN EJECUTIVO se muestra tal cual al usuario en su tutorial y lo lee una persona sin conocimientos financieros: escribelo en segunda persona ("tu", "tienes"), con frases cortas, sin codigos internos (D0 a D6), sin siglas ni jerga. Si necesitas un termino tecnico, explicalo en una frase con palabras de calle (por ejemplo, "lo que te sobra cada mes" en vez de "flujo de caja libre", "lo que tienes menos lo que debes" en vez de "patrimonio neto"). El primer parrafo (3-4 frases) debe poder leerse solo: donde esta hoy, que le preocupa y que es lo primero que hacer.
- Accion: Haz que la primera accion tome menos de 3 minutos.
- ERES EL ASESOR FINANCIERO: NUNCA generes tareas que digan 'Consulta con un asesor financiero' o 'Habla con un profesional'. Eres el asesor de Sherpas que comunica las acciones concretas para el cliente (ej: 'Rebalancear la cartera hacia un perfil 80/20' o 'Emitir ampliacion de poliza con la aseguradora').
- GENERACION ESTRUCTURADA ESTRICTA (JSON limpio sin prefijos):
  * Titulos: Deben ser limpios y naturales (ej: 'Abrir una cuenta IRA tradicional'). NUNCA incluyas corchetes de categoria como '[INVESTMENT]' o '[SAVINGS]', ni emojis como '⚡' o '🎯'.
  * Categoria: Asignala estrictamente al campo `category` ('debt', 'savings', 'investment', 'insurance', 'lifestyle').
  * Semana: El campo `week` guarda el numero entero (1, 2, 3 o 4). NUNCA escribas 'Semana 1 - ' en el titulo ni en la descripcion.
  * Pasos: Se deben devolver como lista JSON de strings en `immediate_action_steps` y `steps`. NUNCA unas los pasos con barras '|'.
  * Impacto: Debe expresarse de forma concisa y cuantificada en su respectivo campo de impacto (ej: '+$7,500/año', '+2 pts', '-$3,500').
- ORTOGRAFIA: En tus respuestas o explicaciones en texto, responde siempre en castellano CON acentos y ortografia correcta."""

    human_content = f"""CASO: {case_id}
CONSULTA DEL USUARIO: {user_query}

PERSONA (Perfil psicologico y tensiones completas):
{persona_md}

SALUD FINANCIERA (Score y Top Moves):
Score: {score_published} ({score.get('band', '')})
Mensaje: {score.get('message', '')}
Top Moves recomendados por Sherpas: {json.dumps(top_moves, ensure_ascii=False)}

PERFIL ECONOMICO BASICO:
Incomes: {json.dumps(profile.get('incomes', []), ensure_ascii=False)}
Expenses: {json.dumps(profile.get('expenses', []), ensure_ascii=False)}
Liabilities: {json.dumps(profile.get('liabilities', []), ensure_ascii=False)}
"""

    try:
        llm = get_reasoning_llm()
        structured_llm = llm.with_structured_output(SynthesizedCaseOutput)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]
        result: SynthesizedCaseOutput = await structured_llm.ainvoke(messages)

        master_plan = MasterPlan(
            case_id=case_id,
            headline=result.headline,
            immediate_action=ImmediateAction(
                title=result.immediate_action_title,
                reason=result.immediate_action_reason,
                instructions=result.immediate_action_steps,
                expected_impact=result.immediate_action_impact
            ),
            weekly_roadmap=result.weekly_roadmaps,
            tasks=result.tasks
        )

        dashboard = DashboardState(
            case_id=case_id,
            health_score=score_published,
            net_worth=result.net_worth,
            total_assets=result.total_assets,
            total_liabilities=result.total_liabilities,
            monthly_income=result.monthly_income,
            monthly_expenses=result.monthly_expenses,
            monthly_free_cashflow=result.monthly_income - result.monthly_expenses,
            metrics={
                "health_score": DashboardMetric(
                    id="health_score",
                    label="Score de Salud Financiera",
                    value=score_published,
                    formatted_value=f"{score_published}/100",
                    unit="pts",
                    status="warning" if score_published < 60 else "success"
                ),
                "net_worth": DashboardMetric(
                    id="net_worth",
                    label="Patrimonio Neto",
                    value=result.net_worth,
                    formatted_value=f"${result.net_worth:,.0f}",
                    unit="$",
                    status="neutral"
                ),
                "monthly_income": DashboardMetric(
                    id="monthly_income",
                    label="Ingresos Mensuales",
                    value=result.monthly_income,
                    formatted_value=f"${result.monthly_income:,.0f}/mes",
                    unit="$",
                    status="neutral"
                ),
                "monthly_expenses": DashboardMetric(
                    id="monthly_expenses",
                    label="Gastos Mensuales",
                    value=result.monthly_expenses,
                    formatted_value=f"${result.monthly_expenses:,.0f}/mes",
                    unit="$",
                    status="neutral"
                ),
                "monthly_cashflow": DashboardMetric(
                    id="monthly_cashflow",
                    label="Flujo de Caja Libre",
                    value=result.monthly_income - result.monthly_expenses,
                    formatted_value=f"${(result.monthly_income - result.monthly_expenses):,.0f}/mes",
                    unit="$",
                    status="success" if (result.monthly_income - result.monthly_expenses) > 0 else "danger"
                ),
            }
        )

        return {
            "executive_summary": result.executive_summary,
            "master_plan": master_plan,
            "dashboard_initial": dashboard
        }

    except Exception as e:
        logger.error(f"Fallo al invocar el modelo de razonamiento maestro: {e}")
        return {"error": f"Fallo al generar el plan maestro con el modelo LLM: {str(e)}"}

def persist_session_node(state: CaseInitState) -> CaseInitState:
    # Persiste los datos unicamente si la inicializacion fue exitosa sin errores
    if state.get("error"):
        return state

    case_id = state.get("case_id", "default")
    session = session_store.get_or_create(session_id="default", case_id=case_id)
    
    if state.get("master_plan"):
        session.master_plan = state["master_plan"]
        session.tasks = list(state["master_plan"].tasks)
    if state.get("dashboard_initial"):
        session.dashboard = state["dashboard_initial"]
    if state.get("executive_summary"):
        session.summary_executive = state["executive_summary"]

    # Sincronizar almacenamiento local para la interfaz de Streamlit (tabla mensual y cajas)
    try:
        from frontend import table_store as ts
        from frontend import boxes_store as bs

        # 1. Inicializar la hoja de calculo mensual a 12 meses
        if state.get("dashboard_initial"):
            d = state["dashboard_initial"]
            ts.initialize_default_table(
                case_id=case_id,
                monthly_income=d.monthly_income,
                monthly_expenses=d.monthly_expenses,
                total_debt=d.total_liabilities,
                net_worth=d.net_worth
            )

        # 2. Inicializar las tarjetas del plan con esquema nativo estructurado
        if state.get("master_plan"):
            mp = state["master_plan"]
            act = mp.immediate_action
            boxes_data = {"boxes": []}
            
            # Caja 1: Objetivo Maestro (Hero)
            boxes_data["boxes"].append({
                "title": "Objetivo Maestro",
                "category": "goal",
                "description": mp.headline,
                "content": mp.headline,
                "impact": "",
                "week": None,
                "steps": []
            })

            # Caja 2: Accion Inmediata (Hoy)
            boxes_data["boxes"].append({
                "title": act.title,
                "category": "immediate",
                "description": act.reason,
                "content": act.reason,
                "impact": act.expected_impact,
                "week": None,
                "steps": list(act.instructions) if act.instructions else []
            })

            # Cajas 3+: Tareas accionables con campos tipados
            for t in mp.tasks:
                boxes_data["boxes"].append({
                    "title": t.title,
                    "category": t.category,
                    "description": t.description,
                    "content": t.description,
                    "impact": t.impact.value if t.impact else "",
                    "week": t.week,
                    "steps": list(t.steps) if getattr(t, "steps", None) else []
                })

            bs.save(boxes_data, case_id=case_id)

            # 3. Sincronizar tambien con el tablero Kanban interactivo con campos estructurados
            try:
                import kanban_store as ks
                import uuid
                kb_cards = []
                act_instr = list(act.instructions) if act.instructions else []
                act_s_desc = act.reason.split(".")[0].strip() if act.reason else act.title
                if len(act_s_desc) > 120:
                    act_s_desc = act_s_desc[:117] + "..."
                kb_cards.append({
                    "id": uuid.uuid4().hex[:6],
                    "title": act.title,
                    "short_description": act_s_desc,
                    "detailed_description": act.reason,
                    "category": "immediate",
                    "impact": act.expected_impact or "",
                    "week": 1,
                    "steps": act_instr,
                    "status": "in_process",
                    "content": act.reason
                })
                for t in mp.tasks:
                    t_steps = list(t.steps) if getattr(t, "steps", None) else []
                    t_desc = t.description or t.title
                    t_s_desc = t_desc.split(".")[0].strip()
                    if len(t_s_desc) > 120:
                        t_s_desc = t_s_desc[:117] + "..."
                    kb_cards.append({
                        "id": getattr(t, "id", None) or uuid.uuid4().hex[:6],
                        "title": t.title,
                        "short_description": t_s_desc,
                        "detailed_description": t_desc,
                        "category": t.category or "savings",
                        "impact": t.impact.value if t.impact else "",
                        "week": t.week or 1,
                        "steps": t_steps,
                        "status": "todo",
                        "content": t_desc
                    })
                ks.save({"cards": kb_cards}, case_id=case_id)
            except Exception as e_kb:
                logger.warning(f"No se pudo sincronizar kanban store: {e_kb}")
    except Exception as e:
        logger.warning(f"No se pudo sincronizar almacenamiento de frontend: {e}")

    return state

# Compilacion del grafo de inicializacion
builder = StateGraph(CaseInitState)
builder.add_node("load_case", load_case_node)
builder.add_node("synthesize", synthesize_case_node)
builder.add_node("persist", persist_session_node)

builder.add_edge(START, "load_case")
builder.add_edge("load_case", "synthesize")
builder.add_edge("synthesize", "persist")
builder.add_edge("persist", END)

init_graph = builder.compile()
