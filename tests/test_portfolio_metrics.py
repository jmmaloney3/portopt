import pandas as pd
import numpy as np
from portopt.portfolio import Portfolio

def test_get_metrics_total_portfolio():
    """Test that getMetrics() without arguments returns correct total portfolio value and allocation."""
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
    
    # Create a mock Portfolio instance
    portfolio = Portfolio(None, None, None)
    
    # Mock the required methods to return our test data
    portfolio.getHoldings = lambda **kwargs: holdings_data
    portfolio.getPrices = lambda **kwargs: prices_data
    
    # Call getMetrics without arguments
    metrics = portfolio.getMetrics()
    
    # Calculate expected values
    expected_total_value = (
        10 * 150.0 +  # AAPL
        20 * 300.0 +  # MSFT
        5 * 200.0     # GOOGL
    )
    
    # Verify results
    assert metrics['Total Value'].sum() == expected_total_value
    assert np.isclose(metrics['Allocation'].sum(), 1.0)  # Allocations should sum to 100%
