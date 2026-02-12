from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from ..auth import require
from ..services.asc740 import TempDiff, compute_deferred_tax, ai_tax_memo

# Router for tax-related endpoints
router = APIRouter(prefix="/tax", tags=["tax"])

# Pydantic models for input validation
class TempDiffIn(BaseModel):
    period: str
    amount: float
    reversal_year: int = Field(..., ge=2000, le=2100)

# Pydantic model for ASC 740 input
class Asc740In(BaseModel):
    company: str
    statutory_rate: float = Field(..., gt=0, lt=1)
    valuation_allowance_pct: float = Field(0, ge=0, le=1)
    differences: List[TempDiffIn]

# Endpoint to calculate deferred tax
@router.post("/asc740/calc")
@require(perms=["reports.memo"])
def calc(inp: Asc740In):
    diffs = [TempDiff(**d.model_dump()) for d in inp.differences]
    return compute_deferred_tax(diffs, inp.statutory_rate, inp.valuation_allowance_pct)

# Endpoint to generate AI tax memo
@router.post("/asc740/memo")
@require(perms=["reports.memo"])
def memo(inp: Asc740In):
    diffs = [TempDiff(**d.model_dump()) for d in inp.differences]
    res = compute_deferred_tax(diffs, inp.statutory_rate, inp.valuation_allowance_pct)
    return {"memo": ai_tax_memo(inp.company, res)}