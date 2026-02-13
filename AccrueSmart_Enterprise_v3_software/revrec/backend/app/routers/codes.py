"""
backend/app/routers/codes.py
CRUD for product codes, revrec codes, and mapping.
"""
from fastapi import APIRouter, HTTPException, Request
from ..auth import require
from ..services.codes_crud import (
    list_products as db_list_products,
    create_product as db_create_product,
    list_revrec_codes as db_list_revrec_codes,
    create_revrec_code as db_create_revrec_code,
    map_product_to_revrec as db_map_product_to_revrec,
)

router = APIRouter(prefix="/codes", tags=["codes"])


# ----- Product Codes -----
@router.get("/products")
@require(perms=["product.manage"])
async def get_products():
    return db_list_products()


@router.post("/products")
@require(perms=["product.manage"])
async def create_product(payload: dict):
    code = payload.get("code")
    name = payload.get("name")
    desc = payload.get("description", "")
    if not code or not name:
        raise HTTPException(400, "code and name required")
    try:
        return db_create_product(code, name, desc)
    except ValueError as e:
        raise HTTPException(409, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


# ----- RevRec Codes -----
@router.get("/revrec")
@require(perms=["revrec.manage"])
async def get_revrec_codes():
    return db_list_revrec_codes()


@router.post("/revrec")
@require(perms=["revrec.manage"])
async def create_revrec(payload: dict):
    code = payload.get("code")
    rule_type = payload.get("rule_type")
    params = payload.get("params", {})
    if not code or not rule_type:
        raise HTTPException(400, "code and rule_type required")
    try:
        return db_create_revrec_code(code, rule_type, params)
    except ValueError as e:
        raise HTTPException(409, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


# ----- Mapping -----
@router.post("/map")
@require(perms=["revrec.manage"])
async def map_product_revrec(payload: dict):
    product_code = payload.get("product_code")
    revrec_code = payload.get("revrec_code")
    if not product_code or not revrec_code:
        raise HTTPException(400, "product_code and revrec_code required")
    try:
        return db_map_product_to_revrec(product_code, revrec_code)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))
