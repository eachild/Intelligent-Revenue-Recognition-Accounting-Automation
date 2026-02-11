# backend/app/services/locks.py
from __future__ import annotations
import json, hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Session, select
from ..db import engine, get_session


class ScheduleLock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contract_id: str = Field(index=True)
    schedule_hash: str
    approver_sub: str
    approver_email: Optional[str] = None
    note: Optional[str] = None
    locked_at: datetime = Field(default_factory=datetime.utcnow)


def init_models():
    SQLModel.metadata.create_all(engine)


def hash_schedule(schedule: Dict[str, Any]) -> str:
    # stable hash by sorting keys
    blob = json.dumps(schedule, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def save_lock(contract_id: str, schedule: Dict[str, Any], approver_sub: str,
              approver_email: Optional[str], note: Optional[str] = None) -> Dict[str, Any]:
    digest = hash_schedule(schedule)
    with get_session() as s:
        lock = ScheduleLock(
            contract_id=contract_id,
            schedule_hash=digest,
            approver_sub=approver_sub,
            approver_email=approver_email,
            note=note or "",
        )
        s.add(lock)
        s.commit()
        s.refresh(lock)
        return {
            "id": lock.id,
            "contract_id": contract_id,
            "hash": digest,
            "approver": approver_email or approver_sub,
            "locked_at": lock.locked_at.isoformat() + "Z",
            "note": lock.note,
        }


def get_lock_status(contract_id: str) -> Dict[str, Any]:
    with get_session() as s:
        stmt = (
            select(ScheduleLock)
            .where(ScheduleLock.contract_id == contract_id)
            .order_by(ScheduleLock.locked_at.desc())
        )
        row = s.exec(stmt).first()
        if not row:
            return {"locked": False}
        return {
            "locked": True,
            "hash": row.schedule_hash,
            "approver": row.approver_email or row.approver_sub,
            "locked_at": row.locked_at.isoformat() + "Z",
            "note": row.note or "",
        }
