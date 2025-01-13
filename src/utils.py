import sys
from typing import Dict, Optional, TextIO, Any
import numpy as np
import pandas as pd
import warnings
from statsmodels.tsa.stattools import adfuller, kpss
from sklearn.preprocessing import StandardScaler

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