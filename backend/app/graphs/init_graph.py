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
        description="Resumen cognitivo y financiero (1500-2000 tokens) que incluye salud financiera, tensiones emocionales y alertas criticas."
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
- Empatia: Si la persona tiene panico o score bajo (ej. 26), no juzgues; dale una victoria rapida.
- Accion: Haz que la primera accion tome menos de 3 minutos."""

    human_content = f"""CASO: {case_id}
CONSULTA DEL USUARIO: {user_query}

PERSONA (Perfil psicologico y tensiones completas):
{persona_md}

SALUD FINANCIERA (Score y Top Moves):
Score: {score_published} ({score.get('band', '')})
Mensaje: {score.get('message', '')}
Top Moves recomendados por Sherpas: {json.dumps(top_moves, ensure_ascii=False)}

PERFIL ECONOMICO BASICO:
Incomes: {json.dumps(profile.get('incomes', [])[:3], ensure_ascii=False)}
Debts: {json.dumps(profile.get('debts', [])[:3], ensure_ascii=False)}
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

        # 2. Inicializar las cajas verticales (Accion Inmediata + Tareas del Plan)
        if state.get("master_plan"):
            mp = state["master_plan"]
            boxes_data = {"boxes": []}
            
            # Caja 1: Accion Inmediata (Hoy)
            act = mp.immediate_action
            steps_txt = " | ".join(act.instructions) if act.instructions else act.reason
            boxes_data["boxes"].append({
                "title": f"⚡ Accion Inmediata: {act.title}",
                "content": f"{steps_txt} - Impacto: {act.expected_impact}",
                "category": "immediate"
            })
            
            # Caja 2: Titular del Plan
            boxes_data["boxes"].append({
                "title": "🎯 Objetivo Maestro",
                "content": mp.headline,
                "category": "goal"
            })

            # Cajas 3+: Tareas accionables
            for t in mp.tasks:
                imp_str = f" ({t.impact.value})" if t.impact else ""
                boxes_data["boxes"].append({
                    "title": f"[{t.category.upper()}] {t.title}{imp_str}",
                    "content": f"Semana {t.week} - {t.description}",
                    "category": t.category
                })

            bs.save(boxes_data, case_id=case_id)
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
