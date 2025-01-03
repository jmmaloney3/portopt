import sys
from typing import Dict, Optional, TextIO, Any
import numpy as np
import pandas as pd

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
    
    # If no columns specified, create default format for all DataFrame columns
    if columns is None:
        columns = {col: {} for col in df.columns}
    
    # Get list of columns to display
    display_cols = list(columns.keys())
    display_df = df[display_cols]
    
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
    header_strs = [formats[col]['hdr_fmt'].format(col) for col in display_cols]
    print(' '.join(header_strs), file=stream)
    
    # Create separator line
    sep_strs = [formats[col]['sep'] * formats[col]['width'] for col in display_cols]
    print(' '.join(sep_strs), file=stream)
    
    # Print data rows
    for _, row in display_df.iterrows():
        data_strs = []
        for col in display_cols:
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