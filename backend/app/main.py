
from fastapi import FastAPI, UploadFile, File
from datetime import date
from typing import Dict
import os
from . import schemas, engine as rev, ai, reporting, posting
from .db import Base, engine

OUT_DIR='./out'
os.makedirs(OUT_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)
app=FastAPI(title='AccrueSmart Backend (Extended)',version='0.3.0')

@app.get('/health')
def health(): return {'ok':True}

@app.post('/ai/parse_text')
async def parse_text(file: UploadFile=File(...)):
    text=(await file.read()).decode('utf-8','ignore'); return ai.contract_parse_text(text)

@app.post('/contracts/allocate', response_model=schemas.AllocationResponse)
def contracts_allocate(contract: schemas.ContractIn):
    ssps=[po.ssp for po in contract.pos]
    allocated=rev.allocate_relative_ssp(ssps, contract.transaction_price)
    schedules:Dict[str,Dict[str,float]]={}; allocated_res=[]
    for po, alloc in zip(contract.pos, allocated):
        allocated_res.append(schemas.AllocResult(po_id=po.po_id, ssp=po.ssp, allocated_price=alloc))
        if po.method=='straight_line':
            schedules[po.po_id]=rev.straight_line(alloc, date.fromisoformat(po.start_date), date.fromisoformat(po.end_date))
        elif po.method=='point_in_time':
            schedules[po.po_id]=rev.point_in_time(alloc, date.fromisoformat(po.start_date))
        elif po.method=='milestone':
            schedules[po.po_id]=rev.milestones(alloc, po.params.get('milestones',[]))
        else:
            schedules[po.po_id]=rev.percent_complete(alloc, po.params.get('percent_schedule',[]))
    comm=None
    if contract.commission:
        m=contract.commission.benefit_months
        if (m>12) or (m<=12 and not contract.commission.practical_expedient_1yr):
            start=next((po.start_date for po in contract.pos if po.start_date),'2025-01-01')
            comm=rev.amortize_commission(contract.commission.total_commission, m, date.fromisoformat(start))
        else:
            key=(contract.pos[0].start_date or '2025-01-01')[:7]; comm={key: contract.commission.total_commission}
    return schemas.AllocationResponse(allocated=allocated_res, schedules=schedules, commission_schedule=comm)

@app.post('/reports/disclosure')
def reports_disclosure(contract: schemas.ContractIn):
    res = contracts_allocate(contract)
    pdf_bytes = reporting.pdf_disclosure(contract.contract_id, contract.customer, contract.transaction_price, res.schedules, res.commission_schedule)
    pdf_path = os.path.join(OUT_DIR, f"Disclosure_{contract.contract_id}.pdf")
    with open(pdf_path,'wb') as f: f.write(pdf_bytes)
    return {'ok': True, 'pdf_path': pdf_path, 'allocated': [a.model_dump() for a in res.allocated]}

@app.post('/post/journal')
def post_journal(contract: schemas.ContractIn):
    res = contracts_allocate(contract)
    ledger = posting.CSVLedger(OUT_DIR)
    rev_posts = posting.post_revenue_schedule(ledger, contract.contract_id, res.schedules)
    comm_posts = []
    if res.commission_schedule:
        comm_posts = posting.post_commission_schedule(ledger, contract.contract_id, res.commission_schedule)
    return {'ok': True, 'journal_csv': ledger.path, 'revenue_entries': rev_posts, 'commission_entries': comm_posts}
