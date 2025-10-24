from typing import Dict
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def pdf_note(title: str, sections: Dict[str, Dict[str,float]]|None=None, bullets: Dict[str,str]|None=None) -> bytes:
    styles=getSampleStyleSheet(); story=[Paragraph(title, styles['Title']), Spacer(1,12)]
    if bullets:
        for k,v in bullets.items(): story.append(Paragraph(f"<b>{k}</b>: {v}", styles['Normal']))
    if sections:
        for name, m in sections.items():
            rows=[["Period","Amount"]]+[[p,f"${v:,.2f}"] for p,v in sorted(m.items())]
            from reportlab.platypus import Table
            t=Table(rows); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey)]))
            story.append(Paragraph(name, styles['Heading2'])); story.append(t)
    buf=BytesIO(); SimpleDocTemplate(buf, pagesize=LETTER, title=title).build(story); return buf.getvalue()