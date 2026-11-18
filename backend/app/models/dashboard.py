from typing import Any, Optional
from pydantic import BaseModel, Field

class DashboardMetric(BaseModel):
    # Metrica individual del panel financiero
    id: str
    label: str
    value: float | int | str
    formatted_value: str
    unit: str = "$"
    category: str = "general"
    status: Optional[str] = "neutral"  # success, warning, danger, neutral
    note: Optional[str] = None
    previous_value: Optional[float | int | str] = None

class DashboardSheetRow(BaseModel):
    # Fila generica para tablas o formato de hoja de calculo
    id: str
    concept: str
    current_value: float
    target_value: Optional[float] = None
    delta: Optional[float] = None
    frequency: str = "monthly"  # monthly, annual, one-time
    notes: Optional[str] = None

class DashboardState(BaseModel):
    # Estado global del dashboard financiero (agnostico y extensible)
    case_id: str
    health_score: int
    net_worth: float
    total_assets: float
    total_liabilities: float
    monthly_income: float
    monthly_expenses: float
    monthly_free_cashflow: float
    metrics: dict[str, DashboardMetric] = Field(default_factory=dict)
    sheet_data: list[DashboardSheetRow] = Field(default_factory=list)
    last_updated: Optional[str] = None
