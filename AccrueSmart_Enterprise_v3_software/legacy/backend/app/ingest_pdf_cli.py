"""Simple CLI to extract text from a PDF and run the project's NLP ingest logic.

Usage (PowerShell):
    python \legacy\backend\app\scripts\ingest_pdf_cli.py C:\path\to\file.pdf

This script avoids importing `main.py` (which pulls FastAPI at import time)
and instead calls the same nlp_rules functions and builds an IngestResult.
"""
import sys
import json
from pathlib import Path

from legacy.backend.app import ocr, nlp_rules
from legacy.backend.app.schemas import IngestResult


def analyze_text_local(filename: str, text: str) -> IngestResult:
    standard, reason = nlp_rules.detect_standard(text)
    currency = nlp_rules.find_currency(text)
    price = nlp_rules.find_total_price(text)
    pos = nlp_rules.extract_pos(text)
    risks = nlp_rules.detect_risks(text)
    comm = nlp_rules.extract_commission(text)
    recs = nlp_rules.recommendations(text)
    if standard == 'ASC606':
        summary = nlp_rules.summarize_revenue(text)
        nonrev = None
    else:
        summary = None
        nonrev = nlp_rules.summarize_nonrevenue(text)
    return IngestResult(
        standard=standard,
        standard_reason=reason,
        currency=currency,
        transaction_price=price,
        performance_obligations=pos,
        risks=risks,
        commissions=comm,
        recommendations=recs,
        revenue_summary=summary,
        nonrevenue_summary=nonrev,
    )


def main(argv):
    if len(argv) < 2:
        print("Usage: python ingest_pdf_cli.py <path-to-pdf>")
        return 2
    p = Path(argv[1])
    if not p.exists():
        print(f"File not found: {p}")
        return 3
    b = p.read_bytes()
    text, pages = ocr.extract_text_from_pdf_bytes(b)
    print(f"Extracted {len(text)} chars across {pages} pages")
    res = analyze_text_local(p.name, text)
    # Print JSON-serializable dict
    out = res.model_dump() if hasattr(res, 'model_dump') else res.dict()
    print(json.dumps(out, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
