import pandas as pd
import cvxpy as cp
import numpy as np
import argparse
from collections import defaultdict

# constants
TICKERS = "tickers"
ASSET_CLASSES = "asset_classes"
FUND_MATRIX = "fund_matrix"
ASSET_CLASS_TARGETS = "asset_class_targets"
FUND_ALLOCATIONS = "fund_allocations"
ASSET_CLASS_ALLOCATIONS = "asset_class_allocations"
OPT_PROBLEM = "opt_problem"

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Optimize portfolio fund allocations based on a CSV file.")
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the CSV file containing fund allocations and target asset class percentages."
    )
    parser.add_argument(
        "-sw", # sparsity weight
        type=float,
        default=0,
        help="Weight for the sparsity penalty in the objective function (default: 0 - no sparsity penalty)."
    )
    parser.add_argument(
        "-mf", # max funds
        type=int,
        default=None,
        help="Optional maximum number of funds to use (default: None - no maximum)."
    )
    parser.add_argument(
        "-f", # funds to consider
        nargs='+',
        type=str,
        default=None,
        help="Optional subset of funds to consider for inclusion in final portfolio " + \
             "(default: None - consider all funds in fund matrix)."
    )
    parser.add_argument(
        "-v", # verbose
        default=False,
        action='store_true',
        help="Optional generate verbose output."
    )

    # Parse command-line arguments
    args = parser.parse_args()

    # load the data
    data = load_data(args.file_path, args.f, args.v)

    # find the optimal fund allocations
    data = opt_port(data, args.sw, args.mf, args.v)

    # output the results
    output_results(data)

def output_results(data):

    fund_allocations      = data[FUND_ALLOCATIONS]
    portfolio_allocations = data[ASSET_CLASS_ALLOCATIONS]
    target_allocations    = data[ASSET_CLASS_TARGETS]
    fund_tickers          = data[TICKERS]
    asset_classes         = data[ASSET_CLASSES]
    problem               = data[OPT_PROBLEM]

    # Output optimal fund allocations
    if (fund_allocations.value is not None):
        print("\nOPTIMAL FUND ALLOCATIONS:")
        print("==========================\n")
        print(f"{"Ticker":10}{"Allocation":>10}")
        print(f"{"--------":<10}{"----------":>10}")
        for ticker, allocation in zip(fund_tickers, fund_allocations.value):
            print(f"{ticker:<10}{allocation:10.2%}")

    if (portfolio_allocations.value is not None):
        print("\nPORTFOLIO ASSET CLASS ALLOCATIONS:")
        print("===================================\n")
        print(f"{"Asset Class":20}{"Actual":>10}{"Target":>10}{"Diff":>10}")
        print(f"{"-------------------":<20}{"--------":>10}{"--------":>10}{"--------":>10}")
        for asset_class, actual, target in zip(asset_classes, portfolio_allocations.value, target_allocations):
            diff = target - actual
            print(f"{asset_class:20}{actual:10.2%}{target:10.2%}{diff:10.2%}")
    
    print(f"\nSolver Status: {problem.status}")
    print(f"Objective Value (total deviation): {problem.value}\n")

def opt_port(data, sparsity_weight=0.0, max_funds=None, verbose=False):

    fund_matrix = data[FUND_MATRIX]
    target_allocations = data[ASSET_CLASS_TARGETS]

    # Define the optimization problem
    num_funds = fund_matrix.shape[0]
    x = cp.Variable(num_funds)  # Allocation to each fund
    z = cp.Variable(num_funds, boolean=True)  # Binary selection variables

    # Resulting portfolio allocation
    portfolio_allocations = fund_matrix.T @ x

    # Objective: Minimize squared difference + sparsity penalty
    objective = cp.Minimize(
        cp.sum_squares(portfolio_allocations - target_allocations)
        + sparsity_weight * cp.sum(z) # Penalize the number of funds
    )

    # Constraints
    constraints = [
        cp.sum(x) == 1,  # Allocations must sum to 100%
        x >= 0,          # No negative allocation
        x <= z,          # Link x and z (if z=0, x=0)
    ]

    # Add maximum funds constraint if specified
    if max_funds is not None:
        constraints.append(cp.sum(z) <= max_funds)

    # Solve the problem using SCIP solver (supports MIQP)
    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.SCIP, verbose=verbose)

    data[FUND_ALLOCATIONS] = x
    data[ASSET_CLASS_ALLOCATIONS] = portfolio_allocations
    data[OPT_PROBLEM] = problem

    return data

def load_data(file_path, funds=None, verbose=False):
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
    # Read only the header row
    headers = pd.read_csv(file_path, nrows=0).columns.tolist()

    # Define the default dtype for all columns except 'Ticker', 'Description, and 'Name'
    dtype_dict = {col: float for col in headers if col not in ['Ticker', 'Description', 'Name']}

    # Read the full file with the dynamically created dtype and converter
    data = pd.read_csv(
        file_path,
        dtype=dtype_dict,  # Set all columns to float except Ticker
        converters={'Ticker': lambda x: x.strip(),      # Strip whitespace from Ticker column
                    'Description': lambda x: x.strip(), # Strip whitespace from Description column
                    'Name': lambda x: x.strip()         # Strip whitespace from Name column
                    }
    )

    # drop Name and Description columns
    drop_columns = data.columns.intersection(['Name', 'Description'])
    data = data.drop(columns=drop_columns)

    # configure header column
    data.set_index('Ticker', inplace=True)

    # extract the matrices and vectors
    return extract_data(data, funds, verbose)

def extract_data(data, funds=None, verbose=False):

    # Extract fund_matrix (all rows except 'Targets')
    if (funds is None):
        fund_matrix = data.query("index != 'Targets'")
    else:
        valid_funds = data.index.intersection(funds)
        fund_matrix = data.loc[valid_funds]
    if (verbose):
        print(f"\nfund_matrix: \n{fund_matrix}")

    # Extract target_allocations ('Targets' row)
    target_allocations = data.loc['Targets']
    if (verbose):
        print(f"\ntarget_allocations: \n{target_allocations}")

    # Extract fund tickers (index column of the fund_matrix)
    fund_tickers = fund_matrix.index
    if (verbose):
        print(f"\nfund_tickers: \n{fund_tickers}")

    # Extract asset classes (column headers)
    asset_classes = data.columns
    if (verbose):
        print(f"\nasset_classes: \n{asset_classes}")

    return {
        FUND_MATRIX: fund_matrix.values,
        ASSET_CLASS_TARGETS: target_allocations.values,
        TICKERS: fund_tickers.values,
        ASSET_CLASSES: asset_classes.values
    }

if __name__ == "__main__":
    main()