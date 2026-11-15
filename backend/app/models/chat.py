from typing import Any, Optional, Literal
from pydantic import BaseModel, Field
from backend.app.models.plan import TaskItem
from backend.app.models.dashboard import DashboardState

class ChatMessage(BaseModel):
    # Mensaje individual dentro del historial de conversacion
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_calls: Optional[list[dict[str, Any]]] = None

class ToolExecutionLog(BaseModel):
    # Registro de una herramienta ejecutada por el agente
    tool: str
    args: dict[str, Any]
    result: Any

class ChatRequest(BaseModel):
    # Peticion de mensaje enviada desde el frontend
    message: str
    case_id: str
    session_id: Optional[str] = "default"
    history: Optional[list[dict[str, str]]] = None

class ChatResponse(BaseModel):
    # Respuesta completa del Co-Pilot incluyendo cambios en el estado
    reply: str
    tools_executed: list[ToolExecutionLog] = Field(default_factory=list)
    tasks: Optional[list[TaskItem]] = None
    dashboard: Optional[DashboardState] = None
    chart_to_render: Optional[dict[str, Any]] = None
