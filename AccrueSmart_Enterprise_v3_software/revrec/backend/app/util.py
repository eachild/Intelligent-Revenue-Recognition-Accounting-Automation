from datetime import date

def to_float(s:str)->float: return float(s.replace(',',''))

def add_months(d:date, n:int) -> date:
    y = d.year + (d.month - 1 + n) // 12
    m = ((d.month - 1 + n) % 12) + 1
    return date(y,m,1)