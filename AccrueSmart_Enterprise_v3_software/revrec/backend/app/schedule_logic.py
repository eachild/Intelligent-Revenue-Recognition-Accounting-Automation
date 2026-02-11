from datetime import date
from typing import Dict, List
from .util import add_months

# Generates all months between start and end dates (inclusive) as date objects
def daterange_months(start:date,end:date):
    cur=date(start.year,start.month,1)
    last=date(end.year,end.month,1)

    # Generate months
    while cur<=last: 
        yield cur
        cur=add_months(cur,1)

# Generates a straight-line revenue recognition schedule over months
def straight_line(price:float,start:date,end:date)->Dict[str,float]:
    months=list(daterange_months(start,end)); 
    if not months: 
        return {}
    
    # Allocate equal amount per month (rounded to 2 decimals)
    per=round(price/len(months),2)

    # Create dictionary with keys "YYYY-MM" and value = amount per month
    out={f"{d.year}-{d.month:02d}":per for d in months}

    # Adjust the last month to ensure the sum matches total price exactly
    k=f"{months[-1].year}-{months[-1].month:02d}"
    out[k]=round(price-sum(v for kk,v in out.items() if kk!=k),2)
    return out

# Allocates revenue all at once at a single date
# It returns a dictionary with key "YYYY-MM" and the full price
def point_in_time(price:float,at:date)->Dict[str,float]: 
    return {f"{at.year}-{at.month:02d}":float(price)}

# Milestone-based allocation
# Milestones: Revenue recognized when specific contract milestones are met (e.g., project phases completed)
def milestones(price:float, ms:List[Dict])->Dict[str,float]:
    total_percent = sum(m.get("percent_of_price", 0.0) for m in ms)
    # Validate that total percentage is approximately 100%; might be a bad idea
    if abs(total_percent - 1.0) > 0.01:  # Allow small floating-point tolerance
        raise ValueError(f"Milestone percentages must sum to 100%, got {total_percent*100}%")
    
    out={}
    for m in ms:
        pct=float(m.get("percent_of_price",0.0)); met=m.get("met_date"); 
        if not met: continue
        from datetime import date as _d; dt=_d.fromisoformat(met); key=f"{dt.year}-{dt.month:02d}"
        out[key]=round(out.get(key,0.0)+pct*price,2)
    return out

# Percent-complete allocation
# Percent-complete: Revenue based on cumulative progress (e.g., construction projects)
def percent_complete(price:float, sched:List[Dict])->Dict[str,float]:
    out={}; prev=0.0
    for r in sched:
        cum=float(r.get("percent_cumulative",0.0)); delta=max(0.0,cum-prev); out[r["period"]]=round(price*delta,2); prev=cum
    return out
