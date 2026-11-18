"""API endpoints for Kanban board state and card management.
"""
from typing import Optional, Literal, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import kanban_store as ks

router = APIRouter(prefix="/cases/{case_id}/kanban", tags=["Kanban Board"])


class ArrangeCardRequest(BaseModel):
    card_id: Optional[str] = None
    to_status: Optional[Literal["todo", "in_process", "done"]] = None
    to_index: Optional[int] = 0
    layout: Optional[dict[str, list[str]]] = None


class AddCardRequest(BaseModel):
    title: str
    category: str = "general"
    short_description: str = ""
    detailed_description: str = ""
    impact: str = ""
    week: Optional[int] = 1
    steps: list[str] = Field(default_factory=list)
    status: Literal["todo", "in_process", "done"] = "todo"


class UpdateCardRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    impact: Optional[str] = None
    week: Optional[int] = None
    steps: Optional[list[str]] = None
    status: Optional[Literal["todo", "in_process", "done"]] = None


@router.get("")
def get_kanban(case_id: str):
    """Devuelve las tarjetas y columnas del tablero Kanban para el caso."""
    try:
        ks.set_case(case_id)
        data = ks.load(case_id)
        return {
            "case_id": case_id,
            "version": ks.version(case_id),
            "statuses": ks.STATUSES,
            "cards": data.get("cards", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando kanban: {str(e)}")


@router.post("/arrange")
def arrange_card(case_id: str, req: ArrangeCardRequest):
    """Mueve una tarjeta de columna o posicion."""
    try:
        ks.set_case(case_id)

        # Si se envio un layout completo de drag-and-drop
        if req.layout is not None:
            updated = ks.arrange(req.layout, case_id=case_id)
            return {
                "success": True,
                "version": ks.version(case_id),
                "cards": updated.get("cards", [])
            }

        # Si se envio card_id y to_status
        if req.card_id and req.to_status:
            data = ks.load(case_id)
            card = ks._find(data, req.card_id)
            card["status"] = req.to_status
            data["cards"].remove(card)

            # Insertar en la posicion correspondiente si to_index esta indicado
            if req.to_index is not None and req.to_index >= 0:
                same_status_indices = [i for i, c in enumerate(data["cards"]) if c.get("status") == req.to_status]
                if req.to_index < len(same_status_indices):
                    insert_idx = same_status_indices[req.to_index]
                    data["cards"].insert(insert_idx, card)
                else:
                    data["cards"].append(card)
            else:
                data["cards"].append(card)

            updated = ks.save(data, case_id=case_id)
            return {
                "success": True,
                "version": ks.version(case_id),
                "cards": updated.get("cards", [])
            }

        raise HTTPException(status_code=400, detail="Debe proporcionar layout o (card_id y to_status)")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reorganizando tarjeta: {str(e)}")


@router.post("/cards")
def add_card(case_id: str, req: AddCardRequest):
    """Anade una nueva tarjeta al tablero."""
    try:
        ks.set_case(case_id)
        saved_data = ks.add_card(
            title=req.title,
            status=req.status,
            short_description=req.short_description,
            detailed_description=req.detailed_description or req.short_description,
            category=req.category,
            impact=req.impact,
            week=req.week,
            steps=req.steps,
            case_id=case_id
        )
        new_card = saved_data.get("cards", [])[-1] if saved_data.get("cards") else None
        return {
            "success": True,
            "card": new_card,
            "version": ks.version(case_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando tarjeta: {str(e)}")


@router.patch("/cards/{card_id}")
def update_card(case_id: str, card_id: str, req: UpdateCardRequest):
    """Actualiza campos de una tarjeta existente."""
    try:
        ks.set_case(case_id)
        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        saved_data = ks.update_card(card_id, **fields, case_id=case_id)
        updated_card = ks._find(saved_data, card_id)
        return {
            "success": True,
            "card": updated_card,
            "version": ks.version(case_id)
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando tarjeta: {str(e)}")


@router.delete("/cards/{card_id}")
def delete_card(case_id: str, card_id: str):
    """Elimina una tarjeta del tablero."""
    try:
        ks.set_case(case_id)
        ks.delete_card(card_id, case_id=case_id)
        return {
            "success": True,
            "deleted_id": card_id,
            "version": ks.version(case_id)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error borrando tarjeta: {str(e)}")
