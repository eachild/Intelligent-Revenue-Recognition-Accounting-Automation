# backend/app/routers/locks.py
from __future__ import annotations
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from ..auth import require
from ..auth import build_principal  # gives sub/email from Supabase JWT
from ..services.locks import save_lock, get_lock_status

router = APIRouter(prefix="/locks", tags=["locks"])

class LockIn(BaseModel):
    contract_id: str = Field(..., example="C-1001")
    schedule: Dict[str, Any] = Field(..., description="Full schedule JSON to hash")
    note: Optional[str] = Field(None, example="Month-end close 2025-01")

@router.post("/schedule")
@require(perms=["schedules.approve"])
async def lock_schedule(request: Request, payload: LockIn):
    try:
        principal = await build_principal(request)
        res = save_lock(
            contract_id=payload.contract_id,
            schedule=payload.schedule,
            approver_sub=principal.get("sub", ""),
            approver_email=principal.get("email"),
            note=payload.note,
        )
        return {"ok": True, "lock": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schedule/status")
@require(perms=["deal.view","revrec.export"])  # any of these ok to view
async def status(contract_id: str):
    return get_lock_status(contract_id)