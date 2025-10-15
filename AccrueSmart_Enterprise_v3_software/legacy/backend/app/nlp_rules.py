
import re
from .util import to_float
def find_currency(text:str):
    m=re.search(r'\b(USD|EUR|GBP|INR|JPY|CAD|AUD)\b', text, re.I); return m.group(1).upper() if m else None
def find_total_price(text:str):
    key = re.search(r'(transaction price|contract value|total consideration|total price)[^\$]{0,40}\$\s?([0-9,]+\.?[0-9]{0,2})', text, re.I)
    if key: return to_float(key.group(2))
    amounts=[a.replace(',','') for a in re.findall(r'\$\s?([0-9][0-9,]*\.?[0-9]{0,2})', text)]
    nums=[float(a) for a in amounts] if amounts else []; return max(nums) if nums else None
def detect_standard(text:str):
    t=text.lower()
    if any(k in t for k in ['lease term','right-of-use asset','rou asset','lease liability']): return 'ASC842','Contains lease terminology'
    if any(k in t for k in ['collaboration','co-development','co marketing']): return 'ASC808','Collaborative arrangement indicators present'
    if any(k in t for k in ['nonfinancial asset','sale of property','intangible sale']): return 'ASC610-20','Sale of nonfinancial assets indicated'
    if any(k in t for k in ['insurance policy','premium','claims handler']): return 'ASC945/944','Insurance-like contract'
    if any(k in t for k in ['customer','deliver','performance obligation','support','subscription','license','maintenance','milestone','implementation']): return 'ASC606','Customer contract indicators present'
    return 'Unknown','No clear match; manual review needed'
def extract_pos(text:str):
    out=[]; import re as _r
    for line in text.splitlines():
        l=line.strip()
        if not l: continue
        if _r.search(r'\b(hardware|device|equipment|handset)\b', l, _r.I): out.append({'description':'Hardware','method':'point_in_time'})
        if _r.search(r'\b(software|license|subscription|saas)\b', l, _r.I): out.append({'description':'Software/Subscription','method':'straight_line'})
        if _r.search(r'\b(maintenance|support|warranty service)\b', l, _r.I): out.append({'description':'Maintenance/Support','method':'straight_line'})
        if _r.search(r'\b(implementation|setup|professional services|deployment)\b', l, _r.I): out.append({'description':'Implementation Services','method':'milestone'})
        if _r.search(r'\b(construction|build|building|facility)\b', l, _r.I): out.append({'description':'Construction Unit','method':'percent_complete'})
    seen=set(); dedup=[]
    for po in out:
        if po['description'] in seen: continue
        seen.add(po['description']); dedup.append(po)
    return dedup
def detect_risks(text:str):
    findings=[]; import re as _r
    def add(t, s, sev='medium', c=None): findings.append({'type':t,'snippet':s[:200],'severity':sev,'comment':c})
    pats=[('right_of_return', r'right to return|returns? allowed|refund within \d+ days', 'high', 'Refund liability & variable consideration'),
          ('acceptance', r'customer acceptance|acceptance testing|acceptance criteria', 'high', 'Defer until acceptance'),
          ('bill_and_hold', r'bill and hold', 'high', 'Strict criteria before recognition'),
          ('consignment', r'consignment|consignor|consignee', 'high', 'End-customer control triggers recognition'),
          ('significant_financing', r'\b(APR|\d+% interest|financing arrangement)\b', 'medium', 'Consider SFC'),
          ('nonrefundable_fee', r'nonrefundable (upfront )?fee', 'medium', 'Defer unless distinct')]
    for key, pat, sev, note in pats:
        m=_r.search(pat, text, _r.I)
        if m: add(key, text[m.start()-30:m.end()+30], sev, note)
    return findings
def extract_commission(text:str):
    import re as _r; m=_r.search(r'(sales commission|commission)\s*(?:of|:)\s*\$\s?([0-9,]+\.?[0-9]{0,2})', text, _r.I); 
    return to_float(m.group(2)) if m else None
def recommendations(text:str):
    recs=[]; low=text.lower()
    if 'right to return' in low and 'restocking fee' not in low: recs.append({'issue':'Right of return','suggested_language':'Add restocking fee and defined return window; specify estimation method.','rationale':'Reduce reversal risk'})
    if 'acceptance' in low and 'criteria' not in low: recs.append({'issue':'Acceptance without criteria','suggested_language':'Define objective criteria and testing responsibility; link recognition to formal acceptance.','rationale':'Prevent premature recognition'})
    return recs
def summarize_revenue(text:str):
    lines=[l.strip() for l in text.splitlines() if l.strip()]; preview=' '.join(lines[:8])[:600]
    return f"This contract appears to include customer deliverables. Preliminary obligations detected. Excerpt: {preview}..."
def summarize_nonrevenue(text:str):
    lines=[l.strip() for l in text.splitlines() if l.strip()]; preview=' '.join(lines[:8])[:600]
    return f"This document likely falls outside ASC 606. Route to appropriate guidance. Excerpt: {preview}..."
