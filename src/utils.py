import sys
from typing import Dict, Optional, TextIO, Any
import numpy as np
import pandas as pd
import warnings
from scipy import stats
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.diagnostic import het_arch
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import adfuller, kpss
import yfinance as yf
import re
import csv

def write_table(df, columns: Optional[Dict[str, Dict[str, Any]]] = None, 
                stream: TextIO = sys.stdout,
                sort_order: Optional[str] = 'asc'):
    """
    Write a formatted table to the specified output stream.

    Args:
        df: pandas DataFrame to display
        columns: Dictionary of column formats. Keys are column names, values are format specs.
                If None, all DataFrame columns are displayed with defaults.
                Columns specified but not in DataFrame are ignored.
        stream: Output stream (defaults to sys.stdout)
        sort_order: Controls table sorting by index (default: 'asc')
                   'asc' - sort ascending
                   'desc' - sort descending
                   None - leave order unchanged

    Format dictionary options:
        type: Data type ('s', 'd', 'f', etc). Default: based on column dtype
        align: Data alignment ('<', '>', '^', '='). Default: based on type
        hdr_align: Header alignment ('<', '>', '^', '='). Default: based on type
        hdr_sep: Header separator character. Default: '='
        sign: Number sign handling ('+', '-', ' '). Default: omitted
        width: Column width. Default: 10
        decimal: Decimal places for floats. Default: 1 for numeric, omitted for others
        prefix: Prefix string for data. Default: omitted
        suffix: Suffix string for data. Default: omitted
    """
    # Map numpy/pandas dtypes to format types
    dtype_to_format = {
        'float64': 'f',
        'float32': 'f',
        'int64': 'd',
        'int32': 'd',
        'int16': 'd',
        'int8': 'd',
        'object': 's',
        'string': 's',
        'bool': 's'
    }

    # Create a copy to avoid modifying the input DataFrame
    display_df = df.copy()

    # Sort by index first, before Index gets converted to a regular column below
    if sort_order == 'asc':
        display_df.sort_index(ascending=True, inplace=True)
    elif sort_order == 'desc':
        display_df.sort_index(ascending=False, inplace=True)
    elif sort_order is not None:
        raise ValueError("sort_order must be 'asc', 'desc', or None")

    # If index is named, include it in the display
    if display_df.index.name is not None:
        display_df = display_df.reset_index()

    # If no columns specified, create default format for all DataFrame columns
    if columns is None:
        columns = {col: {} for col in display_df.columns}
    else:
        # Filter out columns that don't exist in the DataFrame
        columns = {col: specs for col, specs in columns.items() if col in display_df.columns}

    # Select columns to display
    display_df = display_df[list(columns.keys())]
    
    # Process format specifications
    formats = {}
    for col, specs in columns.items():
        # Determine if column is numeric based on dtype
        col_type = dtype_to_format.get(str(display_df[col].dtype), 's')
        is_numeric = col_type in ['f', 'd']
        
        # Start with defaults
        fmt = {
            'type': col_type,
            'align': '>' if is_numeric else '<',      # Right align numeric
            'hdr_align': '^' if is_numeric else '<',  # Center numeric headers
            'hdr_sep': '=',
            'width': 10,
            'prefix': '',
            'suffix': ''
        }
        
        # Add decimal places default for numeric types
        if is_numeric:
            fmt['decimal'] = 1
        
        # Update with provided specifications
        fmt.update(specs)
        
        # Calculate width available for actual data
        data_width = fmt['width'] - len(fmt['prefix']) - len(fmt['suffix'])
        
        # Build format string for data
        fmt_str = '{'
        if fmt['type'] == 's':
            # For strings, truncate or pad to exact width
            fmt_str += ':' + fmt['align'] + str(data_width) + '.' + str(data_width)
        else:
            # For all numeric types (including %), ensure exact width
            fmt_str += ':' + fmt['align'] + str(data_width)
            if 'sign' in fmt:
                fmt_str += fmt['sign']
            if 'decimal' in fmt:
                fmt_str += '.' + str(fmt['decimal'])
            fmt_str += fmt['type']
        fmt_str += '}'
        
        # Add prefix/suffix if specified
        if fmt['prefix']:
            fmt_str = fmt['prefix'] + fmt_str
        if fmt['suffix']:
            fmt_str = fmt_str + fmt['suffix']
        
        # Build header format string (truncate/pad to exact width)
        hdr_fmt = '{:' + fmt['hdr_align'] + str(fmt['width']) + '.' + str(fmt['width']) + '}'
        
        formats[col] = {
            'data_fmt': fmt_str,
            'hdr_fmt': hdr_fmt,
            'width': fmt['width'],
            'sep': fmt['hdr_sep']
        }
    
    # Create header line
    header_strs = [formats[col]['hdr_fmt'].format(col) for col in columns.keys()]
    print(' '.join(header_strs), file=stream)
    
    # Create separator line
    sep_strs = [formats[col]['sep'] * formats[col]['width'] for col in columns.keys()]
    print(' '.join(sep_strs), file=stream)
    
    # Print data rows
    for _, row in display_df.iterrows():
        data_strs = []
        for col in columns.keys():
            try:
                value = row[col]
                if pd.isna(value):
                    # Create a format string for "N/A" using the column's alignment
                    na_fmt = '{:' + fmt['align'] + str(formats[col]['width']) + '}'
                    data_strs.append(na_fmt.format("N/A"))
                else:
                    data_strs.append(formats[col]['data_fmt'].format(value))
            except (ValueError, TypeError):
                # If formatting fails, fall back to string representation
                data_strs.append(formats[col]['data_fmt'].format(str(row[col])))
        print(' '.join(data_strs), file=stream)

def test_stationarity(df):
    """
    Use ADF and KPSS tests to determine if each column in the dataframe
    is stationary.

    Args:
        df: pandas DataFrame with time series data, indexed by date with
        one column per ticker

    Returns:
        pandas DataFrame with test results (test statistic, p-value)
        and stationarity assessment (True if stationary, False otherwise)

    Raises:
        ValueError: If input data contains NaN or infinite values
    """

    # Check for NaN or infinite values
    if df.isna().any().any() or np.isinf(df).any().any():
        raise ValueError("Input data contains NaN or infinite values. Please clean the data first using df.dropna() or similar method.")

    # Create empty DataFrame for results
    results = pd.DataFrame(
        index=df.columns,
        columns=['ADF Statistic', 'ADF p-value', 'KPSS Statistic', 'KPSS p-value', 'Is Stationary']
    )
    results.index.name = 'Ticker'

    # Perform tests for each ticker
    for ticker in df.columns:
        try:
            # ADF test
            adf_stat, adf_pval, _, _, _, _ = adfuller(df[ticker])

            # KPSS test (using 'c' for constant trend)
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', 'The test statistic is outside')
                kpss_stat, kpss_pval, _, _ = kpss(df[ticker], regression='c')

            # Determine stationarity
            is_stationary = (adf_pval < 0.05) and (kpss_pval > 0.05)

            # Store all results
            results.loc[ticker] = [adf_stat, adf_pval, kpss_stat, kpss_pval, is_stationary]

        except Exception as e:
            raise ValueError(f"Error processing ticker {ticker}: {str(e)}. Please ensure data is clean and properly formatted.") from e

    return results

def test_autocorrelation(data: pd.DataFrame | pd.Series,
                        lags: int = 10,
                        significance_level: float = 0.05) -> pd.DataFrame:
    """
    Use Durbin-Watson and Ljung-Box tests to determine if time series has
    autocorrelation.

    Args:
        data: DataFrame with multiple time series or Series with single time series
        lags: int, number of lags to test (default: 10)
        significance_level: float, threshold for statistical significance (default: 0.05)

    Returns:
        DataFrame with test results (test statistic, p-value)
        and autocorrelation assessment (True if autocorrelation, False otherwise)

    Example:
        # For a single series
        results = test_autocorrelation(df['AAPL'])

        # For multiple series
        results = test_autocorrelation(df[['AAPL', 'MSFT']])
    """
    # Convert Series to DataFrame if necessary
    if isinstance(data, pd.Series):
        df = pd.DataFrame(data)
    else:
        df = data

    results = pd.DataFrame(
        index=df.columns,
        columns=['Durbin-Watson', 'DW p-value', 'Ljung-Box p-value', 
                'Has Autocorrelation', 'AC Strength', 'AC Direction']
    )

    for ticker in df.columns:
        # Durbin-Watson test
        residuals = df[ticker].diff().dropna()
        dw_stat = durbin_watson(residuals)
        dw_pval = durbin_watson_pvalue(dw_stat, len(residuals))

        # Ljung-Box test
        lb_result = acorr_ljungbox(df[ticker], lags=[lags])
        lb_pval = lb_result['lb_pvalue'].iloc[0]

        # Determine if autocorrelation exists
        has_autocorr = (dw_pval < significance_level) or (lb_pval < significance_level)

        # Determine strength and direction based on DW statistic
        if not has_autocorr:
            strength = "None"
            direction = "None"
        else:
            # Direction
            if dw_stat < 2:
                direction = "Positive"
            else:
                direction = "Negative"

            # Strength
            dw_deviation = abs(dw_stat - 2)
            if dw_deviation < 0.5:
                strength = "Weak"
            elif dw_deviation < 1.0:
                strength = "Moderate"
            else:
                strength = "Strong"

        results.loc[ticker] = [dw_stat, dw_pval, lb_pval,
                             has_autocorr, strength, direction]

    return results

def durbin_watson_pvalue(dw_stat, n):
    """
    Calculate approximate p-value for Durbin-Watson test.
    """
    # Approximate p-value calculation
    # DW stat of 2 indicates no autocorrelation
    return 2 * (1 - stats.norm.cdf(abs(dw_stat - 2)))

def test_volatility_clustering(df, lags=10):
    """
    Test for ARCH effects (volatility clustering) using Engle's ARCH test.

    Args:
        df: DataFrame with time series data
        lags: int, number of lags to test (default: 10)

    Returns:
        DataFrame with test results including:
        - LM Statistic: Lagrange multiplier test statistic
        - LM p-value: p-value for the test
        - Has ARCH Effect: boolean indicating presence of ARCH effects
        - VC Strength: Strength of volatility clustering (None/Weak/Moderate/Strong)
        - VC Persistence: Number of significant lags showing ARCH effects

    Notes:
        - Null hypothesis (H0): No ARCH effects
        - Alternative hypothesis (H1): ARCH effects present
        - Reject H0 if p-value < 0.05
        - Presence of ARCH effects indicates volatility clustering
    """
    results = pd.DataFrame(
        index=df.columns,
        columns=['LM Statistic', 'LM p-value', 'Has ARCH Effect',
                'VC Strength', 'VC Persistence']
    )

    for ticker in df.columns:
        try:
            # Perform ARCH-LM test
            arch_test = het_arch(df[ticker], nlags=lags)
            lm_stat = arch_test[0]  # First element is the statistic
            lm_pval = arch_test[1]  # Second element is the p-value

            # Determine if ARCH effects exist (at 5% significance)
            has_arch = lm_pval < 0.05

            # Determine strength based on p-value
            if not has_arch:
                strength = "None"
            else:
                if lm_pval > 0.01:
                    strength = "Weak"
                elif lm_pval > 0.001:
                    strength = "Moderate"
                else:
                    strength = "Strong"

            # Calculate persistence (using rolling variance)
            returns = df[ticker]
            rolling_var = returns.rolling(window=20).var()
            autocorr_var = rolling_var.autocorr(lag=1)

            if abs(autocorr_var) < 0.2:
                persistence = "Low"
            elif abs(autocorr_var) < 0.5:
                persistence = "Medium"
            else:
                persistence = "High"

            results.loc[ticker] = [lm_stat, lm_pval, has_arch,
                                 strength, persistence]

        except Exception as e:
            print(f"Error testing {ticker}: {str(e)}")
            results.loc[ticker] = [np.nan, np.nan, np.nan, np.nan, np.nan]

    return results

def standardize_data(df):
    """
    Standardize data to have mean 0 and standard deviation 1.

    Args:
        df: pandas DataFrame to standardize

    Returns:
        pandas DataFrame with standardized data, maintaining original index and columns

    Raises:
        ValueError: If DataFrame contains NaN values or has zero standard deviation
    """
    # Check for NaN values
    if df.isna().any().any():
        raise ValueError("DataFrame contains NaN values. Please clean data first.")

    # Check for zero standard deviation
    if (df.std() == 0).any():
        raise ValueError("One or more columns have zero standard deviation.")

    # Initialize scaler
    scaler = StandardScaler()

    # Fit and transform the data
    standardized_data = scaler.fit_transform(df)

    # Convert back to DataFrame with original index and columns
    df_standardized = pd.DataFrame(
        standardized_data,
        columns=df.columns,
        index=df.index
    )

    return df_standardized

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

def load_holdings(file_path: str) -> pd.DataFrame:
    """
    Load holdings from CSV export file

    The CSV file should contain position details with some or all of:
    * Account information (Account Number, Account Name)
    * Position details (Symbol/SYMBOL/Ticker, Quantity/Shares/UNIT/SHARE OWNED, Cost Basis/Average Cost)
    * Optional non-CSV lines (will be detected and skipped)
    * Optional footer section (will be detected and skipped)

    Special handling:
    * Money market funds: When Quantity is empty, uses Current Value (assuming $1/share)
                         for both Quantity and Cost Basis (if Cost Basis is not provided)
    * Cost Basis:
        1. Uses 'Cost Basis' or 'Cost Basis Total' column if either exists
        2. If neither exists, calculates from Average Cost * Quantity if both are available
        3. Otherwise, sets to NaN
    * Missing columns: Populated with 'N/A' for strings, NaN for numeric values
    * Empty string values: Replaced with 'N/A'
    * Ticker symbols:
        - Extra characters (like '*') are removed from regular symbols
        - Option contracts (e.g., SPY250321P580) are preserved (leading hyphen removed)

    Args:
        file_path: Path to the portfolio CSV file

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Account Number (if available, else 'N/A')
        - Account Name (if available, else 'N/A')
        - Quantity (from Quantity or Shares column)
        - Cost Basis (from Cost Basis/Cost Basis Total columns, or calculated from Average Cost * Quantity)

    Raises:
        ValueError: If file format is invalid, required Symbol column is missing,
                   or neither Quantity nor Shares column is present
    """
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

def get_tickers_data(tickers: set[str] | list[str],
                     start_date: str = "1990-01-01",
                     end_date: str = None,
                     price_type: str = "Adj Close") -> pd.DataFrame:
    """
    Retrieve price data for a set of tickers.

    Args:
        tickers: Set or list of ticker symbols
        start_date: Start date for data retrieval (default: "1990-01-01")
        end_date: End date for data retrieval (default: None, means today)
        price_type: Type of price to retrieve (default: "Adj Close")
                   Options: "Open", "High", "Low", "Close", "Adj Close", "Volume"

    Returns:
        DataFrame indexed by date with tickers as columns containing price data

    Raises:
        ValueError: If no tickers provided or if invalid price_type
        ValueError: If data retrieval fails for any ticker
    """
    # Convert tickers to set if it's a list
    tickers_set = set(tickers)

    if not tickers_set:
        raise ValueError("No tickers provided")

    # Validate price type
    valid_price_types = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    if price_type not in valid_price_types:
        raise ValueError(f"Invalid price_type. Must be one of {valid_price_types}")

    try:
        # Download data for all tickers
        df = yf.download(
            list(tickers_set),  # Convert back to list for yfinance
            start=start_date,
            end=end_date,
            auto_adjust=False
        )[price_type]

        # Check if any tickers are missing
        missing_tickers = tickers_set - set(df.columns)
        if missing_tickers:
            raise ValueError(f"Failed to retrieve data for tickers: {missing_tickers}")

        # Drop any rows with NaN values
        df_clean = df.dropna(axis=0, how='any')

        # Warn if we dropped any dates
        if len(df_clean) < len(df):
            import warnings
            warnings.warn(f"Dropped {len(df) - len(df_clean)} rows containing NaN values")

        return df_clean

    except Exception as e:
        raise ValueError(f"Error retrieving data: {str(e)}")

def get_latest_ticker_prices(tickers: pd.Index | set[str] | list[str], verbose: bool = False) -> pd.DataFrame:
    """
    Retrieve the most recent prices for multiple tickers.

    Args:
        tickers: Index, set, or list of ticker symbols (securities and/or options)
        verbose: If True, print status messages for each ticker (default: False)

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Price (most recent price available)
        Note: Money market funds are assumed to have a stable $1.00 NAV
              Invalid tickers will have NaN prices

    Example:
        # Get prices for a mix of securities and options
        prices = get_latest_ticker_prices(['VTSAX', 'SPY', 'SPY250321P580'])
    """
    # Convert input to set of tickers if it isn't already
    if isinstance(tickers, set):
        tickers_set = tickers
    elif isinstance(tickers, (pd.Index, list)):
        tickers_set = set(tickers)
    else:
        raise TypeError("tickers must be a set, list, or pandas Index")

    if not tickers_set:
        raise ValueError("No tickers provided")

    # Initialize result DataFrame
    result = pd.DataFrame(index=sorted(tickers_set))
    result.index.name = 'Ticker'

    # Process each ticker
    for ticker in tickers_set:
        result.loc[ticker, 'Price'] = get_latest_ticker_price(ticker, verbose=verbose)

    return result

def get_latest_ticker_price(ticker: str, verbose: bool = False) -> float:
    """
    Retrieve the latest price for a single ticker (security or option).

    Args:
        ticker: Ticker symbol (e.g., 'VTSAX', 'SPY250321P580')
        verbose: If True, print status messages (default: False)

    Returns:
        Latest price for the ticker, or NaN if retrieval fails

    Example:
        # Get price for a security
        price = get_latest_ticker_price('VTSAX')

        # Get price for an option
        price = get_latest_ticker_price('SPY250321P580')
    """
    try:
        # Check if it's an option contract
        option_pattern = re.compile(r'^[A-Z]{1,5}\d{6}[CP]\d+$')
        security_pattern = re.compile(r'^[A-Z]{1,5}([A-Z0-9.-]*)?$')

        ticker_str = str(ticker).upper()
        if option_pattern.match(ticker_str):
            return get_latest_option_price(ticker, verbose=verbose)
        elif security_pattern.match(ticker_str):
            return get_latest_security_price(ticker, verbose=verbose)
        else:
            if verbose:
                print(f"Invalid ticker format: {ticker}")
            return np.nan

    except Exception as e:
        if verbose:
            print(f"Error retrieving price for {ticker}: {str(e)}")
        return np.nan

def get_latest_security_price(ticker: str, verbose: bool = False) -> float:
    """
    Retrieve the latest price for a security (stock, bond, ETF, mutual fund).

    Args:
        ticker: Security symbol (e.g., 'VTSAX', 'SPY', 'AAPL')
        verbose: If True, print status messages (default: False)

    Returns:
        Latest price of the security, or NaN if retrieval fails
        Note: Money market funds return $1.00 NAV

    Example:
        # Get price for a mutual fund
        price = get_latest_security_price('VTSAX')
    """
    try:
        # Known money market funds
        money_market_funds = {
            'SPAXX',  # Fidelity Government Money Market Fund
            'FDRXX',  # Fidelity Government Cash Reserves
            'SPRXX',  # Fidelity Money Market Fund
            'FZFXX',  # Fidelity Treasury Money Market Fund
            'VMFXX',  # Vanguard Federal Money Market Fund
            'VMMXX',  # Vanguard Prime Money Market Fund
            'TIMXX',  # RBC BlueBay US Govt Mny Mkt Instl 2
        }

        if ticker in money_market_funds:
            price = 1.0  # Money market funds maintain $1.00 NAV
        else:
            # Get basic info (doesn't download historical data)
            fund = yf.Ticker(ticker)
            info = fund.info

            # Try to get price in order of preference
            price = info.get('regularMarketPrice')  # Current price if market open
            if price is None:
                price = info.get('previousClose')   # Previous close if market closed
            if price is None:
                if verbose:
                    print(f"No price data available for {ticker}")
                return np.nan

        if verbose:
            print(f"Successfully retrieved price for {ticker}: ${price:.2f}")
        return price

    except Exception as e:
        if verbose:
            print(f"Error retrieving price for {ticker}: {str(e)}")
        return np.nan

def get_latest_option_price(option_symbol: str, verbose: bool = False) -> float:
    """
    Retrieve the latest price for an option contract.

    Args:
        option_symbol: Option symbol in OCC format (e.g., 'SPY250321P580')
                      Format: {SYMBOL}{YY}{MM}{DD}{C/P}{STRIKE}
        verbose: If True, print status messages (default: False)

    Returns:
        Latest price of the option contract, or NaN if retrieval fails

    Example:
        # Get price for SPY put option (strike: $580, expiry: March 21, 2025)
        price = get_latest_option_price('SPY250321P580')
    """
    try:
        # Parse OCC symbol components
        match = re.match(r'^([A-Z]{1,5})(\d{2})(\d{2})(\d{2})([CP])(\d+)$', option_symbol)
        if not match:
            raise ValueError(f"Invalid option symbol format: {option_symbol}")

        symbol, yy, mm, dd, opt_type, strike = match.groups()

        # Convert to full year (assuming 20xx)
        year = f"20{yy}"

        # Create date object to format properly for Yahoo
        expiry_date = pd.Timestamp(f"20{yy}-{mm}-{dd}")

        # Convert strike price to proper format (multiply by 1000 for Yahoo's format)
        yahoo_strike = float(strike) * 1000

        # Get option chain for the underlying stock
        ticker = yf.Ticker(symbol)

        # Get all options for the expiration date
        try:
            options = ticker.option_chain(expiry_date.strftime('%Y-%m-%d'))
        except ValueError as e:
            if verbose:
                print(f"No options chain found for {symbol} on {expiry_date.date()}")
            return np.nan

        # Select puts or calls based on option type
        chain = options.puts if opt_type == 'P' else options.calls

        # Find the specific contract
        contract = chain[chain['strike'] == float(strike)]

        if len(contract) == 0:
            if verbose:
                print(f"No contract found for strike ${strike} in {symbol} {opt_type} options")
            return np.nan

        # Get the last price & multiply by 100 since contracts are for 100 shares
        price = contract.iloc[0]['lastPrice'] * 100

        if verbose:
            print(f"Successfully retrieved price for {option_symbol}: ${price:.2f}")

        return price

    except Exception as e:
        if verbose:
            print(f"Error retrieving price for {option_symbol}: {str(e)}")
        return np.nan

def get_portfolio_data(portfolio,
                      start_date: str = "1990-01-01",
                      end_date: str = None,
                      price_type: str = "Adj Close") -> pd.DataFrame:
    """
    Retrieve price data for one or more portfolios.

    Args:
        portfolio: Either:
                  - A dictionary mapping tickers to weights
                  - A dictionary of such dictionaries, with portfolio names as keys
        start_date: Start date for data retrieval (default: "1990-01-01")
        end_date: End date for data retrieval (default: None, means today)
        price_type: Type of price to retrieve (default: "Adj Close")
                   Options: "Open", "High", "Low", "Close", "Adj Close", "Volume"

    Returns:
        DataFrame indexed by date with tickers as columns containing price data

    Example:
        # Single portfolio
        portfolio = {'AAPL': 0.5, 'MSFT': 0.5}
        prices = get_portfolio_data(portfolio)

        # Multiple portfolios
        portfolios = {
            'Conservative': {'SPY': 0.6, 'BND': 0.4},
            'Aggressive': {'QQQ': 0.7, 'SPY': 0.3}
        }
        prices = get_portfolio_data(portfolios)
    """
    # Determine if we have a single portfolio or multiple portfolios
    if all(isinstance(v, (int, float)) for v in portfolio.values()):
        # Single portfolio case
        tickers = set(portfolio.keys())
    else:
        # Multiple portfolios case
        tickers = set()
        for p in portfolio.values():
            if not isinstance(p, dict):
                raise ValueError("Invalid portfolio format")
            tickers.update(p.keys())

    return get_tickers_data(tickers, start_date, end_date, price_type)

def plot_time_series(data: pd.DataFrame | pd.Series,
                    title: str = "Time Series Plot",
                    ylabel: str = "Value",
                    figsize: tuple = (12, 6),
                    legend_loc: str = "best") -> None:
    """
    Plot one or more time series on a line chart.

    Args:
        data: DataFrame or Series containing time series data
        title: Plot title (default: "Time Series Plot")
        ylabel: Y-axis label (default: "Value")
        figsize: Figure size as (width, height) tuple (default: (12, 6))
        legend_loc: Location of legend (default: "best")
                   Options: 'best', 'upper left', 'upper right',
                           'lower left', 'lower right', 'center', etc.

    Returns:
        None (displays plot)

    Example:
        # Single series
        plot_time_series(df['AAPL'], title='Apple Stock Price')

        # Multiple series
        plot_time_series(df[['AAPL', 'MSFT']],
                        title='Tech Stock Comparison',
                        ylabel='Price')
    """

    # Create figure and axis
    plt.figure(figsize=figsize)

    # Handle both Series and DataFrame
    if isinstance(data, pd.Series):
        plt.plot(data.index, data.values, label=data.name)
    else:
        for column in data.columns:
            plt.plot(data.index, data[column], label=column)

    # Customize plot
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Add legend if we have multiple series or if the series has a name
    if isinstance(data, pd.DataFrame) or data.name is not None:
        plt.legend(loc=legend_loc)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Show plot
    plt.show()