
from typing import Dict
from datetime import date
from .engine import add_months

def expected_returns_adjustment(point_in_time_revenue: float, returns_rate: float) -> Dict[str, float]:
    returns_contra_revenue = round(point_in_time_revenue * returns_rate, 2)
    refund_liability = returns_contra_revenue
    returns_asset = round(returns_contra_revenue * 0.6, 2)  # teaching placeholder for cost
    return {"contra_revenue": returns_contra_revenue, "refund_liability": refund_liability, "returns_asset": returns_asset}

def loyalty_liability_allocation(transaction_price: float, loyalty_pct: float) -> float:
    return round(transaction_price * loyalty_pct, 2)

def loyalty_recognition_schedule(loyalty_liability: float, start: date, months: int, breakage_rate: float) -> Dict[str, float]:
    months_list=[add_months(start,i) for i in range(months)]
    expected_redeemed=loyalty_liability*(1-breakage_rate)
    per=round(expected_redeemed/max(1,len(months_list)),2)
    sched={f"{d.year}-{d.month:02d}":per for d in months_list}
    last=f"{months_list[-1].year}-{months_list[-1].month:02d}"
    sched[last]=round(expected_redeemed - sum(v for k,v in sched.items() if k!=last),2)
    return sched
