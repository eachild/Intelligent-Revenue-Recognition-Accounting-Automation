
from datetime import date
from app.engine import allocate_relative_ssp, straight_line, point_in_time, percent_complete, milestones, amortize_commission

def test_allocate_ties_out():
    out = allocate_relative_ssp([80,20], 1000)
    assert sum(out)==1000
    assert round(out[0],2)==800.00

def test_straight_line_trueup():
    sched = straight_line(100, date(2025,1,1), date(2025,3,1))
    assert sum(sched.values())==100
    assert len(sched)==3

def test_point_in_time():
    sched = point_in_time(500, date(2025,1,1))
    assert sched.get("2025-01")==500

def test_percent_complete():
    sched = percent_complete(1000, [{'period':'2025-01','percent_cumulative':0.3},{'period':'2025-02','percent_cumulative':0.8},{'period':'2025-03','percent_cumulative':1.0}])
    assert sum(sched.values())==1000
    assert sched['2025-01']==300

def test_milestones():
    sched = milestones(1000, [{'percent_of_price':0.4,'met_date':'2025-01-15'},{'percent_of_price':0.6,'met_date':'2025-03-01'}])
    assert sum(sched.values())==1000
    assert '2025-01' in sched and '2025-03' in sched

def test_commission_amortization():
    sched = amortize_commission(120, 12, date(2025,1,1))
    assert len(sched)==12
    assert round(sum(sched.values()),2)==120.00
