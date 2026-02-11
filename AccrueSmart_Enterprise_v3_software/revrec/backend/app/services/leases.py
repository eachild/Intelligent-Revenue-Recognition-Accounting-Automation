# backend/app/services/leases.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple
from datetime import date
import math
import csv
import io

# Frequency type for lease payments
Freq = Literal["monthly", "quarterly", "annual"]

# Helper functions for date and period calculations
def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + (0 if end.day < start.day else 0)

# Function to add months to a date
def _add_months(d: date, n: int) -> date:
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    last_day = 28
    for day in (31, 30, 29, 28):
        try:
            return date(y, m, min(d.day, day))
        except ValueError:
            last_day = day
    return date(y, m, last_day)

# Function to calculate number of periods between two dates based on frequency
def _periods(start: date, end: date, freq: Freq) -> int:
    months = _months_between(start, end) + 1  # inclusive-like
    if freq == "monthly":
        return months
    if freq == "quarterly":
        return math.ceil(months / 3)
    return math.ceil(months / 12)

# Function to get the date of the i-th period based on frequency
def _period_date_idx(start: date, i: int, freq: Freq) -> date:
    if freq == "monthly":
        return _add_months(start, i)
    if freq == "quarterly":
        return _add_months(start, i * 3)
    return _add_months(start, i * 12)

# Data class for lease inputs
@dataclass
class LeaseInputs:
    lease_id: str
    start_date: date
    end_date: date
    payment: float
    frequency: Freq
    discount_rate_annual: float
    initial_direct_costs: float = 0.0
    incentives: float = 0.0
    cpi_escalation_pct: float = 0.0  # optional: % increase per year
    cpi_escalation_month: int = 12   # apply every X months (default annually)

# Function to calculate periodic discount rate
def _period_rate(dr_annual: float, freq: Freq) -> float:
    if freq == "monthly":
        return dr_annual / 12.0
    if freq == "quarterly":
        return dr_annual / 4.0
    return dr_annual

# Function to calculate payment amount for a given period with CPI escalation
def _payment_for_period(base_payment: float, i: int, freq: Freq, cpi_pct: float, interval: int) -> float:
    if cpi_pct <= 0:
        return base_payment
    # apply step-up every `interval` months of actual time
    if freq == "monthly":
        bumps = i // interval
    elif freq == "quarterly":
        bumps = (i * 3) // interval
    else:
        bumps = (i * 12) // interval
    return base_payment * ((1.0 + cpi_pct) ** bumps)

# Function to compute lease schedule
def compute_schedule(
    lease_id: str,
    start_date: str,
    end_date: str,
    payment: float,
    frequency: Freq,
    discount_rate_annual: float,
    idc: float = 0.0,
    incentives: float = 0.0,
    cpi_escalation_pct: float = 0.0,
    cpi_escalation_month: int = 12,
) -> Dict:
    """
    Returns a dictionary ready to serialize:
      {
        "lease_id": str,
        "rows": [ ... ],
        "total_interest": float,
        "total_payments": float,
        "opening_liability": float,
        "opening_rou_asset": float
      }
    """
    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date)
    n = _periods(sd, ed, frequency)
    r = _period_rate(discount_rate_annual, frequency)

    # PV of future payments (w/ optional CPI escalations)
    pv = 0.0
    for i in range(n):
        amt = _payment_for_period(payment, i, frequency, cpi_escalation_pct, cpi_escalation_month)
        pv += amt / ((1 + r) ** (i + 1))
    opening_liability = round(pv, 2)
    opening_rou_asset = round(pv + idc - incentives, 2)
    rows: List[Dict] = []
    liability = opening_liability
    rou = opening_rou_asset
    total_interest = 0.0
    total_payments = 0.0

    # Build schedule rows
    for i in range(n):
        dt = _period_date_idx(sd, i, frequency)
        pmt = _payment_for_period(payment, i, frequency, cpi_escalation_pct, cpi_escalation_month)
        interest = liability * r
        principal = pmt - interest
        liability = max(0.0, liability - principal)

        # straight-line ROU amortization by periods
        rou_amort = opening_rou_asset / n
        rou = max(0.0, rou - rou_amort)

        # Append row data for the current period
        rows.append({
            "period": i + 1,
            "date": dt.isoformat(),
            "payment": round(pmt, 2),
            "interest": round(interest, 2),
            "principal": round(principal, 2),
            "ending_liability": round(liability, 2),
            "rou_amortization": round(rou_amort, 2),
            "rou_carrying_amount": round(rou, 2),
        })
        total_interest += interest
        total_payments += pmt
    
    # Return the complete schedule dictionary
    return {
        "lease_id": lease_id,
        "rows": rows,
        "total_interest": round(total_interest, 2),
        "total_payments": round(total_payments, 2),
        "opening_liability": opening_liability,
        "opening_rou_asset": opening_rou_asset,
    }

# Function to build lease journals from schedule
def journals_from_schedule(lease_id: str, sched: Dict) -> List[Dict]:
    """
    Build period journals:
      Dr Lease Interest Expense
      Dr ROU Amortization Expense
      Cr Cash (payment)
      Cr Lease Liability (principal component)
    """
    j = []

    # Iterate over schedule rows to create journal entries
    for r in sched["rows"]:
        j.append({
            "lease_id": lease_id,
            "date": r["date"],
            "account": "Lease Interest Expense",
            "debit": r["interest"], "credit": 0.0, "memo": f"Period {r['period']}"
        })
        j.append({
            "lease_id": lease_id,
            "date": r["date"],
            "account": "ROU Amortization Expense",
            "debit": r["rou_amortization"], "credit": 0.0, "memo": f"Period {r['period']}"
        })
        j.append({
            "lease_id": lease_id,
            "date": r["date"],
            "account": "Cash",
            "debit": 0.0, "credit": r["payment"], "memo": f"Payment period {r['period']}"
        })
        j.append({
            "lease_id": lease_id,
            "date": r["date"],
            "account": "Lease Liability",
            "debit": 0.0, "credit": r["principal"], "memo": f"Principal period {r['period']}"
        })
    return j

# Function to export lease journals as CSV
def export_lease_journals_csv(payload: Dict) -> str:
    """
    payload = {
      lease_id, start_date, end_date, payment, frequency, discount_rate_annual,
      initial_direct_costs?, incentives?, cpi_escalation_pct?, cpi_escalation_month?
    }
    """
    sch = compute_schedule(**payload)
    journ = journals_from_schedule(payload["lease_id"], sch)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["lease_id","date","account","debit","credit","memo"])
    w.writeheader()
    for row in journ:
        w.writerow(row)
    return buf.getvalue()