"""
Portfolio loading and analysis functions.

This module provides functions for loading and analyzing investment portfolio data,
including fund allocations, holdings, and asset class weights. It supports various
input formats and handles special cases like money market funds and options.

Functions:
    load_fund_asset_class_weights: Load fund asset class allocations from CSV
    load_holdings: Load portfolio holdings from CSV export
    consolidate_holdings: Combine holdings across accounts
    get_holding_allocations: Calculate portfolio allocations by security
    get_asset_class_allocations: Calculate portfolio allocations by asset class
    load_and_consolidate_holdings: Load and consolidate holdings from multiple CSV files

Dependencies:
    - pandas: Data manipulation and analysis
    - numpy: Numerical computing
    - re: Regular expressions for parsing symbols
    - market_data: Local module for retrieving security prices
"""

import re
import csv
import numpy as np
import pandas as pd
from typing import Optional
from market_data import get_latest_ticker_prices
import os

def load_fund_asset_class_weights(file_path: str) -> pd.DataFrame:
    """
    Load fund asset class allocations from a CSV file.

    The CSV file should have:
    * First column named 'Ticker' containing fund ticker symbols
    * Additional columns for asset classes containing allocation weights
    * Optional 'Name' column with fund names
    * Optional 'Description' column with fund descriptions
    * Optional 'Accounts' column (will be excluded from output)
    * Optional 'Target' rows (will be excluded from output)

    Args:
        file_path: Path to the CSV file containing fund allocations

    Returns:
        DataFrame indexed by ticker symbols containing asset class allocations.
        Asset class weights sum to 1 (may include negative weights for leveraged positions).

    Raises:
        ValueError: If file format is invalid or if weights don't sum to 1
    """
    # Read only the header row to determine column types
    headers = pd.read_csv(file_path, nrows=0).columns.tolist()

    # Define dtype for each column
    # - String columns: Ticker, Description, Name, Accounts
    # - Float columns: All others (asset class weights)
    dtype_dict = {
        col: float for col in headers
        if col not in ['Ticker', 'Description', 'Name', 'Accounts']
    }

    # Define string handling for non-numeric columns
    converters = {
        'Ticker': lambda x: x.strip(),
        'Description': lambda x: x.strip(),
        'Name': lambda x: x.strip(),
        'Accounts': lambda x: [item.strip() for item in x.split(",") if item.strip()]
    }

    # Read the full file
    data = pd.read_csv(
        file_path,
        dtype=dtype_dict,
        converters=converters
    )

    # Set Ticker as index
    data.set_index('Ticker', inplace=True)

    # Remove Target rows
    data = data[~data.index.str.contains('Target', case=False, na=False)]

    # Remove Accounts column if it exists
    if 'Accounts' in data.columns:
        data = data.drop(columns=['Accounts'])

    # Get weight columns (excluding Name and Description)
    weight_columns = [col for col in data.columns
                     if col not in ['Name', 'Description']]

    # Verify weights sum to approximately 1
    row_sums = data[weight_columns].sum(axis=1)
    if not np.allclose(row_sums, 1.0, rtol=1e-3):
        problematic_funds = data.index[~np.isclose(row_sums, 1.0, rtol=1e-3)]
        raise ValueError(
            f"Fund weights do not sum to 1 for: {list(problematic_funds)}\n"
            f"Sums: {row_sums[problematic_funds]}"
        )

    return data

def load_holdings(file_path: str, verbose: bool = False) -> pd.DataFrame:
    """
    Load holdings from CSV export file

    The CSV file should contain position details with some or all of:
    * Account information (Account Number, Account Name)
    * Position details (Symbol/SYMBOL/Ticker, Quantity/Shares/UNIT/SHARE OWNED, Cost Basis/Average Cost)
    * Dollar Value amount (Balance/BALANCE/Current Value/Total Value)
    * Optional non-CSV lines (will be detected and skipped)
    * Optional footer section (will be detected and skipped)

    Special handling:
    * Money market funds: When Quantity is empty, uses Original Value (assuming $1/share)
                         for both Quantity and Cost Basis (if Cost Basis is not provided)
    * Cost Basis:
        1. Uses 'Cost Basis' or 'Cost Basis Total' column if either exists
        2. If neither exists, calculates from Average Cost * Quantity if both are available
        3. Otherwise, sets to NaN
    * Original Value:
        - Loaded from 'Balance', 'BALANCE', 'Current Value', or 'Total Value' columns
        - If not found, sets to NaN
    * Missing columns: Populated with 'N/A' for strings, NaN for numeric values
    * Empty string values: Replaced with 'N/A'
    * Ticker symbols:
        - Extra characters (like '*') are removed from regular symbols
        - Option contracts (e.g., SPY250321P580) are preserved (leading hyphen removed)

    Args:
        file_path: Path to the portfolio CSV file
        verbose: Optional; if True, prints a message with the number rows loaded.
                 Defaults to False.

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Account Number (if available, else 'N/A')
        - Account Name (if available, else 'N/A')
        - Quantity (from Quantity or Shares column)
        - Cost Basis (from Cost Basis/Cost Basis Total columns, or calculated from Average Cost * Quantity)
        - Original Value (from Balance/BALANCE/Current Value/Total Value columns)

    Raises:
        ValueError:
        - If file_path does not exist or is not a file
        - If file format is invalid, required Symbol column is missing, or neither Quantity
          nor Shares column is present
        TypeError: If file_path is not a string.
    """
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string.")
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")

    def clean_numeric(x):
        if not x or x == '--':
            return None
        # Remove quotes, dollar signs, and commas
        return float(str(x).replace('"', '').replace('$', '').replace(',', ''))

    def clean_string(x):
        return x.strip() if x and x.strip() else 'N/A'

    def clean_ticker(x):
        """Clean ticker symbols, handling various formats"""
        if not x or not x.strip():
            return 'N/A'

        # Convert to uppercase and strip whitespace
        ticker = str(x).strip().upper()

        # Take only the first word (handles "VTSAX Some Fund Name" format)
        ticker = ticker.split()[0]

        # Check if it's an option contract (e.g., -SPY250321P580)
        option_pattern = r'^-?([A-Z]{1,5}\d{6}[CP]\d+)$'
        option_match = re.match(option_pattern, ticker)
        if option_match:
            # Return the option ticker without the leading hyphen
            return option_match.group(1)

        # For regular symbols, remove any non-alphanumeric characters except dots and hyphens
        return re.sub(r'[^A-Z0-9.-]', '', ticker)

    def is_header_row(row):
        """Check if row contains required column headers.

        Args:
            row: A list of column headers to check

        Returns:
            bool: True if row contains required Symbol and Quantity columns
                 (with variations in column names supported)
        """
        # Convert all column names to uppercase for case-insensitive matching
        cols_upper = [col.upper() for col in row]

        # Check for Symbol column (may be called SYMBOL or INVESTMENT)
        has_symbol = any(col in cols_upper for col in ['SYMBOL', 'INVESTMENT'])

        # Check for Quantity column (may be called Shares or UNIT/SHARE OWNED)
        has_quantity = any(col in row for col in ['Quantity', 'Shares', 'UNIT/SHARE OWNED'])

        # Row is a header if it contains both required columns
        return has_symbol and has_quantity

    # Define converters for data cleaning
    converters = {
        'Account Number': clean_string,
        'Account Name': clean_string,
        'Symbol': clean_ticker,
        'SYMBOL': clean_ticker,
        'Investment': clean_ticker,
        'Quantity': clean_numeric,
        'Shares': clean_numeric,
        'UNIT/SHARE OWNED': clean_numeric,
        'Current Value': clean_numeric,
        'Total Value': clean_numeric,
        'Balance': clean_numeric,
        'BALANCE': clean_numeric,
        'Cost Basis': clean_numeric,
        'Cost Basis Total': clean_numeric,
        'Average Cost': clean_numeric
    }

    # Read CSV rows and find header
    header = None
    data_rows = []

    with open(file_path, 'r', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:  # Skip empty rows
                continue

            if header is None:
                # Look for header row with required columns
                if is_header_row(row):
                    header = row
                    header_field_count = len(row)
                continue

            # Only include rows that match header field count
            if len(row) == header_field_count:
                data_rows.append(row)
            else:
                # Stop at first row with different field count (footer)
                break

    if header is None:
        raise ValueError("Could not find header row with required columns")

    # Create DataFrame and apply converters
    data = pd.DataFrame(data_rows, columns=header)
    for col, converter in converters.items():
        if col in data.columns:
            data[col] = data[col].apply(converter)

    # Verify required columns (case-insensitive check for Symbol)
    symbol_col = None
    for col in data.columns:
        if col.upper() in ['SYMBOL', 'INVESTMENT']:
            symbol_col = col
            break
    if symbol_col is None:
        raise ValueError("Required column 'Symbol' or 'Investment' not found")

    # Handle quantity column variations
    quantity_col = None
    for col in ['Quantity', 'Shares', 'UNIT/SHARE OWNED']:
        if col in data.columns:
            quantity_col = col
            break
    if quantity_col is None:
        raise ValueError("CSV must contain either 'Quantity', 'Shares', or 'UNIT/SHARE OWNED' column")

    # Handle value column variations
    value_col = None
    for col in ['Balance', 'BALANCE', 'Current Value', 'Total Value']:
        if col in data.columns:
            value_col = col
            break

    # Handle cost basis
    if 'Cost Basis' in data.columns:
        pass  # Use the column directly
    elif 'Cost Basis Total' in data.columns:
        data['Cost Basis'] = data['Cost Basis Total']
    elif 'Average Cost' in data.columns:
        data['Cost Basis'] = data[quantity_col] * data['Average Cost']
    else:
        data['Cost Basis'] = np.nan

    # Handle money market funds (indicated by missing Quantity)
    if pd.isna(data[quantity_col]).any():
        if 'Current Value' not in data.columns:
            raise ValueError("Current Value column required for money market funds")
        # Use Current Value for Quantity where missing
        data[quantity_col] = data.apply(
            lambda row: row['Current Value'] if pd.isna(row[quantity_col]) else row[quantity_col],
            axis=1
        )
        # Use Current Value for Cost Basis if Cost Basis is missing
        data['Cost Basis'] = data.apply(
            lambda row: row['Current Value'] if pd.isna(row['Cost Basis']) else row['Cost Basis'],
            axis=1
        )

    # Set Symbol as index and rename it to 'Ticker'
    data.set_index(symbol_col, inplace=True)
    data.index.name = 'Ticker'

    # Prepare final DataFrame with required columns
    result = pd.DataFrame(index=data.index)
    result['Account Number'] = data.get('Account Number', 'N/A')
    result['Account Name'] = data.get('Account Name', 'N/A')
    result['Quantity'] = data[quantity_col]
    result['Cost Basis'] = data['Cost Basis']
    result['Original Value'] = data[value_col] if value_col else np.nan

    if verbose:
        print(f"Loaded {result.shape[0]} holdings from file {file_path}")

    return result

def consolidate_holdings(*holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Combine multiple holdings DataFrames into a single consolidated DataFrame.

    Each input DataFrame should be in the format produced by load_holdings():
    - Indexed by ticker symbols
    - Contains Quantity and Cost Basis columns
    - May contain other columns (which will be ignored)

    Args:
        *holdings: One or more holdings DataFrames to consolidate

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Quantity (sum of quantities across all holdings)
        - Cost Basis (sum of total cost basis across all holdings)

    Example:
        df1 = load_holdings('holdings1.csv')
        df2 = load_holdings('holdings2.csv')
        consolidated = consolidate_holdings(df1, df2)
    """
    if not holdings:
        raise ValueError("At least one holdings DataFrame is required")

    # Get all unique tickers
    all_tickers = set()
    for df in holdings:
        all_tickers.update(df.index)

    # Initialize result DataFrame with zeros
    result = pd.DataFrame(0.0,
                         index=sorted(all_tickers),
                         columns=['Quantity', 'Cost Basis'])
    result.index.name = 'Ticker'

    # Accumulate quantities and costs across all holdings
    for df in holdings:
        result.loc[df.index, 'Quantity'] += df['Quantity']
        result.loc[df.index, 'Cost Basis'] += df['Cost Basis']

    return result

def load_and_consolidate_holdings(*args, verbose: bool = False) -> pd.DataFrame:
    """
    Load and consolidate holdings from multiple CSV files.

    This function accepts inputs in any of the following forms:
      - A single argument that is a list of file paths (assumed to be string file paths).
      - A single argument that is a directory path; in this case, all '.csv'
        files in the directory will be used.
      - Multiple arguments, with each argument being a file path.

    The function first builds a candidate list of file paths by processing each argument:
      - If an argument is a list, its items are directly assumed to be valid file paths.
      - If an argument is a string representing a directory, all CSV files in that
        directory are added.
      - Otherwise, if the argument is a string representing a file, it is added.

    Then, it calls `load_holdings` for each candidate file (with the provided verbose flag),
    which performs the necessary file validations.

    Args:
        *args: A list of file paths, a directory path, or multiple file path arguments.
        verbose: Optional; if True, prints verbose messages during loading. Defaults to False.

    Returns:
        pd.DataFrame: A consolidated DataFrame of holdings loaded from all valid CSV files.

    Raises:
        ValueError: If no candidate files are found from the provided arguments.
        TypeError: If an argument is not a string or a list of strings representing file paths.
    """
    candidate_files = []
    for arg in args:
        if isinstance(arg, list):
            candidate_files.extend(arg)
        elif isinstance(arg, str):
            if os.path.isdir(arg):
                candidate_files.extend(
                    [os.path.join(arg, f) for f in os.listdir(arg) if f.lower().endswith('.csv')]
                )
            else:
                candidate_files.append(arg)
        else:
            raise TypeError("Arguments must be a string or a list of strings representing file paths.")

    if not candidate_files:
        raise ValueError("No candidate files found from the provided arguments.")

    # Load holdings for each candidate; file-level validation is handled in load_holdings.
    holdings_list = [load_holdings(file, verbose=verbose) for file in candidate_files]
    # Consolidate all holdings using the existing consolidate_holdings function.
    consolidated = consolidate_holdings(*holdings_list)
    return consolidated

def get_holding_allocations(holdings: pd.DataFrame, 
                          prices: Optional[pd.DataFrame] = None,
                          verbose: bool = False) -> tuple[pd.DataFrame, float, float]:
    """Calculate current allocations for a set of holdings.

    Args:
        holdings: DataFrame in format produced by load_holdings() or consolidate_holdings()
                 Must be indexed by ticker symbols and contain a 'Quantity' column
        prices: Optional DataFrame with price data (default: None)
                If provided, must be indexed by ticker symbols and contain a 'Price' column
                If None, prices will be retrieved using get_latest_ticker_prices()
        verbose: If True, print status messages when retrieving prices (default: False)

    Returns:
        Tuple containing:
        - DataFrame indexed by ticker symbols containing:
          * Quantity (number of shares held)
          * Price (current price per share)
          * Total Value (Quantity * Price)
          * Allocation (percentage of total portfolio value)
        - Float representing total portfolio value in dollars
        - Float representing sum of allocation percentages

    Example:
        # Using retrieved prices
        holdings = load_holdings('portfolio.csv')
        allocations, total_value, total_alloc = get_holding_allocations(holdings)

        # Using provided prices
        prices = get_latest_ticker_prices(holdings.index)
        allocations, total_value, total_alloc = get_holding_allocations(holdings, prices=prices)
    """
    if not isinstance(holdings, pd.DataFrame):
        raise ValueError("holdings must be a pandas DataFrame")

    if 'Quantity' not in holdings.columns:
        raise ValueError("holdings DataFrame must contain a 'Quantity' column")

    # Get or validate prices
    if prices is None:
        # Get current prices for all tickers
        prices = get_latest_ticker_prices(holdings.index, verbose=verbose)
    else:
        # Validate provided prices DataFrame
        if not isinstance(prices, pd.DataFrame):
            raise ValueError("prices must be a pandas DataFrame")
        if 'Price' not in prices.columns:
            raise ValueError("prices DataFrame must contain a 'Price' column")
        if not all(ticker in prices.index for ticker in holdings.index):
            missing_tickers = [ticker for ticker in holdings.index if ticker not in prices.index]
            raise ValueError(f"Missing prices for tickers: {missing_tickers}")

    if prices['Price'].isna().all():
        raise ValueError("No price data retrieved for holdings")

    # Create result DataFrame
    result = pd.DataFrame(index=holdings.index)
    result.index.name = 'Ticker'

    # Add quantity from holdings
    result['Quantity'] = holdings['Quantity']

    # Add current prices
    result['Price'] = prices['Price']

    # Calculate total value for each holding
    result['Total Value'] = result['Quantity'] * result['Price']

    # Calculate allocation percentages
    total_value = result['Total Value'].sum()
    result['Allocation'] = result['Total Value'] / total_value

    return result, total_value, result['Allocation'].sum()

def get_asset_class_allocations(holdings: pd.DataFrame,
                              asset_class_weights: pd.DataFrame,
                              verbose: bool = False) -> tuple[pd.DataFrame, float, float]:
    """Calculate asset class allocations for a portfolio.

    Args:
        holdings: DataFrame indexed by ticker symbols containing:
            - Total Value (current dollar value of holding)
        asset_class_weights: DataFrame indexed by ticker symbols containing
            weight columns for each asset class (weights sum to 1)
        verbose: If True, print status messages (default: False)

    Returns:
        Tuple containing:
        - DataFrame indexed by asset class names containing:
          * Total Value (dollar amount allocated to asset class)
          * Allocation (percentage of total portfolio value)
        - Float representing total allocated value in dollars
        - Float representing sum of allocation percentages

    Example:
        holdings = get_holding_allocations(portfolio_df)[0]  # Get holdings with values
        weights = load_fund_asset_class_weights('asset_classes.csv')
        allocations, total_value, total_alloc = get_asset_class_allocations(holdings, weights)
    """
    # Get total portfolio value
    total_portfolio_value = holdings['Total Value'].sum()

    # Calculate dollar amount allocated to each asset class by each fund
    dollar_allocations = pd.DataFrame(columns=asset_class_weights.columns)
    for ticker in holdings.index:
        if ticker in asset_class_weights.index:
            # Multiply fund value by its asset class weights
            fund_value = holdings.loc[ticker, 'Total Value']
            dollar_allocations.loc[ticker] = asset_class_weights.loc[ticker] * fund_value
        elif verbose:
            print(f"Warning: No asset class weights found for {ticker}")

    # Sum up allocations across all funds for each asset class
    result = pd.DataFrame(index=asset_class_weights.columns)
    result.index.name = 'Asset Class'
    result['Total Value'] = dollar_allocations.sum()
    result['Allocation'] = result['Total Value'] / total_portfolio_value

    return result, result['Total Value'].sum(), result['Allocation'].sum()
