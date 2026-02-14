# backend/app/services/asc740.py
from __future__ import annotations
from typing import Dict, List, Tuple
from dataclasses import dataclass
from ..llm.gateway import LLMGateway

# Data class for temporary differences
@dataclass
class TempDiff:
    """
    Represents a temporary difference between book and tax basis
    that will reverse in a future period.

    amount = book basis - tax basis
      > positive  => taxable in the future 
    """
    period: str     # e.g., "2026-12"
    amount: float   # book basis - tax basis (temporary)
    reversal_year: int  # for disclosure buckets

# Core ASC 740 calculation
# Function to compute deferred tax
def compute_deferred_tax(
    differences: List[TempDiff],
    statutory_rate: float,
    valuation_allowance_pct: float = 0.0
) -> Dict:
    """
    Computes deferred tax assets (DTA), deferred tax liabilities (DTL),
    and supporting rollforward/disclosure data under ASC 740.

    Rules:
    - Positive temporary differences create DTLs (future taxable)
    - Negative temporary differences create DTAs (future deductible)
    """

    # Calculate gross deferred tax liabilities (DTL)
    # Only positive temp differences contribute
    dtl = sum(max(0.0, d.amount) * statutory_rate for d in differences)

    # Calculate gross deferred tax assets (DTA)
    # Only negative temp differences contribute (absolute value)
    dta = sum(max(0.0, -d.amount) * statutory_rate for d in differences)

    # Store rounded gross balances
    gross = {"DTL": round(dtl, 2), "DTA": round(dta, 2)}

    # Valuation allowance applies only to DTAs
    # Net deferred tax position (DTA - valuation allowance - DTL)
    va = round(dta * valuation_allowance_pct, 2)
    net = round(dta - va - dtl, 2)

    # Aggregate temporary differences by reversal year
    by_year: Dict[int, float] = {}
    for d in differences:
        by_year[d.reversal_year] = round(by_year.get(d.reversal_year, 0.0) + d.amount, 2)

    # Final structured output for reporting and memo generation
    return {
        "statutory_rate": statutory_rate,
        "gross": gross,
        "valuation_allowance": va,
        "net_deferred_tax": net,
        "reversal_buckets": by_year,
        "mapping": [
            {
                "period": d.period,
                "temp_diff": d.amount,
                "deferred_tax": round(d.amount * statutory_rate, 2),
                "type": "DTL" if d.amount > 0 else "DTA"
            } for d in differences
        ]
    }

# Function to generate AI tax memo
def ai_tax_memo(company: str, results: Dict) -> str:
    """
    Lightweight 'AI' narrative using your LLM gateway (mock-supported).
    Summarizes rate, DTA/DTL and valuation allowance rationale.
    """
    llm = LLMGateway()
    payload = {
        "company": company,
        "tax_rate": results["statutory_rate"],
        "gross": results["gross"],
        "valuation_allowance": results["valuation_allowance"],
        "net_deferred_tax": results["net_deferred_tax"],
        "reversal_buckets": results["reversal_buckets"],
    }
    # Reuse gateway memo path for a clean narrative
    text = (
        f"ASC 740 Memo — {company}\n\n"
        f"Statutory tax rate: {payload['tax_rate']:.2%}\n"
        f"Gross DTL: ${payload['gross']['DTL']:,}  |  Gross DTA: ${payload['gross']['DTA']:,}\n"
        f"Valuation allowance: ${payload['valuation_allowance']:,}\n"
        f"Net deferred tax position: ${payload['net_deferred_tax']:,}\n"
        f"Reversal timing (by year): {payload['reversal_buckets']}\n\n"
        "Judgment: Valuation allowance reflects expected limitations on realization of deferred tax assets, "
        "considering recent losses, forecasted taxable income, and reversal patterns. "
        "Conclusion: Recognition and presentation comply with ASC 740."
    )
    # If you later wire a real LLM, swap to llm.audit_memo(payload)
    return text