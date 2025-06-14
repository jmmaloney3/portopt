import pandas as pd
import numpy as np
from portopt.metrics import MetricsMixin
from portopt.utils import write_table

VERBOSE = True

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

def getMetricsMixinInstance(holdings_data: pd.DataFrame,
                            prices_data: pd.DataFrame,
                            factors_data: pd.DataFrame = None,
                            factor_weights_data: pd.DataFrame = None):
    """Create a MetricsMixin instance with mock methods."""
    metrics = MetricsMixin()
    metrics.getHoldings = lambda **kwargs: holdings_data
    metrics.getPrices = lambda **kwargs: prices_data
    if factors_data is not None:
        metrics.getFactors = lambda **kwargs: factors_data
    if factor_weights_data is not None:
        metrics.getFactorWeights = lambda **kwargs: factor_weights_data
    return metrics

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