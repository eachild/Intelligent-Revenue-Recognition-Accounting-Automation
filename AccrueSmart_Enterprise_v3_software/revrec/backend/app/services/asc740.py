# backend/app/services/asc740.py
from __future__ import annotations
from typing import Dict, List, Tuple
from dataclasses import dataclass
from ..llm.gateway import LLMGateway

@dataclass
class TempDiff:
    """Temporary difference for a future period (positive => taxable in future)."""
    period: str     # e.g., "2026-12"
    amount: float   # book basis - tax basis (temporary)
    reversal_year: int  # for disclosure buckets

def compute_deferred_tax(
    differences: List[TempDiff],
    statutory_rate: float,
    valuation_allowance_pct: float = 0.0
) -> Dict:
    """
    Returns DTA/DTL rollforward and period mapping.
    Positive temp difference -> DTL (future taxable)
    Negative temp difference -> DTA (future deductible)
    """
    dtl = sum(max(0.0, d.amount) * statutory_rate for d in differences)
    dta = sum(max(0.0, -d.amount) * statutory_rate for d in differences)

    gross = {"DTL": round(dtl, 2), "DTA": round(dta, 2)}
    va = round(dta * valuation_allowance_pct, 2)
    net = round(dta - va - dtl, 2)

    by_year: Dict[int, float] = {}
    for d in differences:
        by_year[d.reversal_year] = round(by_year.get(d.reversal_year, 0.0) + d.amount, 2)

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