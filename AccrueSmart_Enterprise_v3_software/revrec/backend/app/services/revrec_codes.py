"""
backend/app/services/revrec_codes.py
Rule engines that produce schedules for a line item. Reuse your month key "YYYY-MM" format.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from datetime import date

def _to_ym(dt: date) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"

def _month_add(d: date, m: int) -> date:
    y = d.year + (d.month - 1 + m)//12
    mo = (d.month - 1 + m) % 12 + 1
    day = min(d.day, 28)  # keep simple for months
    return date(y, mo, day)

@dataclass
class LineItem:
    product_code: str
    revrec_code: str
    amount: float
    # optional overrides:
    start_date: str | None = None     # "2025-01-01"
    end_date: str | None = None
    recognition_date: str | None = None
    usage_curve: Dict[str, float] | None = None  # {"2025-01":0.1, ...}
    milestones: Dict[str, float] | None = None   # {"M1":0.4, "M2":0.6}
    percent_complete: Dict[str, float] | None = None # {"2025-01":0.2, ...}

def straight_line(amount: float, start: date, months: int) -> Dict[str, float]:
    per = round(amount / months, 2)
    sched: Dict[str, float] = {}
    for i in range(months):
        dt = _month_add(start, i)
        key = _to_ym(dt)
        sched[key] = sched.get(key, 0.0) + per
    # fix rounding penny drift
    diff = round(amount - sum(sched.values()), 2)
    if abs(diff) >= 0.01:
        last_key = _to_ym(_month_add(start, months-1))
        sched[last_key] = round(sched[last_key] + diff, 2)
    return sched

def point_in_time(amount: float, on: date) -> Dict[str, float]:
    return {_to_ym(on): round(amount, 2)}

def usage_based(amount: float, curve: Dict[str, float]) -> Dict[str, float]:
    # curve holds percentages per month summing ~1.0
    sched: Dict[str, float] = {}
    for k, pct in curve.items():
        sched[k] = round(amount * float(pct), 2)
    # normalize rounding
    diff = round(amount - sum(sched.values()), 2)
    if abs(diff) >= 0.01 and sched:
        last = sorted(sched.keys())[-1]
        sched[last] = round(sched[last] + diff, 2)
    return sched

def milestone_based(amount: float, weights: Dict[str, float], month_map: Dict[str, str]) -> Dict[str, float]:
    # weights like {"M1":0.4,"M2":0.6}, month_map like {"M1":"2025-03","M2":"2025-06"}
    out: Dict[str, float] = {}
    for ms, w in weights.items():
        ym = month_map.get(ms)
        if not ym:
            continue
        out[ym] = round(out.get(ym, 0.0) + amount*float(w), 2)
    diff = round(amount - sum(out.values()), 2)
    if abs(diff) >= 0.01 and out:
        last = sorted(out.keys())[-1]
        out[last] = round(out[last] + diff, 2)
    return out

def percent_complete_rule(total_txn_price: float, pct_by_month: Dict[str, float]) -> Dict[str, float]:
    # pct_by_month contains monthly incremental percent complete (not cumulative)
    out: Dict[str, float] = {}
    for ym, pct in pct_by_month.items():
        out[ym] = round(total_txn_price * float(pct), 2)
    diff = round(total_txn_price - sum(out.values()), 2)
    if abs(diff) >= 0.01 and out:
        last = sorted(out.keys())[-1]
        out[last] = round(out[last] + diff, 2)
    return out

def apply_rule(rule_type: str, params: Dict[str, Any], li: LineItem) -> Dict[str, float]:
    if rule_type == "straight_line":
        months = int(params.get("months") or 12)
        start = date.fromisoformat(params.get("start_date") or (li.start_date or "2025-01-01"))
        return straight_line(li.amount, start, months)
    if rule_type == "point_in_time":
        on = date.fromisoformat(params.get("recognition_date") or li.recognition_date or "2025-01-15")
        return point_in_time(li.amount, on)
    if rule_type == "usage":
        curve = li.usage_curve or params.get("curve") or {}
        return usage_based(li.amount, curve)
    if rule_type == "milestone":
        weights = params.get("weights") or (li.milestones or {})
        month_map = params.get("month_map") or {}
        return milestone_based(li.amount, weights, month_map)
    if rule_type == "percent_complete":
        pct = params.get("pct_by_month") or (li.percent_complete or {})
        return percent_complete_rule(li.amount, pct)
    raise ValueError(f"Unknown rule_type: {rule_type}")