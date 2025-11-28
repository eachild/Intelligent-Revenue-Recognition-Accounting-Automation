from datetime import date
from typing import Dict, List

from .schemas import ContractIn, AllocationResponse, AllocResult
from . import variable
from .schedule_logic import straight_line, point_in_time, milestones, percent_complete
from .util import add_months


# Allocates a total price proportionally to a list of stand-alone selling prices (SSPs)
# Rounds allocations to 2 decimals, adjusting the last one to match total exactly
def allocate_relative_ssp(ssps:List[float], total:float)->List[float]:
    # Add up all ssps
    s=sum(ssps); 

    # If all SSPs are zero, allocate zero to each
    if s==0: 
        return [0.0 for _ in ssps]
    
    out=[] # List to hold allocated prices
    run=0.0 # Running total of allocated prices

    # Allocate evenly for all but the last SSP
    for i,v in enumerate(ssps):
        if i<len(ssps)-1:
            a=round(total*(v/s),2) # Round to 2 decimals
            out.append(a); run+=a # Last item gets remainder
        else: 
            out.append(round(total-run,2))
    return out


def amortize_commission(total:float, months:int, start:date)->Dict[str,float]:
    if months<=0: return {}
    months_list=[add_months(start,i) for i in range(months)]; per=round(total/months,2)
    out={f"{d.year}-{d.month:02d}":per for d in months_list}
    k=f"{months_list[-1].year}-{months_list[-1].month:02d}"; out[k]=round(total-sum(v for kk,v in out.items() if kk!=k),2); return out

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
    allocated = allocate_relative_ssp(ssps, current_price)
    
    schedules: Dict[str, Dict[str, float]] = {}
    allocated_res = []
    total_point_in_time_revenue = 0.0 
    
    # BUILD REVENUE SCHEDULES (STEP 5) 
    for po, alloc in zip(contract.pos, allocated):
        allocated_res.append(AllocResult(po_id=po.po_id, ssp=po.ssp, allocated_price=alloc))
        
        if po.method == 'straight_line' and po.start_date and po.end_date:
            schedules[po.po_id] = straight_line(alloc, date.fromisoformat(po.start_date), date.fromisoformat(po.end_date))
        
        elif po.method == 'point_in_time':
            if not po.start_date:
                raise ValueError("start_date is required for point_in_time method")
            schedules[po.po_id] = point_in_time(alloc, date.fromisoformat(po.start_date))
            # Keep track of revenue recognized at a point-in-time
            total_point_in_time_revenue += alloc
        
        elif po.method == 'milestone':
            ms = []
            for m in getattr(po.params, 'milestones', []):
                 if hasattr(m, 'model_dump'): ms.append(m.model_dump())
                 elif hasattr(m, 'dict'): ms.append(m.dict())
                 else: ms.append(m)
            schedules[po.po_id]=milestones(alloc, ms)

        elif po.method == 'percent_complete':
            schedules[po.po_id]=percent_complete(alloc, po.params.percent_schedule)
            
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

"""
Recommendations for further enhancements:
Adding the validation improvements above
Considering timezone-aware datetime handling if dealing with international contracts
Adding logging for audit trails
Extending with the variable consideration features mentioned in your project docs (returns, breakage, etc.)
"""