from typing import Dict, Optional, List
import numpy as np, os, csv
def monthly_rate_from_annual(annual: float) -> float:
    return annual/12.0
def infer_monthly_irr(cashflows: List[float]) -> float:
    try:
        irr = np.irr(cashflows)
        return float(irr) if irr is not None else 0.0
    except Exception:
        return 0.0
def effective_interest_schedule(initial_carry: float, payments: Dict[str, float], annual_rate: Optional[float]=None) -> Dict[str, Dict[str, float]]:
    periods = sorted(payments.keys()); 
    if not periods:
        return {}
    pmts=[payments[p] for p in periods]
    r = monthly_rate_from_annual(annual_rate) if annual_rate is not None else infer_monthly_irr([-initial_carry] + pmts)
    bal = initial_carry
    out = {}
    for p in periods:
        interest = round(bal * r, 2); pay = float(payments[p]); bal = round(bal + interest - pay, 2)
        out[p] = {"interest": interest, "payment": pay, "closing_balance": bal, "monthly_rate": r}
    return out
def export_csv(path:str, schedule: Dict[str, Dict[str, float]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'w',newline='') as f:
        w=csv.writer(f); w.writerow(["Period","Interest","Payment","Closing_Balance","Monthly_Rate"])
        for p, row in sorted(schedule.items()): w.writerow([p, f"{row['interest']:.2f}", f"{row['payment']:.2f}", f"{row['closing_balance']:.2f}", f"{row['monthly_rate']:.6f}"])
    return path