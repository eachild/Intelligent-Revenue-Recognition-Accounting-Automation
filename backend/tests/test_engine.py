# import pytest # suggested
from datetime import date
from app.engine import allocate_relative_ssp, straight_line, point_in_time, percent_complete, milestones, amortize_commission

# Test cases for the core SSP allocation math
def test_allocate_ties_out():
    # Test basic SSP allocation with normal values
    out = allocate_relative_ssp([80,20], 1000)
    assert sum(out)==1000
    assert round(out[0],1)==800.00
    assert round(out[1],1)==200.00

    # Test that allocation handles rounding correctly
    # Should distribute as 33.33, 33.33, 33.34 to sum to 100.00
    ssps = [100.0, 100.0, 100.0]
    total_price = 100.0
    result = allocate_relative_ssp(ssps, total_price)
    assert sum(result) == total_price
    assert len(result) == 3
    assert all(33.00 <= x <= 34.00 for x in result)

    # Test allocation when total SSP is zero
    ssps = [0.0, 0.0, 0.0]
    total_price = 300.0
    result = allocate_relative_ssp(ssps, total_price)
    assert sum(result) == total_price
    assert result == [100.0, 100.0, 100.0]  # Should distribute evenly

    # Test allocation with single performance obligation
    ssps = [500.0]
    total_price = 500.0
    result = allocate_relative_ssp(ssps, total_price)
    assert result == [500.0]
    assert sum(result) == total_price

    # Test allocation with empty SSP list
    ssps = []
    total_price = 500.0
    result = allocate_relative_ssp(ssps, total_price)
    assert result == []

    # Test tricky case that requires careful rounding
    ssps = [33.33, 33.33, 33.34]
    total_price = 100.0
    result = allocate_relative_ssp(ssps, total_price)
    assert sum(result) == total_price
    assert result == [33.33, 33.33, 33.34]

    # Test with large dollar amounts
    ssps = [500000.0, 300000.0, 200000.0]
    total_price = 1000000.0
    result = allocate_relative_ssp(ssps, total_price)
    # 50%, 30%, 20% of 1,000,000
    expected = [500000.0, 300000.0, 200000.0]
    assert result == expected
    assert sum(result) == total_price

    # Test that maintains 2-decimal precision
    ssps = [10.0, 10.0]
    total_price = 13.33
    result = allocate_relative_ssp(ssps, total_price)
    assert all(len(str(x).split('.')[1]) <= 2 for x in result)  # Max 2 decimal places
    assert sum(result) == total_price

    # Test with uneven SSP distribution
    ssps = [75.0, 25.0]
    total_price = 47.89
    result = allocate_relative_ssp(ssps, total_price)
    # 75% of 47.89 = 35.9175 -> 35.92
    # 25% of 47.89 = 11.9725 -> 11.97
    # Total would still be 35.92 + 11.97 = 47.89
    assert sum(result) == total_price
    assert result == [35.92, 11.97]

# Test cases for the various revenue recognition schedules?
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
