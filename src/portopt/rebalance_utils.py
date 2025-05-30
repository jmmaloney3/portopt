"""
This module provides utility functions to assist with creating data structures
required by the rebalance module.
"""

import pandas as pd
import random
from portopt.utils import write_weights
from portopt.rebalance import AccountRebalancer, PortfolioRebalancer
from typing import Union
import numpy as np

TICKERS = ['ABCD', 'EFGH', 'JKLM', 'NOPQ', 'RSTU', 'VWXY', 'ZABC']
FACTORS = ['Factor1', 'Factor2', 'Factor3', 'Factor4', 'Factor5', 'Factor6', 'Factor7']

def create_factor_weights_table(factor_weights: dict,
                                title: str = "Factor Weights Table",
                                verbose: bool = False) -> pd.DataFrame:
    """
    Create a factor weights TABLE DataFrame based on the provided factor weights
    dictionary.  This is different from the factor weights matrix - which is the
    wide format of the factor weights.

    The dictionary has the following format:
    {
        ('ABCD', 'Factor1'): 1.00,
        ('ABCD', 'Factor2'): 0.00,
        ('ABCD', 'Factor3'): 0.00,
        ('EFGH', 'Factor1'): 0.00,
        ('EFGH', 'Factor2'): 1.00,
        ('EFGH', 'Factor3'): 0.00,
        ('JKLM', 'Factor1'): 0.00,
        ('JKLM', 'Factor2'): 0.00,
        ('JKLM', 'Factor3'): 1.00
    }
    """
    # Convert to Series, then to DataFrame
    factor_weights_df = pd.Series(factor_weights).to_frame(name='Weight')
    factor_weights_df.index.names = ['Ticker', 'Factor']
    if verbose:
        write_weights(factor_weights_df, title=title)

    return factor_weights_df

def create_factor_weights_matrix(factor_weights: dict,
                                 title: str = "Factor Weights Matrix",
                                 verbose: bool = False) -> pd.DataFrame:
    """
    Create a factor weights MATRIX DataFrame based on the provided factor weights
    dictionary.  This is different from the factor weights table - which is
    the long format of the factor weights.

    The dictionary has the following format:
    {
        'Factor': ['Factor1', 'Factor2', 'Factor3'],
        'ABCD': [1, 0, 0],
        'EFGH': [0, 1, 0],
        'JKLM': [0, 0, 1]
    }
    """
    factor_weights_df = pd.DataFrame(factor_weights)
    factor_weights_df = factor_weights_df.set_index('Factor').sort_index().sort_index(axis=1)
    factor_weights_df.columns.name = 'Ticker'  # Set column name to match actual DataFrame
    if verbose:
        write_weights(factor_weights_df, title=title)

    return factor_weights_df

def create_ticker_allocations_table(ticker_allocations: dict,
                                    title: str = "Ticker Allocations Table",
                                    verbose: bool = False) -> pd.DataFrame:
    """
    Create a ticker allocations TABLE DataFrame based on the provided ticker allocations
    dictionary.

    The dictionary has the following format:
    {
        ('TestAccount', 'ABCD'): 0.40,
        ('TestAccount', 'EFGH'): 0.25,
        ('TestAccount', 'JKLM'): 0.35
    }
    """
    ticker_allocations_df = pd.Series(ticker_allocations).to_frame(name='Allocation')
    ticker_allocations_df.index.names = ['Account', 'Ticker']
    if verbose:
        write_weights(ticker_allocations_df, title=title)

    return ticker_allocations_df

def create_target_factor_allocations(target_factor_allocations: dict,
                                     title: str = "Target Factor Allocations",
                                     verbose: bool = False) -> pd.Series:
    """
    Create a target factor allocations Series based on the provided target
    factor allocations dictionary.

    The dictionary has the following format:
    {
        'Factor1': 0.25,
        'Factor2': 0.35,
        'Factor3': 0.40
    }
    """
    target_factor_allocations_df = pd.Series(target_factor_allocations, name='Target Allocation')
    target_factor_allocations_df.index.name = 'Factor'
    if verbose:
        write_weights(target_factor_allocations_df, title=title)

    return target_factor_allocations_df

def create_account_rebalancer(account_name: str,
                              ticker_allocations: Union[dict, pd.DataFrame],
                              target_factor_allocations: Union[dict, pd.Series],
                              factor_weights: Union[dict, pd.DataFrame],
                              min_ticker_alloc: float = 0.0,
                              account_align_penalty: float = 1.0,
                              turnover_penalty: float = 0.0,
                              complexity_penalty: float = 0.0,
                              verbose: bool = False) -> AccountRebalancer:
    """
    Create an account rebalancer based on the provided data. The account_name
    needs to be present in the ticker_allocations dictionary or DataFrame.

    Parameters:
    -----------
    account_name : str
        Name of the account to create a rebalancer for
    ticker_allocations : Union[dict, pd.DataFrame]
        Either a dictionary of account-ticker allocations or a DataFrame with MultiIndex
        ['Account', 'Ticker'] and column 'Allocation'
    target_factor_allocations : Union[dict, pd.Series]
        Either a dictionary of factor allocations or a Series with index 'Factor' and name 'Target Allocation'
    factor_weights : Union[dict, pd.DataFrame]
        Either a dictionary of factor weights or a DataFrame with MultiIndex ['Ticker', 'Factor']
        and column 'Weight'
    min_ticker_alloc : float, optional
        Minimum ticker allocation, by default 0.0
    account_align_penalty : float, optional
        Account alignment penalty, by default 1.0
    turnover_penalty : float, optional
        Turnover penalty, by default 0.0
    complexity_penalty : float, optional
        Complexity penalty, by default 0.0
    verbose : bool, optional
        Whether to print verbose output, by default False

    Returns:
    --------
    AccountRebalancer
        An account rebalancer instance for the specified account
    """
    # Create PortfolioRebalancer
    port_rebalancer = create_portfolio_rebalancer(
        account_ticker_allocations=ticker_allocations,
        target_factor_allocations=target_factor_allocations,
        factor_weights=factor_weights,
        min_ticker_alloc=min_ticker_alloc,
        account_align_penalty=account_align_penalty,
        turnover_penalty=turnover_penalty,
        complexity_penalty=complexity_penalty,
        verbose=verbose
    )

    # Get AccountRebalancer instance
    return port_rebalancer.getAccountRebalancer(account_name)

def create_portfolio_rebalancer(account_ticker_allocations: Union[dict, pd.DataFrame],
                                target_factor_allocations: Union[dict, pd.Series],
                                factor_weights: Union[dict, pd.DataFrame],
                                min_ticker_alloc: float = 0.0,
                                account_align_penalty: float = 1.0,
                                turnover_penalty: float = 0.0,
                                complexity_penalty: float = 0.0,
                                verbose: bool = False) -> PortfolioRebalancer:
    """
    Create a portfolio rebalancer based on the provided data.

    Parameters:
    -----------
    account_ticker_allocations : Union[dict, pd.DataFrame]
        Either a dictionary of account-ticker allocations or a DataFrame with MultiIndex
        ['Account', 'Ticker'] and column 'Allocation'
    target_factor_allocations : Union[dict, pd.Series]
        Either a dictionary of factor allocations or a Series with index 'Factor' and name 'Target Allocation'
    factor_weights : Union[dict, pd.DataFrame]
        Either a dictionary of factor weights or a DataFrame with MultiIndex ['Ticker', 'Factor']
        and column 'Weight'
    min_ticker_alloc : float, optional
        Minimum ticker allocation, by default 0.0
    account_align_penalty : float, optional
        Account alignment penalty, by default 1.0
    turnover_penalty : float, optional
        Turnover penalty, by default 0.0
    complexity_penalty : float, optional
        Complexity penalty, by default 0.0
    verbose : bool, optional
        Whether to print verbose output, by default False

    Returns:
    --------
    PortfolioRebalancer
        A portfolio rebalancer instance
    """
    if verbose:
        print("\n==> create_portfolio_rebalancer()")

    # Convert inputs to appropriate DataFrame/Series format if they're dictionaries
    if isinstance(account_ticker_allocations, dict):
        account_ticker_allocations_df = create_ticker_allocations_table(account_ticker_allocations,
                                                                        verbose=verbose)
    else:
        account_ticker_allocations_df = account_ticker_allocations

    if isinstance(target_factor_allocations, dict):
        target_factor_allocations_df = create_target_factor_allocations(target_factor_allocations,
                                                                        verbose=verbose)
    else:
        target_factor_allocations_df = target_factor_allocations

    if isinstance(factor_weights, dict):
        factor_weights_df = create_factor_weights_table(factor_weights,
                                                        verbose=verbose)
    else:
        factor_weights_df = factor_weights

    # Create PortfolioRebalancer
    port_rebalancer = PortfolioRebalancer(
        account_ticker_allocations=account_ticker_allocations_df,
        target_factor_allocations=target_factor_allocations_df,
        factor_weights=factor_weights_df,
        min_ticker_alloc=min_ticker_alloc,
        account_align_penalty=account_align_penalty,
        turnover_penalty=turnover_penalty,
        complexity_penalty=complexity_penalty,
        verbose=verbose
    )

    if verbose:
        print(f"<== create_portfolio_rebalancer() returned: {port_rebalancer}")

    return port_rebalancer

def create_simple_account_rebalancer(account_name: str,
                                     min_ticker_alloc: float = 0.0,
                                     account_align_penalty: float = 1.0,
                                     turnover_penalty: float = 0.0,
                                     complexity_penalty: float = 0.0,
                                     verbose: bool = False) -> AccountRebalancer:
    """
    Create a simple account rebalancer with simple test data.
    """
    # Define account ticker allocations (account is 100% of portfolio)
    ticker_allocations = {
        (account_name, 'ABCD'): 0.40,
        (account_name, 'EFGH'): 0.25,
        (account_name, 'JKLM'): 0.35
    }

    # Define target factor allocations
    target_factor_allocations = {
        'Factor1': 0.25,
        'Factor2': 0.35,
        'Factor3': 0.40
    }
    
    # Define factor weights in long format with MultiIndex
    factor_weights = {
        ('ABCD', 'Factor1'): 1.00,
        ('ABCD', 'Factor2'): 0.00,
        ('ABCD', 'Factor3'): 0.00,
        ('EFGH', 'Factor1'): 0.00,
        ('EFGH', 'Factor2'): 1.00,
        ('EFGH', 'Factor3'): 0.00,
        ('JKLM', 'Factor1'): 0.00,
        ('JKLM', 'Factor2'): 0.00,
        ('JKLM', 'Factor3'): 1.00
    }

    return create_account_rebalancer(account_name,
                                     ticker_allocations,
                                     target_factor_allocations,
                                     factor_weights,
                                     min_ticker_alloc = min_ticker_alloc,
                                     account_align_penalty = account_align_penalty,
                                     turnover_penalty = turnover_penalty,
                                     complexity_penalty = complexity_penalty,
                                     verbose=verbose)

def create_random_ticker_allocations(
    accounts: pd.Series,
    tickers: list[str],
    verbose: bool = False
) -> pd.Series:
    """
    Create random ticker allocations for a set of accounts.

    For each account:
    1. Randomly assigns allocations to some tickers (75% chance for each ticker)
    2. Normalizes the allocations to sum to 1.0
    3. Scales by the account's proportion of the portfolio

    Args:
        accounts: Series indexed by Account containing the proportion
            of the portfolio held in each account
        tickers: List of tickers to potentially allocate
        verbose: If True, print detailed information about the allocations

    Returns:
        Series with hierarchical index [Account, Ticker] containing allocation
        percentages for each account-ticker pair
    """
    if verbose:
        print("\n==> create_random_ticker_allocations()")

    # Create MultiIndex Series for allocations
    index = pd.MultiIndex.from_product([accounts.index, tickers], names=['Account', 'Ticker'])
    ticker_allocations = pd.Series(0.0, index=index, name='Allocation')

    for account_name in accounts.index:
        if verbose:
            print(f"\n - processing {account_name}")
        for ticker in tickers:
            # randomly generate a boolean to determine whether this
            # account should have an allocation for this ticker
            if random.random() < 0.75:
                allocation = round(random.random(), 2)
                if verbose:
                    print(f"   - {account_name} has {ticker} allocation {allocation}")
                # Set the value in the Series
                ticker_allocations[(account_name, ticker)] = allocation
        # Scale ticker allocations to sum to account proportion for this account
        # - use double brackets to select data for the account to create a "slice"
        #   which preserves the MultiIndex
        original_account_allocations = ticker_allocations.loc[[account_name]]
        # initialize normalized and scaled allocations to the original allocations
        normalized_account_allocations = original_account_allocations
        scaled_account_allocations = original_account_allocations
        if original_account_allocations.sum() > 0:  # Only scale if there are non-zero allocations
            # First normalize the allocations to sum to 1.0
            normalized_account_allocations = original_account_allocations / original_account_allocations.sum()
            # Then scale by the account proportion to get final allocations
            scaled_account_allocations = normalized_account_allocations * accounts[account_name]
        # Set the value in the Series
        ticker_allocations.loc[account_name] = scaled_account_allocations
        if verbose:
            # Create DataFrame with all allocation steps
            allocations_df = pd.DataFrame({
                'Original': original_account_allocations,
                'Normalized': normalized_account_allocations,
                'Scaled': scaled_account_allocations,
                'Final': ticker_allocations.loc[[account_name]]
            })
            # Add sum row to show totals for each column
            write_weights(allocations_df, title=f"Allocation Steps for {account_name}")

    if verbose:
        write_weights(ticker_allocations, title="Final Ticker Allocations")
        total_allocations = ticker_allocations.sum()
        print(f"\nTotal allocations: {total_allocations:.2%}")
        print("\n<== create_random_ticker_allocations()")

    return ticker_allocations

def create_random_factor_allocation(
    factors: list[str],
    verbose: bool = False
) -> pd.Series:
    """
    Create random factor allocations that sum to 100%.

    The process:
    1. Generates random allocations for each factor
    2. Normalizes the allocations to sum to 1.0
    3. Adjusts the last factor to ensure the total is exactly 1.0

    Args:
        factors: List of factors to allocate
        verbose: If True, print detailed information about the allocations

    Returns:
        Series indexed by Factor containing allocation percentages
    """
    if verbose:
        print("\n==> create_random_factor_allocation()")

    # Generate random allocations for each factor
    original_allocations = pd.Series({factor: round(random.random(), 2) for factor in factors})
    original_allocations.index.name = 'Factor'
    original_allocations.name = 'Allocation'

    # Normalize allocations to sum to 1.0
    normalized_allocations = original_allocations
    if original_allocations.sum() > 0:
        normalized_allocations = original_allocations / original_allocations.sum()

    # Ensure rounding doesn't affect total by adjusting last factor
    total = normalized_allocations.sum()
    if total != 1.0:
        normalized_allocations[factors[-1]] = normalized_allocations[factors[-1]] + (1.0 - total)

    if verbose:
        # Create DataFrame with allocation steps
        allocations_df = pd.DataFrame({
            'Original': original_allocations,
            'Normalized': normalized_allocations,
            'Final': normalized_allocations
        })
        write_weights(allocations_df, title="Allocation Steps for Factor Allocations")
        total_allocations = normalized_allocations.sum()
        print(f"\nFinal total allocations: {total_allocations:.2%}")
        write_weights(normalized_allocations, title="Final Factor Allocations")
        print("\n<== create_random_factor_allocation()")

    return normalized_allocations

def create_diagonal_ticker_factor_weights(
    tickers: list[str],
    factors: list[str],
    verbose: bool = False
) -> pd.Series:
    """
    Create a diagonal factor weights matrix where each ticker is assigned to exactly one factor.

    The weights are structured as a Series with MultiIndex [Ticker, Factor] where:
    - Each ticker has a weight of 1.0 for exactly one factor
    - The factor with weight 1.0 is determined by the position of the ticker in the list
    - All other factor weights are 0.0

    Args:
        tickers: List of tickers to assign weights to
        factors: List of factors to assign weights from
        verbose: If True, print detailed information about the weights

    Returns:
        Series with hierarchical index [Ticker, Factor] containing factor weights
    """
    if verbose:
        print("\n==> create_diagonal_ticker_factor_weights()")

    # Create multi-index Series with factor weights
    index = pd.MultiIndex.from_product([tickers, factors], names=['Ticker', 'Factor'])
    factor_weights = pd.Series(0.0, index=index, dtype=float)
    factor_weights.name = 'Weight'

    # Set weight to 1.0 if indices match, 0.0 otherwise
    for i, ticker in enumerate(tickers):
        for j, factor in enumerate(factors):
            if i == j:
                factor_weights[(ticker, factor)] = 1.0

    if verbose:
        write_weights(factor_weights, title="Factor Weights")
        print("\n<== create_diagonal_ticker_factor_weights()")

    return factor_weights

def create_random_ticker_factor_weights(
    tickers: list[str],
    factors: list[str],
    density: float = 1.0,
    verbose: bool = False
) -> pd.Series:
    """
    Create random factor weights where each ticker's weights sum to 100%.

    The weights are structured as a Series with MultiIndex [Ticker, Factor] where:
    - Each ticker's factor weights sum to 1.0
    - The density parameter controls how many factors each ticker is exposed to
    - Non-zero weights are randomly generated and normalized to sum to 1.0
    - If no factors are selected or all weights are zero, assigns 100% to a random factor

    Args:
        tickers: List of tickers to assign weights to
        factors: List of factors to assign weights from
        density: Probability (0.0 to 1.0) that a ticker-factor pair gets a non-zero weight.
            Default is 1.0, meaning all tickers are exposed to all factors.
        verbose: If True, print detailed information about the weights

    Returns:
        Series with hierarchical index [Ticker, Factor] containing factor weights
    """
    if verbose:
        print("\n==> create_random_ticker_factor_weights()")

    # Create multi-index Series with factor weights
    index = pd.MultiIndex.from_product([tickers, factors], names=['Ticker', 'Factor'])
    factor_weights = pd.Series(0.0, index=index, dtype=float)
    factor_weights.name = 'Weight'

    # Generate random weights for each ticker
    for ticker in tickers:
        # First determine which factors this ticker will be exposed to
        active_factors = [factor for factor in factors if random.random() < density]

        if active_factors:  # Only proceed if there are any active factors
            # Generate random weights for active factors
            weights = {factor: round(random.random(), 2) for factor in active_factors}
            # Normalize weights to sum to 1.0
            total = sum(weights.values())
            if total > 0:  # Only normalize if there are non-zero weights
                weights = {factor: weight/total for factor, weight in weights.items()}
                # Set the weights in the Series
                for factor, weight in weights.items():
                    factor_weights[(ticker, factor)] = weight
            else:
                # If all weights are zero, assign 100% to a random factor
                random_factor = random.choice(active_factors)
                factor_weights[(ticker, random_factor)] = 1.0
        else:
            # If no factors were selected, assign 100% to a random factor
            random_factor = random.choice(factors)
            factor_weights[(ticker, random_factor)] = 1.0

    if verbose:
        write_weights(factor_weights, title="Factor Weights")
        # Print summary of factor exposures
        ticker_exposures = factor_weights.groupby(level='Ticker').apply(
            lambda x: sum(x > 0)
        )
        print("\nNumber of factors per ticker:")
        print(ticker_exposures.to_string())

    # Verify that weights sum to 1.0 for each ticker
    ticker_sums = factor_weights.groupby(level='Ticker').sum()
    invalid_tickers = ticker_sums[~np.isclose(ticker_sums, 1.0, rtol=1e-5)]
    if not invalid_tickers.empty:
        raise ValueError(
            f"Factor weights must sum to 100% for each ticker. Found invalid sums for tickers:\n"
            f"{invalid_tickers.to_string()}"
        )

    if verbose:
        print("\n<== create_random_ticker_factor_weights()")

    return factor_weights

def create_random_portfolio_rebalancer(account_names: list[str],
                                       min_ticker_alloc: float = 0.0,
                                       account_align_penalty: float = 1.0,
                                       turnover_penalty: float = 0.0,
                                       complexity_penalty: float = 0.0,
                                       verbose: bool = False) -> PortfolioRebalancer:
    """
    Create a portfolio rebalancer with random test data.
    """
    if verbose:
        print("\n==> create_random_portfolio_rebalancer()")

    # --------------------------------------------------------------------------
    # Define accounts
    accounts = pd.Series(0.0, index=account_names, name='Proportion')
    accounts.index.name = 'Account'
    for account_name in account_names:
        accounts[account_name] = round(random.random(), 2)
    # Scale account proportions to sum to 1.0
    accounts = accounts / accounts.sum()
    if verbose:
        write_weights(accounts, title="Account Proportions")

    # --------------------------------------------------------------------------
    # Define account ticker allocations
    ticker_allocations = create_random_ticker_allocations(
        accounts=accounts,
        tickers=TICKERS,
        verbose=verbose
    )

    # --------------------------------------------------------------------------
    # Define target factor allocations
    target_factor_allocations = create_random_factor_allocation(
        factors=FACTORS,
        verbose=verbose
    )

    # --------------------------------------------------------------------------
    # Define factor weights
    factor_weights = create_diagonal_ticker_factor_weights(
        tickers=TICKERS,
        factors=FACTORS,
        verbose=verbose
    )

    # --------------------------------------------------------------------------
    # Create the rebalancer
    rebalancer = create_portfolio_rebalancer(account_ticker_allocations=ticker_allocations,
                                       target_factor_allocations=target_factor_allocations,
                                       factor_weights=factor_weights,
                                       min_ticker_alloc = min_ticker_alloc,
                                       account_align_penalty = account_align_penalty,
                                       turnover_penalty = turnover_penalty,
                                       complexity_penalty = complexity_penalty,
                                       verbose=verbose)

    if verbose:
        print(f"<== create_random_portfolio_rebalancer() returned: {rebalancer}")

    return rebalancer