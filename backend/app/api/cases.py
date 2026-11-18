from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.models.case import CaseSummary, CaseFull
from backend.app.services.case_repository import case_repo

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("", response_model=list[CaseSummary])
async def list_cases():
    """Lista todos los casos disponibles consultando directamente al servidor MCP."""
    try:
        return await case_repo.list_cases()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error consultando listado en el servidor MCP: {str(e)}")

@router.get("/{case_id}", response_model=CaseFull)
async def get_case(case_id: str):
    """Obtiene el caso completo a traves del servidor MCP."""
    try:
        return await case_repo.get_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error obteniendo caso '{case_id}' desde el servidor MCP: {str(e)}")

@router.get("/{case_id}/section")
async def get_case_section(
    case_id: str,
    part: str = Query(..., description="Parte del caso: financial-health, investment-analysis o persona"),
    section: Optional[str] = Query(None, description="Seccion especifica (opcional)")
):
    """Obtiene una seccion especifica bajo demanda consultando al servidor MCP."""
    try:
        data = await case_repo.get_case_section(case_id, part, section)
        return {"case_id": case_id, "part": part, "section": section, "data": data}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error consultando seccion en el servidor MCP: {str(e)}")
