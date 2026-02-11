
import sys
import os
from pprint import pprint

# Add the parent directory to the Python path to allow for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsing_pipeline import run_contract_parsing

def test_parsing():
    """
    Tests the contract parsing pipeline with a sample contract text.
    """
    # You can replace this with text from a file or any other contract text.
    contract_text = """
    Agreement for Office Building Construction

    This contract is entered into for the construction of a new corporate office building.
    The total transaction price for this project is $5,000,000 USD.

    The project is divided into the following distinct performance obligations:
    1. Architectural Design and Permitting: Complete architectural plans and obtain all necessary construction permits.
    2. Construction and Finishing: Construct and finish the building as per the approved design.

    This agreement is governed by the principles of ASC606.
    A sales commission of 2% of the total contract value is applicable.
    """

    print("--- Running Test with Sample Contract Text ---")
    result = run_contract_parsing(contract_text)

    print("\n--- Parsing Result ---")
    # Using pprint for a more readable output of the result object
    pprint(result)
    print("----------------------")


if __name__ == "__main__":
    test_parsing()
