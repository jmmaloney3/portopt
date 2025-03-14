"""
Configuration module.

This module provides functions for loading and managing configuration settings
from YAML files.
"""

import os
import yaml
from typing import Dict, Any, Optional
from constants import Constants

def default_config() -> Dict[str, Any]:
    """
    Get default configuration settings.

    Returns:
        Dictionary containing default configuration settings:
        - proxy_funds: Empty dict for mapping private trust tickers to proxy tickers
        - columns: dict for column name mappings with required columns
        - missing_ticker_patterns: Empty dict for identifying missing tickers
        - ignore_tickers: Empty list of tickers to ignore
        - accounts: Empty dict of account metadata
        - asset_class_hierarchy: Empty dict defining asset class hierarchy
    """
    default_config = {
        'proxy_funds': {},
        'columns': {},
        'field_mappings': {},
        'missing_ticker_patterns': {},
        'ignore_tickers': [],
        'accounts': {},
        'asset_class_hierarchy': {}
    }
    default_config['columns'] = {
        Constants.TICKER_COL: {
            'alt_names': ["Symbol", "Investment"],
            'type': "ticker"
        },
        Constants.QUANTITY_COL: {
            'alt_names': ["Shares", "UNIT/SHARE OWNED"],
            'type': "numeric"
        }
    }
    
    return default_config

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Optional path to config YAML file. If None, looks for
                    'config.yml' in current directory.

    Returns:
        Dictionary containing configuration settings merged with defaults.

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    # Start with default config
    config = default_config()

    # If no config file specified, return default config
    if config_path is None:
        return config

    # Load and merge config file if it exists
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:  # Only update if file contains configuration
                    config.update(file_config)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing config file {config_path}: {e}")

    return config
