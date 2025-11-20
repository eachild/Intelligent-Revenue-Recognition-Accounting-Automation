# backend/app/services/costs.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Literal, Optional
from dateutil.relativedelta import relativedelta

Method = Literal["straight_line", "percent_complete", "custom_curve"]

@dataclass
class CostRow:
    period: int
    date: str
    opening: float
    amortization: float
    closing: float

def _month_list(start: date, months: int) -> List[date]:
    return [start + relativedelta(months=i) for i in range(months)]

def amortize_cost(
    total: float,
    months: int,
    start: date,
    method: Method = "straight_line",
    percent_complete: Optional[List[float]] = None,
    curve: Optional[List[float]] = None,
) -> Dict[str, object]:
    """
    ASC 340-40 costs amortization.
    - straight_line: equal amortization per month
    - percent_complete: weights from percent_complete list (len=months)
    - custom_curve: arbitrary weights list (len=months)
    Returns: { rows: [CostRow...], total_amortization, method }
    """
    if months <= 0:
        raise ValueError("months must be > 0")
    if total < 0:
        raise ValueError("total must be >= 0")

    if method == "straight_line":
        weights = [1] * months
    elif method == "percent_complete":
        if not percent_complete or len(percent_complete) != months:
            raise ValueError("percent_complete must be length == months")
        weights = percent_complete
    elif method == "custom_curve":
        if not curve or len(curve) != months:
            raise ValueError("curve must be length == months")
        weights = curve
    else:
        raise ValueError("invalid method")

    weight_sum = float(sum(weights))
    if weight_sum <= 0:
        raise ValueError("weights must sum > 0")

    schedule: List[CostRow] = []
    remaining = float(total)
    dates = _month_list(start, months)
    # compute raw amort amounts by weights, then fix rounding drift on last row
    raw = [(w / weight_sum) * total for w in weights]
    # round to cents
    rounded = [round(x, 2) for x in raw]
    drift = round(total - sum(rounded), 2)
    if drift != 0:
        rounded[-1] = round(rounded[-1] + drift, 2)

    for i, (dt, amt) in enumerate(zip(dates, rounded), start=1):
        opening = remaining
        amort = min(opening, amt)
        remaining = round(opening - amort, 2)
        schedule.append(
            CostRow(
                period=i,
                date=dt.isoformat()[:7],
                opening=round(opening, 2),
                amortization=round(amort, 2),
                closing=round(remaining, 2),
            )
        )

    return {
        "method": method,
        "rows": [r.__dict__ for r in schedule],
        "total_amortization": round(sum(r.amortization for r in schedule), 2),
    }