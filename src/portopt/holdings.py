"""
Need an overview docstring for the module.
"""
from typing import Optional
import os
import pandas as pd
import numpy as np
import re
import csv

from .constants import Constants
from .utils import CaseInsensitiveDict
from .config import default_config

def holdings_substitute_proxies(holdings: pd.DataFrame,
                              proxy_funds: dict,
                              verbose: bool = False) -> pd.DataFrame:
    """
    Substitute proxy funds for private trust funds in a holdings DataFrame.

    For each private trust fund in the proxy_funds mapping, this function:
    1. Calculates equivalent shares of the proxy fund based on the original value
    2. Preserves the original ticker and quantity in separate columns
    3. Updates the index and quantity to use the proxy fund instead

    Args:
        holdings: DataFrame from load_holdings() containing at minimum:
                 - Quantity
                 - Original Value
                 Must be indexed by ticker symbols
        proxy_funds: Dictionary mapping private trust tickers to proxy tickers
        verbose: If True, print status messages during substitution

    Returns:
        DataFrame with proxy substitutions applied, containing additional columns:
        - Original Ticker (original ticker if proxy used, else same as index)
        - Original Quantity (original quantity if proxy used, else same as Quantity)
    """
    # Create a copy to avoid modifying the input
    result = holdings.copy()

    # Add Original Ticker and Original Quantity columns if they don't exist
    if 'Original Ticker' not in result.columns:
        result['Original Ticker'] = result.index
    if 'Original Quantity' not in result.columns:
        result['Original Quantity'] = result[Constants.QUANTITY_COL]

    # Process proxy fund substitutions
    for private_ticker, proxy_ticker in proxy_funds.items():
        if private_ticker in result.index:
            if verbose:
                print(f"Substituting {private_ticker} with proxy {proxy_ticker}")

            # Get the proxy price
            from portopt.market_data import get_latest_ticker_price
            proxy_price = get_latest_ticker_price(proxy_ticker)

            if proxy_price is None or proxy_price == 0:
                raise ValueError(f"Could not get valid price for proxy ticker {proxy_ticker}")

            # Calculate new quantity based on original value and proxy price
            new_quantity = result.loc[private_ticker, 'Original Value'] / proxy_price

            # Create new row with proxy ticker
            proxy_row = result.loc[private_ticker].copy()
            proxy_row[Constants.QUANTITY_COL] = new_quantity
            proxy_row['Original Ticker'] = private_ticker

            # Remove old row and add new row with proxy ticker
            result = result.drop(private_ticker)
            result.loc[proxy_ticker] = proxy_row

    return result

def holdings_fill_missing_tickers(holdings: pd.DataFrame,
                                missing_ticker_patterns: dict,
                                verbose: bool = False) -> pd.DataFrame:
    """
    Fill in missing tickers based on pattern matching rules.

    Args:
        holdings: DataFrame with holdings data
        missing_ticker_patterns: Dictionary mapping new tickers to pattern matching rules
        verbose: If True, print details about matches found

    Returns:
        DataFrame with missing tickers filled where patterns match

    Example config:
        missing_ticker_patterns:
          "FFTHX":
            match_column: "Description"
            pattern: "RETIREMENT 2035 FUND"
    """
    if not isinstance(holdings, pd.DataFrame):
        raise TypeError("holdings must be a pandas DataFrame")
    if not isinstance(missing_ticker_patterns, dict):
        raise TypeError("missing_ticker_patterns must be a dictionary")

    # Create copy to avoid modifying original
    result = holdings.copy()

    # Skip if no patterns defined
    if not missing_ticker_patterns:
        if verbose:
            print("No missing ticker patterns defined in config")
        return result

    # Track matches found for verbose output
    matches_found = []

    # Create boolean mask for rows where ticker is 'N/A'
    # Example: [True, False, True, False] for a DataFrame where rows 0 and 2 have 'N/A' tickers
    na_mask = result.index == 'N/A'

    for ticker, pattern_info in missing_ticker_patterns.items():
        match_column = pattern_info['match_column']
        pattern = pattern_info['pattern']

        # Skip if match column not found
        if match_column not in result.columns:
            if verbose:
                print(f"Warning: Match column '{match_column}' not found in holdings")
            continue

        # Create boolean mask for rows where pattern matches in the specified column
        # Example: [True, False, False, True] for pattern found in rows 0 and 3
        match_mask = result[match_column].str.contains(pattern, case=False, na=False)

        # Combine masks with AND operation (&) to find rows that need updating
        # True only where BOTH conditions are met: index is 'N/A' AND pattern matches
        # Example using above masks:
        #   na_mask:    [True,  False, True,  False]
        #   match_mask: [True,  False, False, True ]
        #   matches:    [True,  False, False, False]
        # Only row 0 will get its index updated
        matches = match_mask & na_mask

        if matches.any():
            # Create new index with matched ticker
            # Only positions where matches is True will be updated with new ticker
            # Convert index to numpy array, update it, then create new index
            new_index_array = result.index.to_numpy()
            new_index_array[matches] = ticker
            result.index = pd.Index(new_index_array, name=result.index.name)

            if verbose:
                num_matches = matches.sum()
                matches_found.append(f"'{pattern}' → {ticker} ({num_matches} matches)")

    if verbose and matches_found:
        print("Missing ticker patterns matched:")
        for match in matches_found:
            print(f"  {match}")

    return result

def holdings_remove_ignored_tickers(holdings: pd.DataFrame,
                                  ignore_tickers: list,
                                  verbose: bool = False) -> pd.DataFrame:
    """
    Remove specified tickers from holdings DataFrame.

    Args:
        holdings: DataFrame with holdings data
        ignore_tickers: List of ticker symbols to remove
        verbose: If True, print details about removed tickers

    Returns:
        DataFrame with specified tickers removed
    """
    if not isinstance(holdings, pd.DataFrame):
        raise TypeError("holdings must be a pandas DataFrame")
    if not isinstance(ignore_tickers, list):
        raise TypeError("ignore_tickers must be a list")

    # Create copy to avoid modifying original
    result = holdings.copy()

    # Skip if no tickers to ignore
    if not ignore_tickers:
        if verbose:
            print("No tickers specified to ignore")
        return result

    # Create mask for tickers to remove
    ignore_mask = result.index.isin(ignore_tickers)

    # Remove tickers and report if any were found
    if ignore_mask.any():
        ignored_tickers = result.index[ignore_mask]
        if verbose:
            print("Removing ignored tickers:")
            for ticker in ignored_tickers:
                print(f"  {ticker}")
        result = result[~ignore_mask]
    elif verbose:
        print("No matching tickers found to ignore")

    return result

def get_converters(config: dict) -> dict:
    """
    Create a dictionary of data converters based on configuration.

    Args:
        config: Configuration dictionary containing column definitions
               under the 'columns' key

    Returns:
        dict: Mapping of column names to converter functions
    """
    def clean_numeric(x):
        if not x or x == '--':
            return None
        # Convert to string and remove quotes, dollar signs, and commas
        cleaned = str(x).replace('"', '').replace('$', '').replace(',', '')
        # Remove percentage values in parentheses (e.g., " (6.83%)")
        cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)
        return float(cleaned)

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
        option_pattern = r'^-?([A-Z]{1,5}\d{6}[CP]\d+(?:\.\d+)?)$'
        option_match = re.match(option_pattern, ticker)
        if option_match:
            # Return the option ticker without the leading hyphen
            return option_match.group(1)

        # For regular symbols, remove any non-alphanumeric characters except dots and hyphens
        return re.sub(r'[^A-Z0-9.-]', '', ticker)

    # Map config types to cleaner functions
    cleaners = {
        'numeric': clean_numeric,
        'string': clean_string,
        'ticker': clean_ticker
    }

    # Create case-insensitive converter dictionary
    converters = CaseInsensitiveDict()

    # Add converters for configured columns
    for col_name, col_config in config['columns'].items():
        config_type = col_config['type']
        converters[col_name] = cleaners[config_type]
        for alt_name in col_config['alt_names']:
            converters[alt_name] = cleaners[config_type]

    # Add default converters for standard columns
    numeric_columns = [
        'UNIT/SHARE OWNED',
        'Current Value', 'Total Value',
        'Balance', 'BALANCE',
        'Cost Basis', 'Cost Basis Total',
        'Average Cost'
    ]
    string_columns = ['Account Number', 'Account Name']

    for col in numeric_columns:
        converters[col] = clean_numeric
    for col in string_columns:
        converters[col] = clean_string

    return converters

def load_holdings(file_path: str,
                 config: Optional[dict] = None,
                 verbose: bool = False) -> pd.DataFrame:
    """
    Load holdings from CSV export file, optionally substituting proxy funds.

    The CSV file should contain position details with some or all of:
    * Account information (Account Number, Account Name, or derived from filename)
    * Position details (Symbol/SYMBOL/Ticker, Quantity/Shares/UNIT/SHARE OWNED)
    * Dollar Value amount (Balance/BALANCE/Current Value/Total Value)
    * Optional non-CSV lines (will be detected and skipped)
    * Optional footer section (will be detected and skipped)

    Special handling:
    * Money market funds: When Quantity is empty, uses Original Value (assuming $1/share)
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
        config: Optional dictionary containing configuration settings including:
               - proxy_funds: Mapping of private trust tickers to proxy tickers
               - field_mappings: CSV field name mappings
               - missing_ticker_patterns: Rules for identifying missing tickers
        verbose: Optional; if True, prints a message with the number rows loaded.
                 Defaults to False.

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Account (from file, or derived from filename if not in file)
        - Quantity (from Quantity or Shares column)
        - Original Value (from Balance/BALANCE/Current Value/Total Value columns)
        - Original Ticker (original ticker if proxy used, else same as index)
        - Original Quantity (original quantity if proxy used, else same as Quantity)

    Raises:
        ValueError: If file format is invalid or required columns missing
        TypeError: If file_path is not a string
    """
    if config is None:
        config = default_config()

    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string.")
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")

    def is_header_row(row):
        """Check if row contains required column headers.

        Args:
            row: A list of column headers to check

        Returns:
            bool: True if row contains required Ticker and Quantity columns
                 (with variations in column names supported)
        """
        # Convert all column names to uppercase for case-insensitive matching
        cols_upper = [col.upper() for col in row]

        # Check for Ticker column using config-defined names
        ticker_names = [Constants.TICKER_COL.upper()] + [name.upper() for name in config['columns'][Constants.TICKER_COL]['alt_names']]
        has_ticker = any(col in ticker_names for col in cols_upper)

        # Check for Quantity column using config-defined names
        quantity_names = [Constants.QUANTITY_COL.upper()] + [name.upper() for name in config['columns'][Constants.QUANTITY_COL]['alt_names']]
        has_quantity = any(col in quantity_names for col in cols_upper)

        # Row is a header if it contains both required columns
        return has_ticker and has_quantity

    # Define converters for data cleaning
    converters = get_converters(config)

    # Read CSV rows and find header
    header = None
    data_rows = []

    with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
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
            # Allow rows with one extra empty field (trailing comma in CSV)
            row_field_count = len(row)
            if row_field_count == header_field_count:
                data_rows.append(row)
            elif row_field_count == header_field_count + 1 and (not row[-1] or not row[-1].strip()):
                # Row has one extra empty field (trailing comma), strip it
                data_rows.append(row[:header_field_count])
            else:
                # Stop at first row with different field count (footer)
                break

    if header is None:
        raise ValueError("Could not find header row with required columns")

    # Create DataFrame and apply converters
    data = pd.DataFrame(data_rows, columns=header)
    for col in data.columns:
        converter = converters.get(col)
        if converter:
            if verbose:
                print(f"Converting '{col}' column using '{converter.__name__}'")
            data[col] = data[col].apply(converter)
        else:
            if verbose:
                print(f"No converter found for '{col}' column")

    # Find the ticker column using config-defined names
    ticker_col = None
    ticker_config = config['columns'][Constants.TICKER_COL]
    for col in data.columns:
        possible_names = [Constants.TICKER_COL] + ticker_config['alt_names']
        if col.upper() in [name.upper() for name in possible_names]:
            ticker_col = col
            break
    if ticker_col is None:
        raise ValueError(f"Required column '{Constants.TICKER_COL}' or one of {ticker_config['alt_names']} not found")

    # Find the quantity column using config-defined names
    quantity_col = None
    quantity_config = config['columns'][Constants.QUANTITY_COL]
    for col in data.columns:
        possible_names = [Constants.QUANTITY_COL] + quantity_config['alt_names']
        if col.upper() in [name.upper() for name in possible_names]:
            quantity_col = col
            break
    if quantity_col is None:
        raise ValueError(f"Required column '{Constants.QUANTITY_COL}' or one of {quantity_config['alt_names']} not found")

    # Handle value column variations
    value_col = None
    for col in ['Balance', 'BALANCE', 'Current Value', 'Total Value']:
        if col in data.columns:
            value_col = col
            break

    # Handle money market funds (where Quantity is missing):
    # Use Original Value as Quantity (assuming $1/share)
    if pd.isna(data[quantity_col]).any():
        if 'Current Value' not in data.columns:
            raise ValueError("Current Value column required for money market funds")
        # Use Current Value for Quantity where missing
        data[quantity_col] = data.apply(
            lambda row: row['Current Value'] if pd.isna(row[quantity_col]) else row[quantity_col],
            axis=1
        )

    # Set Ticker as index and rename it to 'Ticker'
    data.set_index(ticker_col, inplace=True)
    data.index.name = Constants.TICKER_COL

    # Fill in missing tickers if patterns are defined in config
    if config and 'missing_ticker_patterns' in config:
        data = holdings_fill_missing_tickers(data, config['missing_ticker_patterns'], verbose)

    # Get default account name from filename if Account Name not in data
    default_account = os.path.splitext(os.path.basename(file_path))[0]

    # Prepare final DataFrame with required columns
    result = pd.DataFrame(index=data.index)
    result[Constants.ACCOUNT_COL] = data.get(Constants.ACCOUNT_COL, default_account)
    result[Constants.QUANTITY_COL] = data[quantity_col]
    result['Original Value'] = data[value_col] if value_col else np.nan

    if verbose:
        print(f"Loaded {result.shape[0]} holdings from file {file_path}")

    # Apply proxy fund substitutions if defined in config
    if config and 'proxy_funds' in config:
        result = holdings_substitute_proxies(result, config['proxy_funds'], verbose)

    # Remove ignored tickers if defined in config
    if config and 'ignore_tickers' in config:
        result = holdings_remove_ignored_tickers(result, config['ignore_tickers'], verbose)

    return result

def consolidate_holdings(*holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Combine multiple holdings DataFrames into a single consolidated DataFrame.

    Each input DataFrame should be in the format produced by load_holdings():
    - Indexed by ticker symbols
    - Contains Quantity column
    - May contain other columns (which will be ignored)

    Args:
        *holdings: One or more holdings DataFrames to consolidate

    Returns:
        DataFrame indexed by Ticker symbols and Account Names containing:
        - Quantity

    Example:
        df1 = load_holdings('holdings1.csv')
        df2 = load_holdings('holdings2.csv')
        consolidated = consolidate_holdings(df1, df2)
    """
    if not holdings:
        raise ValueError("At least one holdings DataFrame is required")

    # Concatenate all holdings and set hierarchical index
    result = pd.concat(holdings)
    result.set_index([Constants.ACCOUNT_COL], append=True, inplace=True)
    result = result.reorder_levels(['Ticker', Constants.ACCOUNT_COL])

    return result

def load_and_consolidate_holdings(*args,
                                config: Optional[dict] = None,
                                verbose: bool = False) -> pd.DataFrame:
    """
    Load and consolidate holdings from multiple CSV files.

    This function accepts inputs in any of the following forms:
      - A single argument that is a list of file paths (assumed to be string file paths).
      - A single argument that is a directory path; in this case, all '.csv'
        files in the directory will be used.
      - Multiple arguments, with each argument being a file path.

    Args:
        *args: A list of file paths, a directory path, or multiple file path arguments.
        config: Optional dictionary containing configuration settings including:
               - proxy_funds: Mapping of private trust tickers to proxy tickers
               - field_mappings: CSV field name mappings
               - missing_ticker_patterns: Rules for identifying missing tickers
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
            if verbose:
                print(f"Found non-string and non-list argument: {arg}")
            raise TypeError("Arguments must be a string or a list of strings representing file paths.")

    if not candidate_files:
        raise ValueError("No candidate files found from the provided arguments.")

    # Load holdings for each candidate; file-level validation is handled in load_holdings.
    holdings_list = [load_holdings(file, config=config, verbose=verbose)
                    for file in candidate_files]

    # Consolidate all holdings using the existing consolidate_holdings function.
    consolidated = consolidate_holdings(*holdings_list)
    return consolidated