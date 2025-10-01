
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
RecognitionMethod=Literal['point_in_time','straight_line','milestone','percent_complete']
class Milestone(BaseModel):
    id:str; description:str=""; percent_of_price:float=Field(ge=0.0, le=1.0); met_date:Optional[str]=None
class PerformanceObligationIn(BaseModel):
    po_id:str; description:str; ssp:float; method:RecognitionMethod
    start_date:Optional[str]=None; end_date:Optional[str]=None; params:Dict={}
class CommissionPlanIn(BaseModel):
    total_commission:float; benefit_months:int=12; practical_expedient_1yr:bool=False
class ContractIn(BaseModel):
    contract_id:str; customer:str; transaction_price:float; standard:str="ASC606"; raw_text:Optional[str]=""
    pos:List[PerformanceObligationIn]; commission:Optional[CommissionPlanIn]=None
class AllocResult(BaseModel):
    po_id:str; ssp:float; allocated_price:float
class AllocationResponse(BaseModel):
    allocated:List[AllocResult]; schedules:Dict[str,Dict[str,float]]; commission_schedule:Dict[str,float]|None
