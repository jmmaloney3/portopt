"""
This module provides utility functions to assist with creating data structures
required by the rebalance module.
"""

import pandas as pd
import random
from portopt.utils import write_weights
from portopt.rebalance import AccountRebalancer, PortfolioRebalancer
from typing import Union

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
    # Define account proportions
    account_proportions = pd.Series(0.0, index=account_names, name='Proportion')
    account_proportions.index.name = 'Account'
    for account_name in account_names:
        account_proportions[account_name] = round(random.random(), 2)
    # Scale account proportions to sum to 1.0
    account_proportions = account_proportions / account_proportions.sum()
    if verbose:
        write_weights(account_proportions, title="Account Proportions")

    # --------------------------------------------------------------------------
    # Define account ticker allocations
    index = pd.MultiIndex.from_product([account_names, TICKERS], names=['Account', 'Ticker'])
    # Create a Series first, then convert to DataFrame
    ticker_allocations = pd.Series(0.0, index=index, name='Allocation')

    for account_name in account_names:
        if verbose:
            print(f"\n - processing {account_name}")
        for ticker in TICKERS:
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
            scaled_account_allocations = normalized_account_allocations * account_proportions[account_name]
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

    # --------------------------------------------------------------------------
    # Define target factor allocations
    # Generate random allocations for each factor
    original_target_factor_allocations = pd.Series({factor: round(random.random(), 2) for factor in FACTORS})
    original_target_factor_allocations.index.name = 'Factor'
    original_target_factor_allocations.name = 'Allocation'

    normalized_target_factor_allocations = original_target_factor_allocations
    if original_target_factor_allocations.sum() > 0:
        normalized_target_factor_allocations = original_target_factor_allocations / original_target_factor_allocations.sum()

    # Ensure rounding doesn't affect total by adjusting last factor
    total = normalized_target_factor_allocations.sum()
    if total != 1.0:
        normalized_target_factor_allocations[FACTORS[-1]] = normalized_target_factor_allocations[FACTORS[-1]] + (1.0 - total)

    if verbose:
        # create data frame with allocation steps
        allocations_df = pd.DataFrame({
            'Original': original_target_factor_allocations,
            'Normalized': normalized_target_factor_allocations,
            'Final': normalized_target_factor_allocations
        })
        write_weights(allocations_df, title="Allocation Steps for Target Factor Allocations")
        total_allocations = normalized_target_factor_allocations.sum()
        print(f"\nFinal total allocations: {total_allocations:.2%}")

        write_weights(normalized_target_factor_allocations, title="Final Target Factor Allocations")
    # Use normalized target factor allocations as the target factor allocations
    target_factor_allocations = normalized_target_factor_allocations

    # --------------------------------------------------------------------------
    # Define factor weights in long format with MultiIndex
    # Create multi-index Series with factor weights
    index = pd.MultiIndex.from_product([TICKERS, FACTORS], names=['Ticker', 'Factor'])
    factor_weights_series = pd.Series(0.0,index=index, dtype=float)
    factor_weights_series.name = 'Weight'
    for i, ticker in enumerate(TICKERS):
        for j, factor in enumerate(FACTORS):
            # Set weight to 1.0 if indices match, 0.0 otherwise
            if i == j:
                factor_weights_series[(ticker, factor)] = 1.0

    if verbose:
        write_weights(factor_weights_series, title="Final Factor Weights")

    # Use Series as the factor weights
    factor_weights = factor_weights_series

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