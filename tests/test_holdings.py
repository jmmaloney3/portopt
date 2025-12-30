"""
Tests for holdings module functions.
"""
import pytest
import pandas as pd
from portopt.holdings import get_converters
from portopt.config import default_config


class TestCleanTicker:
    """Test cases for clean_ticker function within get_converters."""
    
    def test_clean_option_tickers_whole_strike(self):
        """Test cleaning option tickers with whole number strikes."""
        converters = get_converters(default_config())
        clean_ticker = converters['ticker']
        
        test_cases = [
            ('-SPY250321P580', 'SPY250321P580'),  # Remove leading hyphen
            ('SPY250321P580', 'SPY250321P580'),   # No change needed
            ('-AAPL250321C150', 'AAPL250321C150'), # Remove leading hyphen
        ]
        
        for input_ticker, expected in test_cases:
            result = clean_ticker(input_ticker)
            assert result == expected, f"Failed to clean {input_ticker}"
    
    def test_clean_option_tickers_decimal_strike(self):
        """Test cleaning option tickers with decimal strike prices."""
        converters = get_converters(default_config())
        clean_ticker = converters['ticker']
        
        test_cases = [
            ('-SVIX251017C18.5', 'SVIX251017C18.5'),  # Remove leading hyphen, preserve decimal
            ('SVIX251017C18.5', 'SVIX251017C18.5'),   # No change needed
            ('-SPY250321P580.5', 'SPY250321P580.5'),  # Remove leading hyphen, preserve decimal
            ('-AAPL250321C150.25', 'AAPL250321C150.25'), # Remove leading hyphen, preserve decimal
        ]
        
        for input_ticker, expected in test_cases:
            result = clean_ticker(input_ticker)
            assert result == expected, f"Failed to clean {input_ticker}"
    
    def test_clean_regular_tickers(self):
        """Test cleaning regular security tickers."""
        converters = get_converters(default_config())
        clean_ticker = converters['ticker']
        
        test_cases = [
            ('AAPL', 'AAPL'),           # No change
            ('SPY**', 'SPY'),           # Remove asterisks
            ('VTSAX Some Fund', 'VTSAX'), # Take first word only
            ('BRK.A', 'BRK.A'),         # Preserve dots
            ('BRK-B', 'BRK-B'),         # Preserve hyphens
            ('', 'N/A'),                # Empty string
            ('   ', 'N/A'),             # Whitespace only
        ]
        
        for input_ticker, expected in test_cases:
            result = clean_ticker(input_ticker)
            assert result == expected, f"Failed to clean {input_ticker}"
    
    def test_clean_invalid_option_tickers(self):
        """Test cleaning invalid option ticker formats."""
        converters = get_converters(default_config())
        clean_ticker = converters['ticker']
        
        # These should be treated as regular tickers and cleaned accordingly
        test_cases = [
            ('SPY250321', 'SPY250321'),     # Missing C/P and strike
            ('SPY250321P', 'SPY250321P'),   # Missing strike
            ('SPY250321X580', 'SPY250321X580'), # Invalid option type
        ]
        
        for input_ticker, expected in test_cases:
            result = clean_ticker(input_ticker)
            assert result == expected, f"Failed to clean {input_ticker}"


class TestCleanNumeric:
    """Test cases for clean_numeric function within get_converters."""

    def test_clean_numeric_with_percentage(self):
        """Test cleaning numeric values with percentage in parentheses."""
        converters = get_converters(default_config())
        clean_numeric = converters['Balance']

        test_cases = [
            ('$12,545.48 (6.83%)', 12545.48),
            ('"$12,545.48 (6.83%)"', 12545.48),  # With quotes
            ('$0.08 (0.0%)', 0.08),
            ('$84,681.63 (46.19%)', 84681.63),
            ('$20,582.69 (11.23%)', 20582.69),
            ('$1,880.42 (1.03%)', 1880.42),
            ('$3,809.67 (2.08%)', 3809.67),
            ('$57,960.08 (31.62%)', 57960.08),
            ('12545.48 (6.83%)', 12545.48),  # Without dollar sign
            ('12,545.48 (6.83%)', 12545.48),  # Without dollar sign, with comma
        ]

        for input_value, expected in test_cases:
            result = clean_numeric(input_value)
            assert result == expected, f"Failed to clean {input_value}: got {result}, expected {expected}"

    def test_clean_numeric_without_percentage(self):
        """Test cleaning numeric values without percentage (regression tests)."""
        converters = get_converters(default_config())
        clean_numeric = converters['Balance']

        test_cases = [
            ('$12,545.48', 12545.48),
            ('"$12,545.48"', 12545.48),  # With quotes
            ('$0.08', 0.08),
            ('12545.48', 12545.48),  # Without dollar sign
            ('12,545.48', 12545.48),  # Without dollar sign, with comma
            ('1000', 1000.0),
            ('1,000.50', 1000.50),
        ]

        for input_value, expected in test_cases:
            result = clean_numeric(input_value)
            assert result == expected, f"Failed to clean {input_value}: got {result}, expected {expected}"

    def test_clean_numeric_edge_cases(self):
        """Test cleaning numeric values with edge cases."""
        converters = get_converters(default_config())
        clean_numeric = converters['Balance']

        test_cases = [
            ('--', None),  # Invalid marker
            ('', None),  # Empty string
            (None, None),  # None value
            ('$0.00 (0.0%)', 0.0),  # Zero with percentage
            ('$0.00', 0.0),  # Zero without percentage
            ('$1,234.56 (100.0%)', 1234.56),  # 100% percentage
            ('$999,999.99 (99.99%)', 999999.99),  # Large number with percentage
        ]

        for input_value, expected in test_cases:
            result = clean_numeric(input_value)
            assert result == expected, f"Failed to clean {input_value}: got {result}, expected {expected}"
