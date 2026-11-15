from typing import Any, Optional
from pydantic import BaseModel, Field

class HouseholdMember(BaseModel):
    # Miembro individual del hogar familiar
    first_name: str
    role: str
    age: Optional[int] = None

class CaseScore(BaseModel):
    # Puntuacion de salud financiera asignada por Sherpas
    published_score: int = Field(default=0)
    band: Optional[str] = None
    interpretation: Optional[str] = None

class CaseSummary(BaseModel):
    # Resumen basico del caso para listados iniciales
    id: str
    title: str
    city: Optional[str] = None
    score: int
    household: list[HouseholdMember] = Field(default_factory=list)
    short_description: str = ""

class CaseFull(BaseModel):
    # Informacion completa del caso incluyendo los dos JSONs y persona.md
    id: str
    summary: CaseSummary
    financial_health: dict[str, Any]
    investment_analysis: dict[str, Any]
    persona_markdown: str
