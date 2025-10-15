
from datetime import date
from typing import Dict, List

# adds "n" months to a given date and returns the first day of the resulitng month
def add_months(d:date, n:int) -> date:
    y = d.year + (d.month - 1 + n) // 12
    m = ((d.month - 1 + n) % 12) + 1
    return date(y,m,1)

# Generates all months between start and end dates (inclusive) as date objects
def daterange_months(start:date,end:date):
    cur=date(start.year,start.month,1)
    last=date(end.year,end.month,1)
    while cur<=last: 
        yield cur
        cur=add_months(cur,1)

# Allocates a total price proportionally to a list of stand-alone selling prices (SSPs)
# Rounds allocations to 2 decimals, adjusting the last one to match total exactly
def allocate_relative_ssp(ssps:List[float], total:float)->List[float]:
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
            out.append(a); run+=a
        else: 
            out.append(round(total-run,2))
    return out

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
