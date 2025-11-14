# backend/app/services/auditor.py
from __future__ import annotations
from typing import Dict, Any
from ..llm.gateway import LLMGateway

def summarize_audit(findings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate schedules and generate narrative commentary via LLM.
    """
    llm = LLMGateway()
    prompt = {
        "objective": "Summarize accounting compliance health.",
        "modules": list(findings.keys()),
        "details": findings,
    }

    # Basic structured interpretation before AI summary
    scores = {}
    notes = []
    for k, v in findings.items():
        if not v:
            scores[k] = 0
            notes.append(f"{k}: missing data.")
            continue
        if "errors" in v:
            scores[k] = 40
            notes.append(f"{k}: found {len(v['errors'])} error(s).")
        elif "total_interest" in v:
            scores[k] = 90
            notes.append(f"{k}: lease schedule OK.")
        elif "gross" in v:
            scores[k] = 85
            notes.append(f"{k}: deferred tax calculated.")
        elif "forecast" in v:
            scores[k] = 80
            notes.append(f"{k}: forecast generated.")
        else:
            scores[k] = 70
            notes.append(f"{k}: generic OK.")

    avg = round(sum(scores.values()) / len(scores), 1) if scores else 0
    memo = llm.audit_memo({
        "title": "AI Auditor Summary",
        "scores": scores,
        "notes": notes,
        "avg_score": avg,
    })

    return {
        "avg_score": avg,
        "scores": scores,
        "notes": notes,
        "summary_memo": memo or "Audit memo generated.",
    }