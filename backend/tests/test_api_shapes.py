
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code==200 and r.json()['ok'] is True

def test_allocate_basic():
    payload = {
      "contract_id":"C-TEST-1","customer":"X","transaction_price":1200,
      "pos":[
        {"po_id":"PO-1","description":"Device","ssp":900,"method":"point_in_time","start_date":"2025-01-01"},
        {"po_id":"PO-2","description":"Maintenance 36mo","ssp":300,"method":"straight_line","start_date":"2025-01-01","end_date":"2027-12-01"}
      ],
      "commission": {"total_commission":120,"benefit_months":36,"practical_expedient_1yr":False}
    }
    r = client.post('/contracts/allocate', json=payload)
    assert r.status_code==200
    data=r.json()
    assert 'allocated' in data and 'schedules' in data and 'commission_schedule' in data

def test_disclosure_and_posting():
    payload = {
      "contract_id":"C-TEST-2","customer":"Y","transaction_price":1000,
      "pos":[
        {"po_id":"PO-1","description":"License delivery","ssp":700,"method":"point_in_time","start_date":"2025-01-01"},
        {"po_id":"PO-2","description":"Support 12mo","ssp":300,"method":"straight_line","start_date":"2025-01-01","end_date":"2025-12-01"}
      ]
    }
    r = client.post('/reports/disclosure', json=payload); assert r.status_code==200
    r2 = client.post('/post/journal', json=payload); assert r2.status_code==200
