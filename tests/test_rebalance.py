"""
This module provides test cases for the rebalance module.
"""


import pytest
import pandas as pd
import numpy as np
from portopt.rebalance import PortfolioRebalancer, AccountRebalancer
import portopt.rebalance_utils as rebu
from portopt.utils import write_weights

verbose = False

def test_simple_factor_weights():
    """
    Test that the AccountRebalancer creates the factor weights matrix correctly
    based on a long-form factor weights table.
    """
    # Create simple account rebalancer
    account_rebalancer = rebu.create_simple_account_rebalancer('TestAccount')

    # Get factor weights matrix from account rebalancer
    factor_matrix = account_rebalancer.getFactorWeights()
    if verbose:
        write_weights(factor_matrix, title="Factor Matrix")

    # Create factor weights matrix for comparison
    factor_weights_compare = {
        'Factor': ['Factor1', 'Factor2', 'Factor3'],
        'ABCD': [1, 0, 0],
        'EFGH': [0, 1, 0],
        'JKLM': [0, 0, 1]
    }
    factor_weights_compare_df = rebu.create_factor_weights_matrix(factor_weights_compare)

    # Verify that the factor weights matrix is equal
    pd.testing.assert_frame_equal(factor_matrix, factor_weights_compare_df, check_dtype=False)

def test_simple_rebalance():
    """
    Test a simple rebalance scenario that uses a simple set of tickers and factors and
    only the factor objective (all penalty factors are zero except the account align
    penalty).
    """
    # Define original ticker allocations
    ticker_allocations = {
        ('TestAccount', 'ABCD'): 0.40,
        ('TestAccount', 'EFGH'): 0.25,
        ('TestAccount', 'JKLM'): 0.35
    }

    # Define target factor allocations
    #  -- Factor1: 25%, Factor2: 35%, Factor3: 40%
    target_factor_allocations = {
        'Factor1': 0.25,
        'Factor2': 0.35,
        'Factor3': 0.40
    }
    target_factor_allocations_df = rebu.create_target_factor_allocations(target_factor_allocations, verbose=verbose)
    # Define factor weights TABLE
    factor_weights_table = {
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

    # Create account rebalancer
    # -- the dictionaries are passed to this method
    account_name = 'TestAccount'
    account_rebalancer = rebu.create_account_rebalancer(account_name=account_name,
                                                        ticker_allocations=ticker_allocations,
                                                        target_factor_allocations=target_factor_allocations,
                                                        factor_weights=factor_weights_table,
                                                        verbose=verbose)

    problem = account_rebalancer.rebalance(verbose=verbose)

    if verbose:
        print(f"\nOptimization complete:")
        print(f" - Status: {problem.status}")
        print(f" - Objective value: {problem.value:.12f}")

    # Get results
    ticker_results = account_rebalancer.getTickerResults()
    if verbose:
        write_weights(ticker_results, title="Ticker Results")
    factor_results = account_rebalancer.getFactorResults()
    if verbose:
        write_weights(factor_results, title="Factor Results")

    # Verify results

    # Check that allocations sum to 100%
    assert np.isclose(ticker_results['New Allocation'].sum(), 1.0)
    # Factor weights are constructed such that final ticker allocations
    # match target factor allocations
    assert np.allclose(ticker_results['New Allocation'], target_factor_allocations_df, atol=0.01)

    # Check that factor allocations sum to 100% and match targets (account is 100% of portfolio)
    assert np.isclose(factor_results['New Allocation'].sum(), 1.0)
    assert np.allclose(factor_results['New Allocation'], target_factor_allocations_df, atol=0.01)