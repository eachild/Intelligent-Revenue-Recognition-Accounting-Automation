
import os, csv
from typing import Dict, List

class CSVLedger:
    def __init__(self, folder:str='./out'):
        self.folder=folder; os.makedirs(self.folder, exist_ok=True)
        self.path=os.path.join(self.folder, 'journal_entries.csv')
        if not os.path.exists(self.path):
            with open(self.path,'w',newline='') as f:
                w=csv.writer(f); w.writerow(['period','debit','credit','amount','memo','contract_id'])

    def post(self, period:str, debit:str, credit:str, amount:float, memo:str, contract_id:str):
        with open(self.path,'a',newline='') as f:
            w=csv.writer(f); w.writerow([period,debit,credit,f"{amount:.2f}",memo,contract_id])
        return {'ok':True,'path':self.path}

def post_revenue_schedule(ledger:CSVLedger, contract_id:str, schedules:Dict[str,Dict[str,float]], revenue_acct='4000-Revenue', deferred_acct='2100-Deferred Revenue'):
    totals: Dict[str, float] = {}
    for _, sched in schedules.items():
        for period, amt in sched.items():
            totals[period]=totals.get(period,0.0)+float(amt)
    results=[]
    for period, amt in sorted(totals.items()):
        results.append(ledger.post(period, deferred_acct, revenue_acct, amt, f"Revenue recognition {contract_id}", contract_id))
    return results

def post_commission_schedule(ledger:CSVLedger, contract_id:str, comm:Dict[str,float], expense_acct='6100-Commission Expense', deferred_cost_acct='1305-Deferred Contract Costs'):
    results=[]
    for period, amt in sorted(comm.items()):
        results.append(ledger.post(period, expense_acct, deferred_cost_acct, amt, f"Commission amortization {contract_id}", contract_id))
    return results

def post_returns_at_inception(ledger:CSVLedger, contract_id:str, period:str, amounts:Dict[str,float]):
    out=[]
    if 'contra_revenue' in amounts and amounts['contra_revenue']>0:
        out.append(ledger.post(period, '4800-Sales Returns & Allowances', '2350-Refund Liability', amounts['contra_revenue'], 'Expected returns (contra revenue)', contract_id))
    if 'returns_asset' in amounts and amounts['returns_asset']>0:
        out.append(ledger.post(period, '1405-Returns Asset', '5000-Cost of Sales', amounts['returns_asset'], 'Expected return asset recognized', contract_id))
    return out

def post_loyalty_defer(ledger:CSVLedger, contract_id:str, period:str, loyalty_deferred:float):
    return [ledger.post(period, '2105-Loyalty Deferred Revenue', '4000-Revenue', loyalty_deferred, 'Defer loyalty material right', contract_id)]

def post_loyalty_recognition(ledger:CSVLedger, contract_id:str, schedule:Dict[str,float]):
    out=[]
    for period, amt in sorted(schedule.items()):
        out.append(ledger.post(period, '2105-Loyalty Deferred Revenue', '4000-Revenue', amt, 'Recognize loyalty revenue', contract_id))
    return out
