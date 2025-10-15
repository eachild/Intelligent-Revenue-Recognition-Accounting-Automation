
from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, List, Optional
import os
from datetime import date
from .schemas import ContractIn, AllocationResponse, AllocResult, IngestResult, ConsolidationIn
from . import engine as rev, sfc_effective, consolidation, reporting, ocr, nlp_rules
from .ledger import CSVLedger

OUT_DIR='./out'; os.makedirs(OUT_DIR, exist_ok=True)
app=FastAPI(title='AccrueSmart Ultimate v2.1', version='2.1')

@app.get('/health') def health(): return {'ok':True}

def build_allocation(contract: ContractIn) -> AllocationResponse:
    ssps=[po.ssp for po in contract.pos]; allocated=rev.allocate_relative_ssp(ssps, contract.transaction_price)
    schedules:Dict[str,Dict[str,float]]={}; allocated_res=[]
    for po, alloc in zip(contract.pos, allocated):
        allocated_res.append(AllocResult(po_id=po.po_id, ssp=po.ssp, allocated_price=alloc))
        if po.method=='straight_line' and po.start_date and po.end_date:
            schedules[po.po_id]=rev.straight_line(alloc, date.fromisoformat(po.start_date), date.fromisoformat(po.end_date))
        elif po.method=='point_in_time' and po.start_date:
            schedules[po.po_id]=rev.point_in_time(alloc, date.fromisoformat(po.start_date))
        elif po.method=='milestone':
            schedules[po.po_id]=rev.milestones(alloc, [m.model_dump() for m in po.params.milestones])
        elif po.method=='percent_complete':
            schedules[po.po_id]=rev.percent_complete(alloc, po.params.percent_schedule)
        else:
            schedules[po.po_id]={}
    return AllocationResponse(allocated=allocated_res, schedules=schedules)

@app.post('/contracts/allocate', response_model=AllocationResponse)
def contracts_allocate(contract: ContractIn): return build_allocation(contract)

@app.post('/contracts/modify/catchup')
def modify_catchup(base: ContractIn, modification: Dict):
    old = build_allocation(base)
    pos = [p for p in base.pos if p.po_id not in modification.get('remove_po_ids',[])] + modification.get('add_pos',[])
    new = base.model_copy(update={'transaction_price': round(base.transaction_price + modification.get('transaction_price_delta',0.0),2), 'pos': pos})
    new_res = build_allocation(new)
    def sum_map(m): out={}; 

    for _,sched in m.items(): 

        for p,a in sched.items(): out[p]=round(out.get(p,0.0)+float(a),2)
    old_sum=sum_map(old.schedules); new_sum=sum_map(new_res.schedules)
    periods=set(list(old_sum.keys())+list(new_sum.keys())); delta={p: round(new_sum.get(p,0.0)-old_sum.get(p,0.0),2) for p in periods}
    eff_key=modification['effective_date'][:7]; catchup=sum(v for k,v in delta.items() if k<eff_key)
    final={}; 

    for p,a in old_sum.items():
        if p<eff_key: final[p]=round(final.get(p,0.0)+a,2)
    for p,a in new_sum.items():
        if p>=eff_key: final[p]=round(final.get(p,0.0)+a,2)
    final[eff_key]=round(final.get(eff_key,0.0)+catchup,2)
    ledger=CSVLedger(OUT_DIR); je=ledger.post(eff_key,'2100-Deferred Revenue','4000-Revenue', catchup, f"Catch-up on modification", base.contract_id)
    return {'old':old_sum,'new':new_sum,'delta_by_period':delta,'effective_catchup':eff_key,'catchup_amount':round(catchup,2),'final':final,'journal_entry':je}

@app.post('/sfc/schedule')
def sfc_schedule(initial_carry: float = Body(...), payments: Dict[str, float] = Body(...), annual_rate: Optional[float] = Body(None)):
    return sfc_effective.effective_interest_schedule(initial_carry, payments, annual_rate)
@app.post('/sfc/export_csv')
def sfc_export_csv(initial_carry: float = Body(...), payments: Dict[str, float] = Body(...), annual_rate: Optional[float] = Body(None)):
    sched = sfc_effective.effective_interest_schedule(initial_carry, payments, annual_rate)
    path=os.path.join(OUT_DIR,'sfc_amortization.csv'); sfc_effective.export_csv(path, sched); return {'ok':True,'csv_path':path}

@app.post('/consolidation/multientity')
def consolidate(inp: ConsolidationIn): from . import consolidation as cons; return cons.consolidate(inp)

@app.post('/ingest/pdf', response_model=IngestResult)
async def ingest_pdf(file: UploadFile = File(...)):
    b = await file.read(); text, pages = ocr.extract_text_from_pdf_bytes(b); return analyze_text(file.filename, text)
@app.post('/ingest/text', response_model=IngestResult)
def ingest_text(filename:str=Body(...), text:str=Body(...)): return analyze_text(filename, text)

def analyze_text(filename:str, text:str)->IngestResult:
    standard, reason = nlp_rules.detect_standard(text)
    currency = nlp_rules.find_currency(text); price = nlp_rules.find_total_price(text)
    pos = nlp_rules.extract_pos(text); risks = nlp_rules.detect_risks(text)
    comm = nlp_rules.extract_commission(text); recs = nlp_rules.recommendations(text)
    if standard == 'ASC606': summary = nlp_rules.summarize_revenue(text); nonrev=None
    else: summary=None; nonrev = nlp_rules.summarize_nonrevenue(text)
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
