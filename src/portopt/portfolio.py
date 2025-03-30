"""
Portfolio module for managing investment portfolio data and analysis.

This module provides a Portfolio class that serves as a unified interface for accessing
and analyzing portfolio data. It handles:

- Holdings data across multiple accounts
- Account dimension data (institution, type, owner)
- Tickers dimension data (name, long name, type, category, family)
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
from typing import Dict

from .holdings import load_and_consolidate_holdings
from .account import load_account_dimension
from .factor import load_factor_dimension
from .factor import load_factor_weights
from .market_data import get_latest_ticker_prices, get_tickers_info
from .rebalance import RebalanceMixin

"""
Portfolio class for managing investment portfolio data and analysis.

This class provides a unified interface for accessing and analyzing
portfolio data including holdings, accounts, prices, factors, and
factor weights.
"""

class Portfolio(RebalanceMixin):
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
        self._tickers_cache = None

    def getHoldings(self, forceRefresh: bool = False, verbose: bool = False) -> pd.DataFrame:
        """
        Get consolidated holdings data across all accounts.

        Args:
            forceRefresh: If True, force reload from source files. Default is False.
            verbose: If True, print status messages. Default is False.

        Returns:
            DataFrame with hierarchical index [Ticker, Account Name] containing:
            - Quantity
            - Original Value
        """
        if forceRefresh or self._holdings_cache is None:
            self._holdings_cache = load_and_consolidate_holdings(
                *self.holdings_files,
                config=self.config,
                verbose=verbose
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

    def getPrices(self, forceRefresh: bool = False, verbose: bool = False) -> pd.DataFrame:
        """
        Get latest prices for all holdings.

        Args:
            forceRefresh: If True, force refresh from market data source. Default is False.
            verbose: If True, print status messages. Default is False.

        Returns:
            DataFrame indexed by Ticker containing:
            - Price
        """
        if forceRefresh or self._prices_cache is None:
            # Get holdings to extract unique tickers
            holdings = self.getHoldings(verbose=verbose)
            tickers = holdings.index.get_level_values('Ticker').unique()

            # Get latest prices for all tickers
            self._prices_cache = get_latest_ticker_prices(tickers, verbose=verbose)

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

    def getTickers(self, forceRefresh: bool = False, verbose: bool = False) -> pd.DataFrame:
        """
        Get information about all tickers in the portfolio from Yahoo Finance.

        Args:
            forceRefresh: If True, force refresh from Yahoo Finance. Default is False.
            verbose: If True, print status messages for each ticker. Default is False.

        Returns:
            DataFrame indexed by Ticker containing:
            - Name: Short name of the security
            - Long Name: Full name of the security
            - Type: Security type (ETF, MUTUALFUND, EQUITY, etc.)
            - Category: Fund category/investment strategy
            - Family: Fund family/provider name
            Note: Some fields may be NaN if not available for a particular security
        """
        if forceRefresh or self._tickers_cache is None:
            # Get holdings to extract unique tickers
            holdings = self.getHoldings(verbose=verbose)
            tickers = holdings.index.get_level_values('Ticker').unique()

            # Get ticker information from Yahoo Finance
            self._tickers_cache = get_tickers_info(tickers, verbose=verbose)

        return self._tickers_cache

    def getMetrics(
        self,
        *dimensions,
        filters: Dict[str, str] = None,
        portfolio_allocation: bool = False,
        verbose: bool = False,
    ) -> pd.DataFrame:
        """Get portfolio metrics grouped by specified dimensions with optional filtering.

        Args:
            *dimensions: Variable number of dimension names ('Ticker', 'Factor', 'Level_0', etc.)
            filters: Dictionary of filters to apply. Keys are dimension names, values are
                    lists of values to include (single values should be in a list).
                    Example: {'Account': ['IRA', '401k'], 'Level_0': ['Equity']}
            verbose: If True, print the generated SQL query. Default is False.
            portfolio_allocation: If True, calculate allocations relative to total portfolio value
                                If False, calculate relative to filtered portfolio value (default)

        Returns:
            DataFrame: Portfolio metrics including Total Value and Allocation %,
                      grouped by the requested dimensions.

        Example:
            # Get metrics by account for specific accounts
            metrics = portfolio.getMetrics('Account', filters={'Account': ['IRA', '401k']})

            # Get metrics by factor level for equity investments only
            metrics = portfolio.getMetrics('Level_0', 'Level_1', filters={'Level_0': ['Equity']})

            # Get metrics by ticker including security information
            metrics = portfolio.getMetrics('Ticker')  # Includes Name and Type columns
        """
        import duckdb

        # Get required data
        holdings = self.getHoldings(verbose=verbose).reset_index()
        prices = self.getPrices(verbose=verbose).reset_index()
        factors = self.getFactors().reset_index()
        factor_weights = self.getFactorWeights().reset_index()
        tickers = self.getTickers().reset_index() if 'Ticker' in dimensions else None

        # Create DuckDB connection
        con = duckdb.connect()

        try:
            # Register DataFrames as tables
            con.register("holdings", holdings)
            con.register("prices", prices)
            con.register("factors", factors)
            con.register("factor_weights", factor_weights)
            if tickers is not None:
                con.register("tickers", tickers)

            # Construct list of dimension column names to be used in
            # SELECT, GROUP BY, and ORDER BY clauses
            dim_cols = []

            # Flags to control query building
            include_weights = False
            include_quantity = False
            include_ticker_info = False

            if 'Ticker' in dimensions:
                dim_cols.append('h.Ticker')
                include_quantity = True
                include_ticker_info = True

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

            dim_cols_clause = ', '.join(dim_cols)

            if not dim_cols:  # If no dimensions specified, group by 1
                dim_cols_clause = "1"

            # Add ticker info columns if Ticker dimension is included
            ticker_info_cols = ", t.Name, t.Type" if include_ticker_info else ""

            # Build WHERE clause for filters
            where_conditions = []
            if filters:
                for dim, values in filters.items():
                    # Convert single values to list
                    values_list = values if isinstance(values, (list, tuple)) else [values]
                    values_str = ", ".join(f"'{v}'" for v in values_list)

                    if dim == 'Account':
                        where_conditions.append(f"h.Account IN ({values_str})")
                    elif dim == 'Ticker':
                        where_conditions.append(f"h.Ticker IN ({values_str})")
                    elif dim == 'Factor':
                        where_conditions.append(f"f.Factor IN ({values_str})")
                    elif dim.startswith('Level_'):
                        where_conditions.append(f"f.{dim} IN ({values_str})")

            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

            # Build the query
            query = f"""
            WITH portfolio_value AS (
                SELECT SUM(p.Price * h.Quantity{" * w.Weight" if include_weights else ""}) as total
                FROM holdings h
                JOIN prices p ON h.Ticker = p.Ticker
                {"JOIN factor_weights w ON h.Ticker = w.Ticker" if include_weights else ""}
                {"JOIN factors f ON w.Factor = f.Factor" if include_weights else ""}
                {where_clause if not portfolio_allocation else ""}
            )
            SELECT
                {dim_cols_clause}{ticker_info_cols},
                {"SUM(h.Quantity) as Quantity," if include_quantity else ""}
                SUM(p.Price * h.Quantity{" * w.Weight" if include_weights else ""}) as "Total Value",
                SUM(p.Price * h.Quantity{" * w.Weight" if include_weights else ""}) / (
                    SELECT total FROM portfolio_value
                ) as Allocation
            FROM holdings h
                JOIN prices p ON h.Ticker = p.Ticker
                {"JOIN factor_weights w ON h.Ticker = w.Ticker" if include_weights else ""}
                {"JOIN factors f ON w.Factor = f.Factor" if include_weights else ""}
                {"LEFT JOIN tickers t ON h.Ticker = t.Ticker" if include_ticker_info else ""}
            {where_clause}
            GROUP BY {dim_cols_clause}{ticker_info_cols}
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

    def getAccountTickers(self, verbose: bool = False) -> pd.DataFrame:
        """
        Get mapping of valid Account-Ticker pairs.

        Args:
            verbose: If True, print status messages. Default is False.

        Returns:
            DataFrame with hierarchical index [Account, Ticker]
        """
        # Get holdings to extract Account-Ticker pairs
        holdings = self.getHoldings(verbose=verbose)

        # Create DataFrame with Account-Ticker pairs from holdings index
        account_tickers = pd.DataFrame(index=holdings.index)

        return account_tickers