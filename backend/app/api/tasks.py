from typing import Optional, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.models.plan import TaskItem, TaskImpact
from backend.app.services.session_store import session_store

router = APIRouter(prefix="/cases/{case_id}/tasks", tags=["Task List"])

class UpdateTaskRequest(BaseModel):
    # Parametros para actualizar una tarea existente
    status: Optional[Literal["pending", "in_progress", "completed"]] = None
    title: Optional[str] = None
    description: Optional[str] = None
    session_id: Optional[str] = "default"

class CreateTaskRequest(BaseModel):
    # Parametros para crear una tarea manualmente
    id: Optional[str] = None
    title: str
    description: str = ""
    week: int = 1
    category: Literal["debt", "savings", "investment", "insurance", "lifestyle"] = "savings"
    impact_metric: Optional[str] = None
    impact_value: Optional[str] = None
    session_id: Optional[str] = "default"

@router.get("", response_model=list[TaskItem])
def get_tasks(case_id: str, session_id: str = "default"):
    """Devuelve la lista actual de tareas interactivas para el caso seleccionado."""
    session = session_store.get_or_create(session_id, case_id)
    return session.tasks

@router.patch("/{task_id}", response_model=TaskItem)
def update_task(case_id: str, task_id: str, req: UpdateTaskRequest):
    """Actualiza el estado (ej: marcar como completada) o detalles de una tarea."""
    session = session_store.get_or_create(req.session_id or "default", case_id)
    target = None
    for t in session.tasks:
        if t.id == task_id:
            target = t
            break
    if not target:
        raise HTTPException(status_code=404, detail=f"Tarea '{task_id}' no encontrada.")
    
    if req.status:
        target.status = req.status
    if req.title:
        target.title = req.title
    if req.description:
        target.description = req.description

    return target

@router.post("", response_model=TaskItem)
def create_task(case_id: str, req: CreateTaskRequest):
    """Crea manualmente una nueva tarea en la lista."""
    session = session_store.get_or_create(req.session_id or "default", case_id)
    new_id = req.id or f"task_{len(session.tasks) + 1}"
    
    impact = None
    if req.impact_metric and req.impact_value:
        impact = TaskImpact(metric=req.impact_metric, value=req.impact_value)

    new_task = TaskItem(
        id=new_id,
        title=req.title,
        description=req.description,
        week=req.week,
        category=req.category,
        impact=impact
    )
    session.add_task(new_task)
    return new_task
