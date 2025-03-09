import sys
from typing import Dict, Optional, TextIO, Any, Union, List
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
import csv

from market_data import get_tickers_data

def write_table(df, columns: Optional[Dict[str, Dict[str, Any]]] = None, 
                stream: TextIO = sys.stdout,
                sort_order: Optional[str] = 'asc'):
    """
    Write a formatted table to the specified output stream.

    Args:
        df: pandas DataFrame to display (supports hierarchical index)
        columns: Dictionary of column formats. Keys are column names, values are format specs.
                For hierarchical indices, include index level names to display them.
                If None, all DataFrame columns and index levels are displayed with defaults.
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

    # Convert all indices to columns
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

class CaseInsensitiveDict(dict):
    """
    Dictionary that enables case insensitive searching while preserving case sensitivity
    when keys are listed.

    Args:
        *args: Variable length argument list passed to dict constructor
        **kwargs: Arbitrary keyword arguments passed to dict constructor

    Example:
        >>> d = CaseInsensitiveDict({'Name': 'John', 'AGE': 30})
        >>> d['name']  # Returns 'John'
        >>> d['AGE']   # Returns 30
        >>> d['age']   # Returns 30
        >>> list(d.keys())  # Returns ['Name', 'AGE'] (original case preserved)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lower_to_original = {key.lower(): key for key in self.keys()}

    def __getitem__(self, key):
        return super().__getitem__(self._lower_to_original[key.lower()])

    def __setitem__(self, key, value):
        lower_key = key.lower()
        if lower_key in self._lower_to_original:
            super().__setitem__(self._lower_to_original[lower_key], value)
        else:
            self._lower_to_original[lower_key] = key
            super().__setitem__(key, value)

    def __delitem__(self, key):
        lower_key = key.lower()
        super().__delitem__(self._lower_to_original[lower_key])
        del self._lower_to_original[lower_key]

    def __contains__(self, key):
        return key.lower() in self._lower_to_original

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

def aggregate_by_level(df: pd.DataFrame,
                      dimensions: Union[str, int, List[Union[str, int]]],
                      measures: List[str]) -> pd.DataFrame:
    """
    Aggregate DataFrame by specified dimensions and measures.

    Args:
        df: DataFrame with hierarchical index
        dimensions: Level name(s) or position(s) to aggregate by
        measures: List of column names to sum

    Returns:
        DataFrame aggregated by specified dimensions
    """
    return df.groupby(level=dimensions)[measures].sum()