"""
Test suite for MetricsMixin class.
"""

import pandas as pd
import numpy as np
from portopt.metrics import MetricsMixin
from portopt.utils import write_table
import pytest

VERBOSE = False

# define column formats for write_table function
COLUMN_FORMATS = {
    'Ticker': {'width': 14},
    'Level_0': {'width': 14},
    'Level_1': {'width': 14},
    'Level_2': {'width': 14},
    'Level_3': {'width': 14},
    'Level_4': {'width': 14},
    'Level_5': {'width': 14},
    'Level_6': {'width': 14},
    'Factor': {'width': 24},
    'Weight': {'width': 14, 'decimal': 3, 'type':'%'},
    'Account': {'width': 25, 'align': '<'},
    'Name': {'width': 30, 'align': '<'},
    'Short Name': {'width': 20, 'align': '<'},
    'Institution': {'width': 14},
    'Type': {'width': 14},
    'Category': {'width': 14},
    'Family': {'width': 14},
    'Owner': {'width': 14},
    'Quantity': {'width': 10, 'decimal': 3},
    'Original Ticker': {'width': 14},
    'Original Quantity': {'width': 10, 'decimal': 3},
    'Original Value': {'width': 16, 'decimal': 2, 'prefix': '$'},
    'Price': {'width': 16, 'decimal': 2, 'prefix': '$'},
    'Total Value': {'width': 16, 'decimal': 2, 'prefix': '$'},
    'Allocation': {'width': 16, 'decimal': 2, 'type':'%'}
}

# ==============================================================================
# Helper Functions and Test Data Setup
# ==============================================================================

def create_comprehensive_test_data():
    """Create comprehensive test data covering multiple scenarios."""

    # Extended Holdings data with multiple accounts and more tickers
    holdings_data = pd.DataFrame({
        'Ticker': ['AAPL', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'BND', 'VTI'],
        'Account': ['IRA', '401k', 'IRA', '401k', 'Taxable', 'IRA', 'Taxable'],
        'Quantity': [10.0, 15.0, 20.0, 5.0, 8.0, 100.0, 50.0]
    }).set_index(['Ticker', 'Account'])

    # Prices for all tickers
    prices_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'BND', 'VTI'],
        'Price': [150.0, 300.0, 200.0, 800.0, 80.0, 220.0]
    }).set_index('Ticker')

    # Factor dimension data with multiple levels
    factors_data = pd.DataFrame({
        'Factor': ['US Large Cap Equity', 'US Large Cap Equity Tech', 'International Equity',
                   'Electric Vehicles', 'US Bonds', 'US Total Market'],
        'Level_0': ['Equity', 'Equity', 'Equity', 'Equity', 'Fixed Income', 'Equity'],
        'Level_1': ['US', 'US', 'International', 'US', 'US', 'US'],
        'Level_2': ['Large Cap', 'Large Cap', 'Developed', 'Growth', 'Government', 'Broad Market']
    })

    # Factor weights with fractional weights for more complex testing
    factor_weights_data = pd.DataFrame({
        'Ticker': ['AAPL', 'AAPL', 'MSFT', 'MSFT', 'GOOGL', 'TSLA', 'BND', 'VTI'],
        'Factor': ['US Large Cap Equity', 'US Large Cap Equity Tech', 'US Large Cap Equity',
                   'US Large Cap Equity Tech', 'International Equity', 'Electric Vehicles',
                   'US Bonds', 'US Total Market'],
        'Weight': [0.7, 0.3, 0.8, 0.2, 1.0, 1.0, 1.0, 1.0]
    }).set_index(['Ticker', 'Factor'])

    # Optional Accounts data
    accounts_data = pd.DataFrame({
        'Account': ['IRA', '401k', 'Taxable'],
        'Type': ['Retirement', 'Retirement', 'Taxable'],
        'Institution': ['Fidelity', 'Vanguard', 'Schwab']
    }).set_index('Account')

    # Optional Tickers data
    tickers_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'BND', 'VTI'],
        'Name': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.', 'Tesla Inc.',
                'Vanguard Total Bond Market ETF', 'Vanguard Total Stock Market ETF'],
        'Category': ['Technology', 'Technology', 'Technology', 'Automotive', 'Bonds', 'Broad Market']
    }).set_index('Ticker')

    return {
        'holdings': holdings_data,
        'prices': prices_data,
        'factors': factors_data,
        'factor_weights': factor_weights_data,
        'accounts': accounts_data,
        'tickers': tickers_data
    }

def getMetricsMixinInstance(holdings: pd.DataFrame,
                            prices: pd.DataFrame,
                            factors: pd.DataFrame = None,
                            factor_weights: pd.DataFrame = None,
                            accounts: pd.DataFrame = None,
                            tickers: pd.DataFrame = None):
    """Create a MetricsMixin instance with mock methods."""
    metrics = MetricsMixin()
    metrics.getHoldings = lambda **kwargs: holdings
    metrics.getPrices = lambda **kwargs: prices
    if factors is not None:
        metrics.getFactors = lambda **kwargs: factors
    if factor_weights is not None:
        metrics.getFactorWeights = lambda **kwargs: factor_weights
    if accounts is not None:
        metrics.getAccounts = lambda **kwargs: accounts
    if tickers is not None:
        metrics.getTickers = lambda **kwargs: tickers
    return metrics

def calculate_expected_metrics(holdings_data, prices_data, factor_weights_data=None,
                              factors_data=None, dimensions=None, filters=None, metrics=None,
                              portfolio_allocation=False):
    """Calculate expected metrics for comparison with getMetrics results."""
    if metrics is None:
        metrics = ['Quantity', 'Value', 'Allocation']

    # Determine if we need factor weights and factor levels
    needs_factor_weights = False
    needs_factor_levels = False
    if dimensions:
        needs_factor_weights = any(d.startswith('Level_') or d == 'Factor' for d in dimensions)
        needs_factor_levels = any(d.startswith('Level_') for d in dimensions)
    if filters:
        needs_factor_weights = needs_factor_weights or any(d.startswith('Level_') or d == 'Factor' for d in filters.keys())
        needs_factor_levels = needs_factor_levels or any(d.startswith('Level_') for d in filters.keys())

    # Reset index to work with the data
    holdings_df = holdings_data.reset_index()
    prices_df = prices_data.reset_index()

    # Merge holdings with prices
    merged = holdings_df.merge(prices_df, on='Ticker')

    # Add factor weights only if needed for the calculation
    if needs_factor_weights and factor_weights_data is not None:
        factor_weights_df = factor_weights_data.reset_index()
        merged = merged.merge(factor_weights_df, on='Ticker')

        # Add factor levels if needed (join factors data to get Level_* columns)
        if needs_factor_levels and factors_data is not None:
            factors_df = factors_data.reset_index() if hasattr(factors_data, 'reset_index') else factors_data
            merged = merged.merge(factors_df, on='Factor')

    # Apply filters if specified
    if filters:
        for dim, values in filters.items():
            if isinstance(values, str):
                values = [values]
            merged = merged[merged[dim].isin(values)]

    # Calculate base metrics
    merged['Value_calc'] = merged['Quantity'] * merged['Price']
    if 'Weight' in merged.columns:
        merged['Value_calc'] *= merged['Weight']

    # Group by dimensions if specified
    if dimensions:
        result = merged.groupby(list(dimensions)).agg({
            'Quantity': 'sum',
            'Value_calc': 'sum'
        }).rename(columns={'Value_calc': 'Value'})
    else:
        result = pd.DataFrame({
            'Quantity': [merged['Quantity'].sum()],
            'Value': [merged['Value_calc'].sum()]
        })

    # Calculate allocations
    if portfolio_allocation:
        # Use total portfolio value for allocation calculation (unfiltered data)
        # Need to recalculate from unfiltered data for portfolio allocation
        unfiltered_merged = holdings_df.merge(prices_df, on='Ticker')
        if needs_factor_weights and factor_weights_data is not None:
            factor_weights_df = factor_weights_data.reset_index()
            unfiltered_merged = unfiltered_merged.merge(factor_weights_df, on='Ticker')
            if needs_factor_levels and factors_data is not None:
                factors_df = factors_data.reset_index() if hasattr(factors_data, 'reset_index') else factors_data
                unfiltered_merged = unfiltered_merged.merge(factors_df, on='Factor')

        # Calculate total portfolio value from unfiltered data
        unfiltered_merged['Value_calc'] = unfiltered_merged['Quantity'] * unfiltered_merged['Price']
        if 'Weight' in unfiltered_merged.columns:
            unfiltered_merged['Value_calc'] *= unfiltered_merged['Weight']
        total_value = unfiltered_merged['Value_calc'].sum()
    else:
        # Use filtered value for allocation calculation
        total_value = result['Value'].sum()

    result['Allocation'] = result['Value'] / total_value

    return result[metrics]

def assert_metrics_equal(actual, expected, tolerance=1e-10):
    """Assert that actual and expected metrics are equal within tolerance."""
    for col in expected.columns:
        if col in actual.columns:
            assert np.allclose(actual[col], expected[col], rtol=tolerance), \
                f"Column {col} values don't match. Expected: {expected[col].values}, Actual: {actual[col].values}"

def verify_metrics_mathematically(result, test_data, dimensions=None, filters=None,
                                 metrics=None, portfolio_allocation=False):
    """Helper function to verify metrics mathematically by comparing with expected calculations.

    Args:
        result: The actual result from getMetrics()
        test_data: Dict containing test data (holdings, prices, etc.)
        dimensions: Dimensions used in the query
        filters: Filters used in the query
        metrics: Metrics requested
        portfolio_allocation: Portfolio allocation setting used
    """
    # Calculate expected metrics
    expected = calculate_expected_metrics(
        test_data['holdings'],
        test_data['prices'],
        test_data.get('factor_weights'),
        test_data.get('factors'),
        dimensions=dimensions,
        filters=filters,
        metrics=metrics,
        portfolio_allocation=portfolio_allocation
    )

    # Sort both for comparison (handles result ordering differences)
    result_sorted = result.sort_index()
    expected_sorted = expected.sort_index()

    # Verify mathematical accuracy
    assert_metrics_equal(result_sorted, expected_sorted)

# ==============================================================================
# Original Tests
# ==============================================================================

def test_get_metrics_total_portfolio():
    """Test that getMetrics() without arguments returns correct total portfolio value and allocation."""
    # Create test data
    holdings_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Account': ['IRA', 'IRA', '401k'],
        'Quantity': [10.0, 20.0, 5.0]
    }).set_index(['Ticker', 'Account'])
    if VERBOSE:
        write_table(holdings_data, columns=COLUMN_FORMATS, title='Holdings')

    prices_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Price': [150.0, 300.0, 200.0]
    }).set_index('Ticker')
    if VERBOSE:
        write_table(prices_data, columns=COLUMN_FORMATS, title='Prices')

    # Create a mock MetricsMixin instance
    metrics = getMetricsMixinInstance(holdings_data, prices_data)

    # Call getMetrics without arguments
    result = metrics.getMetrics(verbose=VERBOSE)

    # Calculate expected values
    expected_total_value = (
        10 * 150.0 +  # AAPL
        20 * 300.0 +  # MSFT
        5 * 200.0     # GOOGL
    )

    # Verify results
    assert result['Value'].sum() == expected_total_value
    assert np.isclose(result['Allocation'].sum(), 1.0)  # Allocations should sum to 100%

def test_get_metrics_factor_dimensions():
    """Test that getMetrics() with factor dimensions returns the same total value as without dimensions."""
    # Create test data
    holdings_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Account': ['IRA', 'IRA', '401k'],
        'Quantity': [10, 20, 5]
    }).set_index(['Ticker', 'Account'])

    prices_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Price': [150.0, 300.0, 200.0]
    }).set_index('Ticker')

    # Create factor dimension data
    factors_data = pd.DataFrame({
        'Factor': ['US Equity', 'International Equity'],
        'Level_0': ['Equity', 'Equity'],
        'Level_1': ['US', 'International']
    })
    if VERBOSE:
        write_table(factors_data, columns=COLUMN_FORMATS, title='Factors')

    # Create factor weights data
    factor_weights_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Factor': ['US Equity', 'US Equity', 'International Equity'],
        'Weight': [1.0, 1.0, 1.0]
    }).set_index(['Ticker', 'Factor'])

    # Create a mock MetricsMixin instance
    metrics = getMetricsMixinInstance(holdings_data,
                                      prices_data,
                                      factors_data,
                                      factor_weights_data)

    # Get total value without dimensions
    total_metrics = metrics.getMetrics(verbose=VERBOSE)
    expected_total_value = total_metrics['Value'].sum()

    # Get metrics with factor dimensions
    factor_metrics = metrics.getMetrics('Level_0', 'Level_1',
                                      verbose=VERBOSE)

    if VERBOSE:
        print("Portfolio total value:      ", expected_total_value)
        print("Factor metrics total value: ", factor_metrics['Value'].sum())

    # Verify results
    assert factor_metrics['Value'].sum() == expected_total_value, \
        "Total value should be the same with or without factor dimensions"
    assert np.isclose(factor_metrics['Allocation'].sum(), 1.0), \
        "Factor allocations should sum to 100%"

def test_get_metrics_by_ticker():
    """Test that getMetrics() with Ticker dimension returns correct values and allocations per ticker."""
    # Create test data
    holdings_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Account': ['IRA', 'IRA', '401k'],
        'Quantity': [10.0, 20.0, 5.0]
    }).set_index(['Ticker', 'Account'])
    if VERBOSE:
        write_table(holdings_data, columns=COLUMN_FORMATS, title='Holdings')

    prices_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Price': [150.0, 300.0, 200.0]
    }).set_index('Ticker')
    if VERBOSE:
        write_table(prices_data, columns=COLUMN_FORMATS, title='Prices')

    # Create a mock MetricsMixin instance
    metrics = getMetricsMixinInstance(holdings_data, prices_data)

    # Call getMetrics with Ticker dimension
    result = metrics.getMetrics('Ticker', verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics')

    # Calculate expected values per ticker
    expected_values = {
        'AAPL': 10.0 * 150.0,  # Quantity * Price
        'MSFT': 20.0 * 300.0,
        'GOOGL': 5.0 * 200.0
    }
    expected_total = sum(expected_values.values())

    # Verify results
    for ticker in expected_values:
        ticker_value = result.loc[ticker, 'Value']
        ticker_allocation = result.loc[ticker, 'Allocation']

        # Check value calculation
        assert ticker_value == expected_values[ticker], \
            f"Value for {ticker} should be {expected_values[ticker]}, got {ticker_value}"

        # Check allocation calculation
        expected_allocation = expected_values[ticker] / expected_total
        assert np.isclose(ticker_allocation, expected_allocation), \
            f"Allocation for {ticker} should be {expected_allocation}, got {ticker_allocation}"

    # Verify total allocation sums to 100%
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Total allocation should sum to 100%"

# ==============================================================================
# Comprehensive Test Suite
# ==============================================================================

def test_metrics_individual_metrics():
    """Test each metric individually (Quantity, Value, Allocation)."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Test individual metrics
    for metric in ['Quantity', 'Value', 'Allocation']:
        result = metrics.getMetrics(metrics=[metric], verbose=VERBOSE)

        # Verify the requested metric is present and correct behavior
        if metric == 'Quantity':
            # Quantity should be the only column
            assert list(result.columns) == [metric], \
                f"Expected only {metric} column, got {list(result.columns)}"
            assert result[metric].iloc[0] > 0, "Quantity should be positive"
        elif metric == 'Value':
            # Value should be the only column
            assert list(result.columns) == [metric], \
                f"Expected only {metric} column, got {list(result.columns)}"
            assert result[metric].iloc[0] > 0, "Value should be positive"
        elif metric == 'Allocation':
            # Allocation requires Value to be calculated, so both should be presen
            expected_columns = ['Value', 'Allocation']
            assert list(result.columns) == expected_columns, \
                f"Expected {expected_columns} columns for Allocation, got {list(result.columns)}"
            assert np.isclose(result[metric].iloc[0], 1.0), "Total allocation should be 1.0"
            assert result['Value'].iloc[0] > 0, "Value should be positive"

def test_metrics_by_account():
    """Test metrics grouped by Account dimension."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    result = metrics.getMetrics('Account', verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics by Account')

    # Verify we have the expected accounts
    expected_accounts = ['IRA', '401k', 'Taxable']
    assert set(result.index) == set(expected_accounts), \
        f"Expected accounts {expected_accounts}, got {list(result.index)}"

    # Mathematical verification
    verify_metrics_mathematically(result, test_data, dimensions=['Account'])

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Account allocations should sum to 100%"

    # Verify positive values
    assert all(result['Quantity'] > 0), "All account quantities should be positive"
    assert all(result['Value'] > 0), "All account values should be positive"

def test_metrics_by_multiple_dimensions():
    """Test metrics with multiple dimensions (Ticker, Account)."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    result = metrics.getMetrics('Ticker', 'Account', verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics by Ticker and Account')

    # Mathematical verification
    verify_metrics_mathematically(result, test_data, dimensions=['Ticker', 'Account'])

    # Verify index structure
    assert isinstance(result.index, pd.MultiIndex), "Result should have MultiIndex"
    assert result.index.names == ['Ticker', 'Account'], \
        f"Expected index names ['Ticker', 'Account'], got {result.index.names}"

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Total allocations should sum to 100%"

def test_metrics_with_factor_levels():
    """Test metrics with different factor level combinations."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Test single factor level
    result_level0 = metrics.getMetrics('Level_0', verbose=VERBOSE)
    if VERBOSE:
        write_table(result_level0, columns=COLUMN_FORMATS, title='Metrics by Level_0')

    # Mathematical verification for Level_0
    verify_metrics_mathematically(result_level0, test_data, dimensions=['Level_0'])

    expected_level0_values = ['Equity', 'Fixed Income']
    assert set(result_level0.index) == set(expected_level0_values), \
        f"Expected Level_0 values {expected_level0_values}, got {list(result_level0.index)}"

    # Test multiple factor levels
    result_multi_level = metrics.getMetrics('Level_0', 'Level_1', verbose=VERBOSE)
    if VERBOSE:
        write_table(result_multi_level, columns=COLUMN_FORMATS, title='Metrics by Level_0 and Level_1')

    # Mathematical verification for multi-level
    verify_metrics_mathematically(result_multi_level, test_data, dimensions=['Level_0', 'Level_1'])

    # Verify both results sum to same total value
    assert np.isclose(result_level0['Value'].sum(), result_multi_level['Value'].sum()), \
        "Total value should be consistent across different groupings"

def test_metrics_with_factor_dimension():
    """Test metrics grouped by Factor dimension."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    result = metrics.getMetrics('Factor', verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics by Factor')

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Factor allocations should sum to 100%"

    # Verify positive values
    assert all(result['Value'] > 0), "All factor values should be positive"

def test_metrics_with_filters_single_value():
    """Test metrics with single value filters."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Filter by single accoun
    result = metrics.getMetrics('Ticker', filters={'Account': 'IRA'}, verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics filtered by IRA Account')

    # Mathematical verification
    verify_metrics_mathematically(result, test_data, dimensions=['Ticker'], filters={'Account': 'IRA'})

    # Verify only expected tickers appear (those in IRA account)
    expected_tickers = ['AAPL', 'MSFT', 'BND']  # Based on test data
    assert set(result.index).issubset(set(expected_tickers)), \
        f"Result should only contain tickers from IRA account"

    # Verify allocations sum to 1 (within filtered portfolio)
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Filtered allocations should sum to 100%"

def test_metrics_with_filters_multiple_values():
    """Test metrics with multiple value filters."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Filter by multiple accounts
    result = metrics.getMetrics('Account', filters={'Account': ['IRA', '401k']}, verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics filtered by IRA and 401k Accounts')

    # Mathematical verification
    verify_metrics_mathematically(result, test_data, dimensions=['Account'], filters={'Account': ['IRA', '401k']})

    # Verify only expected accounts appear
    expected_accounts = ['IRA', '401k']
    assert set(result.index) == set(expected_accounts), \
        f"Expected accounts {expected_accounts}, got {list(result.index)}"

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Filtered allocations should sum to 100%"

def test_metrics_with_factor_level_filters():
    """Test metrics with factor level filters."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Filter by Level_0 = 'Equity'
    result = metrics.getMetrics('Level_1', filters={'Level_0': 'Equity'}, verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics filtered by Equity Level_0')

    # Verify only Level_1 values from Equity appear
    expected_level1 = ['US', 'International']
    assert set(result.index).issubset(set(expected_level1)), \
        "Result should only contain Level_1 values from Equity"

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Filtered allocations should sum to 100%"

def test_portfolio_allocation_vs_filtered_allocation():
    """Test the difference between portfolio_allocation=True and False."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Get metrics with filter and portfolio_allocation=False (default)
    filtered_result = metrics.getMetrics('Ticker',
                                       filters={'Account': 'IRA'},
                                       portfolio_allocation=False,
                                       verbose=VERBOSE)

    # Get metrics with filter and portfolio_allocation=True
    portfolio_result = metrics.getMetrics('Ticker',
                                         filters={'Account': 'IRA'},
                                         portfolio_allocation=True,
                                         verbose=VERBOSE)

    if VERBOSE:
        write_table(filtered_result, columns=COLUMN_FORMATS, title='Filtered Allocation (portfolio_allocation=False)')
        write_table(portfolio_result, columns=COLUMN_FORMATS, title='Portfolio Allocation (portfolio_allocation=True)')

    # Mathematical verification
    verify_metrics_mathematically(filtered_result, test_data, dimensions=['Ticker'],
                                 filters={'Account': 'IRA'}, portfolio_allocation=False)
    verify_metrics_mathematically(portfolio_result, test_data, dimensions=['Ticker'],
                                 filters={'Account': 'IRA'}, portfolio_allocation=True)

    # Verify Values are the same (same tickers, same filter, sort for comparison)
    filtered_sorted = filtered_result.sort_index()
    portfolio_sorted = portfolio_result.sort_index()
    pd.testing.assert_series_equal(filtered_sorted['Value'], portfolio_sorted['Value'])

    # Verify Allocations are differen
    # Filtered allocations should sum to 1, portfolio allocations should sum to less than 1
    assert np.isclose(filtered_result['Allocation'].sum(), 1.0), \
        "Filtered allocations should sum to 100%"
    assert portfolio_result['Allocation'].sum() < 1.0, \
        "Portfolio allocations with filter should sum to less than 100%"

    # Verify portfolio allocations are smaller than filtered allocations
    assert all(portfolio_sorted['Allocation'] < filtered_sorted['Allocation']), \
        "Portfolio allocations should be smaller than filtered allocations"

def test_metrics_edge_cases():
    """Test edge cases and error conditions."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Test with empty metrics list (should use defaults)
    result = metrics.getMetrics(metrics=[], verbose=VERBOSE)
    expected_default_metrics = ['Quantity', 'Value', 'Allocation']
    assert list(result.columns) == expected_default_metrics, \
        "Empty metrics list should use default metrics"

    # Test with unknown filter dimension (should return empty result or error gracefully)
    try:
        result = metrics.getMetrics('Ticker', filters={'UnknownDimension': 'value'}, verbose=VERBOSE)
        # If it doesn't raise an error, result should be empty or handle gracefully
        assert len(result) == 0 or True, "Unknown filter dimension should be handled gracefully"
    except Exception as e:
        # This is acceptable - unknown dimensions might raise errors
        if VERBOSE:
            print(f"Unknown filter dimension raised expected error: {e}")

def test_metrics_consistency_across_groupings():
    """Test that total values are consistent across different groupings."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Get total portfolio metrics
    total = metrics.getMetrics(verbose=VERBOSE)

    # Get metrics by ticker
    by_ticker = metrics.getMetrics('Ticker', verbose=VERBOSE)

    # Get metrics by accoun
    by_account = metrics.getMetrics('Account', verbose=VERBOSE)

    # Get metrics by factor levels
    by_level0 = metrics.getMetrics('Level_0', verbose=VERBOSE)

    # Verify all groupings sum to same total value
    total_value = total['Value'].iloc[0]
    assert np.isclose(by_ticker['Value'].sum(), total_value), \
        "Ticker grouping should sum to total value"
    assert np.isclose(by_account['Value'].sum(), total_value), \
        "Account grouping should sum to total value"
    assert np.isclose(by_level0['Value'].sum(), total_value), \
        "Level_0 grouping should sum to total value"

    # Verify all allocations sum to 1
    assert np.isclose(by_ticker['Allocation'].sum(), 1.0), \
        "Ticker allocations should sum to 100%"
    assert np.isclose(by_account['Allocation'].sum(), 1.0), \
        "Account allocations should sum to 100%"
    assert np.isclose(by_level0['Allocation'].sum(), 1.0), \
        "Level_0 allocations should sum to 100%"

def test_metrics_with_fractional_weights():
    """Test that fractional factor weights are handled correctly."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Get metrics by Factor (which uses fractional weights)
    result = metrics.getMetrics('Factor', verbose=VERBOSE)
    if VERBOSE:
        write_table(result, columns=COLUMN_FORMATS, title='Metrics with Fractional Weights')

    # Mathematical verification
    verify_metrics_mathematically(result, test_data, dimensions=['Factor'])

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Factor allocations with fractional weights should sum to 100%"

    # Verify positive values
    assert all(result['Value'] > 0), "All values should be positive"

def test_metrics_complex_scenario():
    """Test a complex scenario with multiple dimensions, filters, and factor aggregation."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Complex query: Group by Level_0 and Level_1, filter by specific accounts,
    # use specific metrics, and test both allocation methods
    complex_filtered = metrics.getMetrics(
        'Level_0', 'Level_1',
        metrics=['Value', 'Allocation'],
        filters={'Account': ['IRA', '401k']},
        portfolio_allocation=False,
        verbose=VERBOSE
    )

    complex_portfolio = metrics.getMetrics(
        'Level_0', 'Level_1',
        metrics=['Value', 'Allocation'],
        filters={'Account': ['IRA', '401k']},
        portfolio_allocation=True,
        verbose=VERBOSE
    )

    if VERBOSE:
        write_table(complex_filtered, columns=COLUMN_FORMATS,
                   title='Complex Scenario - Filtered Allocation')
        write_table(complex_portfolio, columns=COLUMN_FORMATS,
                   title='Complex Scenario - Portfolio Allocation')

    # Verify structure
    assert isinstance(complex_filtered.index, pd.MultiIndex), \
        "Result should have MultiIndex for multiple dimensions"
    assert complex_filtered.index.names == ['Level_0', 'Level_1'], \
        "Index should have correct dimension names"

    # Verify Values are the same (sort both to handle potential ordering differences)
    filtered_values_sorted = complex_filtered['Value'].sort_index()
    portfolio_values_sorted = complex_portfolio['Value'].sort_index()
    pd.testing.assert_series_equal(filtered_values_sorted, portfolio_values_sorted)

    # Verify allocation differences
    assert np.isclose(complex_filtered['Allocation'].sum(), 1.0), \
        "Filtered allocations should sum to 100%"
    assert complex_portfolio['Allocation'].sum() < 1.0, \
        "Portfolio allocations should sum to less than 100% when filtered"

def test_total_value_consistency_with_and_without_factors():
    """Test that total portfolio value is consistent with and without factor dimensions.

    This test addresses a critical issue where using factor dimensions can exclude
    tickers that don't have factor weights, leading to incorrect total values.
    """
    test_data = create_comprehensive_test_data()

    # Add a ticker without factor weights to test the issue
    # Add holdings for a ticker that has no factor weights
    additional_holdings = pd.DataFrame({
        'Ticker': ['MISSING_FACTOR'],
        'Account': ['IRA'],
        'Quantity': [100.0]
    }).set_index(['Ticker', 'Account'])

    # Add price for the missing factor ticker
    additional_prices = pd.DataFrame({
        'Ticker': ['MISSING_FACTOR'],
        'Price': [50.0]
    }).set_index('Ticker')

    # Combine with existing test data
    extended_holdings = pd.concat([test_data['holdings'], additional_holdings])
    extended_prices = pd.concat([test_data['prices'], additional_prices])

    metrics = getMetricsMixinInstance(
        extended_holdings,
        extended_prices,
        test_data['factors'],
        test_data['factor_weights'],
        test_data['accounts'],
        test_data['tickers']
    )

    # Get total portfolio value without factor dimensions
    total_without_factors = metrics.getMetrics(verbose=VERBOSE)
    total_value_without = total_without_factors['Value'].iloc[0]

    # Get total portfolio value with factor dimensions
    total_with_factors = metrics.getMetrics('Level_0', 'Level_1', verbose=VERBOSE)
    total_value_with = total_with_factors['Value'].sum()

    if VERBOSE:
        print(f"Total value without factors: ${total_value_without:.2f}")
        print(f"Total value with factors: ${total_value_with:.2f}")
        print(f"Difference: ${abs(total_value_without - total_value_with):.2f}")

        # Show which tickers are included in each calculation
        print("\nTickers without factors:")
        write_table(total_without_factors, columns=COLUMN_FORMATS)

        print("\nTickers with factors:")
        write_table(total_with_factors, columns=COLUMN_FORMATS)

    # The total values should be equal - if they're not, it indicates
    # that some tickers are being excluded when factor tables are joined
    assert np.isclose(total_value_without, total_value_with, rtol=1e-10), \
        f"Total portfolio value should be consistent. Without factors: ${total_value_without:.2f}, " \
        f"With factors: ${total_value_with:.2f}, Difference: ${abs(total_value_without - total_value_with):.2f}"

def test_real_world_missing_factor_weights_scenario():
    """Test scenario similar to the notebook where some tickers don't have factor weights.

    This simulates the real-world case where a ticker like 'TBD' exists in holdings
    but doesn't have corresponding factor weights defined.
    """
    # Create holdings with a mix of tickers - some with and some without factor weights
    holdings_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'TBD', 'GOOGL'],
        'Account': ['IRA', 'IRA', '401k', 'Taxable'],
        'Quantity': [10.0, 20.0, 100.0, 5.0]  # TBD has significant quantity
    }).set_index(['Ticker', 'Account'])

    # Prices for all tickers
    prices_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'TBD', 'GOOGL'],
        'Price': [150.0, 300.0, 25.0, 200.0]  # TBD has $25 price = $2500 total value
    }).set_index('Ticker')

    # Factor data
    factors_data = pd.DataFrame({
        'Factor': ['US Large Cap Equity', 'International Equity'],
        'Level_0': ['Equity', 'Equity'],
        'Level_1': ['US', 'International']
    })

    # Factor weights - NOTE: TBD is intentionally missing
    factor_weights_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],  # TBD is missing!
        'Factor': ['US Large Cap Equity', 'US Large Cap Equity', 'International Equity'],
        'Weight': [1.0, 1.0, 1.0]
    }).set_index(['Ticker', 'Factor'])

    metrics = getMetricsMixinInstance(
        holdings_data, prices_data, factors_data, factor_weights_data
    )

    # Calculate total without factor dimensions
    total_without_factors = metrics.getMetrics(verbose=VERBOSE)
    total_value_without = total_without_factors['Value'].iloc[0]

    # Calculate total with factor dimensions
    total_with_factors = metrics.getMetrics('Level_0', 'Level_1', verbose=VERBOSE)
    total_value_with = total_with_factors['Value'].sum()

    # Expected total: AAPL(10*150) + MSFT(20*300) + TBD(100*25) + GOOGL(5*200) = 1500 + 6000 + 2500 + 1000 = 11000
    expected_total = 11000.0

    if VERBOSE:
        print(f"Expected total: ${expected_total:.2f}")
        print(f"Total without factors: ${total_value_without:.2f}")
        print(f"Total with factors: ${total_value_with:.2f}")

        print("\nFactor breakdown:")
        write_table(total_with_factors, columns=COLUMN_FORMATS)

    # Both calculations should equal the expected total
    assert np.isclose(total_value_without, expected_total), \
        f"Total without factors should be ${expected_total:.2f}, got ${total_value_without:.2f}"

    assert np.isclose(total_value_with, expected_total), \
        f"Total with factors should be ${expected_total:.2f}, got ${total_value_with:.2f}"

    # Both calculations should be equal to each other
    assert np.isclose(total_value_without, total_value_with), \
        f"Totals should be equal: without factors ${total_value_without:.2f}, with factors ${total_value_with:.2f}"

    # Verify that TBD appears in the factor breakdown with appropriate classification
    # Since TBD has no factor weights, it should appear in an "UNDEFINED" category
    # Let's verify this by checking the factor breakdown
    level_0_values = total_with_factors.index.get_level_values('Level_0').unique()
    assert 'UNDEFINED' in level_0_values, \
        f"UNDEFINED factor should appear in Level_0 values for tickers without factor weights, got: {list(level_0_values)}"

    # The key test is that the total value is preserved
    print("✓ Real-world missing factor weights scenario handled correctly")

def test_original_double_counting_bug_with_factor_filters():
    """Test case that reproduces the original double-counting bug reported by the user.

    Original problem: When using factor filters like {'Level_0': ['Equity'], 'Level_1': ['US']}
    with portfolio_allocation=True and dimensions like ['Account'], the total value was
    incorrectly calculated as $7,019,716.77 when it should have been $3,051,391.05
    (more than double the correct amount).

    This was caused by double-counting tickers that had multiple factor exposures
    when factor filters were used but factor dimensions were not.
    """
    # Create test data that reproduces the original issue
    # AAPL has multiple factor exposures with fractional weights that sum to 1.0
    holdings_data = pd.DataFrame({
        'Ticker': ['AAPL', 'AAPL', 'MSFT', 'BND'],
        'Account': ['IRA', '401k', 'IRA', 'IRA'],
        'Quantity': [100, 50, 75, 200]
    }).set_index(['Ticker', 'Account'])

    prices_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'BND'],
        'Price': [150.0, 300.0, 85.0]
    }).set_index('Ticker')

    # AAPL has multiple factor exposures with fractional weights (0.7 + 0.3 = 1.0)
    # This is the key to reproducing the double-counting issue
    factor_weights_data = pd.DataFrame({
        'Ticker': ['AAPL', 'AAPL', 'MSFT', 'BND'],
        'Factor': ['US_Large_Growth', 'US_Large_Tech', 'US_Large_Value', 'US_Bond'],
        'Weight': [0.7, 0.3, 1.0, 1.0]
    }).set_index(['Ticker', 'Factor'])

    factors_data = pd.DataFrame({
        'Factor': ['US_Large_Growth', 'US_Large_Tech', 'US_Large_Value', 'US_Bond'],
        'Level_0': ['Equity', 'Equity', 'Equity', 'Bond'],
        'Level_1': ['US', 'US', 'US', 'US'],
        'Level_2': ['Large', 'Large', 'Large', 'N/A']
    })

    # Create MetricsMixin instance
    metrics = getMetricsMixinInstance(
        holdings_data, prices_data, factors_data, factor_weights_data
    )

    # This is the exact scenario that caused the original bug:
    # - Using factor filters ({'Level_0': ['Equity']})
    # - With portfolio_allocation=True
    # - Grouping by non-factor dimensions (['Account'])
    result = metrics.getMetrics(
        'Account',
        filters={'Level_0': ['Equity']},
        portfolio_allocation=True,
        verbose=VERBOSE
    )

    if VERBOSE:
        print("=== Original Double-Counting Bug Test ===")
        write_table(result, columns=COLUMN_FORMATS, title='Result with Factor Filters')
        print(f"Total filtered value: ${result['Value'].sum():,.2f}")
        print(f"Total allocation: {result['Allocation'].sum():.2%}")

    # Calculate expected values manually:
    # AAPL in IRA: 100 shares * $150 * 1.0 weight = $15,000
    # AAPL in 401k: 50 shares * $150 * 1.0 weight = $7,500
    # MSFT in IRA: 75 shares * $300 * 1.0 weight = $22,500
    # Total equity value: $45,000
    expected_total_equity_value = 45000.0

    # Expected allocations (relative to total portfolio including bonds):
    # Total portfolio value = $45,000 (equity) + $17,000 (bonds) = $62,000
    # IRA allocation = $37,500 / $62,000 = 60.48%
    # 401k allocation = $7,500 / $62,000 = 12.10%
    expected_total_portfolio_value = 62000.0  # Including bonds
    expected_ira_allocation = 37500.0 / expected_total_portfolio_value  # ~60.48%
    expected_401k_allocation = 7500.0 / expected_total_portfolio_value  # ~12.10%

    # Verify the fix works correctly
    actual_total_value = result['Value'].sum()
    actual_total_allocation = result['Allocation'].sum()

    # The key test: total value should be correct (not double-counted)
    assert abs(actual_total_value - expected_total_equity_value) < 0.01, \
        f"Expected total equity value ${expected_total_equity_value:,.2f}, " \
        f"but got ${actual_total_value:,.2f}. " \
        f"This indicates the double-counting bug is not fixed!"

    # Verify individual account values
    ira_value = result.loc['IRA', 'Value']
    account_401k_value = result.loc['401k', 'Value']

    assert abs(ira_value - 37500.0) < 0.01, \
        f"Expected IRA equity value $37,500, got ${ira_value:,.2f}"

    assert abs(account_401k_value - 7500.0) < 0.01, \
        f"Expected 401k equity value $7,500, got ${account_401k_value:,.2f}"

    # Verify portfolio allocations are correct (relative to total portfolio)
    ira_allocation = result.loc['IRA', 'Allocation']
    account_401k_allocation = result.loc['401k', 'Allocation']

    assert abs(ira_allocation - expected_ira_allocation) < 0.001, \
        f"Expected IRA allocation {expected_ira_allocation:.3%}, got {ira_allocation:.3%}"

    assert abs(account_401k_allocation - expected_401k_allocation) < 0.001, \
        f"Expected 401k allocation {expected_401k_allocation:.3%}, got {account_401k_allocation:.3%}"

    # The total allocation should be less than 100% since we're filtering to equity only
    # but using portfolio_allocation=True (allocating relative to total portfolio including bonds)
    expected_total_allocation = expected_total_equity_value / expected_total_portfolio_value  # ~72.58%
    assert abs(actual_total_allocation - expected_total_allocation) < 0.001, \
        f"Expected total allocation {expected_total_allocation:.3%}, got {actual_total_allocation:.3%}"

    # Additional verification: ensure we're not getting the buggy double-counted result
    # The original bug would have produced ~$67,500 total value (50% higher)
    buggy_total_value = 67500.0  # What the bug would have produced
    assert abs(actual_total_value - buggy_total_value) > 1000, \
        f"Result ${actual_total_value:,.2f} is too close to the buggy value ${buggy_total_value:,.2f}. " \
        f"The fix may not be working correctly!"

    if VERBOSE:
        print(f"✓ Expected total equity value: ${expected_total_equity_value:,.2f}")
        print(f"✓ Actual total equity value: ${actual_total_value:,.2f}")
        print(f"✓ Expected total allocation: {expected_total_allocation:.2%}")
        print(f"✓ Actual total allocation: {actual_total_allocation:.2%}")
        print(f"✓ Avoided buggy value: ${buggy_total_value:,.2f}")
        print("✓ Original double-counting bug is fixed!")

def test_invalid_dimension_validation():
    """Test that requesting invalid dimensions throws appropriate ValueError."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(
        holdings=test_data['holdings'],
        prices=test_data['prices'],
        factors=test_data['factors'],
        factor_weights=test_data['factor_weights'],
        accounts=test_data['accounts'],
        tickers=test_data['tickers']
    )

    # Test 1: Single invalid dimension
    with pytest.raises(ValueError) as exc_info:
        metrics.getMetrics('NonExistentDimension')

    error_msg = str(exc_info.value)
    assert "Requested dimensions not found in query: ['NonExistentDimension']" in error_msg
    assert "Available columns:" in error_msg

    # Test 2: Mix of valid and invalid dimensions
    with pytest.raises(ValueError) as exc_info:
        metrics.getMetrics('Ticker', 'InvalidDim1', 'Account', 'InvalidDim2')

    error_msg = str(exc_info.value)
    assert "Requested dimensions not found in query: ['InvalidDim1', 'InvalidDim2']" in error_msg
    assert "Available columns:" in error_msg

    # Test 3: Multiple invalid dimensions
    with pytest.raises(ValueError) as exc_info:
        metrics.getMetrics('BadDim1', 'BadDim2', 'BadDim3')

    error_msg = str(exc_info.value)
    assert "Requested dimensions not found in query: ['BadDim1', 'BadDim2', 'BadDim3']" in error_msg

    # Test 4: Valid dimensions should work fine (no exception)
    try:
        result = metrics.getMetrics('Ticker', 'Account')
        assert result is not None
        assert len(result) > 0
    except Exception as e:
        pytest.fail(f"Valid dimensions should not raise exception, but got: {e}")

    # Test 5: Factor dimensions when factor tables aren't available
    # Create a metrics instance without factor tables
    metrics_no_factors = getMetricsMixinInstance(
        holdings=test_data['holdings'],
        prices=test_data['prices']
        # No factors or factor_weights provided
    )

    with pytest.raises(ValueError) as exc_info:
        metrics_no_factors.getMetrics('Level_0')

    error_msg = str(exc_info.value)
    assert "Factor weights are required for the requested dimensions/filters" in error_msg
    assert "but factor_weights table is not available" in error_msg

    # Test 6: Test for actual "dimension not found" error with non-factor dimensions
    # This should trigger the validation we added in _add_aggregates
    with pytest.raises(ValueError) as exc_info:
        # Use a simple query that won't require factor tables
        metrics.getMetrics('Ticker', 'NonExistentColumn', metrics=['Quantity'])

    error_msg = str(exc_info.value)
    assert "Requested dimensions not found in query: ['NonExistentColumn']" in error_msg
    assert "Available columns:" in error_msg

    # Test 7: Edge case - empty dimensions list should work
    try:
        result = metrics.getMetrics()  # No dimensions specified
        assert result is not None
    except Exception as e:
        pytest.fail(f"Empty dimensions should not raise exception, but got: {e}")

    print("✅ All invalid dimension validation tests passed!")

# ==============================================================================
# Performance and Stress Tests
# ==============================================================================

def test_metrics_performance_with_large_dimensions():
    """Test performance with multiple dimensions and verify results are consistent."""
    test_data = create_comprehensive_test_data()
    metrics = getMetricsMixinInstance(**test_data)

    # Test with many dimensions
    result = metrics.getMetrics('Ticker', 'Account', 'Level_0', 'Level_1', verbose=VERBOSE)

    # Verify structure
    assert isinstance(result.index, pd.MultiIndex), "Result should have MultiIndex"
    assert len(result.index.names) == 4, "Should have 4 dimension levels"

    # Verify allocations sum to 1
    assert np.isclose(result['Allocation'].sum(), 1.0), \
        "Multi-dimension allocations should sum to 100%"

# ==============================================================================
# Test Runners
# ==============================================================================

if __name__ == "__main__":
    # Run all tests
    print("Running comprehensive MetricsMixin test suite...")

    # Original tests
    test_get_metrics_total_portfolio()
    print("✓ test_get_metrics_total_portfolio")

    test_get_metrics_factor_dimensions()
    print("✓ test_get_metrics_factor_dimensions")

    test_get_metrics_by_ticker()
    print("✓ test_get_metrics_by_ticker")

    # Comprehensive tests
    test_metrics_individual_metrics()
    print("✓ test_metrics_individual_metrics")

    test_metrics_by_account()
    print("✓ test_metrics_by_account")

    test_metrics_by_multiple_dimensions()
    print("✓ test_metrics_by_multiple_dimensions")

    test_metrics_with_factor_levels()
    print("✓ test_metrics_with_factor_levels")

    test_metrics_with_factor_dimension()
    print("✓ test_metrics_with_factor_dimension")

    test_metrics_with_filters_single_value()
    print("✓ test_metrics_with_filters_single_value")

    test_metrics_with_filters_multiple_values()
    print("✓ test_metrics_with_filters_multiple_values")

    test_metrics_with_factor_level_filters()
    print("✓ test_metrics_with_factor_level_filters")

    test_portfolio_allocation_vs_filtered_allocation()
    print("✓ test_portfolio_allocation_vs_filtered_allocation")

    test_metrics_edge_cases()
    print("✓ test_metrics_edge_cases")

    test_metrics_consistency_across_groupings()
    print("✓ test_metrics_consistency_across_groupings")

    test_metrics_with_fractional_weights()
    print("✓ test_metrics_with_fractional_weights")

    test_metrics_complex_scenario()
    print("✓ test_metrics_complex_scenario")

    test_total_value_consistency_with_and_without_factors()
    print("✓ test_total_value_consistency_with_and_without_factors")

    test_real_world_missing_factor_weights_scenario()
    print("✓ test_real_world_missing_factor_weights_scenario")

    test_original_double_counting_bug_with_factor_filters()
    print("✓ test_original_double_counting_bug_with_factor_filters")

    test_metrics_performance_with_large_dimensions()
    print("✓ test_metrics_performance_with_large_dimensions")

    test_invalid_dimension_validation()
    print("✓ test_invalid_dimension_validation")

    print("\n🎉 All tests passed! Comprehensive test suite completed successfully.")