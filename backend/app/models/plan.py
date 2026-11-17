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
    title: str = Field(description="Titulo claro de la accion concreta (sin prefijos de categoria ni corchetes)")
    short_description: str = Field(default="", description="Descripcion breve concisa de 1 linea para la vista previa")
    detailed_description: str = Field(default="", description="Explicacion detallada y extendida accesible al hacer click")
    description: str = Field(default="", description="Pasos especificos para ejecutarla de forma comprensible para no expertos")
    week: int = Field(default=1, description="Semana asignada en el roadmap (1 a 4)")
    status: Literal["pending", "in_progress", "completed"] = "pending"
    category: Literal["debt", "savings", "investment", "insurance", "lifestyle", "immediate", "goal", "general"] = "savings"
    impact: Optional[TaskImpact] = None
    steps: list[str] = Field(default_factory=list, description="Lista de pasos secuenciales para ejecutar la tarea")

class ActionBox(BaseModel):
    # Tarjeta de accion estructurada para la interfaz visual
    title: str = Field(description="Titulo limpio y conciso de la accion")
    category: Literal["goal", "immediate", "debt", "savings", "investment", "insurance", "lifestyle", "alerta", "general"] = "general"
    short_description: str = Field(default="", description="Descripcion breve concisa de 1 linea")
    detailed_description: str = Field(default="", description="Explicacion detallada y contexto extendido")
    description: str = Field(default="", description="Explicacion clara y accesible del motivo o procedimiento")
    impact: str = Field(default="", description="Impacto cuantificado conciso (ej: +$500/mes, +2 pts)")
    week: Optional[int] = Field(default=None, description="Semana asignada (1 a 4) si aplica")
    steps: list[str] = Field(default_factory=list, description="Lista secuencial de pasos a realizar")
    content: str = Field(default="", description="Alias retrocompatible de description")

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
