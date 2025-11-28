from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, List, Optional
import os
from datetime import date
from .schemas import ContractIn, AllocationResponse, AllocResult, IngestResult, ConsolidationIn, PerformanceObligationIn
from . import engine as rev, ocr, sfc_effective, consolidation, reporting, variable, parsing_pipeline
from .ledger import CSVLedger

app=FastAPI(title='AccrueSmart RevRec Superset', version='3.0')

# From routers/tax.py and services/asc_740.py
from .routers import tax
app.include_router(tax.router)  # add after other routers

# From forecast.py
from .routers import forecast
app.include_router(forecast.router)

# From auditor.py
from .routers import auditor
app.include_router(auditor.router)

# From disclosure_pack.py
from app.routers.disclosure_pack import router as disclosure_pack_router
app.include_router(disclosure_pack_router)

# From costs.py
from .routers import costs
app.include_router(costs.router)

# From locks.py
from .routers import locks
app.include_router(locks.router)

OUT_DIR='./out'; os.makedirs(OUT_DIR, exist_ok=True)

# # build_allocation: expanded to support milestone and percent_complete and to use PO params
# def build_allocation(contract: ContractIn) -> AllocationResponse:
#     ssps=[po.ssp for po in contract.pos]; allocated=rev.allocate_relative_ssp(ssps, contract.transaction_price)
#     schedules:Dict[str,Dict[str,float]]={}; allocated_res=[]
#     for po, alloc in zip(contract.pos, allocated):
#         allocated_res.append(AllocResult(po_id=po.po_id, ssp=po.ssp, allocated_price=alloc))
#         if po.method=='straight_line' and po.start_date and po.end_date:
#             schedules[po.po_id]=rev.straight_line(alloc, date.fromisoformat(po.start_date), date.fromisoformat(po.end_date))
#         elif po.method=='point_in_time' and po.start_date:
#             schedules[po.po_id]=rev.point_in_time(alloc, date.fromisoformat(po.start_date))
#         elif po.method=='milestone':
#             # po.params.milestones may be pydantic models; convert to dicts if needed
#             ms = []
#             for m in getattr(po.params, 'milestones', []):
#                 if hasattr(m, 'model_dump'):
#                     ms.append(m.model_dump())
#                 elif hasattr(m, 'dict'):
#                     ms.append(m.dict())
#                 else:
#                     ms.append(m)
#             schedules[po.po_id]=rev.milestones(alloc, ms)
#         elif po.method=='percent_complete':
#             schedules[po.po_id]=rev.percent_complete(alloc, po.params.percent_schedule)
#         else:
#             schedules[po.po_id]={}
#     return AllocationResponse(allocated=allocated_res, schedules=schedules)

@app.post('/contracts/allocate', response_model=AllocationResponse)
def allocate(c: ContractIn): return rev.build_allocation(c)

@app.post('/sfc/schedule')
def sfc_schedule(initial_carry: float = Body(...), payments: Dict[str, float] = Body(...), annual_rate: Optional[float] = Body(None)):
    return sfc_effective.effective_interest_schedule(initial_carry, payments, annual_rate)

@app.post('/sfc/export_csv')
def sfc_export_csv(initial_carry: float = Body(...), payments: Dict[str, float] = Body(...), annual_rate: Optional[float] = Body(None)):
    sched = sfc_effective.effective_interest_schedule(initial_carry, payments, annual_rate)
    path=os.path.join(OUT_DIR,'sfc_amortization.csv'); sfc_effective.export_csv(path, sched); return {'ok':True,'csv_path':path}

@app.post('/consolidation/multientity')
def consolidate(inp: ConsolidationIn): return consolidation.consolidate(inp)

@app.post('/ingest/pdf', response_model=IngestResult)
async def ingest_pdf(file: UploadFile = File(...)):
    b = await file.read(); result = ocr.extract_text_from_pdf_bytes(b)
    # handle both (text, pages) and text-only returns
    if isinstance(result, tuple): text, pages = result
    else: text = result; pages = None
    return analyze_text(file.filename, text)

@app.post('/ingest/text', response_model=IngestResult)
def ingest_text(filename:str=Body(...), text:str=Body(...)): return analyze_text(filename, text)

def analyze_text(filename:str, text:str)->IngestResult:
    return parsing_pipeline.run_contract_parsing(text)

@app.post('/chat')
def chat(prompt:str=Body(...)):
    p=prompt.lower()
    if 'summarize' in p or 'explain' in p: return {'reply':'Upload or paste contract text on /ingest; system will summarize and flag revenue risks automatically.'}
    if 'allocate' in p: return {'reply':'Use /allocate with your contract payload to calculate allocation and schedules.'}
    if 'disclosure' in p: return {'reply':'Use /reports → Disclosure Pack endpoint to generate a PDF note.'}
    return {'reply':'I can route: summarize, allocate, disclosure, SFC, consolidation. Try: "Summarize this contract", "Allocate a $120k SaaS deal", "Generate Q1 disclosure".'}

@app.post('/reports/disclosure_pack')
def disclosure_pack(title:str=Body(...), bullets:Dict[str,str]=Body(default={}), sections:Dict[str,Dict[str,float]]=Body(default={})):
    pdf=reporting.pdf_note(title, sections, bullets); path=os.path.join(OUT_DIR,'Disclosure_Pack.pdf'); open(path,'wb').write(pdf); return {'ok':True,'pdf_path':path}

@app.get('/files/get')
def files_get(path: str):
    full = os.path.abspath(path); base = os.path.abspath(OUT_DIR)
    if not full.startswith(base) or not os.path.exists(full): raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full, filename=os.path.basename(full))
