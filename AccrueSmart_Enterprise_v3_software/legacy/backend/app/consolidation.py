
from typing import Dict, DefaultDict
from collections import defaultdict
from .schemas import ConsolidationIn
def consolidate(inp: ConsolidationIn) -> Dict:
    fx: DefaultDict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for r in inp.fx_rates:
        typ = r.rate_type or 'month_end'; fx[r.period][r.currency][typ] = r.rate_to_parent
    parent = inp.parent_currency; rev_parent = {}; comm_parent = {}
    def pick_rate(period: str, ccy: str) -> float:
        by_ccy = fx.get(period, {}).get(ccy, {}); 
        if inp.rate_type in by_ccy: return by_ccy[inp.rate_type]
        return by_ccy.get('month_end', by_ccy.get('average', 1.0))
    for ent in inp.entities:
        for p, amt in ent.schedules.items():
            rate = pick_rate(p, ent.currency); rev_parent[p] = round(rev_parent.get(p, 0.0) + amt*rate, 2)
        for p, amt in ent.commissions.items():
            rate = pick_rate(p, ent.currency); comm_parent[p] = round(comm_parent.get(p, 0.0) + amt*rate, 2)
    elim_total = {}
    for row in inp.eliminations:
        elim_total[row["period"]] = round(elim_total.get(row["period"],0.0) + float(row.get("amount_parent_ccy",0.0)),2)
    for m in inp.intercompany:
        p=m.get("period"); amt=float(m.get("amount_parent_ccy",0.0)); elim_total[p]=round(elim_total.get(p,0.0)+amt,2)
    for p, amt in elim_total.items(): rev_parent[p] = round(rev_parent.get(p, 0.0) - amt, 2)
    periods = sorted(set(list(rev_parent.keys()) + list(comm_parent.keys()))); rows = [{"period": p, "revenue_parent": rev_parent.get(p,0.0), "commission_parent": comm_parent.get(p,0.0)} for p in periods]
    return {"parent_currency": parent, "rows": rows, "eliminations_applied": elim_total, "rate_type_used": inp.rate_type}
