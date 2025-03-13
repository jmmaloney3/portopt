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
        from portfolio import load_config
        config = load_config()

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
