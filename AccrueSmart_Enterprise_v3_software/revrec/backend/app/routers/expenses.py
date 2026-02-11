# backend/app/routers/expenses.py
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Any
from datetime import date
from ..services.ocr import extract_text  # add a small helper in ocr.py or reuse ingest
from ..services.expenses import classify_expense, amortize_prepaid
from ..authz import require

# Create a router for all "expenses" endpoints.
router = APIRouter(prefix="/expenses", tags=["expenses"])

#create endpoint for classify
@router.post("/classify")
@require(perms=["mods.edit"])
async def classify(payload: Dict[str,Any] = Body(...)):
    """
    payload = { text: "...", amount: 123.45 }
    """
    return classify_expense(payload.get("text",""), float(payload.get("amount",0.0)))

#create endpoint for prepaid/schedule
@router.post("/prepaid/schedule")
@require(perms=["mods.edit"])
async def prepaid(payload: Dict[str,Any] = Body(...)):
    """
    payload = { amount: 1200, months: 12, start: "2025-01-01" }
    """
    try:
        return {"schedule": amortize_prepaid(float(payload["amount"]), int(payload["months"]), date.fromisoformat(payload["start"]))}
    except Exception as e:
        raise HTTPException(400, str(e))
