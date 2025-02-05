"""
Market data retrieval functions for financial securities.

This module provides functions for retrieving price data and other market information
for various types of financial instruments including stocks, ETFs, mutual funds, and
options.

Functions:
    get_tickers_data: Retrieve historical price data for multiple securities
    get_latest_ticker_prices: Get current prices for multiple securities
    get_latest_ticker_price: Get current price for a single security or option
    get_latest_security_price: Get current price for a stock/ETF/mutual fund
    get_latest_option_price: Get current price for an options contract

Dependencies:
    - yfinance: Yahoo Finance API wrapper for market data
    - pandas: Data manipulation and analysis
    - numpy: Numerical computing
    - re: Regular expressions for parsing symbols
"""

import re
import warnings
import numpy as np
import pandas as pd
import yfinance as yf

def get_tickers_data(tickers: set[str] | list[str],
                     start_date: str = "1990-01-01",
                     end_date: str = None,
                     price_type: str = "Adj Close") -> pd.DataFrame:
    """
    Retrieve price data for a set of tickers.

    Args:
        tickers: Set or list of ticker symbols
        start_date: Start date for data retrieval (default: "1990-01-01")
        end_date: End date for data retrieval (default: None, means today)
        price_type: Type of price to retrieve (default: "Adj Close")
                   Options: "Open", "High", "Low", "Close", "Adj Close", "Volume"

    Returns:
        DataFrame indexed by date with tickers as columns containing price data

    Raises:
        ValueError: If no tickers provided or if invalid price_type
        ValueError: If data retrieval fails for any ticker
    """
    # Convert tickers to set if it's a list
    tickers_set = set(tickers)

    if not tickers_set:
        raise ValueError("No tickers provided")

    # Validate price type
    valid_price_types = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    if price_type not in valid_price_types:
        raise ValueError(f"Invalid price_type. Must be one of {valid_price_types}")

    try:
        # Download data for all tickers
        df = yf.download(
            list(tickers_set),  # Convert back to list for yfinance
            start=start_date,
            end=end_date,
            auto_adjust=False
        )[price_type]

        # Check if any tickers are missing
        missing_tickers = tickers_set - set(df.columns)
        if missing_tickers:
            raise ValueError(f"Failed to retrieve data for tickers: {missing_tickers}")

        # Drop any rows with NaN values
        df_clean = df.dropna(axis=0, how='any')

        # Warn if we dropped any dates
        if len(df_clean) < len(df):
            import warnings
            warnings.warn(f"Dropped {len(df) - len(df_clean)} rows containing NaN values")

        return df_clean

    except Exception as e:
        raise ValueError(f"Error retrieving data: {str(e)}")

def get_latest_ticker_prices(tickers: pd.Index | set[str] | list[str], verbose: bool = False) -> pd.DataFrame:
    """
    Retrieve the most recent prices for multiple tickers.

    Args:
        tickers: Index, set, or list of ticker symbols (securities and/or options)
        verbose: If True, print status messages for each ticker (default: False)

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Price (most recent price available)
        Note: Money market funds are assumed to have a stable $1.00 NAV
              Invalid tickers will have NaN prices

    Example:
        # Get prices for a mix of securities and options
        prices = get_latest_ticker_prices(['VTSAX', 'SPY', 'SPY250321P580'])
    """
    # Convert input to set of tickers if it isn't already
    if isinstance(tickers, set):
        tickers_set = tickers
    elif isinstance(tickers, (pd.Index, list)):
        tickers_set = set(tickers)
    else:
        raise TypeError("tickers must be a set, list, or pandas Index")

    if not tickers_set:
        raise ValueError("No tickers provided")

    # Initialize result DataFrame
    result = pd.DataFrame(index=sorted(tickers_set))
    result.index.name = 'Ticker'

    # Process each ticker
    for ticker in tickers_set:
        result.loc[ticker, 'Price'] = get_latest_ticker_price(ticker, verbose=verbose)

    return result

def get_latest_ticker_price(ticker: str, verbose: bool = False) -> float:
    """
    Retrieve the latest price for a single ticker (security or option).

    Args:
        ticker: Ticker symbol (e.g., 'VTSAX', 'SPY250321P580')
        verbose: If True, print status messages (default: False)

    Returns:
        Latest price for the ticker, or NaN if retrieval fails

    Example:
        # Get price for a security
        price = get_latest_ticker_price('VTSAX')

        # Get price for an option
        price = get_latest_ticker_price('SPY250321P580')
    """
    try:
        # Check if it's an option contract
        option_pattern = re.compile(r'^[A-Z]{1,5}\d{6}[CP]\d+$')
        security_pattern = re.compile(r'^[A-Z]{1,5}([A-Z0-9.-]*)?$')

        ticker_str = str(ticker).upper()
        if option_pattern.match(ticker_str):
            return get_latest_option_price(ticker, verbose=verbose)
        elif security_pattern.match(ticker_str):
            return get_latest_security_price(ticker, verbose=verbose)
        else:
            if verbose:
                print(f"Invalid ticker format: {ticker}")
            return np.nan

    except Exception as e:
        if verbose:
            print(f"Error retrieving price for {ticker}: {str(e)}")
        return np.nan

def get_latest_security_price(ticker: str, verbose: bool = False) -> float:
    """
    Retrieve the latest price for a security (stock, bond, ETF, mutual fund).

    Args:
        ticker: Security symbol (e.g., 'VTSAX', 'SPY', 'AAPL')
        verbose: If True, print status messages (default: False)

    Returns:
        Latest price of the security, or NaN if retrieval fails
        Note: Money market funds return $1.00 NAV

    Example:
        # Get price for a mutual fund
        price = get_latest_security_price('VTSAX')
    """
    try:
        # Known money market funds
        money_market_funds = {
            'SPAXX',  # Fidelity Government Money Market Fund
            'FDRXX',  # Fidelity Government Cash Reserves
            'SPRXX',  # Fidelity Money Market Fund
            'FZFXX',  # Fidelity Treasury Money Market Fund
            'VMFXX',  # Vanguard Federal Money Market Fund
            'VMMXX',  # Vanguard Prime Money Market Fund
            'TIMXX',  # RBC BlueBay US Govt Mny Mkt Instl 2
        }

        if ticker in money_market_funds:
            price = 1.0  # Money market funds maintain $1.00 NAV
        else:
            # Get basic info (doesn't download historical data)
            fund = yf.Ticker(ticker)
            info = fund.info

            # Try to get price in order of preference
            price = info.get('regularMarketPrice')  # Current price if market open
            if price is None:
                price = info.get('previousClose')   # Previous close if market closed
            if price is None:
                if verbose:
                    print(f"No price data available for {ticker}")
                return np.nan

        if verbose:
            print(f"Successfully retrieved price for {ticker}: ${price:.2f}")
        return price

    except Exception as e:
        if verbose:
            print(f"Error retrieving price for {ticker}: {str(e)}")
        return np.nan

def get_latest_option_price(option_symbol: str, verbose: bool = False) -> float:
    """
    Retrieve the latest price for an option contract.

    Args:
        option_symbol: Option symbol in OCC format (e.g., 'SPY250321P580')
                      Format: {SYMBOL}{YY}{MM}{DD}{C/P}{STRIKE}
        verbose: If True, print status messages (default: False)

    Returns:
        Latest price of the option contract, or NaN if retrieval fails

    Example:
        # Get price for SPY put option (strike: $580, expiry: March 21, 2025)
        price = get_latest_option_price('SPY250321P580')
    """
    try:
        # Parse OCC symbol components
        match = re.match(r'^([A-Z]{1,5})(\d{2})(\d{2})(\d{2})([CP])(\d+)$', option_symbol)
        if not match:
            raise ValueError(f"Invalid option symbol format: {option_symbol}")

        symbol, yy, mm, dd, opt_type, strike = match.groups()

        # Convert to full year (assuming 20xx)
        year = f"20{yy}"

        # Create date object to format properly for Yahoo
        expiry_date = pd.Timestamp(f"20{yy}-{mm}-{dd}")

        # Convert strike price to proper format (multiply by 1000 for Yahoo's format)
        yahoo_strike = float(strike) * 1000

        # Get option chain for the underlying stock
        ticker = yf.Ticker(symbol)

        # Get all options for the expiration date
        try:
            options = ticker.option_chain(expiry_date.strftime('%Y-%m-%d'))
        except ValueError as e:
            if verbose:
                print(f"No options chain found for {symbol} on {expiry_date.date()}")
            return np.nan

        # Select puts or calls based on option type
        chain = options.puts if opt_type == 'P' else options.calls

        # Find the specific contract
        contract = chain[chain['strike'] == float(strike)]

        if len(contract) == 0:
            if verbose:
                print(f"No contract found for strike ${strike} in {symbol} {opt_type} options")
            return np.nan

        # Get the last price & multiply by 100 since contracts are for 100 shares
        price = contract.iloc[0]['lastPrice'] * 100

        if verbose:
            print(f"Successfully retrieved price for {option_symbol}: ${price:.2f}")

        return price

    except Exception as e:
        if verbose:
            print(f"Error retrieving price for {option_symbol}: {str(e)}")
        return np.nan