
from io import BytesIO
from pdfminer.high_level import extract_text
def extract_text_from_pdf_bytes(b: bytes) -> str: return extract_text(BytesIO(b)) or ""
