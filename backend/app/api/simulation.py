"""Endpoints de simulacion What-If y generacion de informes de sesion.
"""
import re
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.services.simulation_engine import (
    ScenarioParams,
    SimulationResult,
    run_scenario_simulation,
    get_case_preset_scenarios
)
from backend.app.services.session_store import session_store
from backend.app.services.case_repository import case_repo
from backend.app.services.report_generator import generate_client_handover_report

router = APIRouter(prefix="/cases/{case_id}", tags=["Simulation & Reports"])


class CustomSimulationRequest(BaseModel):
    scenario_name: Optional[str] = "Escenario personalizado"
    params: ScenarioParams
    session_id: Optional[str] = "default"


@router.get("/scenarios")
async def get_preset_scenarios(case_id: str):
    """Devuelve los presets de simulacion recomendados especificos para el caso."""
    try:
        presets = get_case_preset_scenarios(case_id)
        return {"case_id": case_id, "presets": presets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo presets: {str(e)}")


@router.post("/simulate", response_model=SimulationResult)
async def simulate_case_scenario(case_id: str, request: CustomSimulationRequest):
    """Ejecuta una simulacion matematica de impacto What-If sobre el caso."""
    session = session_store.get_or_create(request.session_id or "default", case_id)

    # Obtener valores base desde el dashboard o desde el repositorio de casos
    income = 15000.0
    expenses = 9000.0
    debt = 25000.0
    net_worth = 200000.0
    score = 50

    if session.dashboard:
        db = session.dashboard
        income = db.monthly_income
        expenses = db.monthly_expenses
        debt = db.total_liabilities
        net_worth = db.net_worth
        score = db.health_score
    else:
        try:
            raw_case = await case_repo.get_case(case_id)
            fh = raw_case.financial_health or {}
            prof = fh.get("profile", {})
            score = fh.get("score", {}).get("published_score", score)
            km = fh.get("key_metrics", {})
            net_worth = float(km.get("net_worth") or net_worth)
            debt = float(km.get("total_liabilities") or debt)
            incomes = prof.get("incomes", [])
            exps = prof.get("expenses", [])
            if incomes:
                income = sum(float(i.get("yearly", 0)) / 12 for i in incomes)
            if exps:
                expenses = sum(float(e.get("monthly", 0)) or (float(e.get("yearly", 0)) / 12) for e in exps)
        except Exception:
            pass

    try:
        result = run_scenario_simulation(
            case_id=case_id,
            base_income=income,
            base_expenses=expenses,
            base_debt=debt,
            base_net_worth=net_worth,
            base_score=score,
            params=request.params,
            scenario_name=request.scenario_name or "Simulacion personalizada"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando simulacion: {str(e)}")


@router.get("/report")
async def get_handover_report(case_id: str, session_id: str = "default"):
    """Genera el informe ejecutivo para entrega al cliente y reunion con el asesor."""
    try:
        report = await generate_client_handover_report(case_id=case_id, session_id=session_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando informe: {str(e)}")


def _parse_persona_insights(persona_markdown: str) -> dict[str, Any]:
    """Extrae las dimensiones clave de persona.md de forma dinamica sin hardcoding."""
    sections: dict[str, list[str]] = {}
    current_header = None
    for line in (persona_markdown or "").split("\n"):
        if line.startswith("## "):
            current_header = line.replace("## ", "").strip()
            sections[current_header] = []
        elif current_header:
            sections[current_header].append(line)

    sec_map = {k: "\n".join(v).strip() for k, v in sections.items()}

    # Extraer wealth tier
    wealth_tier = sec_map.get("D0: Wealth tier", "Emergente").split(".")[0].strip()
    if not wealth_tier:
        wealth_tier = "Emergente"

    # Extraer risk profile
    risk_raw = sec_map.get("D4: Risk orientation", "Moderado").split("\n")[0].strip()
    risk_profile = re.sub(r"^[*-]\s*(\*\*D4a stated:\*\*)?\s*", "", risk_raw).strip()

    # Extraer decision style
    decision_raw = sec_map.get("D5: Decision-making style", "Analitico").split("\n")[0].strip()
    decision_style = re.sub(r"^[*-]\s*", "", decision_raw).strip()

    # Extraer tension principal
    tension_raw = sec_map.get("Tensions", "Alineacion de objetivos patrimoniales").split("\n")[0].strip()
    primary_tension = re.sub(r"^[*-]\s*(\*\*T\d+[^:]*:\*\*)?\s*", "", tension_raw).strip()

    # Extraer arquetipo motivacional
    anchor_raw = sec_map.get("D6: Motivational anchor", "Orientado a la seguridad").split("\n")[0].strip()
    emotional_archetype = re.sub(r"^[*-]\s*", "", anchor_raw).strip()

    # Extraer alertas clave desde Transition alerts y Objective concerns
    alerts = []
    combined_alerts_text = sec_map.get("Transition alerts", "") + "\n" + sec_map.get("Objective concerns", "")
    for bullet in re.findall(r"^[*-]\s+(.+)", combined_alerts_text, re.MULTILINE):
        clean_b = re.sub(r"[*_#]", "", bullet).strip()
        if clean_b and len(clean_b) > 8:
            alerts.append(clean_b[:140])

    return {
        "wealth_tier": wealth_tier,
        "risk_profile": risk_profile or "Moderado",
        "decision_style": decision_style or "Analitico",
        "primary_tension": primary_tension or "Optimizacion financiera global",
        "emotional_archetype": emotional_archetype or "Estabilidad patrimonial",
        "key_alerts": alerts[:4]
    }


@router.get("/persona-insights")
async def get_persona_insights(case_id: str):
    """Extrae las dimensiones clave de persona.md de forma dinamica."""
    try:
        raw_case = await case_repo.get_case(case_id)
        persona_text = raw_case.persona_markdown or ""
        parsed = _parse_persona_insights(persona_text)

        insights = {
            "case_id": case_id,
            "title": raw_case.summary.title if raw_case.summary else case_id,
            "city": raw_case.summary.city if raw_case.summary else "",
            **parsed
        }
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo insights: {str(e)}")
