from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.models.dashboard import DashboardState
from backend.app.services.session_store import session_store

router = APIRouter(prefix="/cases/{case_id}/dashboard", tags=["Dashboard"])

class UpdateMetricRequest(BaseModel):
    # Parametros para actualizar una metrica del dashboard
    metric_key: str
    value: float
    reason: Optional[str] = ""
    session_id: Optional[str] = "default"

@router.get("", response_model=Optional[DashboardState])
def get_dashboard(case_id: str, session_id: str = "default"):
    """Devuelve el estado actual de las metricas y la tabla o excel del dashboard."""
    session = session_store.get_or_create(session_id, case_id)
    return session.dashboard

@router.patch("", response_model=DashboardState)
def update_dashboard_metric(case_id: str, req: UpdateMetricRequest):
    """Actualiza una metrica o celda del dashboard."""
    session = session_store.get_or_create(req.session_id or "default", case_id)
    if not session.dashboard:
        raise HTTPException(status_code=400, detail="El dashboard aun no ha sido inicializado para este caso.")
    
    success = session.update_dashboard_metric(req.metric_key, req.value, req.reason or "")
    if not success:
        raise HTTPException(status_code=400, detail=f"No se pudo actualizar la metrica '{req.metric_key}'.")
    return session.dashboard
