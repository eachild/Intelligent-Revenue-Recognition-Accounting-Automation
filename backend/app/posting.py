
import os, csv
from typing import Dict

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
