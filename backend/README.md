
# AccrueSmart Backend (Extended)

## Run
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8011
```

## Endpoints
- `POST /contracts/allocate` → relative SSP allocation + schedules + commission
- `POST /reports/disclosure` → writes PDF disclosure to `./out/Disclosure_<contract>.pdf`
- `POST /post/journal` → writes journal entries to `./out/journal_entries.csv`
- `POST /ai/parse_text` → heuristic PO extraction from raw contract text

## Tests
```
pytest -q
```
