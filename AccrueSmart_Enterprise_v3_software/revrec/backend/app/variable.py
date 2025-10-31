'''
Customer Returns (expected_returns_adjustment): This function calculates the adjustment if we expect customers to return a product. 
It reduces the revenue recognized today (contra_revenue) and sets up a liability for the cash you'll have to pay back (refund_liability).

Customer Loyalty Points (loyalty_liability_allocation & loyalty_recognition_schedule): This logic treats loyalty points as a "material right."

The loyalty_liability_allocation function calculates how much of the initial sale price should be deferred (set aside) to represent the value of 
the points given to the customer.

The loyalty_recognition_schedule function then creates a new revenue schedule showing how to recognize this deferred revenue over time as 
the customer either redeems their points or the points expire (breakage).
'''



from datetime import date
from typing import Dict

from .engine import straight_line, add_months


def expected_returns_adjustment(
    point_in_time_revenue: float, 
    returns_rate: float
) -> Dict[str, float]:
    """
    Calculates the adjustment for expected returns on point-in-time revenue.
    
    Per ASC 606, revenue is constrained, and a refund liability is recognized.
    This also creates a "Returns Asset" for the cost of goods expected back.
    The spec suggests a 60% proxy for the asset cost.
    """
    if returns_rate == 0.0 or point_in_time_revenue == 0.0:
        return {"contra_revenue": 0.0, "refund_liability": 0.0, "returns_asset": 0.0}

    # The amount of revenue to *reverse* (constrain)
    adjustment_amount = round(point_in_time_revenue * returns_rate, 2)
    
    # cost of the asset we expect to receive back 
    asset_cost_proxy = round(adjustment_amount * 0.60, 2) 
    
    return {
        # This is a debit to Revenue
        "contra_revenue": -adjustment_amount,  
        
        # This is a credit to the Refund Liability account
        "refund_liability": adjustment_amount, 
        
        # This is a debit to the Returns Asset account
        "returns_asset": asset_cost_proxy     
    }

def loyalty_liability_allocation(
    transaction_price: float, 
    loyalty_pct: float
) -> float:
    """
    Calculates the portion of the transaction price to defer for a material right
    (customer loyalty points), based on a simple percentage of the price
    """
    if loyalty_pct == 0.0:
        return 0.0
    
    # This deferred amount will be subtracted from the transaction price
    # *before* allocating the remainder to other POs.
    deferred_amount = round(transaction_price * loyalty_pct, 2)
    return deferred_amount

def loyalty_recognition_schedule(
    loyalty_liability: float, 
    start: date, 
    months: int, 
    breakage_rate: float
) -> Dict[str, float]:
    """
    Creates a straight-line recognition schedule for the loyalty liability.
    
    It recognizes the amount expected to be redeemed evenly over the
    redemption period (`loyalty_months`)
    
    It recognizes the expected breakage in the final period as a 
    simplification
    """
    if months <= 0 or loyalty_liability == 0.0:
        return {}

    # Calculate the end date for the loyalty redemption period
    end_date = add_months(start, months - 1)
    
    # The total value of points expected to be redeemed
    expected_redemption_value = round(loyalty_liability * (1.0 - breakage_rate), 2)
    
    # The value of points expected to be "broken" (never redeemed) 
    breakage_value = round(loyalty_liability - expected_redemption_value, 2)

    # normal straight-line schedule for the redeemed portion
    schedule = straight_line(expected_redemption_value, start, end_date)
    
    # total breakage amount to the final period of the schedule
    final_period_key = f"{end_date.year}-{end_date.month:02d}"
    schedule[final_period_key] = round(schedule.get(final_period_key, 0.0) + breakage_value, 2)
    
    return schedule
