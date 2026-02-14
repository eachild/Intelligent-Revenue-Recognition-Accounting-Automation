# backend/app/routers/leases.py
from fastapi import APIRouter, Request, HTTPException
from ..auth import require
from ..services.leases import compute_schedule, export_lease_journals_csv

# Router for lease-related endpoints
router = APIRouter(prefix="/leases", tags=["leases"])

# Endpoint to compute lease schedule
@router.post("/schedule")
@require(perms=["leases.edit"])
async def schedule(request: Request):
    body = await request.json()
    try:
        return compute_schedule(**body)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Bad payload: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to export lease journals as CSV
@router.post("/export/journals")
@require(perms=["leases.export"])
async def export_journals(request: Request):
    body = await request.json()
    try:
        csv_data = export_lease_journals_csv(body)
        return {"filename": "lease_journals.csv", "content": csv_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))