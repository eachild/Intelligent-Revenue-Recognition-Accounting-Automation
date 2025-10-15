
from io import BytesIO
from typing import Tuple
from pdfminer.high_level import extract_text
def extract_text_from_pdf_bytes(b: bytes) -> Tuple[str, int]:
    text = extract_text(BytesIO(b)) or ""; pages = text.count('\f') + 1 if text else 0; return text, pages
