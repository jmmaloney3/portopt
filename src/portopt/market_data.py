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

def is_security_ticker(ticker: str, verbose: bool = False) -> bool:
    """
    Check if the given ticker symbol is a valid security ticker.

    A valid security ticker is composed of 1 to 5 uppercase letters,
    optionally followed by additional alphanumeric characters, dots, or hyphens.

    Args:
        ticker: Ticker symbol as a string.
        verbose: If True, prints a diagnostic message when the ticker does not match.

    Returns:
        True if the ticker matches the security pattern, False otherwise.
    """
    ticker_str = str(ticker).upper()
    security_pattern = re.compile(r'^[A-Z]{1,5}([A-Z0-9.-]*)?$')
    result = bool(security_pattern.match(ticker_str))
    if verbose and not result:
        print(f"Ticker {ticker} does not match the security ticker pattern.")
    return result

def is_option_ticker(ticker: str, verbose: bool = False) -> bool:
    """
    Check if the given ticker symbol is a valid option ticker.

    A valid option ticker should match the OCC format:
    1 to 5 letters, 6 digits for the expiration date, a 'C' or 'P' for call/put,
    followed by one or more digits for the strike price.

    Args:
        ticker: Option ticker symbol as a string.
        verbose: If True, prints a diagnostic message when the ticker does not match.

    Returns:
        True if the ticker matches the option pattern, False otherwise.
    """
    ticker_str = str(ticker).upper()
    option_pattern = re.compile(r'^[A-Z]{1,5}\d{6}[CP]\d+$')
    result = bool(option_pattern.match(ticker_str))
    if verbose and not result:
        print(f"Ticker {ticker} does not match the option ticker pattern.")
    return result

def is_money_market_ticker(ticker: str, verbose: bool = False) -> bool:
    """
    Check if the given ticker corresponds to a known money market fund.

    Args:
        ticker: Security ticker symbol.
        verbose: If True, prints a diagnostic message when the ticker is recognized as a money market fund.

    Returns:
        True if the ticker is recognized as a money market fund, otherwise False.
    """
    money_market_funds = {
        'SPAXX',  # Fidelity Government Money Market Fund
        'FDRXX',  # Fidelity Government Cash Reserves
        'SPRXX',  # Fidelity Money Market Fund
        'FZFXX',  # Fidelity Treasury Money Market Fund
        'VMFXX',  # Vanguard Federal Money Market Fund
        'VMMXX',  # Vanguard Prime Money Market Fund
        'TIMXX',  # RBC BlueBay US Govt Mny Mkt Instl 2
        'DAGXX',  # Dreyfus Government Cash Management Fund
        'AMAXX',  # PIMCO Government Money Market Fund A
    }
    ticker_str = str(ticker).upper()
    if ticker_str in money_market_funds:
        if verbose:
            print(f"{ticker_str} identified as a money market fund.")
        return True
    return False

def parse_option_symbol(option_symbol: str) -> dict:
    """
    Parse an option symbol in OCC format into its components.

    Args:
        option_symbol: Option symbol in OCC format (e.g., 'SPY250321P580')
                      Format: {SYMBOL}{YY}{MM}{DD}{C/P}{STRIKE}

    Returns:
        Dictionary containing parsed components:
        - symbol: Underlying security symbol
        - expiry_date: Pandas Timestamp of expiration date
        - opt_type: 'P' for put or 'C' for call
        - opt_type_name: 'Put' or 'Call'
        - strike: Strike price as float
        - description: Human-readable description of the option

    Raises:
        ValueError: If the option symbol format is invalid
    """
    match = re.match(r'^([A-Z]{1,5})(\d{2})(\d{2})(\d{2})([CP])(\d+)$', str(option_symbol).upper())
    if not match:
        raise ValueError(f"Invalid option symbol format: {option_symbol}")

    symbol, yy, mm, dd, opt_type, strike = match.groups()
    expiry_date = pd.Timestamp(f"20{yy}-{mm}-{dd}")
    opt_type_name = 'Put' if opt_type == 'P' else 'Call'
    strike_price = float(strike)

    description = (f"{symbol} ${strike_price} {opt_type_name} "
                  f"expiring {expiry_date.strftime('%Y-%m-%d')}")

    return {
        'symbol': symbol,
        'expiry_date': expiry_date,
        'opt_type': opt_type,
        'opt_type_name': opt_type_name,
        'strike': strike_price,
        'description': description
    }

def get_tickers_date_ranges(tickers: set[str] | list[str],
                     price_type: str = "Adj Close",
                     verbose: bool = False) -> pd.DataFrame:
    """
    Retrieve the maximum available historical price data for each ticker and return
    a DataFrame with the following information for each ticker:
      - min date
      - max date
      - number of data points

    Args:
        tickers: Set or list of ticker symbols.
        price_type: Type of price to retrieve (default: "Adj Close").
        verbose: If True, prints diagnostic messages.

    Returns:
        DataFrame with ticker symbols as index and columns:
            - "min date"
            - "max date"
            - "# of data points"
    """
    # Ensure tickers is a set to eliminate duplicates.
    if not isinstance(tickers, set):
        tickers_set = set(tickers)
    else:
        tickers_set = tickers
    tickers_list = list(tickers_set)

    if verbose:
        print(f"Downloading maximum available historical price data for tickers: {', '.join(tickers_list)}")

    # Download the maximum available price data using yfinance.
    data = yf.download(tickers_list, period="max", auto_adjust=False)[price_type]

    # yf.download returns a Series if only one ticker is provided; convert to DataFrame.
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers_list[0])

    info = []
    # For each ticker, compute the desired statistics.
    for ticker in data.columns:
        series = data[ticker].dropna()
        if series.empty:
            min_date = pd.NaT
            max_date = pd.NaT
            count = 0
        else:
            min_date = series.index.min()
            max_date = series.index.max()
            count = series.shape[0]
        info.append({
            "Ticker": ticker,
            "min date": min_date,
            "max date": max_date,
            "# of data points": count
        })

    df_info = pd.DataFrame(info)
    df_info.set_index("Ticker", inplace=True)
    return df_info

def get_portfolio_tickers(portfolio: dict) -> list[str]:
    """
    Convert a portfolio dict or a dict of portfolio dicts into a sorted list of unique tickers.

    Args:
        portfolio: Either a single portfolio represented by a dict mapping ticker symbols to allocation weights,
                   or a dict mapping portfolio names to such dictionaries.

    Returns:
        Sorted list of unique ticker symbols present in the portfolio or portfolios.
    """
    if not portfolio:
        return []

    # Determine if we have a single portfolio or multiple portfolios
    if all(isinstance(v, (int, float)) for v in portfolio.values()):
        # Single portfolio case
        tickers = set(portfolio.keys())
    else:
        # Multiple portfolios case
        tickers = set()
        for p in portfolio.values():
            if not isinstance(p, dict):
                raise ValueError("Invalid portfolio format")
            tickers.update(p.keys())

    return sorted(tickers)

def get_portfolio_data(portfolio,
                      start_date: str = "1990-01-01",
                      end_date: str = None,
                      price_type: str = "Adj Close",
                      verbose: bool = False) -> pd.DataFrame:
    """
    Retrieve price data for one or more portfolios.

    Args:
        portfolio: Either:
                  - A dictionary mapping tickers to weights
                  - A dictionary of such dictionaries, with portfolio names as keys
        start_date: Start date for data retrieval (default: "1990-01-01")
        end_date: End date for data retrieval (default: None, means today)
        price_type: Type of price to retrieve (default: "Adj Close")
                   Options: "Open", "High", "Low", "Close", "Adj Close", "Volume"

    Returns:
        DataFrame indexed by date with tickers as columns containing price data

    Example:
        # Single portfolio
        portfolio = {'AAPL': 0.5, 'MSFT': 0.5}
        prices = get_portfolio_data(portfolio)

        # Multiple portfolios
        portfolios = {
            'Conservative': {'SPY': 0.6, 'BND': 0.4},
            'Aggressive': {'QQQ': 0.7, 'SPY': 0.3}
        }
        prices = get_portfolio_data(portfolios)
    """
    tickers = get_portfolio_tickers(portfolio)

    return get_tickers_data(tickers, start_date, end_date, price_type, verbose)

def get_tickers_data(tickers: set[str] | list[str],
                     start_date: str = "1990-01-01",
                     end_date: str | None = None,
                     price_type: str = "Adj Close",
                     verbose: bool = False) -> tuple[pd.DataFrame, dict]:
    """
    Retrieve price data for a set of tickers and return cleaned data along with
    cleaning statistics.

    Args:
        tickers: Set or list of ticker symbols
        start_date: Start date for data retrieval (default: "1990-01-01")
        end_date: End date for data retrieval (default: None, means today)
        price_type: Type of price to retrieve (default: "Adj Close")
                   Options: "Open", "High", "Low", "Close", "Adj Close", "Volume"

    Returns:
        A tuple containing:
          - A pandas DataFrame indexed by date with tickers as columns containing
            the price data after dropping any rows with N/A values.
          - A dictionary with cleaning statistics structured as follows:
            {
              "pre-clean stats": {
                     "row count": <number>,
                     "min date": <min date>,
                     "max date": <max date>
              },
              "post-clean stats": {
                     "row count": <number>,
                     "min date": <min date>,
                     "max date": <max date>
              },
              "data retention": <percentage of rows retained>
            }

    Raises:
        ValueError: If no tickers provided, an invalid price type is specified,
                    or data retrieval fails
    """
    # Convert tickers to set if it's a list - eliminates duplicates
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

        # Create the statistics dictionary
        stats = {
            "pre-clean stats": {
                "row count": df.shape[0],
                "min date": df.index.min(),
                "max date": df.index.max()
            },
            "post-clean stats": {
                "row count": df_clean.shape[0],
                "min date": df_clean.index.min() if not df_clean.empty else None,
                "max date": df_clean.index.max() if not df_clean.empty else None
            },
            "data retention": (df_clean.shape[0] / df.shape[0]) if df.shape[0] > 0 else 0
        }

        if verbose:
            print("Data retrieval statistics:")
            print("pre-clean stats:")
            print(f"  row count: {stats['pre-clean stats']['row count']}")
            print(f"  min date: {stats['pre-clean stats']['min date']}")
            print(f"  max date: {stats['pre-clean stats']['max date']}")
            print("post-clean stats:")
            print(f"  row count: {stats['post-clean stats']['row count']}")
            print(f"  min date: {stats['post-clean stats']['min date']}")
            print(f"  max date: {stats['post-clean stats']['max date']}")
            print(f"data retention: {stats['data retention'] * 100:.2f}%")

        # Warn the user if rows were dropped during cleaning
        if df_clean.shape[0] < df.shape[0]:
            warnings.warn(f"Dropped {df.shape[0] - df_clean.shape[0]} rows containing N/A values")

        return df_clean, stats

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

    This function determines whether the ticker corresponds to an option contract or
    a security (stock, bond, ETF, mutual fund) and calls the appropriate function
    to retrieve the latest price.

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
        ticker_str = str(ticker).upper()
        if is_option_ticker(ticker_str, verbose=verbose):
            return get_latest_option_price(ticker, verbose=verbose)
        elif is_security_ticker(ticker_str, verbose=verbose):
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
        # Check if this ticker is a money market fund
        if is_money_market_ticker(ticker, verbose=verbose):
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
                # Fallback: Retrieve historical data and use the last available close price
                hist = fund.history(period="1d")
                if not hist.empty and "Close" in hist.columns:
                    price = hist["Close"].iloc[-1]
                    if verbose:
                        print(f"Using historical data for {ticker}: Close price = ${price:.2f}")
                else:
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
        # Parse the option symbol
        try:
            option_info = parse_option_symbol(option_symbol)
        except ValueError as e:
            if verbose:
                print(str(e))
            return np.nan

        # Get option chain for the underlying stock
        ticker = yf.Ticker(option_info['symbol'])

        # Get all options for the expiration date
        try:
            options = ticker.option_chain(option_info['expiry_date'].strftime('%Y-%m-%d'))
        except ValueError as e:
            if verbose:
                print(f"No options chain found for {option_info['symbol']} on {option_info['expiry_date'].date()}")
            return np.nan

        # Select puts or calls based on option type
        chain = options.puts if option_info['opt_type'] == 'P' else options.calls

        # Find the specific contract
        contract = chain[chain['strike'] == option_info['strike']]

        if len(contract) == 0:
            if verbose:
                print(f"No contract found for strike ${option_info['strike']} in {option_info['symbol']} {option_info['opt_type_name']} options")
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

def get_tickers_info(tickers: pd.Index | set[str] | list[str], verbose: bool = False) -> pd.DataFrame:
    """
    Retrieve basic information for multiple tickers from Yahoo Finance.
    Handles both securities (stocks, ETFs, mutual funds) and options.

    Args:
        tickers: Index, set, or list of ticker symbols
        verbose: If True, print status messages for each ticker (default: False)

    Returns:
        DataFrame indexed by ticker symbols containing:
        - Name: Short name of the security or option description
        - Short Name: Short name or option symbol
        - Type: Security type (ETF, MUTUALFUND, EQUITY, OPTION)
        - Category: Fund category/investment strategy (securities only)
        - Family: Fund family/provider name (securities only)
        Note: Some fields may be NaN if not available for a particular security

    Example:
        # Get info for a mix of securities and options
        info = get_tickers_info(['VTSAX', 'SPY', 'SPY250321P580'])
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

    # Define the fields we want to retrieve for securities
    fields = {
        'Name': 'longName',
        'Short Name': 'shortName',
        'Type': 'quoteType',
        'Category': 'category',
        'Family': 'fundFamily'
    }

    # Initialize result DataFrame with proper dtypes
    result = pd.DataFrame(
        index=sorted(tickers_set),
        columns=fields.keys(),
        dtype='object'  # Use object dtype for string data
    )
    result.index.name = 'Ticker'

    # Process each ticker
    for ticker in tickers_set:
        try:
            ticker_str = str(ticker).upper()

            if is_option_ticker(ticker_str, verbose=verbose):
                # Handle option ticker
                try:
                    option_info = parse_option_symbol(ticker_str)

                    # Set option information using parsed data
                    result.at[ticker, 'Name'] = option_info['description']
                    result.at[ticker, 'Short Name'] = ticker_str
                    result.at[ticker, 'Type'] = 'OPTION'
                    result.at[ticker, 'Category'] = pd.NA
                    result.at[ticker, 'Family'] = pd.NA

                    if verbose:
                        print(f"Processed option ticker: {ticker}")
                except ValueError as e:
                    if verbose:
                        print(str(e))
                    # Set all fields to NA for invalid option ticker
                    for col in fields.keys():
                        result.at[ticker, col] = pd.NA

            elif is_security_ticker(ticker_str, verbose=verbose):
                # Handle security ticker
                if verbose:
                    print(f"Retrieving info for security: {ticker}")

                # Get ticker info from Yahoo Finance
                yf_ticker = yf.Ticker(ticker)
                info = yf_ticker.info

                # Extract desired fields
                for col, field in fields.items():
                    result.at[ticker, col] = info.get(field, pd.NA)
            else:
                if verbose:
                    print(f"Invalid ticker format: {ticker}")
                # Set all fields to NA for invalid ticker
                for col in fields.keys():
                    result.at[ticker, col] = pd.NA

        except Exception as e:
            if verbose:
                print(f"Error retrieving info for {ticker}: {str(e)}")
            # Set all fields to NA for this ticker
            for col in fields.keys():
                result.at[ticker, col] = pd.NA

    return result