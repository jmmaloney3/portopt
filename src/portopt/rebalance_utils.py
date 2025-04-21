"""
This module provides utility functions to assist with creating data structures
required by the rebalance module.
"""

import pandas as pd
from portopt.utils import write_weights
from portopt.rebalance import AccountRebalancer, PortfolioRebalancer

def create_factor_weights_table(factor_weights: dict,
                                title: str = "Factor Weights Table") -> pd.DataFrame:
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
    write_weights(factor_weights_df, title=title)

    return factor_weights_df

def create_factor_weights_matrix(factor_weights: dict,
                                 title: str = "Factor Weights Matrix") -> pd.DataFrame:
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
    write_weights(factor_weights_df, title=title)

    return factor_weights_df

def create_ticker_allocations_table(ticker_allocations: dict,
                                    title: str = "Ticker Allocations Table") -> pd.DataFrame:
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
    write_weights(ticker_allocations_df, title=title)

    return ticker_allocations_df

def create_target_factor_allocations(target_factor_allocations: dict,
                                     title: str = "Target Factor Allocations") -> pd.Series:
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
    write_weights(target_factor_allocations_df, title=title)

    return target_factor_allocations_df

def create_account_rebalancer(account_name: str,
                              ticker_allocations: dict,
                              target_factor_allocations: dict,
                              factor_weights: dict) -> AccountRebalancer:
    """
    Create an account rebalancer based on the provided data.  The account_name
    needs to be present in the ticker_allocations dictionary.
    
    The input dictionaries are in the formats required by the following functions:
    - create_ticker_allocations_table
    - create_target_factor_allocations
    - create_factor_weights_table
    """
    ticker_allocations_df = create_ticker_allocations_table(ticker_allocations)
    target_factor_allocations_df = create_target_factor_allocations(target_factor_allocations)
    factor_weights_df = create_factor_weights_table(factor_weights)

    # Create PortfolioRebalancer
    port_rebalancer = PortfolioRebalancer(
        account_ticker_allocations=ticker_allocations_df,
        target_factor_allocations=target_factor_allocations_df,
        factor_weights=factor_weights_df,
        verbose=True
    )
    
    # Get AccountRebalancer instance
    return port_rebalancer.getAccountRebalancer(account_name)

def create_simple_account_rebalancer(account_name: str):
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
                                     factor_weights)
