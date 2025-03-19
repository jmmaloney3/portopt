"""
Portfolio loading and analysis functions.

This module provides functions for loading and analyzing investment portfolio data,
including fund allocations, holdings, and asset class weights. It supports various
input formats and handles special cases like money market funds and options.

Functions:
    load_fund_asset_class_weights: Load fund asset class allocations from CSV
    load_holdings: Load portfolio holdings from CSV export
    consolidate_holdings: Combine holdings across accounts
    get_holding_allocations: Calculate portfolio allocations by security
    get_asset_class_allocations: Calculate portfolio allocations by asset class
    load_and_consolidate_holdings: Load and consolidate holdings from multiple CSV files
    load_config: Load configuration settings from YAML file

Dependencies:
    - pandas: Data manipulation and analysis
    - numpy: Numerical computing
    - re: Regular expressions for parsing symbols
    - market_data: Local module for retrieving security prices
"""

import re
import csv
import numpy as np
import pandas as pd
from typing import Optional, Union, List, Dict, Any
from market_data import get_latest_ticker_prices
from constants import Constants
import os
import yaml
from utils import CaseInsensitiveDict
from config import default_config

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
        if col not in [Constants.TICKER_COL, 'Description', 'Name', 'Accounts']
    }

    # Define string handling for non-numeric columns
    converters = {
        Constants.TICKER_COL: lambda x: x.strip(),
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
    data.set_index(Constants.TICKER_COL, inplace=True)

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

def get_holding_allocations(holdings: pd.DataFrame, 
                          prices: Optional[pd.DataFrame] = None,
                          verbose: bool = False) -> pd.DataFrame:
    """
    Get holdings with current prices and allocations.

    Args:
        holdings: DataFrame in format produced by load_holdings() or consolidate_holdings()
                 Must have a hierarchical index (Ticker, Account Name)
                 and contain a 'Quantity' column
        prices: Optional DataFrame with price data (default: None)
                If provided, must be indexed by ticker symbols and contain a 'Price' column
                If None, prices will be retrieved using get_latest_ticker_prices()
        verbose: If True, print status messages (default: False)

    Returns:
        DataFrame with hierarchical index (Ticker, Account Name) containing:
        - Quantity
        - Price
        - Total Value (Quantity * Price)
        - Allocation (percentage of total value)

    Example:
        # Using retrieved prices
        holdings = load_holdings('portfolio.csv')
        allocations = get_holding_allocations(holdings)

        # Using provided prices
        prices = get_latest_ticker_prices(holdings.index)
        allocations = get_holding_allocations(holdings, prices=prices)
    """
    if not isinstance(holdings, pd.DataFrame):
        raise ValueError("holdings must be a pandas DataFrame")

    if Constants.QUANTITY_COL not in holdings.columns:
        raise ValueError(f"holdings DataFrame must contain a '{Constants.QUANTITY_COL}' column")

    # Get or validate prices
    tickers = holdings.index.get_level_values('Ticker').unique()
    if prices is None:
        # Get current prices for all tickers
        prices = get_latest_ticker_prices(tickers, verbose=verbose)
    else:
        # Validate provided prices DataFrame
        if not isinstance(prices, pd.DataFrame):
            raise ValueError("prices must be a pandas DataFrame")
        if 'Price' not in prices.columns:
            raise ValueError("prices DataFrame must contain a 'Price' column")
        if not all(ticker in prices.index for ticker in tickers):
            missing_tickers = [ticker for ticker in tickers if ticker not in prices.index]
            raise ValueError(f"Missing prices for tickers: {missing_tickers}")

    if prices['Price'].isna().all():
        raise ValueError("No price data retrieved for holdings")

    # Create result DataFrame preserving hierarchical index
    result = holdings[[Constants.QUANTITY_COL]].copy()

    # Add price and calculated columns
    result['Price'] = prices.loc[result.index.get_level_values('Ticker'), 'Price'].values
    result['Total Value'] = result[Constants.QUANTITY_COL] * result['Price']
    result['Allocation'] = result['Total Value'] / result['Total Value'].sum()

    return result

def get_asset_class_allocations(holdings: pd.DataFrame,
                              asset_class_weights: pd.DataFrame,
                              config: Optional[dict] = None,
                              verbose: bool = False) -> pd.DataFrame:
    """
    Calculate asset class allocations with hierarchical grouping.

    Args:
        holdings: DataFrame with hierarchical index (Ticker, Account Name)
                 containing Total Value column
        asset_class_weights: DataFrame indexed by ticker symbols containing
                           weight columns for each asset class.  Nested dict
                           defining the hierarchy of asset classes
                 Example:
                 {
                     'Equity': {
                         'US': {
                             'Large Cap': {
                                 'Growth': 'US Large Cap Growth',
                                 'Value': 'US Large Cap Value'
                             }
                         }
                     }
                 }
        config: Configuration dictionary containing asset_class_hierarchy
        verbose: If True, print status messages

    Returns:
        DataFrame with hierarchical index (Asset Class Levels, Ticker, Account Name)
        containing:
        - Total Value (dollar amount allocated)
        - Allocation (percentage of total portfolio)
    Example:
        holdings = get_holding_allocations(portfolio_df)[0]  # Get holdings with values
        weights = load_fund_asset_class_weights('asset_classes.csv')
        allocations = get_asset_class_allocations(holdings, weights,
                                                  config=config,
                                                  verbose=verbose)

    """
    def find_path_to_asset_class(hierarchy: dict, target: str, path: list = None) -> list:
        """Recursively find the path to an asset class in the hierarchy."""
        if path is None:
            path = []

        for key, value in hierarchy.items():
            if isinstance(value, dict):
                # Recurse into dictionary
                result = find_path_to_asset_class(value, target, path + [key])
                if result:
                    return result
            elif isinstance(value, str) and value == target:
                # Found the target asset class
                return path + [key]
        return None

    def get_max_depth(hierarchy: dict, depth: int = 0) -> int:
        """Recursively find the maximum depth of the hierarchy."""
        if not isinstance(hierarchy, dict):
            return depth
        if not hierarchy:
            return depth
        return max(get_max_depth(v, depth + 1) if isinstance(v, dict) else depth + 1
                  for v in hierarchy.values())

    # Initialize data storage
    data = []
    total_portfolio_value = holdings['Total Value'].sum()

    if verbose:
        print(f"Initial portfolio value: ${total_portfolio_value:,.2f}")

    # Calculate allocations
    allocated_value = 0.0
    for ticker, account in holdings.index:
        if ticker in asset_class_weights.index:
            position_value = holdings.loc[(ticker, account), 'Total Value']

            # Get weights for this ticker
            weights = asset_class_weights.loc[ticker]
            weights = weights[weights > 0]  # Only keep non-zero weights
            weight_sum = weights.sum()

            # Normalize weights if they sum to more than 1.0
            if weight_sum > 1.0:
                if verbose:
                    print(f"Warning: {ticker} weights sum to {weight_sum:.3f}, normalizing")
                weights = weights / weight_sum

            ticker_allocated = 0.0
            for asset_class, weight in weights.items():
                # Find path in hierarchy
                path = find_path_to_asset_class(config['asset_class_hierarchy'],
                                                asset_class) if config else []
                if not path:
                    path = ['Unclassified']

                value = position_value * weight
                ticker_allocated += value
                allocated_value += value

                # Store all components
                data.append({
                    'Level_0': path[0] if len(path) > 0 else 'Unclassified',
                    'Level_1': path[1] if len(path) > 1 else None,
                    'Level_2': path[2] if len(path) > 2 else None,
                    'Level_3': path[3] if len(path) > 3 else None,
                    'Ticker': ticker,
                    'Account Name': account,
                    'Total Value': value,
                    'Allocation': value / total_portfolio_value
                })

            if verbose and not np.isclose(ticker_allocated, position_value, rtol=1e-3):
                print(f"Warning: {ticker} in {account} allocated {ticker_allocated:,.2f} "
                      f"vs position value {position_value:,.2f}")

    if verbose:
        print(f"Total allocated value: ${allocated_value:,.2f}")
        print(f"Allocation percentage: {(allocated_value/total_portfolio_value)*100:.2f}%")

    # Create DataFrame
    result = pd.DataFrame(data)

    # Set up hierarchical index
    index_levels = ['Level_0', 'Level_1', 'Level_2', 'Level_3', 'Ticker', 'Account Name']
    result = result.set_index(['Level_0', 'Level_1', 'Level_2', 'Level_3', 'Ticker', 'Account Name'])
    result.index.names = index_levels

    # Sort index
    result = result.sort_index()

    return result

"""
Portfolio class for managing investment portfolio data and analysis.

This class provides a unified interface for accessing and analyzing
portfolio data including holdings, accounts, prices, factors, and
factor weights.
"""

from holdings import load_and_consolidate_holdings
from config import load_config
from account import load_account_dimension
from factor import load_factor_dimension
from factor import load_factor_weights
from market_data import get_latest_ticker_prices

class Portfolio:
    """
    Portfolio management class that provides access to portfolio data and analysis.

    Attributes:
        config (dict): Configuration dictionary for portfolio settings
        holdings_args (tuple): Arguments for loading holdings data
    """

    def __init__(self,
                 config: dict,
                 factor_weights_file: str,
                 *holdings_files):
        """
        Initialize Portfolio instance.

        Args:
            config: Configuration dictionary containing settings (typically from config.load_config())
            factor_weights_file: Path to factor weights matrix file
            *holdings_files: Variable arguments specifying holdings data sources. Can be:
                      - A list of file paths
                      - A directory path containing CSV files
                      - Multiple file path arguments
        """
        if not os.path.exists(factor_weights_file):
            raise ValueError(f"Factor weights file not found: {factor_weights_file}")

        self.config = config
        self.holdings_files = holdings_files
        self.factor_weights_file = factor_weights_file

        # Initialize cache
        self._holdings_cache = None
        self._accounts_cache = None
        self._prices_cache = None
        self._factors_cache = None
        self._factor_weights_cache = None

    def getHoldings(self, forceRefresh: bool = False) -> pd.DataFrame:
        """
        Get consolidated holdings data across all accounts.

        Args:
            forceRefresh: If True, force reload from source files. Default is False.

        Returns:
            DataFrame with hierarchical index [Ticker, Account Name] containing:
            - Quantity
            - Original Value
        """
        if forceRefresh or self._holdings_cache is None:
            self._holdings_cache = load_and_consolidate_holdings(
                *self.holdings_files,
                config=self.config
            )
        return self._holdings_cache

    def getAccounts(self, forceRefresh: bool = False) -> pd.DataFrame:
        """
        Get account dimension data.

        Args:
            forceRefresh: If True, force reload from configuration. Default is False.

        Returns:
            DataFrame indexed by Account Name containing:
            - Institution
            - Type
            - Owner
            - Additional configured columns
        """
        if forceRefresh or self._accounts_cache is None:
            self._accounts_cache = load_account_dimension(self.config)
        return self._accounts_cache

    def getPrices(self, forceRefresh: bool = False) -> pd.DataFrame:
        """
        Get latest prices for all holdings.

        Args:
            forceRefresh: If True, force refresh from market data source. Default is False.

        Returns:
            DataFrame indexed by Ticker containing:
            - Price
        """
        if forceRefresh or self._prices_cache is None:
            # Get holdings to extract unique tickers
            holdings = self.getHoldings()
            tickers = holdings.index.get_level_values('Ticker').unique()

            # Get latest prices for all tickers
            self._prices_cache = get_latest_ticker_prices(tickers)

        return self._prices_cache

    def getFactors(self, forceRefresh: bool = False) -> pd.DataFrame:
        """
        Get factor (asset class) dimension data.

        Args:
            forceRefresh: If True, force reload from configuration. Default is False.

        Returns:
            DataFrame with hierarchical index [Level_0, Level_1, ...] containing:
            - Factor
        """
        if forceRefresh or self._factors_cache is None:
            self._factors_cache = load_factor_dimension(self.config)
        return self._factors_cache

    def getFactorWeights(self, forceRefresh: bool = False) -> pd.DataFrame:
        """
        Get factor weights for all holdings.

        Args:
            forceRefresh: If True, force reload from source files. Default is False.

        Returns:
            DataFrame indexed by [Ticker, Factor] containing:
            - Weight
        """
        if forceRefresh or self._factor_weights_cache is None:
            # Get factor dimension data
            factors = self.getFactors()

            # Get weights file path from config
            if not self.factor_weights_file:
                raise ValueError("factor_weights_file not specified in config")

            # Load factor weights
            self._factor_weights_cache = load_factor_weights(
                self.factor_weights_file,
                factors
            )
        return self._factor_weights_cache

    def getMetrics(self, *dimensions):
        """Get portfolio metrics grouped by specified dimensions.

        Args:
            *dimensions: Variable number of dimension names ('Ticker', 'Factor', 'Level_0', etc.)
                       Note: 'Account' dimension is temporarily disabled

        Returns:
            DataFrame: Portfolio metrics including Total Value and Allocation %,
                      grouped by the requested dimensions.

        Example:
            # Get metrics by account
            metrics = portfolio.getMetrics('Account')

            # Get metrics by factor level and account
            metrics = portfolio.getMetrics('Level_0', 'Account')
        """
        import duckdb

        # Get required data
        holdings = self.getHoldings().reset_index()
        prices = self.getPrices().reset_index()
        factors = self.getFactors().reset_index()
        factor_weights = self.getFactorWeights().reset_index()

        # Create DuckDB connection
        con = duckdb.connect()

        try:
            # Register DataFrames as tables
            con.register("holdings", holdings)
            con.register("prices", prices)
            con.register("factors", factors)
            con.register("factor_weights", factor_weights)

            # Construct list of dimension column names to be used in
            # SELECT, GROUP BY, and ORDER BY clauses
            dim_cols = []
            includes_factors = False

            if 'Ticker' in dimensions:
                dim_cols.append('h.Ticker')

            #if 'Account' in dimensions:
            #    dim_cols.append('h.Account')

            if 'Factor' in dimensions:
                dim_cols.append('f.Factor')
                includes_factors = True
            # Add Level_X dimensions if requested
            for dim in dimensions:
                if dim.startswith('Level_'):
                    dim_cols.append(f'f.{dim}')
                    includes_factors = True

            # Build the query
            dim_cols_clause = ', '.join(dim_cols)

            if not dim_cols:  # If no dimensions specified, group by 1
                dim_cols_clause = "1"

            # build query
            query = f"""
            SELECT
                {dim_cols_clause},
                {"SUM(h.Quantity) as Quantity," if not includes_factors else ""}
                SUM(p.Price * h.Quantity{" * w.Weight" if includes_factors else ""}) as "Total Value",
                SUM(p.Price * h.Quantity{" * w.Weight" if includes_factors else ""}) / (
                    SELECT SUM(p.Price * h.Quantity)
                    FROM holdings h
                    JOIN prices p ON h.Ticker = p.Ticker
                ) as Allocation
            FROM holdings h
                JOIN prices p ON h.Ticker = p.Ticker
                {"JOIN factor_weights w ON h.Ticker = w.Ticker" if includes_factors else ""}
                {"JOIN factors f ON w.Factor = f.Factor" if includes_factors else ""}
            GROUP BY {dim_cols_clause}
            ORDER BY {dim_cols_clause}
            """

            print(query)

            # Execute query and get results
            result = con.execute(query).df()

            # Set index based on dimensions
            if dimensions:
                result.set_index(list(dimensions), inplace=True)

            return result

        except Exception as e:
            raise RuntimeError(f"Error executing metrics query: {str(e)}") from e

        finally:
            # Ensure connection is closed
            con.close()