
from fastapi import FastAPI, UploadFile, File, Body
from .schemas import ContractIn, AllocationResponse, AllocResult
from . import engine as rev, ocr, ai
from datetime import date
from typing import Dict

app=FastAPI(title='AccrueSmart RevRec API', version='3.0')

#function to handle the SSP (stand alone selling price) allocation anf revenue schedules
def build_allocation(contract: ContractIn) -> AllocationResponse:
    ssps=[po.ssp for po in contract.pos]; 
    
    allocated=rev.allocate_relative_ssp(ssps, contract.transaction_price)
    
    schedules:Dict[str,Dict[str,float]]={}; 
    allocated_res=[]
    
    for po, alloc in zip(contract.pos, allocated):
        allocated_res.append(AllocResult(po_id=po.po_id, ssp=po.ssp, allocated_price=alloc))
        if po.method=='straight_line' and po.start_date and po.end_date:
            schedules[po.po_id]=rev.straight_line(alloc, date.fromisoformat(po.start_date), date.fromisoformat(po.end_date))
        elif po.method=='point_in_time' and po.start_date:
            schedules[po.po_id]=rev.point_in_time(alloc, date.fromisoformat(po.start_date))
    return AllocationResponse(allocated=allocated_res, schedules=schedules)
@app.get('/health')
def health(): return {"ok":True}
@app.post('/contracts/allocate', response_model=AllocationResponse)
def allocate(c: ContractIn): return build_allocation(c)
@app.post('/ingest/text')
def ingest_text(filename:str=Body(...), text:str=Body(...)):
    std, reason = ai.classify_standard(text); pos=ai.extract_pos(text); risks=ai.detect_risks(text); rec=ai.recommend_language(text)
    return {"standard":std,"standard_reason":reason,"performance_obligations":pos,"risks":risks,"recommendations":rec}
@app.post('/ingest/pdf')
async def ingest_pdf(file: UploadFile = File(...)):
    text = ocr.extract_text_from_pdf_bytes(await file.read())
    return ingest_text(filename=file.filename, text=text)
