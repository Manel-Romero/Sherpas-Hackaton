from typing import Annotated, Optional, Any
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from backend.app.models.case import CaseFull
from backend.app.models.plan import MasterPlan
from backend.app.models.dashboard import DashboardState

class CaseInitState(TypedDict, total=False):
    # Estado para el grafo de inicializacion maestra
    case_id: str
    user_query: Optional[str]
    raw_case: Optional[CaseFull]
    executive_summary: Optional[str]
    master_plan: Optional[MasterPlan]
    dashboard_initial: Optional[DashboardState]
    error: Optional[str]

class CopilotState(TypedDict, total=False):
    # Estado para el bucle conversacional del Co-Pilot
    messages: Annotated[list[AnyMessage], add_messages]
    case_id: str
    session_id: str
    summary: str
    persona_notes: str
    dashboard_summary: str
    tasks_summary: str
