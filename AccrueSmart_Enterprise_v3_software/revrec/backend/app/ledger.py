import os, csv
class CSVLedger:
    def __init__(self, folder='./out', name='journal_entries.csv'):
        self.folder=folder; os.makedirs(self.folder, exist_ok=True)
        self.path=os.path.join(self.folder, name)
        if not os.path.exists(self.path):
            with open(self.path,'w',newline='') as f:
                csv.writer(f).writerow(['period','debit','credit','amount','memo','contract_id'])
    def post(self, period, debit, credit, amount, memo, contract_id):
        with open(self.path,'a',newline='') as f:
            csv.writer(f).writerow([period,debit,credit,f"{amount:.2f}",memo,contract_id])
        return {'period':period,'debit':debit,'credit':credit,'amount':round(amount,2),'memo':memo,'contract_id':contract_id}