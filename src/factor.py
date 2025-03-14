"""
Factor (Asset Class) dimension module.

This module provides functions for loading and managing factor (asset class)
information from configuration files.

Functions:
    load_factor_dimension: Load factor hierarchy into a DataFrame
    load_factor_weights: Load factor weights for tickers
    validate_factor_hierarchy: Validate factor hierarchy configuration
"""

import pandas as pd
import numpy as np
from constants import Constants
from typing import Optional, Dict, Any, List, Tuple

def get_hierarchy_depth(hierarchy: Dict[str, Any]) -> int:
    """
    Recursively determine the maximum depth of the hierarchy.

    Args:
        hierarchy: Nested dictionary defining the factor hierarchy

    Returns:
        Maximum depth of the hierarchy (1-based)
    """
    if not isinstance(hierarchy, dict):
        return 0
    if not hierarchy:
        return 0
    return 1 + max(get_hierarchy_depth(v) for v in hierarchy.values())

def find_path_to_factor(hierarchy: dict, target: str, path: list = None) -> List[str]:
    """
    Recursively find the path to a factor in the hierarchy.

    Args:
        hierarchy: Nested dictionary defining the factor hierarchy
        target: Target factor name to find
        path: Current path (used in recursion)

    Returns:
        List of strings representing path to the factor, or None if not found
    """
    if path is None:
        path = []

    for key, value in hierarchy.items():
        if isinstance(value, dict):
            # Recurse into dictionary
            result = find_path_to_factor(value, target, path + [key])
            if result:
                return result
        elif isinstance(value, str) and value == target:
            # Found the target factor
            return path + [key]
    return None

def validate_factor_hierarchy(hierarchy: Dict[str, Any]) -> None:
    """
    Validate factor hierarchy configuration.

    Args:
        hierarchy: Nested dictionary defining the factor hierarchy

    Raises:
        ValueError: If hierarchy is invalid
    """
    if not isinstance(hierarchy, dict):
        raise ValueError("Factor hierarchy must be a dictionary")

    def validate_level(node: Any, path: str) -> set:
        """Recursively validate hierarchy and collect factor names."""
        if isinstance(node, str):
            return {node}
        
        if not isinstance(node, dict):
            raise ValueError(f"Invalid node type at {path}: {type(node)}")
        
        factors = set()
        for key, value in node.items():
            sub_factors = validate_level(value, f"{path}.{key}")
            if sub_factors.intersection(factors):
                raise ValueError(f"Duplicate factor found at {path}.{key}")
            factors.update(sub_factors)
        
        return factors

    validate_level(hierarchy, "root")

def extract_factors_from_hierarchy(hierarchy: Dict[str, Any]) -> Tuple[List[Tuple], List[str]]:
    """
    Extract all factors and their hierarchical paths from the configuration.

    Args:
        hierarchy: Nested dictionary defining the factor hierarchy

    Returns:
        Tuple containing:
        - List of tuples containing level values for each factor
        - List of level names (Level_0, Level_1, etc.)
    """
    factors = []
    max_depth = get_hierarchy_depth(hierarchy)
    level_names = [f'Level_{i}' for i in range(max_depth)]
    
    def process_level(node: Any, path: List[str]):
        if isinstance(node, str):
            # Pad path with None to ensure max_depth levels
            padded_path = path + [None] * (max_depth - len(path))
            factors.append(tuple(padded_path[:max_depth]) + (node,))
        elif isinstance(node, dict):
            for key, value in node.items():
                process_level(value, path + [key])
    
    process_level(hierarchy, [])
    return factors, level_names

def load_factor_dimension(config: Optional[dict] = None) -> pd.DataFrame:
    """
    Load factor dimension from configuration.

    Args:
        config: Optional configuration dictionary. If None, loads from default config.

    Returns:
        DataFrame with dynamically determined hierarchical index [Level_0, Level_1, ...]
        and columns:
        - Factor: The leaf-level factor name
        Additional metadata columns may be added in the future.

    Raises:
        KeyError: If asset_class_hierarchy section is missing from config
        ValueError: If hierarchy is invalid
    """
    # Load configuration if not provided
    if config is None:
        from config import default_config
        config = default_config()

    # Extract and validate hierarchy
    if 'asset_class_hierarchy' not in config:
        raise KeyError("Configuration missing 'asset_class_hierarchy' section")

    hierarchy = config['asset_class_hierarchy']
    validate_factor_hierarchy(hierarchy)
    
    # Extract factors and create DataFrame
    factors, level_names = extract_factors_from_hierarchy(hierarchy)
    df = pd.DataFrame(
        factors,
        columns=level_names + ['Factor']
    )
    
    # Set hierarchical index
    df = df.set_index(level_names)
    
    return df

def get_factors_by_level(factor_dim: pd.DataFrame, level: str) -> pd.Index:
    """
    Get all factors at a specific hierarchy level.

    Args:
        factor_dim: Factor dimension DataFrame from load_factor_dimension()
        level: Hierarchy level name (e.g., Level_0, Level_1, etc.)

    Returns:
        Index of unique values at the specified level
    """
    if level not in factor_dim.index.names:
        raise ValueError(f"Invalid level name: {level}. Valid levels are: {factor_dim.index.names}")
    
    return factor_dim.index.get_level_values(level).unique()

def get_child_factors(factor_dim: pd.DataFrame, parent_factor: str, 
                     parent_level: str) -> pd.DataFrame:
    """
    Get all child factors under a parent factor.

    Args:
        factor_dim: Factor dimension DataFrame from load_factor_dimension()
        parent_factor: Name of the parent factor
        parent_level: Level of the parent factor (e.g., Level_0, Level_1, etc.)

    Returns:
        DataFrame of child factors
    """
    if parent_level not in factor_dim.index.names:
        raise ValueError(f"Invalid parent level name: {parent_level}")
    
    # Get the level number
    level_num = int(parent_level.split('_')[1])
    
    # Verify it's not the last level
    if level_num >= len(factor_dim.index.names) - 1:
        raise ValueError(f"Cannot get child factors for the lowest level: {parent_level}")
    
    # Filter for the parent factor at its level
    mask = factor_dim.index.get_level_values(parent_level) == parent_factor
    
    return factor_dim[mask]

def load_fund_factor_weights(file_path: str) -> pd.DataFrame:
    """
    Load fund factor weights from a CSV file.

    The CSV file should have:
    * First column named 'Ticker' containing fund ticker symbols
    * Additional columns for factors containing factor weights

    The following columns are optional and will be excluded from output:
    * Optional 'Name' column with fund names
    * Optional 'Description' column with fund descriptions
    * Optional 'Accounts' column (will be excluded from output)
    * Optional 'Target' rows (will be excluded from output)

    Args:
        file_path: Path to the CSV file containing fund factor weights

    Returns:
        DataFrame indexed by ticker symbols containing factor weights.
        Factor weights sum to 1 (may include negative weights for leveraged positions).

    Raises:
        ValueError: If file format is invalid or if weights don't sum to 1
        FileNotFoundError: If the file doesn't exist
    """
    try:
        # Read only the header row to determine column types
        headers = pd.read_csv(file_path, nrows=0).columns.tolist()
    except FileNotFoundError:
        raise FileNotFoundError(f"Factor weights file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading factor weights file: {e}")

    if Constants.TICKER_COL not in headers:
        raise ValueError(f"CSV file must contain '{Constants.TICKER_COL}' column")

    # Define dtype for each column
    # - String columns: Ticker, Description, Name, Accounts
    # - Float columns: All others (factor weights)
    dtype_dict = {
        col: float for col in headers
        if col not in [Constants.TICKER_COL, 'Description', 'Name', 'Accounts']
    }

    # Define string handling for non-numeric columns
    converters = {
        Constants.TICKER_COL: lambda x: x.strip(),
        'Description': lambda x: x.strip() if pd.notna(x) else x,
        'Name': lambda x: x.strip() if pd.notna(x) else x,
        'Accounts': lambda x: [item.strip() for item in str(x).split(",")] if pd.notna(x) else []
    }

    try:
        # Read the full file
        data = pd.read_csv(
            file_path,
            dtype=dtype_dict,
            converters=converters
        )
    except Exception as e:
        raise ValueError(f"Error parsing factor weights file: {e}")

    # Set Ticker as index
    data.set_index(Constants.TICKER_COL, inplace=True)

    # Remove Target rows
    data = data[~data.index.str.contains('Target', case=False, na=False)]

    # Remove unnecessary columns if they exist
    optional_columns = ['Accounts', 'Name', 'Description']
    data = data.drop(columns=[col for col in optional_columns if col in data.columns])

    # Fill NaN values with 0
    data = data.fillna(0.0)

    # Verify weights sum to approximately 1
    row_sums = data.sum(axis=1)
    problematic_funds = data.index[~np.isclose(row_sums, 1.0, rtol=1e-3)]
    if not problematic_funds.empty:
        raise ValueError(
            f"Fund weights do not sum to 1 for: {list(problematic_funds)}\n"
            f"Sums: {row_sums[problematic_funds].to_dict()}"
        )

    return data

def load_factor_weights(file_path: str,
                       factor_dim: pd.DataFrame,
                       verbose: bool = False) -> pd.DataFrame:
    """
    Load factor weights for tickers from file and validate against factor dimension.

    Args:
        file_path: Path to CSV file containing fund factor weights
        factor_dim: Factor dimension DataFrame from load_factor_dimension()
        verbose: If True, print status messages

    Returns:
        DataFrame indexed by [Ticker, Factor] containing:
        - Weight: The weight (allocation) of the factor for the ticker

    Example:
        >>> factor_dim = load_factor_dimension()
        >>> weights = load_factor_weights('fund_weights.csv', factor_dim)
        >>> weights.loc['VTSAX']
        Factor
        US Equity: Large Cap Core    0.70
        US Equity: Mid Cap Core      0.20
        US Equity: Small Cap Core    0.10
        Name: VTSAX, dtype: float64

    Raises:
        ValueError: If weights file is invalid or contains undefined factors
        FileNotFoundError: If the file doesn't exist
    """
    # Get valid factors from dimension
    valid_factors = set(factor_dim['Factor'])

    # Load fund weights using existing function
    weights_df = load_fund_factor_weights(file_path)

    # Validate factor columns exist in factor dimension
    invalid_factors = set(weights_df.columns) - valid_factors
    if invalid_factors:
        raise ValueError(f"Found weights for undefined factors: {invalid_factors}")

    # Convert wide format to long format (melting)
    weights_long = weights_df.reset_index().melt(
        id_vars=[Constants.TICKER_COL],
        var_name='Factor',
        value_name='Weight'
    )

    # Filter out zero weights
    weights_long = weights_long[weights_long['Weight'] > 0].copy()

    # Set multi-index and sort
    weights_long = weights_long.set_index([Constants.TICKER_COL, 'Factor']).sort_index()

    if verbose:
        print(f"Loaded weights for {len(weights_long.index.unique(level=Constants.TICKER_COL))} "
              f"funds across {len(weights_long.index.unique(level='Factor'))} factors "
              f"from {file_path}")

    return weights_long