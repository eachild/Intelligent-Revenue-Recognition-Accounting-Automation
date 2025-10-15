import unittest
from datetime import date
from AccrueSmart_Enterprise_v3_software.revrec.backend.app.engine import add_months, daterange_months, allocate_relative_ssp, straight_line, point_in_time

class TestEngineFunctions(unittest.TestCase):
    #test add_monthspython test_engine.py
    def test1_add_months_basic(self):
        d = date(2025, 1, 1)
        result = add_months(d, 1)
        print("\nTest 1: add 1 month--> ", d, "-->", result)

        result2 = add_months(d, 12)
        print("Test 1.1: add 12 months-->", d, "-->", result2)
        
        result3 = add_months(d, 16)
        print("Test 1.2: add 15 months-->", d, "-->", result3, "\n")
        

    #test daterange_months
    def test2_daterange_months(self):
        start = date(2025, 1, 15)
        end = date(2025, 3, 10)
        months = list(daterange_months(start, end))
        print("Test 2: Creates daterange--> ", months, "\n")

    #test allocate_relative_ssp
    def test3_allocate_relative_ssp(self):
        ssps = [100, 200, 300, 50]
        total = 650
        allocation = allocate_relative_ssp(ssps, total)
        print("Test 3: allocate relative ssp--> ", allocation)

        #test rounding
        ssps = [1, 1, 1]
        total = 100
        allocation = allocate_relative_ssp(ssps, total)
        print("Test 3.1: allocate relative ssp--> ", allocation)

        #test all zeros
        ssps = [0, 0, 0, 0, 0]
        total = 100
        allocation = allocate_relative_ssp(ssps, total)
        print("Test 3.2: allocate relative ssp--> ", allocation, "\n")

    #test straight_line
    def test4_straight_line(self):
        start = date(2025, 1, 1)
        end = date(2025, 3, 1)
        price = 300
        schedule = straight_line(price, start, end)
        print("Test 4: Straight line allocation--> ", schedule, "\n")

    #test point_in_time
    def test5_point_in_time(self):
        all_at_once_date = date(2025, 12, 10)
        price = 500
        schedule2 = point_in_time(price, all_at_once_date)
        print("Test 5: point in time allocation--> ", schedule2)

#run the tests
if __name__ == "__main__":
    unittest.main()
