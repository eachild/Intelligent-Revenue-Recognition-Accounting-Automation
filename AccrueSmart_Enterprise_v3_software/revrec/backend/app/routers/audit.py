# backend/app/routers/audit.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

# Import the modules we created
try:
    from ..db import get_session
    from ..llm.gateway import LLMGateway
except ImportError:
    # Fallback for when modules aren't set up yet
    print("Warning: Database or LLM gateway not configured")
    get_session = None
    LLMGateway = None

router = APIRouter(prefix="/audit", tags=["AI Audit Insights"])


class AuditInsightsResponse(BaseModel):
    """Response model for audit insights"""
    modules: Dict[str, Any]
    anomalies: List[str]
    stats: Dict[str, int]
    ai_commentary: str


class JournalStats(BaseModel):
    """Journal statistics"""
    total_journals: int = 0
    posted_journals: int = 0
    unposted_journals: int = 0


@router.get("/insights", response_model=AuditInsightsResponse)
def ai_audit_insights():
    """
    Aggregates ASC606 / ASC842 / Deferral schedules + Journals,
    then runs AI summary via LLMGateway.
    """
    # Initialize data structures
    modules: Dict[str, Any] = {
        "ASC606": None,
        "ASC842": None,
        "Prepaid Revenue": None,
        "Accrued Expense": None,
    }
    
    anomalies: List[str] = []
    stats = JournalStats()
    
    # If database is available, fetch actual data
    if get_session is not None:
        try:
            with get_session() as session:
                # Example query - adjust based on your actual schema
                # from sqlmodel import select
                # from ..models import JournalEntry
                # 
                # total = session.exec(select(func.count(JournalEntry.id))).one()
                # posted = session.exec(select(func.count(JournalEntry.id)).where(JournalEntry.posted == True)).one()
                # 
                # stats.total_journals = total or 0
                # stats.posted_journals = posted or 0
                # stats.unposted_journals = (total or 0) - (posted or 0)
                
                # For now, mock data
                stats.total_journals = 42
                stats.posted_journals = 38
                stats.unposted_journals = 4
                
        except Exception as e:
            print(f"Database error: {e}")
            # Continue with mock data
            pass
    
    # Basic validation and anomaly detection
    for name, sched in modules.items():
        if not sched:
            anomalies.append(f"{name}: No schedule data available.")
    
    if stats.unposted_journals > 0:
        anomalies.append(f"{stats.unposted_journals} journal entries pending posting.")
    
    # Generate AI commentary
    if LLMGateway is not None:
        llm = LLMGateway()
        memo = llm.audit_memo({
            "stats": stats.dict(),
            "anomalies": anomalies,
            "modules": list(modules.keys())
        })
    else:
        memo = "AI commentary not available - LLMGateway not configured."
    
    return AuditInsightsResponse(
        modules=modules,
        anomalies=anomalies,
        stats=stats.dict(),
        ai_commentary=memo
    )


@router.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "audit",
        "database_available": get_session is not None,
        "llm_available": LLMGateway is not None
    }