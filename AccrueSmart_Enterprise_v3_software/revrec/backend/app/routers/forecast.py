"""
backend/app/routers/forecast.py
Wire it up in backend/app/main.py:
from .routers import forecast   # add import
app.include_router(forecast.router)
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional
from ..auth import require
from ..services.forecast import forecast_revenue

# Router for forecast-related endpoints
router = APIRouter(prefix="/forecast", tags=["forecast"])

# Pydantic model for forecast input
class ForecastIn(BaseModel):
    history: Dict[str, float]  # {"2024-01": 10000, ...}
    horizon: int = Field(12, ge=1, le=60)
    method: Literal["exp_smooth","seasonal_ma"] = "exp_smooth"
    alpha: Optional[float] = Field(0.35, ge=0.01, le=0.99)
    season: Optional[int] = Field(12, ge=2, le=24)

# Endpoint to forecast revenue
@router.post("/revenue")
@require(perms=["revrec.export"])  # or a new "forecast.run" perm if you add it
def forecast(inp: ForecastIn):
    kwargs = {}
    if inp.method == "exp_smooth":
        kwargs["alpha"] = inp.alpha
    else:
        kwargs["season"] = inp.season
    return forecast_revenue(inp.history, inp.horizon, method=inp.method, **kwargs)