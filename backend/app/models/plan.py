from typing import Optional, Literal
from pydantic import BaseModel, Field

class TaskImpact(BaseModel):
    # Metrica cuantificada y beneficio practico de una tarea
    metric: str = Field(description="Metrica sobre la que impacta, ej: Ahorro mensual, Deuda liquidada, Score")
    value: str = Field(description="Valor cuantitativo del impacto, ej: +$350/mes, -$18,000, +8 pts")
    emotional_benefit: Optional[str] = Field(default=None, description="Tranquilidad o alivio concreto para la familia")

class TaskItem(BaseModel):
    # Elemento individual de la lista de tareas
    id: str = Field(description="Identificador unico, ej: task_1")
    title: str = Field(description="Titulo claro de la accion concreta")
    description: str = Field(description="Pasos especificos para ejecutarla")
    week: int = Field(default=1, description="Semana asignada en el roadmap (1 a 4)")
    status: Literal["pending", "in_progress", "completed"] = "pending"
    category: Literal["debt", "savings", "investment", "insurance", "lifestyle"] = "savings"
    impact: Optional[TaskImpact] = None

class WeeklyRoadmap(BaseModel):
    # Bloque tematico semanal del plan de accion
    week_number: int
    theme: str = Field(description="Objetivo de la semana, ej: Detener la hemorragia de intereses")
    focus: str = Field(description="Enfoque principal en el que debe concentrarse la familia")
    task_ids: list[str] = Field(default_factory=list)

class ImmediateAction(BaseModel):
    # Accion inicial de entrada para romper la inercia en menos de 3 minutos
    title: str = Field(description="La primera accion que deben realizar hoy")
    reason: str = Field(description="Por que esta accion desbloquea el resto del plan")
    instructions: list[str] = Field(default_factory=list, description="Pasos exactos a seguir")
    expected_impact: str = Field(description="Impacto inmediato esperado")

class MasterPlan(BaseModel):
    # Plan global sintetizado por el inicializador maestro
    case_id: str
    headline: str = Field(description="Titular motivador personalizado")
    immediate_action: ImmediateAction
    weekly_roadmap: list[WeeklyRoadmap] = Field(default_factory=list)
    tasks: list[TaskItem] = Field(default_factory=list)
