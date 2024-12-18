import pandas as pd
import cvxpy as cp
import numpy as np
import argparse
from collections import defaultdict

# constants
ACCOUNT_NAME = "account_name"
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
        "-ma", # minimum fund allocation
        type=float,
        default=0,
        help="Optional minimum non-zero fund allocation - fund allocation is either greater than " + \
             "this amount or zero (default: 0 - no minimum)."
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
        "-a", # accounts to process
        nargs='+',
        type=str,
        default=None,
        help="Optional subset of accounts to process " + \
             "(default: None - process all accounts)."
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
    data = load_data(args.file_path, args.v)

    # get list of accounts
    accounts = get_accounts(data, args.v)
    # filter accounts if necessary
    if (args.a is not None):
        accounts = accounts.intersection(args.a)

    # iterate over accounts:
    # - generate optimal portfolio
    # - output the results
    for account_name in accounts:
        # extract the matrices and vectors
        account_data = extract_data(data, account_name, args.f, args.v)

        # find the optimal fund allocations
        results = opt_port(account_data, args.sw, args.mf, args.ma, args.v)

        # output the results
        output_results(results)

def output_results(data):

    account_name          = data[ACCOUNT_NAME]
    fund_allocations      = data[FUND_ALLOCATIONS]
    portfolio_allocations = data[ASSET_CLASS_ALLOCATIONS]
    target_allocations    = data[ASSET_CLASS_TARGETS]
    fund_tickers          = data[TICKERS]
    asset_classes         = data[ASSET_CLASSES]
    problem               = data[OPT_PROBLEM]

    # Output account name
    if (account_name is not None):
        line = "=" * 80
        print(f"\n{line}")
        print(f"{account_name.upper()}")
        print(f"{line}")

    # Output optimal fund allocations
    if (fund_allocations.value is not None):
        # add Name column if not provided by inputs
        if ('Name' not in fund_tickers.columns):
            fund_tickers['Name'] = 'N/A'

        print("\nOPTIMAL FUND ALLOCATIONS:")
        print("==========================\n")
        print(f"{"Ticker":10}{"Name":50}{"Allocation":>10}")
        print(f"{"-"*8:<10}{"-"*48:<50}{"-"*10:>10}")
        for (ticker, name), allocation in zip(fund_tickers.itertuples(name=None), fund_allocations.value):
            print(f"{ticker:<10}{name[:48]:<50}{allocation:10.2%}")

    if (portfolio_allocations.value is not None):
        print("\nPORTFOLIO ASSET CLASS ALLOCATIONS:")
        print("===================================\n")
        print(f"{"Asset Class":20}{"Actual":>10}{"Target":>10}{"Diff":>10}")
        print(f"{"-------------------":<20}{"--------":>10}{"--------":>10}{"--------":>10}")
        for asset_class, actual, target in zip(asset_classes, portfolio_allocations.value, target_allocations):
            diff = target - actual
            print(f"{asset_class:20}{actual:10.2%}{target:10.2%}{diff:10.2%}")

    # output solver information
    if (problem is not None):
        print(f"\nSolver Status: {problem.status}")
        print(f"Objective Value (total deviation): {problem.value}\n")

def opt_port(data, sparsity_weight=0.0, max_funds=None, min_alloc=0.0, verbose=False):

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
        x >= min_alloc *z, # Positive fund allocations must be greater than min_alloc
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

def load_data(file_path, verbose=False):
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

    # Define the default dtype for all columns except 'Ticker', 'Description, 'Name' and 'Account'
    dtype_dict = {col: float for col in headers if col not in ['Ticker', 'Description', 'Name', 'Accounts']}

    # Read the full file with the dynamically created dtype and converter
    data = pd.read_csv(
        file_path,
        dtype=dtype_dict,  # Set all columns to float except Ticker
        converters={'Ticker': lambda x: x.strip(),      # Strip whitespace from Ticker column
                    'Description': lambda x: x.strip(), # Strip whitespace from Description column
                    'Name': lambda x: x.strip(),        # Strip whitespace from Name column
                    'Accounts': lambda x: [item.strip() for item in x.split(",")]
        }
    )

    # configure header column
    data.set_index('Ticker', inplace=True)

    return data

def get_accounts(data, verbose=False):
    # get a list of the account names
    if 'Accounts' in data.columns:
        return set(data['Accounts'].explode().unique())
    else:
        return { None }

def drop_columns(data, drop_columns, verbose=False):
    drop_columns = data.columns.intersection(drop_columns)
    return data.drop(columns=drop_columns)

def extract_data(data, account_name=None, funds=None, verbose=False):

    # if account_name is provided then filter out data that is not for
    # the specified account
    if account_name is not None:
        data = data[data['Accounts'].apply(lambda x: account_name in x)]

    # if fund list is provided then only keep funds in the list
    if (funds is not None):
        # keep targets
        keep_funds = funds + ['Targets']
        data = data.loc[data.index.intersection(keep_funds)]

    # Extract fund tickers (with name)
    fund_matrix_columns = data.columns.intersection(['Name'])
    fund_tickers = data.query("index != 'Targets'")[fund_matrix_columns]

    if (verbose):
        print(f"\nfund_tickers: \n{fund_tickers}")

    # drop columns - not needed for other data sets
    data = drop_columns(data, ['Name', 'Description', 'Accounts'])

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
    if (isinstance(target_allocations, pd.DataFrame)):
        # target_allocations is a DataFrame if multiple targets exist
        # otherwise it is a Series
        # giving CVXPY multiple target rows will cause a segmentation fault
        raise ValueError("Expected exactly one target row, but found {}".format(target_allocations.shape[0]))

    # Extract asset classes (column headers)
    asset_classes = data.columns
    if (verbose):
        print(f"\nasset_classes: \n{asset_classes}")

    return {
        ACCOUNT_NAME: account_name,
        FUND_MATRIX: fund_matrix.to_numpy(),
        ASSET_CLASS_TARGETS: target_allocations.to_numpy(),
        TICKERS: fund_tickers,
        ASSET_CLASSES: asset_classes
    }

if __name__ == "__main__":
    main()