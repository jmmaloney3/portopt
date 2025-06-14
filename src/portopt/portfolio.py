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
from .metrics import MetricsMixin

"""
Portfolio class for managing investment portfolio data and analysis.

This class provides a unified interface for accessing and analyzing
portfolio data including holdings, accounts, prices, factors, and
factor weights.
"""

class Portfolio(RebalanceMixin, MetricsMixin):
    """
    Portfolio management class that provides access to portfolio data and analysis.

    Attributes:
        config (dict): Configuration dictionary for portfolio settings
        holdings_args (tuple): Arguments for loading holdings data
    """

    def __init__(self,
                 config: dict,
                 factor_weights_file: str | None,
                 *holdings_files):
        """
        Initialize Portfolio instance.

        Args:
            config: Configuration dictionary containing settings (typically from config.load_config())
            factor_weights_file: Optional path to factor weights matrix file. If None, factor-based
                               analysis will not be available.
            *holdings_files: Variable arguments specifying holdings data sources. Can be:
                      - A list of file paths
                      - A directory path containing CSV files
                      - Multiple file path arguments
        """
        if factor_weights_file is not None and not os.path.exists(factor_weights_file):
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

        Raises:
            ValueError: If factor_weights_file is not available
        """
        if forceRefresh or self._factor_weights_cache is None:
            # Get factor dimension data
            factors = self.getFactors()

            # Get weights file path from config
            if not self.factor_weights_file:
                raise ValueError("Factor weights file not provided.")

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

    def getAccountTickers(self, accounts: list[str] | None = None, verbose: bool = False) -> pd.DataFrame:
        """
        Get mapping of valid Account-Ticker pairs.

        Args:
            accounts: Optional list of accounts to include. If None, includes all accounts.
            verbose: If True, print status messages. Default is False.

        Returns:
            DataFrame with hierarchical index [Account, Ticker]

        Example:
            # Get all account-ticker pairs
            all_pairs = portfolio.getAccountTickers()

            # Get pairs for specific accounts
            ira_pairs = portfolio.getAccountTickers(accounts=['IRA', 'Roth IRA'])
        """
        # Get holdings to extract Account-Ticker pairs
        holdings = self.getHoldings(verbose=verbose)

        # Filter by accounts if specified
        if accounts is not None:
            # Convert single account to list if needed
            if isinstance(accounts, str):
                accounts = [accounts]

            # Filter holdings to only include specified accounts
            holdings = holdings[holdings.index.get_level_values('Account').isin(accounts)]

            if verbose:
                print(f"Filtered to {len(accounts)} accounts: {', '.join(accounts)}")

        # Create DataFrame with Account-Ticker pairs from holdings index
        account_tickers = pd.DataFrame(index=holdings.index)

        if verbose:
            print(f"Found {len(account_tickers)} account-ticker pairs")

        return account_tickers