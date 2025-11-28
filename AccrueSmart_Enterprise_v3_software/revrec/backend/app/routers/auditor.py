"""
# backend/app/routers/auditor.py
Add this line to main.py:
from .routers import auditor
app.include_router(auditor.router)
"""
from fastapi import APIRouter, Request
from app.auth import require
from ..services.auditor import summarize_audit

router = APIRouter(prefix="/auditor", tags=["auditor"])

@router.post("/summary")
@require(perms=["reports.memo"])
async def summary(request: Request):
    payload = await request.json()
    """
    payload may include:
      {
        "revrec": {...},
        "leases": {...},
        "tax": {...},
        "forecast": {...}
      }
    """
    return summarize_audit(payload)