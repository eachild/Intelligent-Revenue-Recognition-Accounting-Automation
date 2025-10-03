
# AccrueSmart Backend (Consolidated + Variable Consideration + Streamlit)

Run:
```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8011
```

New endpoints:
- `GET /contracts/list` — list stored contracts
- `POST /contracts/save` — save a contract JSON to the repository
- `POST /reports/disclosure/consolidated` — consolidated CSV across multiple or all contracts

Variable consideration fields:
- `variable.returns_rate` (0..1), `variable.loyalty_pct` (0..1), `variable.loyalty_months`, `variable.loyalty_breakage_rate`
