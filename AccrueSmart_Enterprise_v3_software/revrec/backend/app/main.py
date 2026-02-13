from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List, Optional
import os
from datetime import date
from .schemas import ContractIn, AllocationResponse, AllocResult, IngestResult, ConsolidationIn, PerformanceObligationIn
from . import engine as rev, ocr, ai, nlp_rules, sfc_effective, consolidation, reporting, variable
from .ledger import CSVLedger

# Create the app first
OUT_DIR='./out'; os.makedirs(OUT_DIR, exist_ok=True)
app=FastAPI(title='AccrueSmart RevRec Superset', version='3.0')

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3060", "http://127.0.0.1:3060"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Then import and include routers (after app creation to avoid circular imports)
from .routers import tax, forecast, auditor, costs, locks, leases, codes, schedules
from .routers.disclosure_pack import router as disclosure_pack_router
from .routers import audit
from .db import init_db

# Initialize DB tables at startup
init_db()

# Include all routers
app.include_router(tax.router)
app.include_router(forecast.router)
app.include_router(auditor.router)
app.include_router(disclosure_pack_router)
app.include_router(costs.router)
app.include_router(locks.router)
app.include_router(audit.router)
app.include_router(leases.router)
app.include_router(codes.router)
app.include_router(schedules.router)

# Health check endpoint
@app.get('/health')
def health(): return {'ok':True}

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

def build_allocation(contract: ContractIn) -> AllocationResponse:
    
    current_price = contract.transaction_price
    adjustments = {} # To store our new VC results
    
    # HANDLE VARIABLE CONSIDERATION (STEP 3) 
    if contract.variable:
        
        # Adjust for Loyalty Points (Material Right)
        if contract.variable.loyalty_pct > 0.0:
            
            # Calculate the value of the liability for loyalty points
            loyalty_liability = variable.loyalty_liability_allocation(
                current_price, 
                contract.variable.loyalty_pct
            )
            
            # The transaction price to be allocated to other POs is *net* of this liability
            current_price = current_price - loyalty_liability
            adjustments["loyalty_deferred_revenue"] = loyalty_liability
            
            # Also calculate the recognition schedule for this loyalty liability
            if contract.pos:
                # Use the first PO's start date as a simple proxy for the schedule start
                start_date = date.fromisoformat(contract.pos[0].start_date)
                adjustments["loyalty_recognition_schedule"] = variable.loyalty_recognition_schedule(
                    loyalty_liability,
                    start_date,
                    contract.variable.loyalty_months,
                    contract.variable.loyalty_breakage_rate
                )

    # ALLOCATE THE PRICE (STEP 4) 
    ssps = [po.ssp for po in contract.pos]
    allocated = rev.allocate_relative_ssp(ssps, current_price)
    
    schedules: Dict[str, Dict[str, float]] = {}
    allocated_res = []
    total_point_in_time_revenue = 0.0 
    
    # BUILD REVENUE SCHEDULES (STEP 5) 
    for po, alloc in zip(contract.pos, allocated):
        allocated_res.append(AllocResult(po_id=po.po_id, ssp=po.ssp, allocated_price=alloc))
        
        if po.method == 'straight_line' and po.start_date and po.end_date:
            schedules[po.po_id] = rev.straight_line(alloc, date.fromisoformat(po.start_date), date.fromisoformat(po.end_date))
        
        elif po.method == 'point_in_time' and po.start_date:
            schedules[po.po_id] = rev.point_in_time(alloc, date.fromisoformat(po.start_date))
            # Keep track of revenue recognized at a point-in-time
            total_point_in_time_revenue += alloc
        
        elif po.method == 'milestone':
            ms = []
            for m in getattr(po.params, 'milestones', []):
                 if hasattr(m, 'model_dump'): ms.append(m.model_dump())
                 elif hasattr(m, 'dict'): ms.append(m.dict())
                 else: ms.append(m)
            schedules[po.po_id]=rev.milestones(alloc, ms)

        elif po.method == 'percent_complete':
            schedules[po.po_id]=rev.percent_complete(alloc, po.params.percent_schedule)
            
        else:
            schedules[po.po_id] = {}

    # HANDLE RETURNS ADJUSTMENT (STEP 3) 
    if contract.variable and contract.variable.returns_rate > 0.0:
        
        # Calculate the refund liability based on the PoT revenue
        returns_adj = variable.expected_returns_adjustment(
            total_point_in_time_revenue,
            contract.variable.returns_rate
        )
        adjustments["returns_adjustment"] = returns_adj

    return AllocationResponse(
        allocated=allocated_res, 
        schedules=schedules,
        adjustments=adjustments
    )

@app.post('/contracts/allocate', response_model=AllocationResponse)
def allocate(c: ContractIn): return build_allocation(c)

def calculate_catchup_adjustment(base_contract: ContractIn, modification: Dict) -> Dict:
    
    # Old vs. New 
    old_schedules = build_allocation(base_contract).schedules
    
    new_contract = _create_modified_contract(base_contract, modification)
    new_schedules = build_allocation(new_contract).schedules

    # Sum Schedules by Period 
    old_sum = _sum_schedules_by_period(old_schedules)
    new_sum = _sum_schedules_by_period(new_schedules)
    
    # Calculate Delta and Catch-up 
    all_periods = set(list(old_sum.keys()) + list(new_sum.keys()))
    delta_by_period = {
        period: round(new_sum.get(period, 0.0) - old_sum.get(period, 0.0), 2)
        for period in all_periods
    }
    
    effective_month = modification['effective_date'][:7] # Assumes "YYYY-MM"
    catchup_amount = sum(amount for period, amount in delta_by_period.items() if period < effective_month)

    final_schedule = {}
    # Add all old periods before the change
    for period, amount in old_sum.items():
        if period < effective_month:
            final_schedule[period] = round(final_schedule.get(period, 0.0) + amount, 2)
            
    # Add all new periods on or after the change
    for period, amount in new_sum.items():
        if period >= effective_month:
            final_schedule[period] = round(final_schedule.get(period, 0.0) + amount, 2)
            
    # Add the catch-up amount to the effective month
    final_schedule[effective_month] = round(final_schedule.get(effective_month, 0.0) + catchup_amount, 2)

    # Prepare Journal Entry Data (no post)
    journal_entry_data = {
        'period': effective_month,
        'debit_acct': '2100-Deferred Revenue',
        'credit_acct': '4000-Revenue',
        'amount': catchup_amount,
        'memo': f"Catch-up on modification for {base_contract.contract_id}"
    }

    return {
        'old': old_sum,
        'new': new_sum,
        'delta_by_period': delta_by_period,
        'effective_catchup_month': effective_month,
        'catchup_amount': round(catchup_amount, 2),
        'final_schedule': final_schedule,
        'journal_entry_data': journal_entry_data
    }

@app.post('/contracts/modify/catchup')
def modify_catchup(base: ContractIn, modification: Dict):
    """
    Endpoint to process a contract modification.
    """
    results = calculate_catchup_adjustment(base, modification)
    ledger = CSVLedger(OUT_DIR)
    je_data = results['journal_entry_data']
    
    je = ledger.post(
        period=je_data['period'],
        debit=je_data['debit_acct'],
        credit=je_data['credit_acct'],
        amount=je_data['amount'],
        memo=je_data['memo'],
        contract_id=base.contract_id
    )
    
    results['journal_entry_posted'] = je
    
    return results

def _sum_schedules_by_period(schedules_by_po: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Helper to flatten PO schedules into a single sum by period."""
    summed_schedule = {}
    for po_schedule in schedules_by_po.values():
        for period, amount in po_schedule.items():
            summed_schedule[period] = round(summed_schedule.get(period, 0.0) + float(amount), 2)
    return summed_schedule


def _create_modified_contract(base: ContractIn, modification: Dict) -> ContractIn:
    """
    Robustly creates a new ContractIn object from a base and a modification dict.
    Handles Pydantic v1/v2 compatibility.
    """
    
    # Filter out removed POs
    existing_pos = [p for p in base.pos if p.po_id not in modification.get('remove_po_ids', [])]
    
    # Convert new PO dicts into Pydantic models
    new_pos_list = [PerformanceObligationIn(**p) for p in modification.get('add_pos', [])]

    all_pos = existing_pos + new_pos_list
    
    # Calculate new price
    new_price = round(base.transaction_price + modification.get('transaction_price_delta', 0.0), 2)
    
    # Handle Pydantic v1 vs v2
    if hasattr(base, 'model_copy'):
        # Pydantic v2 (preferred)
        return base.model_copy(update={'transaction_price': new_price, 'pos': all_pos})
    else:
        # Pydantic v1 (fallback)
        from pydantic import parse_obj_as
        d = base.dict()
        d.update({'transaction_price': new_price, 'pos': all_pos})
        return parse_obj_as(type(base), d)

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
    # prefer richer nlp_rules if available
    try:
        standard, reason = nlp_rules.detect_standard(text)
        currency = nlp_rules.find_currency(text); price = nlp_rules.find_total_price(text)
        pos = nlp_rules.extract_pos(text); risks = nlp_rules.detect_risks(text)
        comm = nlp_rules.extract_commission(text); recs = nlp_rules.recommendations(text)
        if standard == 'ASC606': summary = nlp_rules.summarize_revenue(text); nonrev=None
        else: summary=None; nonrev = nlp_rules.summarize_nonrevenue(text)
    except Exception:
        # fallback to the lightweight ai module
        standard, reason = ai.classify_standard(text); pos=ai.extract_pos(text); risks=ai.detect_risks(text); recs=ai.recommend_language(text)
        currency=None; price=None; comm=None; summary=None; nonrev=None
    return IngestResult(standard=standard, standard_reason=reason, currency=currency, transaction_price=price, performance_obligations=pos, risks=risks, commissions=comm, recommendations=recs, revenue_summary=summary, nonrevenue_summary=nonrev)

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