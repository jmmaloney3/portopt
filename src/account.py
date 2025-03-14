"""
Account dimension module.

This module provides functions for loading and managing account information
from configuration files.

Functions:
    load_account_dimension: Load account information into a DataFrame
    validate_account_dimension: Validate account dimension data
"""

import pandas as pd
from typing import Optional, Dict, Any
import yaml
from config import default_config

def validate_account_dimension(accounts_dict: Dict[str, Dict[str, Any]]) -> None:
    """
    Validate account configuration data.

    Args:
        accounts_dict: Dictionary of account configurations from YAML

    Raises:
        ValueError: If required fields are missing or invalid
    """
    if not isinstance(accounts_dict, dict):
        raise ValueError("Accounts configuration must be a dictionary")

    required_fields = {'Institution', 'Type', 'Owner'}
    
    for account_name, account_info in accounts_dict.items():
        if not isinstance(account_info, dict):
            raise ValueError(f"Account '{account_name}' configuration must be a dictionary")
            
        missing_fields = required_fields - set(account_info.keys())
        if missing_fields:
            raise ValueError(
                f"Account '{account_name}' is missing required fields: {missing_fields}"
            )

def load_account_dimension(config: Optional[dict] = None) -> pd.DataFrame:
    """
    Load account dimension from configuration.

    Args:
        config: Optional configuration dictionary. If None, loads from default config.

    Returns:
        DataFrame indexed by Account Name with columns:
        - Institution
        - Type
        - Owner
        - Additional columns as defined in config

    Raises:
        ValueError: If account configuration is invalid
        KeyError: If 'accounts' section is missing from config
    """
    # Load configuration if not provided
    if config is None:
        config = default_config()

    # Extract accounts section
    if 'accounts' not in config:
        raise KeyError("Configuration missing 'accounts' section")

    accounts = config['accounts']
    
    # Validate account data
    validate_account_dimension(accounts)
    
    # Convert to DataFrame
    df = pd.DataFrame.from_dict(accounts, orient='index')
    
    # Ensure standard column order for required fields
    standard_columns = ['Institution', 'Type', 'Owner']
    other_columns = [col for col in df.columns if col not in standard_columns]
    df = df[standard_columns + other_columns]
    
    # Set index name
    df.index.name = 'Account Name'
    
    return df