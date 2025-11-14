"""
backend/app/routers/codes.py
CRUD for product codes, revrec codes, and mapping
"""
from fastapi import APIRouter, HTTPException, Request
from ..auth import require
import asyncpg, os, json

router = APIRouter(prefix="/codes", tags=["codes"])
DB_URL = os.getenv("DATABASE_URL")

async def _conn():
    if not DB_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set")
    return await asyncpg.connect(DB_URL)

# ----- Product Codes -----
@router.get("/products")
@require(perms=["product.manage"])
async def list_products():
    conn = await _conn()
    rows = await conn.fetch("select * from product_catalog order by code asc;")
    await conn.close()
    return [dict(r) for r in rows]

@router.post("/products")
@require(perms=["product.manage"])
async def create_product(payload: dict):
    code = payload.get("code"); name = payload.get("name"); desc = payload.get("description","")
    if not code or not name:
        raise HTTPException(400, "code and name required")
    conn = await _conn()
    try:
        row = await conn.fetchrow(
            "insert into product_codes(code,name,description) values($1,$2,$3) returning *",
            code, name, desc
        )
        await conn.close()
        return dict(row)
    except Exception as e:
        await conn.close()
        raise HTTPException(400, str(e))

# ----- RevRec Codes -----
@router.get("/revrec")
@require(perms=["revrec.manage"])
async def list_revrec_codes():
    conn = await _conn()
    rows = await conn.fetch("select id, code, rule_type, params from revrec_codes order by code asc;")
    await conn.close()
    return [dict(r) for r in rows]

@router.post("/revrec")
@require(perms=["revrec.manage"])
async def create_revrec(code: str, rule_type: str, params: dict = {}):
    conn = await _conn()
    row = await conn.fetchrow(
        "insert into revrec_codes(code,rule_type,params) values($1,$2,$3::jsonb) returning *",
        code, rule_type, json.dumps(params)
    )
    await conn.close()
    return dict(row)

# ----- Mapping -----
@router.post("/map")
@require(perms=["revrec.manage"])
async def map_product_revrec(product_code: str, revrec_code: str):
    conn = await _conn()
    row = await conn.fetchrow("select id from product_codes where code=$1", product_code)
    if not row:
        await conn.close()
        raise HTTPException(404, "product not found")
    product_id = row["id"]
    r = await conn.fetchrow("select id from revrec_codes where code=$1", revrec_code)
    if not r:
        await conn.close()
        raise HTTPException(404, "revrec code not found")
    revrec_id = r["id"]
    await conn.execute("""
      insert into product_revrec_map(product_id,revrec_id) values($1,$2)
      on conflict (product_id) do update set revrec_id=excluded.revrec_id
    """, product_id, revrec_id)
    await conn.close()
    return {"ok": True}