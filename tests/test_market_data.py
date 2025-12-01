"""
Tests for market_data module functions.
"""
import pytest
import pandas as pd
from portopt.market_data import (
    is_option_ticker,
    is_security_ticker,
    parse_option_symbol,
    is_underlying_ticker
)


class TestIsOptionTicker:
    """Test cases for is_option_ticker function."""
    
    def test_valid_option_tickers_whole_strike(self):
        """Test valid option tickers with whole number strike prices."""
        valid_tickers = [
            'SPY250321P580',  # SPY put, strike 580
            'AAPL250321C150', # AAPL call, strike 150
            'QQQ250321P400',  # QQQ put, strike 400
            'TSLA250321C200', # TSLA call, strike 200
        ]
        
        for ticker in valid_tickers:
            assert is_option_ticker(ticker), f"Should recognize {ticker} as valid option"
    
    def test_valid_option_tickers_decimal_strike(self):
        """Test valid option tickers with decimal strike prices."""
        valid_tickers = [
            'SVIX251017C18.5',  # SVIX call, strike 18.5
            'SPY250321P580.5',  # SPY put, strike 580.5
            'AAPL250321C150.25', # AAPL call, strike 150.25
            'QQQ250321P400.75',  # QQQ put, strike 400.75
        ]
        
        for ticker in valid_tickers:
            assert is_option_ticker(ticker), f"Should recognize {ticker} as valid option"
    
    def test_invalid_option_tickers(self):
        """Test invalid option ticker formats."""
        invalid_tickers = [
            'SPY',           # Regular security
            'SPY250321',     # Missing C/P and strike
            'SPY250321P',    # Missing strike
            'SPY250321X580', # Invalid option type (X instead of C/P)
            'SPY250321P',    # Missing strike
            'SPY250321P58.5.5', # Multiple decimal points
            'SPY250321P.5',  # Decimal without leading digit
        ]
        
        for ticker in invalid_tickers:
            assert not is_option_ticker(ticker), f"Should not recognize {ticker} as valid option"


class TestParseOptionSymbol:
    """Test cases for parse_option_symbol function."""
    
    def test_parse_whole_strike_options(self):
        """Test parsing option symbols with whole number strikes."""
        test_cases = [
            {
                'symbol': 'SPY250321P580',
                'expected': {
                    'symbol': 'SPY',
                    'expiry_date': pd.Timestamp('2025-03-21'),
                    'opt_type': 'P',
                    'opt_type_name': 'Put',
                    'strike': 580.0,
                    'description': 'SPY $580.0 Put expiring 2025-03-21'
                }
            },
            {
                'symbol': 'AAPL250321C150',
                'expected': {
                    'symbol': 'AAPL',
                    'expiry_date': pd.Timestamp('2025-03-21'),
                    'opt_type': 'C',
                    'opt_type_name': 'Call',
                    'strike': 150.0,
                    'description': 'AAPL $150.0 Call expiring 2025-03-21'
                }
            }
        ]
        
        for case in test_cases:
            result = parse_option_symbol(case['symbol'])
            assert result == case['expected'], f"Failed to parse {case['symbol']}"
    
    def test_parse_decimal_strike_options(self):
        """Test parsing option symbols with decimal strike prices."""
        test_cases = [
            {
                'symbol': 'SVIX251017C18.5',
                'expected': {
                    'symbol': 'SVIX',
                    'expiry_date': pd.Timestamp('2025-10-17'),
                    'opt_type': 'C',
                    'opt_type_name': 'Call',
                    'strike': 18.5,
                    'description': 'SVIX $18.5 Call expiring 2025-10-17'
                }
            },
            {
                'symbol': 'SPY250321P580.5',
                'expected': {
                    'symbol': 'SPY',
                    'expiry_date': pd.Timestamp('2025-03-21'),
                    'opt_type': 'P',
                    'opt_type_name': 'Put',
                    'strike': 580.5,
                    'description': 'SPY $580.5 Put expiring 2025-03-21'
                }
            },
            {
                'symbol': 'AAPL250321C150.25',
                'expected': {
                    'symbol': 'AAPL',
                    'expiry_date': pd.Timestamp('2025-03-21'),
                    'opt_type': 'C',
                    'opt_type_name': 'Call',
                    'strike': 150.25,
                    'description': 'AAPL $150.25 Call expiring 2025-03-21'
                }
            }
        ]
        
        for case in test_cases:
            result = parse_option_symbol(case['symbol'])
            assert result == case['expected'], f"Failed to parse {case['symbol']}"
    
    def test_parse_invalid_option_symbols(self):
        """Test parsing invalid option symbol formats."""
        invalid_symbols = [
            'SPY',           # Regular security
            'SPY250321',     # Missing C/P and strike
            'SPY250321P',    # Missing strike
            'SPY250321X580', # Invalid option type
            'SPY250321P58.5.5', # Multiple decimal points
            'SPY250321P.5',  # Decimal without leading digit
        ]
        
        for symbol in invalid_symbols:
            with pytest.raises(ValueError, match="Invalid option symbol format"):
                parse_option_symbol(symbol)


class TestIsSecurityTicker:
    """Test cases for is_security_ticker and is_underlying_ticker functions."""
    
    def test_security_tickers_include_options(self):
        """is_security_ticker should return True for both underlying and options."""
        security_like = [
            'AAPL', 'SPY', 'VTSAX', 'BRK.A', 'BRK-B', 'SPY.UN',
            'SPY250321P580', 'SVIX251017C18.5'
        ]
        for ticker in security_like:
            assert is_security_ticker(ticker), f"{ticker} should be considered a security"
    
    def test_underlying_tickers_exclude_options(self):
        """is_underlying_ticker should return True only for non-option securities."""
        underlying = ['AAPL', 'SPY', 'VTSAX', 'BRK.A', 'BRK-B']
        options = ['SPY250321P580', 'SVIX251017C18.5']
        for ticker in underlying:
            assert is_underlying_ticker(ticker), f"{ticker} should be underlying"
        for ticker in options:
            assert not is_underlying_ticker(ticker), f"{ticker} should not be underlying"


class TestTickerTypeDetection:
    """Test cases for ticker type detection logic."""
    
    def test_option_vs_security_detection(self):
        """Test that tickers are correctly classified as options vs securities."""
        # These should be detected as options
        option_tickers = [
            'SPY250321P580',      # Whole strike
            'SVIX251017C18.5',    # Decimal strike
            'AAPL250321C150.25',  # Decimal strike
        ]
        
        # These should be detected as securities
        security_tickers = [
            'AAPL',      # Stock
            'SPY',       # ETF
            'VTSAX',     # Mutual fund
            'BRK.A',     # Class A stock
        ]
        
        for ticker in option_tickers:
            assert is_option_ticker(ticker), f"{ticker} should be detected as option"
            assert is_security_ticker(ticker), f"{ticker} should also be a security"
            assert not is_underlying_ticker(ticker), f"{ticker} should not be an underlying"
        
        for ticker in security_tickers:
            assert is_security_ticker(ticker), f"{ticker} should be detected as security"
            assert not is_option_ticker(ticker), f"{ticker} should not be detected as option"
            assert is_underlying_ticker(ticker), f"{ticker} should be an underlying"