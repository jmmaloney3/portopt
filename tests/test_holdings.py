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
