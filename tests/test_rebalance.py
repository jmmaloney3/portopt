"""
This module provides test cases for the rebalance module.
"""

import pytest
import pandas as pd
import numpy as np
from portopt.rebalance import PortfolioRebalancer, AccountRebalancer
import portopt.rebalance_utils as rebu
from portopt.utils import write_weights

verbose = True

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

def test_simple_factor_only_rebalance():
    """
    Test a simple rebalance scenario that uses a simple set of tickers and factors and
    only the factor objective (all penalty factors are zero except the account align
    penalty).
    """
    # Create simple account rebalancer
    account_name = 'TestAccount'
    account_rebalancer = rebu.create_simple_account_rebalancer(account_name)

    # rebalance the account
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
    target_factor_allocations_df = account_rebalancer.getTargetFactorAllocations()

    # Check that ticker allocations sum to 100%
    assert np.isclose(ticker_results['New Allocation'].sum(), 1.0)
    # Factor weights are constructed such that final ticker allocations
    # match target factor allocations
    assert np.allclose(ticker_results['New Allocation'], target_factor_allocations_df, atol=0.01)

    # Check that factor allocations sum to 100% and match targets (account is 100% of portfolio)
    assert np.isclose(factor_results['New Allocation'].sum(), 1.0)
    assert np.allclose(factor_results['New Allocation'], target_factor_allocations_df, atol=0.01)

    # Verify the optimization status is optimal
    assert problem.status == 'optimal', \
        f"Expected optimization status 'optimal', got '{problem.status}'"

def test_simple_turnover_only_rebalance():
    """
    Test a simple rebalance scenario that uses a simple set of tickers and factors and
    only the turnover objective (all penalty factors are zero except the turnover
    penalty).
    """
    # Create simple account rebalancer
    account_name = 'TestAccount'
    account_rebalancer = rebu.create_simple_account_rebalancer(account_name,
                                                               account_align_penalty = 0.0,
                                                               turnover_penalty = 1.0)

    # rebalance the account
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
    # Check that ticker allocations sum to 100%
    assert np.isclose(ticker_results['New Allocation'].sum(), 1.0)
    # For this scenario, the ticker allocations should not change from the original
    original_ticker_allocations_df = account_rebalancer.getOriginalTickerAllocations()
    assert np.allclose(ticker_results['New Allocation'], original_ticker_allocations_df, atol=0.01)

    # Check that factor allocations sum to 100%
    assert np.isclose(factor_results['New Allocation'].sum(), 1.0)
    # For this scenario, the factor allocations should not change from the original
    original_factor_allocations_df = account_rebalancer.getOriginalFactorAllocations()
    assert np.allclose(factor_results['New Allocation'], original_factor_allocations_df, atol=0.01)

    # Verify the optimization status is optimal
    assert problem.status == 'optimal', \
        f"Expected optimization status 'optimal', got '{problem.status}'"

def test_simple_complexity_only_rebalance():
    """
    Test a simple rebalance scenario that uses a simple set of tickers and factors and
    only the complexity objective (all penalty factors are zero except the complexity
    penalty).
    """
    # Create simple account rebalancer
    account_name = 'TestAccount'
    account_rebalancer = rebu.create_simple_account_rebalancer(account_name,
                                                               account_align_penalty = 0.0,
                                                               turnover_penalty = 0.0,
                                                               complexity_penalty = 1.0)
    # rebalance the account
    problem = account_rebalancer.rebalance(verbose=verbose)

    if verbose:
        print(f"\nOptimization complete:")
        print(f" - Status: {problem.status}")
        print(f" - Objective value: {problem.value:.12f}")
        print(f" - Number of iterations: {problem.solver_stats.num_iters}")

    # Get results
    ticker_results = account_rebalancer.getTickerResults()
    if verbose:
        write_weights(ticker_results, title="Ticker Results")
    factor_results = account_rebalancer.getFactorResults()
    if verbose:
        write_weights(factor_results, title="Factor Results")

    # Verify results
    # Check that ticker allocations sum to 100%
    assert np.isclose(ticker_results['New Allocation'].sum(), 1.0)

    # For complexity-only scenario, we expect exactly one ticker with 100% allocation
    # and all others with 0% allocation
    non_zero_allocations = ticker_results['New Allocation'][ticker_results['New Allocation'] > 0]
    assert len(non_zero_allocations) == 1, \
        f"Expected exactly one non-zero allocation, got {len(non_zero_allocations)}"
    assert np.isclose(non_zero_allocations.iloc[0], 1.0), \
        f"Expected the non-zero allocation to be 100%, got {non_zero_allocations.iloc[0]:.2%}"

    # Verify the objective value is 1.0 (only one ticker selected)
    assert np.isclose(problem.value, 1.0), \
        f"Expected objective value of 1.0, got {problem.value}"

    # Verify the optimization status is optimal
    assert problem.status == 'optimal', \
        f"Expected optimization status 'optimal', got '{problem.status}'"