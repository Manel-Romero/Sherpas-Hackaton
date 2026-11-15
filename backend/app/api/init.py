from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.graphs.init_graph import init_graph
from backend.app.models.plan import MasterPlan, TaskItem
from backend.app.models.dashboard import DashboardState
from backend.app.services.session_store import session_store

router = APIRouter(prefix="/cases", tags=["Case Initialization"])

class CaseInitRequest(BaseModel):
    user_query: Optional[str] = None
    session_id: Optional[str] = "default"

class CaseInitResponse(BaseModel):
    case_id: str
    headline: str
    executive_summary: str
    master_plan: MasterPlan
    tasks: list[TaskItem]
    dashboard: DashboardState

@router.post("/{case_id}/init", response_model=CaseInitResponse)
async def initialize_case(case_id: str, request: Optional[CaseInitRequest] = None):
    """
    Ejecuta el Inicializador Maestro (Monolito) una sola vez por caso:
    Carga el caso desde el servidor MCP, genera el Plan, la Guia semanal,
    las Tareas iniciales con impacto, el Resumen y el Dashboard inicial.
    """
    session_id = request.session_id if request else "default"
    user_query = request.user_query if request else None

    result = await init_graph.ainvoke({
        "case_id": case_id,
        "user_query": user_query
    })

    if result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])

    master_plan = result.get("master_plan")
    dashboard = result.get("dashboard_initial")
    summary = result.get("executive_summary")

    if not master_plan or not dashboard or not summary:
        raise HTTPException(
            status_code=500,
            detail="La respuesta del modelo no contiene la estructura requerida para inicializar el caso."
        )

    # Guardar en el almacen de sesiones
    session = session_store.get_or_create(session_id, case_id)
    session.master_plan = master_plan
    session.tasks = list(master_plan.tasks)
    session.dashboard = dashboard
    session.summary_executive = summary

    return CaseInitResponse(
        case_id=case_id,
        headline=master_plan.headline,
        executive_summary=summary,
        master_plan=master_plan,
        tasks=master_plan.tasks,
        dashboard=dashboard
    )
