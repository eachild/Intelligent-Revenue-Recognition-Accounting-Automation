from fastapi import APIRouter, Request
from ..auth import require
from ..services.auditor import summarize_audit

# Router for auditor-related endpoints
router = APIRouter(prefix="/auditor", tags=["auditor"])

# Endpoint to summarize audit findings
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