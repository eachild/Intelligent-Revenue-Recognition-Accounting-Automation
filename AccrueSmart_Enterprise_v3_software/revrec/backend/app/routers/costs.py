# backend/app/routers/costs.py
from __future__ import annotations
from datetime import date
from typing import List, Optional, Literal, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, conlist, confloat
from ..authz import require  # uses your decorator-based enforcement
from ..services.costs import amortize_cost

router = APIRouter(prefix="/costs", tags=["costs"])

Method = Literal["straight_line", "percent_complete", "custom_curve"]

class CostsIn(BaseModel):
    total: confloat(ge=0) = Field(..., example=2400.0)
    months: int = Field(..., gt=0, example=24)
    start: str = Field(..., example="2025-01-01")
    method: Method = Field("straight_line")
    percent_complete: Optional[conlist(confloat(ge=0), min_items=1)] = None
    curve: Optional[conlist(confloat(ge=0), min_items=1)] = None

@router.post("/amortize")
@require(perms=["costs.run"])  # add this perm in schema below
def amortize(body: CostsIn) -> Dict[str, Any]:
    try:
        res = amortize_cost(
            total=float(body.total),
            months=int(body.months),
            start=date.fromisoformat(body.start),
            method=body.method,
            percent_complete=body.percent_complete,
            curve=body.curve,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))