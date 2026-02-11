"""
backend/app/services/codes_crud.py
CRUD operations for product codes, revrec codes, and their mapping.
Uses SQLModel / SQLite (same pattern as locks.py).
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

from sqlmodel import Field, SQLModel, Session, select
from sqlalchemy.exc import IntegrityError
from ..db import engine, get_session


# ── SQLModel tables ──────────────────────────────────────────────

class ProductCode(SQLModel, table=True):
    __tablename__ = "product_codes"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RevrecCode(SQLModel, table=True):
    __tablename__ = "revrec_codes"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    code: str = Field(index=True, unique=True)
    rule_type: str          # straight_line, point_in_time, usage, milestone, percent_complete
    params: str = "{}"      # JSON string of rule parameters
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductRevrecMap(SQLModel, table=True):
    __tablename__ = "product_revrec_map"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    product_id: str = Field(index=True)
    revrec_id: str = Field(index=True)
    mapped_at: datetime = Field(default_factory=datetime.utcnow)


# ── Product CRUD ─────────────────────────────────────────────────

def list_products() -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.exec(select(ProductCode).order_by(ProductCode.code)).all()
        results = []
        for p in rows:
            # look up mapped revrec code
            mp = s.exec(
                select(ProductRevrecMap).where(ProductRevrecMap.product_id == p.id)
            ).first()
            revrec_code = None
            rule_type = None
            if mp:
                rc = s.get(RevrecCode, mp.revrec_id)
                if rc:
                    revrec_code = rc.code
                    rule_type = rc.rule_type
            results.append({
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "revrec_code": revrec_code,
                "rule_type": rule_type,
            })
        return results


def create_product(code: str, name: str, description: str = "") -> Dict[str, Any]:
    with get_session() as s:
        product = ProductCode(code=code, name=name, description=description)
        s.add(product)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise ValueError(f"Product code '{code}' already exists")
        s.refresh(product)
        return {"id": product.id, "code": product.code, "name": product.name,
                "description": product.description}


# ── RevRec Code CRUD ─────────────────────────────────────────────

def list_revrec_codes() -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.exec(select(RevrecCode).order_by(RevrecCode.code)).all()
        return [
            {"id": r.id, "code": r.code, "rule_type": r.rule_type,
             "params": json.loads(r.params)}
            for r in rows
        ]


def create_revrec_code(code: str, rule_type: str, params: Dict = None) -> Dict[str, Any]:
    with get_session() as s:
        rc = RevrecCode(code=code, rule_type=rule_type,
                        params=json.dumps(params or {}))
        s.add(rc)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise ValueError(f"RevRec code '{code}' already exists")
        s.refresh(rc)
        return {"id": rc.id, "code": rc.code, "rule_type": rc.rule_type,
                "params": json.loads(rc.params)}


# ── Mapping ──────────────────────────────────────────────────────

def map_product_to_revrec(product_code: str, revrec_code: str) -> Dict[str, Any]:
    with get_session() as s:
        # find product
        product = s.exec(
            select(ProductCode).where(ProductCode.code == product_code)
        ).first()
        if not product:
            raise ValueError(f"Product code '{product_code}' not found")

        # find revrec code
        rc = s.exec(
            select(RevrecCode).where(RevrecCode.code == revrec_code)
        ).first()
        if not rc:
            raise ValueError(f"RevRec code '{revrec_code}' not found")

        # upsert: delete old mapping for this product, then insert new one
        old = s.exec(
            select(ProductRevrecMap).where(ProductRevrecMap.product_id == product.id)
        ).first()
        if old:
            s.delete(old)

        mapping = ProductRevrecMap(product_id=product.id, revrec_id=rc.id)
        s.add(mapping)
        s.commit()
        return {"ok": True, "product_code": product_code, "revrec_code": revrec_code}
