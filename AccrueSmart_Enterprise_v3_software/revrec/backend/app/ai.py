
def classify_standard(text:str): 
    t=text.lower()
    if "lease" in t: return "ASC842","Lease keywords"
    if "customer" in t or "subscription" in t or "license" in t: return "ASC606","Customer terms"
    return "Unknown","No clear match"
def extract_pos(text:str):
    out=[]
    if "hardware" in text.lower(): out.append({"description":"Hardware","method":"point_in_time","start_date":"2025-01-01","ssp":800.0,"snippet":"...hardware..."})
    if "saas" in text.lower() or "software" in text.lower(): out.append({"description":"SaaS","method":"straight_line","start_date":"2025-01-01","end_date":"2025-12-01","ssp":400.0,"snippet":"...saas..."})
    return out
def detect_risks(text:str):
    r=[]; t=text.lower()
    if "right to return" in t: r.append({"type":"right_of_return","severity":"high","snippet":"...right to return..."})
    return r
def recommend_language(text:str):
    rec=[]; t=text.lower()
    if "right to return" in t: rec.append({"issue":"Return clause","suggested_language":"Define estimation method for returns."})
    return rec
