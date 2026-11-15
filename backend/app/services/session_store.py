from typing import Any, Optional
from datetime import datetime, timezone
from backend.app.models.plan import MasterPlan, TaskItem, TaskImpact
from backend.app.models.dashboard import DashboardState, DashboardMetric
from backend.app.models.chat import ChatMessage, ToolExecutionLog

class SessionData:
    # Contenedor de datos reactivos por sesion
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.master_plan: Optional[MasterPlan] = None
        self.tasks: list[TaskItem] = []
        self.dashboard: Optional[DashboardState] = None
        self.summary_executive: str = ""
        self.persona_highlights: str = ""
        self.chat_history: list[ChatMessage] = []
        self.pending_charts: list[dict[str, Any]] = []
        self.last_tools_executed: list[ToolExecutionLog] = []

    def add_task(self, task: TaskItem) -> None:
        self.tasks.append(task)

    def update_task_status(self, task_id: str, status: str) -> bool:
        for t in self.tasks:
            if t.id == task_id or t.title.lower() == task_id.lower():
                t.status = status  # type: ignore
                return True
        return False

    def remove_task(self, task_id: str) -> bool:
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id and t.title.lower() != task_id.lower()]
        return len(self.tasks) < initial_len

    def update_dashboard_metric(self, key: str, value: float, reason: str = "") -> bool:
        if not self.dashboard:
            return False
        
        updated = False
        # Comprobar campos estandar
        if hasattr(self.dashboard, key):
            setattr(self.dashboard, key, value)
            updated = True
        
        # Comprobar diccionario de metricas para tarjetas visuales
        if key in self.dashboard.metrics:
            m = self.dashboard.metrics[key]
            m.previous_value = m.value
            m.value = value
            m.formatted_value = f"${value:,.0f}" if m.unit == "$" else f"{value} {m.unit}"
            m.note = reason
            updated = True
        elif not updated:
            # Anadir nueva metrica personalizada si no existia en ningun lado
            self.dashboard.metrics[key] = DashboardMetric(
                id=key,
                label=key.replace("_", " ").capitalize(),
                value=value,
                formatted_value=f"${value:,.0f}",
                unit="$",
                note=reason
            )
            updated = True

        if updated:
            self.dashboard.last_updated = datetime.now(timezone.utc).isoformat()
            return True
        return False

class SessionStore:
    # Almacen en memoria indexado por identificador de sesion y caso
    def __init__(self):
        self._sessions: dict[str, SessionData] = {}

    def get_or_create(self, session_id: str, case_id: str) -> SessionData:
        key = f"{session_id}:{case_id}"
        if key not in self._sessions:
            self._sessions[key] = SessionData(case_id=case_id)
        return self._sessions[key]

    def get(self, session_id: str, case_id: str) -> Optional[SessionData]:
        return self._sessions.get(f"{session_id}:{case_id}")

    def save(self, session_id: str, case_id: str, data: SessionData) -> None:
        self._sessions[f"{session_id}:{case_id}"] = data

session_store = SessionStore()
