"""
backend/app/services/schedules_crud.py
CRUD for schedule grid rows (schedules_edit table).
"""
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime
import uuid

from sqlmodel import Field, SQLModel, Session, select, Column
from sqlalchemy import JSON
from ..db import get_session


# ── SQLModel table ──────────────────────────────────────────────

class ScheduleEditRow(SQLModel, table=True):
    __tablename__ = "schedules_edit"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    contract_id: str = Field(index=True)
    line_no: int
    period: str          # YYYY-MM
    amount: float = 0.0
    product_code: str = ""
    revrec_code: str = ""
    source: str = ""     # "manual" | "ai" | "csv"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Grid CRUD ───────────────────────────────────────────────────

def get_grid(contract_id: str) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.exec(
            select(ScheduleEditRow)
            .where(ScheduleEditRow.contract_id == contract_id)
            .order_by(ScheduleEditRow.line_no)
        ).all()
        return [
            {
                "line_no": r.line_no,
                "period": r.period,
                "amount": r.amount,
                "product_code": r.product_code,
                "revrec_code": r.revrec_code,
            }
            for r in rows
        ]


def save_grid(contract_id: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Replace all rows for a contract with the provided list."""
    with get_session() as s:
        # delete existing rows
        existing = s.exec(
            select(ScheduleEditRow)
            .where(ScheduleEditRow.contract_id == contract_id)
        ).all()
        for row in existing:
            s.delete(row)
        s.flush()

        # insert new rows
        for r in rows:
            s.add(ScheduleEditRow(
                contract_id=contract_id,
                line_no=r.get("line_no", 0),
                period=r.get("period", ""),
                amount=float(r.get("amount", 0)),
                product_code=r.get("product_code", ""),
                revrec_code=r.get("revrec_code", ""),
                source=r.get("source", "manual"),
            ))
        s.commit()
        return {"ok": True, "contract_id": contract_id, "rows_saved": len(rows)}
