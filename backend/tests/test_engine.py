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

    # Test various SSP allocation scenarios
    # Basic 50/50 split
    result = allocate_relative_ssp([100, 100], 200)
    assert result == [100.0, 100.0]
    assert sum(result) == 200

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

    """Test basic straight-line revenue recognition"""
    # 3-month contract for $300 → $100/month
    sched = straight_line(300, date(2025, 1, 1), date(2025, 3, 1))
    assert len(sched) == 3
    assert sum(sched.values()) == 300
    assert sched["2025-01"] == 100
    assert sched["2025-02"] == 100  
    assert sched["2025-03"] == 100

    """Test that final month adjusts for rounding errors"""
    # $100 over 3 months can't divide evenly → 33.33, 33.33, 33.34
    sched = straight_line(100, date(2025, 1, 1), date(2025, 3, 1))
    assert sum(sched.values()) == 100
    # Last month should have the adjustment
    values = list(sched.values())
    assert values[-1] == 100 - sum(values[:-1])

    """Test across year boundaries"""
    sched = straight_line(600, date(2025, 12, 1), date(2026, 2, 1))
    assert len(sched) == 3
    assert "2025-12" in sched
    assert "2026-01" in sched
    assert "2026-02" in sched
    assert sum(sched.values()) == 600

def test_point_in_time():
    sched = point_in_time(500, date(2025,1,1))
    assert sched.get("2025-01")==500

    """Test one-time revenue recognition"""
    sched = point_in_time(1500, date(2025, 6, 15))
    assert len(sched) == 1
    assert sched["2025-06"] == 1500

    """Test point-in-time at year boundaries"""
    sched = point_in_time(500, date(2025, 12, 31))
    assert sched["2025-12"] == 500

def test_percent_complete():
    sched = percent_complete(1000, [{'period':'2025-01','percent_cumulative':0.3},{'period':'2025-02','percent_cumulative':0.8},{'period':'2025-03','percent_cumulative':1.0}])
    assert sum(sched.values())==1000
    assert sched['2025-01']==300

    """Test percent-complete method (common in construction)"""
    progress_data = [
        {"period": "2025-01", "percent_cumulative": 0.2},  # 20% complete
        {"period": "2025-02", "percent_cumulative": 0.6},  # 40% more (60% total)
        {"period": "2025-03", "percent_cumulative": 1.0}   # 40% more (100% total)
    ]
    sched = percent_complete(500000, progress_data)  # $500K construction project
    assert len(sched) == 3
    assert sum(sched.values()) == 500000
    assert sched["2025-01"] == 100000  # 20% of 500,000
    assert sched["2025-02"] == 200000  # 40% of 500,000 (60% - 20%)
    assert sched["2025-03"] == 200000  # 40% of 500,000 (100% - 60%)

    """Test that percent-complete doesn't go backward"""
    progress_data = [
        {"period": "2025-01", "percent_cumulative": 0.5},
        {"period": "2025-02", "percent_cumulative": 0.3}  # This would be invalid
    ]
    sched = percent_complete(1000, progress_data)
    # Should handle decreasing percentages gracefully (0 revenue for negative progress)
    assert sched["2025-02"] == 0

def test_milestones():
    sched = milestones(1000, [{'percent_of_price':0.4,'met_date':'2025-01-15'},{'percent_of_price':0.6,'met_date':'2025-03-01'}])
    assert sum(sched.values())==1000
    assert '2025-01' in sched and '2025-03' in sched

    """Test milestone-based revenue recognition"""
    milestones_data = [
        {"percent_of_price": 0.3, "met_date": "2025-01-15"},  # 30% at design approval
        {"percent_of_price": 0.4, "met_date": "2025-02-20"},  # 40% at prototype
        {"percent_of_price": 0.3, "met_date": "2025-03-25"}   # 30% at final delivery
    ]
    sched = milestones(10000, milestones_data)
    assert len(sched) == 3
    assert sum(sched.values()) == 10000
    assert sched["2025-01"] == 3000  # 30% of 10,000
    assert sched["2025-02"] == 4000  # 40% of 10,000
    assert sched["2025-03"] == 3000  # 30% of 10,000

    """Test multiple milestones in same month"""
    milestones_data = [
        {"percent_of_price": 0.2, "met_date": "2025-01-10"},
        {"percent_of_price": 0.3, "met_date": "2025-01-20"}
    ]
    sched = milestones(1000, milestones_data)
    assert sched["2025-01"] == 500  # 20% + 30% = 50% of 1000
    # ValueError: Milestone percentages must sum to 100%, got 50.0%

def test_commission_amortization():
    sched = amortize_commission(120, 12, date(2025,1,1))
    assert len(sched)==12
    assert round(sum(sched.values()),2)==120.00

    """Test commission expense amortization"""
    sched = amortize_commission(1200, 12, date(2025, 1, 1))  # $1200 over 12 months
    assert len(sched) == 12
    assert sum(sched.values()) == 1200
    # Should be approximately $100/month with final month adjustment
    assert all(99 <= amount <= 101 for amount in sched.values())

    """Test commission with short amortization"""
    sched = amortize_commission(250, 3, date(2025, 1, 1))
    assert len(sched) == 3
    assert sum(sched.values()) == 250
    # Should handle uneven division: 83.33, 83.33, 83.34

    """Test immediate commission expense (practical expedient)"""
    sched = amortize_commission(500, 1, date(2025, 1, 1))
    assert len(sched) == 1
    assert sched["2025-01"] == 500
