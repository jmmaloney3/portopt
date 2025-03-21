"""
Portfolio module for managing investment portfolio data and analysis.

This module provides a Portfolio class that serves as a unified interface for accessing
and analyzing portfolio data. It handles:

- Holdings data across multiple accounts
- Account dimension data (institution, type, owner)
- Latest security prices
- Factor (asset class) dimension data
- Factor weights for asset allocation analysis
- Portfolio metrics calculation and aggregation

The Portfolio class implements a caching pattern for efficient data access while
allowing forced refresh when needed. It integrates with DuckDB for performant
metric calculations across various portfolio dimensions.

Classes:
    Portfolio: Main class for portfolio data management and analysis

Dependencies:
    - pandas: Data manipulation and analysis
    - duckdb: SQL query execution
    - holdings: Holdings data loading and consolidation
    - account: Account dimension management
    - factor: Factor dimension and weights handling
    - market_data: Security price retrieval
"""

import pandas as pd
import os

from .holdings import load_and_consolidate_holdings
from .account import load_account_dimension
from .factor import load_factor_dimension
from .factor import load_factor_weights
from .market_data import get_latest_ticker_prices

"""
Portfolio class for managing investment portfolio data and analysis.

This class provides a unified interface for accessing and analyzing
portfolio data including holdings, accounts, prices, factors, and
factor weights.
"""

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

    def getMetrics(self, *dimensions, verbose: bool = False):
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

            # Flags to control query building
            include_weights = False
            include_quantity = False

            if 'Ticker' in dimensions:
                dim_cols.append('h.Ticker')
                include_quantity = True

            if 'Account' in dimensions:
                dim_cols.append('h.Account')

            if 'Factor' in dimensions:
                dim_cols.append('f.Factor')
                include_quantity = False
                include_weights = True

            # Add Level_X dimensions if requested
            for dim in dimensions:
                if dim.startswith('Level_'):
                    dim_cols.append(f'f.{dim}')
                    include_quantity = False
                    include_weights = True

            # Build the query
            dim_cols_clause = ', '.join(dim_cols)

            if not dim_cols:  # If no dimensions specified, group by 1
                dim_cols_clause = "1"

            # build query
            query = f"""
            SELECT
                {dim_cols_clause},
                {"SUM(h.Quantity) as Quantity," if include_quantity else ""}
                SUM(p.Price * h.Quantity{" * w.Weight" if include_weights else ""}) as "Total Value",
                SUM(p.Price * h.Quantity{" * w.Weight" if include_weights else ""}) / (
                    SELECT SUM(p.Price * h.Quantity)
                    FROM holdings h
                    JOIN prices p ON h.Ticker = p.Ticker
                ) as Allocation
            FROM holdings h
                JOIN prices p ON h.Ticker = p.Ticker
                {"JOIN factor_weights w ON h.Ticker = w.Ticker" if include_weights else ""}
                {"JOIN factors f ON w.Factor = f.Factor" if include_weights else ""}
            GROUP BY {dim_cols_clause}
            ORDER BY {dim_cols_clause}
            """

            if verbose:
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