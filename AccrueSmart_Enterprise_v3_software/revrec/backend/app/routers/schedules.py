"""
backend/app/routers/schedules.py
Schedule grid endpoints: load, save, CSV import/export, AI generate.
"""
from __future__ import annotations
import csv
import io
from datetime import date
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from ..auth import require
from ..services.schedules_crud import get_grid, save_grid
from ..schedule_logic import straight_line

router = APIRouter(prefix="/schedules", tags=["schedules"])


# ── Grid CRUD ───────────────────────────────────────────────────

@router.get("/grid/{contract_id}")
@require(perms=["revrec.manage"])
async def load_grid(contract_id: str):
    return get_grid(contract_id)


@router.post("/grid/{contract_id}")
@require(perms=["revrec.manage"])
async def save_grid_endpoint(contract_id: str, payload: dict):
    rows = payload.get("rows", [])
    return save_grid(contract_id, rows)


# ── CSV Export ──────────────────────────────────────────────────

@router.get("/grid/{contract_id}/export/csv")
@require(perms=["revrec.export"])
async def export_csv(contract_id: str):
    rows = get_grid(contract_id)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["line_no", "period", "amount", "product_code", "revrec_code"])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={contract_id}_schedule.csv"},
    )


# ── CSV Import ──────────────────────────────────────────────────

@router.post("/grid/{contract_id}/import/csv")
@require(perms=["revrec.manage"])
async def import_csv(contract_id: str, file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    for i, row in enumerate(reader):
        rows.append({
            "line_no": int(row.get("line_no", i + 1)),
            "period": row.get("period", ""),
            "amount": float(row.get("amount", 0)),
            "product_code": row.get("product_code", ""),
            "revrec_code": row.get("revrec_code", ""),
            "source": "csv",
        })
    return save_grid(contract_id, rows)


# ── AI Generate ─────────────────────────────────────────────────

@router.post("/ai-generate")
@require(perms=["revrec.manage"])
async def ai_generate(payload: dict):
    """
    Generate a straight-line schedule from contract hints.
    Accepts: { contract_id, text, default_start, line_hints: [{product_code, amount}] }
    Returns: { schedule: { "YYYY-MM": amount, ... } }
    """
    contract_id = payload.get("contract_id", "")
    default_start = payload.get("default_start", "")
    line_hints = payload.get("line_hints", [])
    # text = payload.get("text", "")  # reserved for future LLM integration

    if not default_start:
        raise HTTPException(400, "default_start is required (YYYY-MM-DD)")

    # Sum up all line hint amounts
    total = sum(float(h.get("amount", 0)) for h in line_hints)
    if total <= 0:
        raise HTTPException(400, "line_hints must have positive amounts")

    # Default: 12-month straight-line from default_start
    start = date.fromisoformat(default_start)
    end_date = date(start.year + 1, start.month, 1) if start.month <= 12 else date(start.year + 1, 12, 1)
    # 12 months from start
    from ..util import add_months
    end_date = add_months(start, 11)

    schedule = straight_line(total, start, end_date)

    return {"contract_id": contract_id, "schedule": schedule}
