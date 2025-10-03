
import os, json
from typing import Dict, List
class ContractRepo:
    def __init__(self, folder='./out'):
        self.folder=folder; os.makedirs(self.folder, exist_ok=True)
        self.path=os.path.join(folder, 'contracts.json')
        if not os.path.exists(self.path):
            with open(self.path,'w') as f: json.dump([], f)
    def list(self)->List[Dict]:
        with open(self.path) as f: return json.load(f)
    def save(self, contract: Dict):
        data=self.list()
        data=[c for c in data if c.get('contract_id')!=contract.get('contract_id')] + [contract]
        with open(self.path,'w') as f: json.dump(data, f, indent=2)
        return {'ok':True,'count':len(data)}
    def get_many(self, ids: List[str])->List[Dict]:
        data=self.list()
        return [c for c in data if c.get('contract_id') in ids] if ids else data
