# backend/app/services/expenses.py
from __future__ import annotations
from typing import Dict, Any, List
from datetime import date
from ..llm.gateway import LLMGateway

def classify_expense(text: str, amount: float) -> Dict[str,Any]:
    """
    LLM-based classification: "COGS", "SG&A", "CapEx", "Deferred (prepaid)"
    """
    llm = LLMGateway()
    # mock heuristic + note
    label = "SG&A"
    note = "Default classification (mock)."
    if "hosting" in text.lower() or "warehouse" in text.lower():
        label = "COGS"
    if "equipment" in text.lower() or "server" in text.lower():
        label = "CapEx"
    if "annual" in text.lower() or "prepaid" in text.lower():
        label = "Deferred"
    return {"label": label, "amount": amount, "note": note}

def amortize_prepaid(amount: float, months: int, start: date) -> List[Dict[str,Any]]:
    per = round(amount / months, 2) if months > 0 else 0.0
    out: List[Dict[str,Any]] = []
    y, m = start.year, start.month
    for i in range(months):
        dt = date(y, m, 1).isoformat()
        out.append({"period": dt[:7], "date": dt, "expense": per, "remaining": round(amount - per*(i+1), 2)})
        m += 1
        if m > 12:
            m = 1; y += 1
    return out
