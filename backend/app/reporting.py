
from typing import Dict
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def summarize_schedules(schedules: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    total: Dict[str, float] = {}
    for _, sched in schedules.items():
        for period, amt in sched.items():
            total[period] = round(total.get(period, 0.0) + float(amt), 2)
    return dict(sorted(total.items()))

def pdf_disclosure(contract_id: str, customer: str, tp: float,
                   schedules_by_po: Dict[str, Dict[str, float]],
                   commission_schedule: Dict[str, float] | None = None,
                   adjustments: Dict | None = None) -> bytes:
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"ASC 606 Disclosure — Contract {contract_id}", styles['Title']))
    story.append(Paragraph(f"Customer: {customer}", styles['Normal']))
    story.append(Paragraph(f"Transaction Price: ${tp:,.2f}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Disaggregation of Revenue (by Performance Obligation)", styles['Heading2']))
    for poid, sched in schedules_by_po.items():
        rows=[["Period","Revenue"]] + [[p, f"${v:,.2f}"] for p,v in sorted(sched.items())]
        t=Table(rows, hAlign='LEFT'); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey)]))
        story.append(Paragraph(f"{poid}", styles['Heading3'])); story.append(t); story.append(Spacer(1,8))

    total_sched = summarize_schedules(schedules_by_po)
    story.append(Paragraph("Contract Balances Rollforward", styles['Heading2']))
    rows=[["Period","Revenue Recognized","Deferred Revenue (End)"]]
    deferred=tp
    for period, rev in sorted(total_sched.items()):
        deferred = round(deferred - rev, 2)
        rows.append([period, f"${rev:,.2f}", f"${deferred:,.2f}"])
    t=Table(rows, hAlign='LEFT'); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey)]))
    story.append(t); story.append(Spacer(1,8))

    if adjustments:
        story.append(Paragraph("Variable Consideration & Loyalty Adjustments", styles['Heading2']))
        for k,v in adjustments.items():
            if isinstance(v, dict):
                rows=[["Key","Amount"]] + [[kk, f"${vv:,.2f}"] for kk,vv in v.items()]
                t=Table(rows, hAlign='LEFT'); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey)]))
                story.append(Paragraph(k, styles['Heading3'])); story.append(t)
            else:
                story.append(Paragraph(f"{k}: ${v:,.2f}", styles['Normal']))
        story.append(Spacer(1,8))

    end_deferred = round(tp - sum(total_sched.values()), 2)
    story.append(Paragraph(f"Remaining Performance Obligations (RPO): ${end_deferred:,.2f}", styles['Normal']))
    story.append(Spacer(1, 8))

    if commission_schedule:
        story.append(Paragraph("Deferred Contract Costs — Commission Amortization", styles['Heading2']))
        rows=[["Period","Commission Expense","Deferred Cost (End)"]]
        total_comm = sum(commission_schedule.values())
        remaining = total_comm
        for period, exp in sorted(commission_schedule.items()):
            remaining = round(remaining - exp, 2)
            rows.append([period, f"${exp:,.2f}", f"${remaining:,.2f}"])
        t=Table(rows, hAlign='LEFT'); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey)]))
        story.append(t)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, title="ASC606 Disclosure")
    doc.build(story)
    return buf.getvalue()
