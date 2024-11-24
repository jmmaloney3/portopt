import pandas as pd
import cvxpy as cp
import numpy as np
import argparse
from collections import defaultdict

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Optimize portfolio fund allocations based on a CSV file.")
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the CSV file containing fund allocations and target asset class percentages."
    )

    # Parse command-line arguments
    args = parser.parse_args()

    # load the data
    fund_matrix, target_allocations, fund_tickers, asset_classes = \
        load_data(args.file_path)

    # find the optimal fund allocations
    fund_allocations, portfolio_allocations, obj_value = opt_port(fund_matrix, target_allocations)

    # Output optimal fund allocations
    print("\nOPTIMAL FUND ALLOCATIONS:")
    print("==========================\n")
    print(f"{"Ticker":10}{"Allocation":>10}")
    print(f"{"--------":<10}{"----------":>10}")
    for ticker, allocation in zip(fund_tickers, fund_allocations.value):
        print(f"{ticker:<10}{allocation:10.2%}")

    print("\nPORTFOLIO ASSET CLASS ALLOCATIONS:")
    print("===================================\n")
    print(f"{"Asset Class":20}{"Actual":>10}{"Target":>10}{"Diff":>10}")
    print(f"{"-------------------":<20}{"--------":>10}{"--------":>10}{"--------":>10}")
    for asset_class, actual, target in zip(asset_classes, portfolio_allocations.value, target_allocations):
        diff = target - actual
        print(f"{asset_class:20}{actual:10.2%}{target:10.2%}{diff:10.2%}")
    
    print(f"\nObjective Value (total deviation): {obj_value}\n")


def opt_port(fund_matrix, target_allocations):

    # Define the optimization problem
    num_funds = fund_matrix.shape[0]
    x = cp.Variable(num_funds)  # Allocation to each fund

    # Resulting portfolio allocation
    portfolio_allocations = fund_matrix.T @ x

    # Objective: Minimize the squared difference between actual and desired allocations
    objective = cp.Minimize(cp.sum_squares(portfolio_allocations - target_allocations))

    # Constraints
    constraints = [
        cp.sum(x) == 1,  # Allocations must sum to 100%
        x >= 0           # No negative allocation
    ]

    # Solve the problem
    problem = cp.Problem(objective, constraints)
    problem.solve()

    return x, portfolio_allocations, problem.value

def load_data(file_path):
    """
    Load the fund and target asset allocations from a csv file.  The
    csv file has the following structure:
    * header row with first column named "Ticker" and the remaining columns
      names corresponding to asset classes
    * one row for each fund with the fund ticker symbol and the fund's asset
      class allocations
    * footer row containing the desired asset class allocations for the final
      portfolio

    Args:
        file_path (string): path to the file holding the data matrix
        b (int): The second number.

    Returns:
        fund_matrix: matrix containing the asset class allocations for each
          fund
        target_allocations: array of the desired asset class allocations for
          the final portfolio
        fund_tickers: array of fund tickers
        asset_classes: array of asset class names

    Raises:
        Error: ???
    """
    default_types = defaultdict(lambda: float, Ticker="str")
    data = pd.read_csv(file_path, dtype=default_types)
    return extract_data(data)


def extract_data(data):

    # Extract fund_matrix (all rows except the footer and first column)
    fund_matrix = data.iloc[:-1, 1:].values

    # Extract target_allocations (footer row, excluding the first column)
    target_allocations = data.iloc[-1, 1:].values

    # Extract fund tickers (first column, excluding the footer row)
    fund_tickers = data.iloc[:-1, 0].values

    # Extract asset classes (header row, excluding the first column)
    asset_classes = data.columns[1:]

    return fund_matrix, target_allocations, fund_tickers, asset_classes

if __name__ == "__main__":
    main()