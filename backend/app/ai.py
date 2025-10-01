
import re, statistics
METHOD_KEYWORDS={'point_in_time':['delivery','transfer','shipment','upon acceptance','one-time'],
                 'straight_line':['subscription','saas','over','monthly','annually','maintenance'],
                 'milestone':['milestone','phase','go-live','acceptance','stage'],
                 'percent_complete':['percent complete','cost-to-cost','progress','completion']}
def contract_parse_text(text:str):
    lines=[l.strip() for l in text.splitlines() if l.strip()]
    pos=[]; idx=0
    for line in lines:
        low=line.lower()
        if any(k in low for k in ['subscription','maintenance','implementation','training','device','license','building','construction']):
            idx+=1
            method='straight_line'
            for m,kws in METHOD_KEYWORDS.items():
                if any(k in low for k in kws): method=m; break
            m=re.search(r"(\d+(?:\.\d{2})?)", line.replace(',','')); ssp=float(m.group(1)) if m else 0.0
            pos.append({'po_id':f'PO-{idx:02d}','description':line,'ssp':ssp,'method':method})
    nums=re.findall(r"(\$?\d[\d,]*(?:\.\d{2})?)", text.replace(',',''))
    return {'pos':pos,'amounts_found':nums}
def suggest_ssp(history):
    if not history: return 0.0
    return round(statistics.median(history),2)
