
from fastapi import FastAPI, Body
from datetime import date
from typing import Dict, List
import os, csv
from . import schemas, engine as rev, reporting, posting, variable, repository
from .db import Base, engine

OUT_DIR='./out'
os.makedirs(OUT_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)
app=FastAPI(title='AccrueSmart Backend (Consolidated + VC + Streamlit)',version='0.4.0')

repo = repository.ContractRepo(OUT_DIR)

@app.get('/health')
def health(): return {'ok':True}

@app.get('/contracts/list')
def contracts_list(): return repo.list()

@app.post('/contracts/save')
def contracts_save(contract: schemas.ContractIn):
    repo.save(contract.model_dump())
    return {'ok':True}

def build_allocation(contract: schemas.ContractIn) -> schemas.AllocationResponse:
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

    adjustments = {}
    if contract.variable and contract.variable.returns_rate>0:
        pit_total = sum(alloc for po, alloc in zip(contract.pos, allocated) if po.method=='point_in_time')
        if pit_total>0:
            adjustments['returns'] = variable.expected_returns_adjustment(pit_total, contract.variable.returns_rate)
    if contract.variable and contract.variable.loyalty_pct>0:
        loyalty_deferred = variable.loyalty_liability_allocation(contract.transaction_price, contract.variable.loyalty_pct)
        adjustments['loyalty_deferred'] = loyalty_deferred
        start = next((po.start_date for po in contract.pos if po.start_date), '2025-01-01')
        sched = variable.loyalty_recognition_schedule(loyalty_deferred, date.fromisoformat(start), contract.variable.loyalty_months, contract.variable.loyalty_breakage_rate)
        adjustments['loyalty_recognition_schedule'] = sched

    return schemas.AllocationResponse(allocated=allocated_res, schedules=schedules, commission_schedule=comm, adjustments=adjustments or None)

@app.post('/contracts/allocate', response_model=schemas.AllocationResponse)
def contracts_allocate(contract: schemas.ContractIn):
    return build_allocation(contract)

@app.post('/reports/disclosure')
def reports_disclosure(contract: schemas.ContractIn):
    res = build_allocation(contract)
    pdf_bytes = reporting.pdf_disclosure(contract.contract_id, contract.customer, contract.transaction_price, res.schedules, res.commission_schedule, res.adjustments)
    pdf_path = os.path.join(OUT_DIR, f"Disclosure_{contract.contract_id}.pdf")
    with open(pdf_path,'wb') as f: f.write(pdf_bytes)
    return {'ok': True, 'pdf_path': pdf_path}

@app.post('/reports/disclosure/consolidated')
def reports_disclosure_consolidated(contract_ids: List[str] = Body(default=[])):
    items = repo.get_many(contract_ids)
    total_rev_by_period: Dict[str, float] = {}
    total_comm_by_period: Dict[str, float] = {}
    notes = []
    for c in items:
        contract = schemas.ContractIn(**c)
        res = build_allocation(contract)
        for _, sched in res.schedules.items():
            for p, amt in sched.items():
                total_rev_by_period[p] = round(total_rev_by_period.get(p,0.0)+float(amt),2)
        if res.commission_schedule:
            for p, amt in res.commission_schedule.items():
                total_comm_by_period[p] = round(total_comm_by_period.get(p,0.0)+float(amt),2)
        if res.adjustments: notes.append({"contract_id": contract.contract_id, "adjustments": res.adjustments})

    out_csv = os.path.join(OUT_DIR, "consolidated_revenue.csv")
    periods = sorted(set(total_rev_by_period.keys()) | set(total_comm_by_period.keys()))
    with open(out_csv,'w',newline='') as f:
        w=csv.writer(f); w.writerow(["Period","Revenue","Commission_Expense"])
        for p in periods:
            w.writerow([p, f"{total_rev_by_period.get(p,0.0):.2f}", f"{total_comm_by_period.get(p,0.0):.2f}"])
    return {"ok": True, "csv_path": out_csv, "contracts": [c["contract_id"] for c in items], "notes": notes}

@app.post('/post/journal')
def post_journal(contract: schemas.ContractIn):
    res = build_allocation(contract)
    ledger = posting.CSVLedger(OUT_DIR)
    posts = []
    inception = (contract.pos[0].start_date or '2025-01-01')[:7]
    if res.adjustments and 'returns' in res.adjustments:
        posts += posting.post_returns_at_inception(ledger, contract.contract_id, inception, res.adjustments['returns'])
    if res.adjustments and 'loyalty_deferred' in res.adjustments:
        posts += posting.post_loyalty_defer(ledger, contract.contract_id, inception, res.adjustments['loyalty_deferred'])
        posts += posting.post_loyalty_recognition(ledger, contract.contract_id, res.adjustments['loyalty_recognition_schedule'])
    posts += posting.post_revenue_schedule(ledger, contract.contract_id, res.schedules)
    if res.commission_schedule:
        posts += posting.post_commission_schedule(ledger, contract.contract_id, res.commission_schedule)
    return {'ok': True, 'journal_csv': ledger.path, 'entries': posts}
