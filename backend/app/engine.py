from datetime import date
from typing import Dict, List

def add_months(d:date,n:int)->date: y=d.year+(d.month-1+n)//12; m=((d.month-1+n)%12)+1; return date(y,m,1)

def daterange_months(start:date,end:date):
    cur=date(start.year,start.month,1); last=date(end.year,end.month,1)
    while cur<=last: yield cur; cur=add_months(cur,1)

# Allocate a total amount based on a list of SSP values proportionally
def allocate_relative_ssp(ssps:List[float], total:float)->List[float]:
    """
    Core relative SSP (Standalone Selling Price) allocation involves
    a mathematical process to distribute a total transaction price
    among different performance obligations (goods or services) within
    a contract based on their relative standalone selling prices.
    This ensures that the transaction price is allocated proportionally,
    reflecting the individual value of each component.
    Contract total price (Transaction Price): $500
    Performance Obligation 1: Software: SSP = $800
    Performance Obligation 2: Training: SSP = $200
    Total SSP: $800 (Software) + $200 (Training) = $1,000
    SSP Ratios:
        Software: $800 / $1,000 = 80%
        Training: $200 / $1,000 = 20%
    Allocated Amounts:
        Software: 80% x $500 = $400
        Training: 20% x $500 = $100
    The $500 transaction price is now split, with $400 attributed to the
    software and $100 to the training, based on their relative standalone selling prices
    """
    # Handle empty case
    if not ssps:
        return []
    
    # Handle zero total SSP case - distribute evenly
    total_ssp = sum(ssps)
    if total_ssp == 0:
        equal_share = round(total / len(ssps), 2) if len(ssps) > 0 else 0
        return [equal_share] * len(ssps)
    
    # Calculate allocations using precise math first, then round at the end
    allocations = []
    running_total = 0.0
    
    # Allocate for all but the last item using precise calculation
    for i in range(len(ssps) - 1):
        ratio = ssps[i] / total_ssp
        allocated_amount = total * ratio
        rounded_amount = round(allocated_amount, 2)
        allocations.append(rounded_amount)
        running_total += rounded_amount
    
    # Last item gets the remaining amount to ensure perfect total
    last_allocation = round(total - running_total, 2)
    allocations.append(last_allocation)
    return allocations

# returns dictionary?
def straight_line(price:float,start:date,end:date)->Dict[str,float]:
    months=list(daterange_months(start,end)); 
    if not months: return {}
    per=round(price/len(months),2); out={f"{d.year}-{d.month:02d}":per for d in months}
    k=f"{months[-1].year}-{months[-1].month:02d}"; out[k]=round(price-sum(v for kk,v in out.items() if kk!=k),2); return out

def point_in_time(price:float,at:date)->Dict[str,float]: return {f"{at.year}-{at.month:02d}":float(price)}

def milestones(price:float, ms:List[Dict])->Dict[str,float]:
    out={}
    for m in ms:
        pct=float(m.get("percent_of_price",0.0)); met=m.get("met_date"); 
        if not met: continue
        from datetime import date as _d; dt=_d.fromisoformat(met); key=f"{dt.year}-{dt.month:02d}"
        out[key]=round(out.get(key,0.0)+pct*price,2)
    return out

def percent_complete(price:float, sched:List[Dict])->Dict[str,float]:
    out={}; prev=0.0
    for r in sched:
        cum=float(r.get("percent_cumulative",0.0)); delta=max(0.0,cum-prev); out[r["period"]]=round(price*delta,2); prev=cum
    return out

def amortize_commission(total:float, months:int, start:date)->Dict[str,float]:
    if months<=0: return {}
    months_list=[add_months(start,i) for i in range(months)]; per=round(total/months,2)
    out={f"{d.year}-{d.month:02d}":per for d in months_list}
    k=f"{months_list[-1].year}-{months_list[-1].month:02d}"; out[k]=round(total-sum(v for kk,v in out.items() if kk!=k),2); return out
