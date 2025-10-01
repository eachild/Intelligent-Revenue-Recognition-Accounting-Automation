
from datetime import date
from typing import Dict, List
def add_months(d:date,n:int)->date: y=d.year+(d.month-1+n)//12; m=((d.month-1+n)%12)+1; return date(y,m,1)
def daterange_months(start:date,end:date):
    cur=date(start.year,start.month,1); last=date(end.year,end.month,1)
    while cur<=last: yield cur; cur=add_months(cur,1)
def allocate_relative_ssp(ssps:List[float], total:float)->List[float]:
    s=sum(ssps); 
    if s==0: return [0.0 for _ in ssps]
    out=[]; run=0.0
    for i,v in enumerate(ssps):
        if i<len(ssps)-1: a=round(total*(v/s),2); out.append(a); run+=a
        else: out.append(round(total-run,2))
    return out
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
