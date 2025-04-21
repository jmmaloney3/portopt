"""
This module provides test cases for the rebalance module.
"""

from portopt.rebalance_utils import *
import pytest
import pandas as pd
import numpy as np
from portopt.rebalance import PortfolioRebalancer, AccountRebalancer

def test_simple_factor_weights():
    """
    Test that the AccountRebalancer creates the factor weights matrix correctly
    based on a long-form factor weights table.
    """
    # Create simple account rebalancer
    account_rebalancer = create_simple_account_rebalancer('TestAccount')

    # Get factor weights matrix from account rebalancer
    factor_matrix = account_rebalancer.getFactorWeights()
    from portopt.utils import write_weights
    write_weights(factor_matrix, title="Factor Matrix")

    # Create factor weights matrix for comparison
    factor_weights_compare = {
        'Factor': ['Factor1', 'Factor2', 'Factor3'],
        'ABCD': [1, 0, 0],
        'EFGH': [0, 1, 0],
        'JKLM': [0, 0, 1]
    }
    factor_weights_compare_df = create_factor_weights_matrix(factor_weights_compare)

    # Verify that the factor weights matrix is equal
    pd.testing.assert_frame_equal(factor_matrix, factor_weights_compare_df, check_dtype=False)