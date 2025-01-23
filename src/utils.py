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

def write_table(df, columns: Optional[Dict[str, Dict[str, Any]]] = None, 
                stream: TextIO = sys.stdout):
    """
    Write a formatted table to the specified output stream.
    
    Args:
        df: pandas DataFrame to display
        columns: Dictionary of column formats. Keys are column names, values are format specs.
                If None, all DataFrame columns are displayed with defaults.
        stream: Output stream (defaults to sys.stdout)
    
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
    
    # If index is named, include it in the display
    if df.index.name is not None:
        df = df.reset_index()

    # If no columns specified, create default format for all DataFrame columns
    if columns is None:
        columns = {col: {} for col in df.columns}
    
    # Select columns to display
    display_df = df[list(columns.keys())]
    
    # Process format specifications
    formats = {}
    for col, specs in columns.items():
        # Determine if column is numeric based on dtype
        col_type = dtype_to_format.get(str(df[col].dtype), 's')
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
        import yfinance as yf
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