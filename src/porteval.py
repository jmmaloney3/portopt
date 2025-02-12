# this module contains utility functions that can be used to evaluate
# and compare portfolios.

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import pandas as pd
import bt
from market_data import get_tickers_data
from utils import test_stationarity

@dataclass
class PortfolioStats:
    """Class for holding portfolio evaluation statistics"""
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    avg_correlation: float
    portfolio_size: int
    max_weight: float
    min_weight: float
    
    def to_dict(self):
        """Convert statistics to dictionary"""
        return {
            'Annual Return': f"{self.annual_return:.2%}",
            'Annual Volatility': f"{self.annual_volatility:.2%}",
            'Sharpe Ratio': f"{self.sharpe_ratio:.2f}",
            'Maximum Drawdown': f"{self.max_drawdown:.2%}",
            'Average Correlation': f"{self.avg_correlation:.2f}",
            'Portfolio Size': f"{self.portfolio_size}",
            'Maximum Weight': f"{self.max_weight:.2%}",
            'Minimum Weight': f"{self.min_weight:.2%}"
        }

    
    def __str__(self):
        """Format statistics for display with aligned decimal points"""
        stats = self.to_dict()
        
        # Find the longest label and value
        max_label_length = max(len(label) for label in stats.keys())
        max_value_length = max(len(str(value)) for value in stats.values())
        
        # Calculate total line length (label + colon + space + value)
        line_length = max_label_length + 1 + 1 + max_value_length
        
        # Create the header with matching line length
        result = ["Portfolio Statistics:", "-" * line_length]
        
        # Format each line with proper alignment
        for label, value in stats.items():
            result.append(f"{label + ':':<{max_label_length + 1}} {value:>{max_value_length}}")
            
        return "\n".join(result)
    
    def __repr__(self):
        """Same as __str__ for consistent notebook display"""
        return self.__str__()

def evaluate_portfolio(
    portfolio: Dict[str, float],
    original_returns: pd.DataFrame,
    standardized_returns: pd.DataFrame,
    risk_free_rate: float = 0.02,
    risk_model: str = 'sample_cov'
) -> PortfolioStats:
    """
    Evaluate a portfolio using both standardized and original returns.
    
    Args:
        portfolio: Dict mapping tickers to weights (must sum to 1)
        standardized_returns: DataFrame of standardized returns for risk calculations
        original_returns: DataFrame of original returns for return calculations
        risk_free_rate: Annual risk-free rate (default: 0.02)
        risk_model: Type of risk model to use (default: 'sample_cov')
        
    Returns:
        PortfolioStats object containing evaluation metrics
    """
    # Verify portfolio tickers exist in both datasets
    tickers = list(portfolio.keys())
    weights = np.array(list(portfolio.values()))
    
    # Check standardized returns
    missing_standardized = [t for t in tickers if t not in standardized_returns.columns]
    if missing_standardized:
        raise ValueError(f"Missing tickers in standardized returns: {missing_standardized}")
        
    # Check original returns
    missing_original = [t for t in tickers if t not in original_returns.columns]
    if missing_original:
        raise ValueError(f"Missing tickers in original returns: {missing_original}")
    
    # Verify weights sum to 1
    if not np.isclose(sum(weights), 1.0, rtol=1e-05):
        raise ValueError("Portfolio weights must sum to 1")
    
    # Check that both datasets have the same index
    if not standardized_returns.index.equals(original_returns.index):
        raise ValueError("Standardized and original returns have different time indices")
    
    # Check for NaN values
    if standardized_returns[tickers].isna().any().any():
        raise ValueError("Standardized returns contain NaN values")
    if original_returns[tickers].isna().any().any():
        raise ValueError("Original returns contain NaN values")
    
    # Verify standardization properties (mean ≈ 0, std ≈ 1)
    std_means = standardized_returns[tickers].mean()
    std_stds = standardized_returns[tickers].std()
    if not (np.abs(std_means) < 0.01).all():
        raise ValueError("Standardized returns do not have mean close to 0")
    if not ((std_stds - 1).abs() < 0.01).all():
        raise ValueError("Standardized returns do not have standard deviation close to 1")
    
    # Check stationarity of standardized returns
    stationarity_results = test_stationarity(standardized_returns[tickers])
    non_stationary = stationarity_results[~stationarity_results['Is Stationary']]
    if not non_stationary.empty:
        non_stationary_tickers = non_stationary.index.tolist()
        raise ValueError(f"Non-stationary standardized returns detected for: {non_stationary_tickers}")
    
    # Calculate returns using original data
    port_returns = original_returns[tickers].dot(weights)
    annual_return = port_returns.mean() * 252
    
    # Calculate risk metrics using standardized data
    if risk_model == 'sample_cov':
        cov_matrix = standardized_returns[tickers].cov()
    elif risk_model == 'exp_weighted':
        decay = 0.94
        cov_matrix = standardized_returns[tickers].ewm(alpha=1-decay).cov()
    else:
        raise ValueError(f"Unsupported risk model: {risk_model}")
    
    # Calculate correlation matrix using standardized data
    corr_matrix = standardized_returns[tickers].corr()
    avg_corr = (corr_matrix.sum().sum() - len(tickers)) / (len(tickers) * (len(tickers) - 1))
    
    # Calculate volatility using standardized data
    annual_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    
    # Calculate Sharpe ratio
    sharpe = (annual_return - risk_free_rate) / annual_vol
    
    # Calculate maximum drawdown using original returns
    cum_returns = (1 + port_returns).cumprod()
    rolling_max = cum_returns.expanding().max()
    drawdowns = cum_returns / rolling_max - 1
    max_drawdown = drawdowns.min()
    
    # Create and return stats object
    stats = PortfolioStats(
        annual_return=annual_return,
        annual_volatility=annual_vol,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        avg_correlation=avg_corr,
        portfolio_size=len(tickers),
        max_weight=max(weights),
        min_weight=min(weights)
    )
    
    return stats

def evaluate_portfolios(
    portfolios: Dict[str, Dict[str, float]],
    standardized_returns: pd.DataFrame,
    original_returns: pd.DataFrame,
    risk_free_rate: float = 0.02,
    risk_model: str = 'sample_cov'
) -> pd.DataFrame:
    """
    Evaluate multiple portfolios using both standardized and original returns.

    Args:
        portfolios: Dict mapping portfolio names to portfolio weights.
                   Example: {
                       'Conservative': {'SPY': 0.6, 'BND': 0.4},
                       'Aggressive': {'QQQ': 0.7, 'SPY': 0.3}
                   }
        standardized_returns: DataFrame of standardized returns for risk calculations
        original_returns: DataFrame of original returns for return calculations
        risk_free_rate: Annual risk-free rate (default: 0.02)
        risk_model: Type of risk model to use (default: 'sample_cov')

    Returns:
        DataFrame with portfolio statistics as index and portfolio names as columns
    """
    # Initialize results dictionary
    results = {}

    # Evaluate each portfolio
    for name, portfolio in portfolios.items():
        try:
            stats = evaluate_portfolio(
                portfolio,
                standardized_returns,
                original_returns,
                risk_free_rate,
                risk_model
            )
            # Convert stats to dictionary and store
            results[name] = stats.to_dict()

        except Exception as e:
            print(f"Warning: Failed to evaluate portfolio '{name}': {str(e)}")
            continue

    if not results:
        raise ValueError("No portfolios were successfully evaluated")

    # Return results as a DataFrame with portfolio names as columns and
    # statistics as index
    df_results = pd.DataFrame(results)

    return df_results

def backtest_model_portfolio(model_portfolio: dict[str, float],
                             start_date: str,
                             end_date: str | None = None,
                             rebalance_freq: str = "quarterly",
                             price_data: pd.DataFrame | None = None,
                             verbose: bool = False) -> dict:
    """
    Perform a backtest on a model portfolio defined by a dictionary mapping
    ticker symbols to allocation percentages with a specified rebalancing
    frequency.

    Historical adjusted close prices for these tickers are retrieved using the
    get_tickers_data function (unless price_data is provided), and those
    prices are used to compute daily returns. The portfolio is rebalanced
    according to the specified frequency (supported: "daily", "weekly",
    "monthly", "quarterly", "annually") to match the target allocations. This
    function then calculates:
      - Daily sample variance and daily average return.
      - Annualized variance and annualized return (assuming 252 trading days per year).
      - Sharpe ratio computed as: sharpe_ratio = annualized_return / sqrt(annualized_variance)
                                  (Assuming a risk-free rate of 0)
      - Minimum and maximum dates for the data used.
      - Number of data points used.
      - Percentage of the original dataset retained after dropping NA rows.
      - Maximum drawdown based on the cumulative portfolio returns.
      - Average pairwise correlation among portfolio constituents' daily returns.

    When the optional price_data argument is provided, it should be a DataFrame structured
    similar to the DataFrame returned by get_tickers_data. In this case, price data
    statistics will not be printed.

    Args:
        model_portfolio: Dict mapping ticker symbols to allocation percentages.
        start_date: Start date for historical price data retrieval (e.g., "2020-01-01").
        end_date: End date for historical price data retrieval (default: None, meaning today).
        rebalance_freq: Rebalancing frequency. Options include "daily",
                       "weekly", "monthly", "quarterly", "annually"
                       (default is "quarterly").
        verbose: If True, prints detailed status messages (default: False).
        price_data: Optional DataFrame containing price data. If provided, it
                    is used directly and price data statistics are not printed.

    Returns:
        A dictionary containing:
            - "daily_sample_variance": Daily sample variance of portfolio returns.
            - "daily_average_return": Daily average return.
            - "annualized_variance": Annualized variance.
            - "annualized_return": Annualized average return.
            - "sharpe_ratio": Sharpe ratio of the portfolio.
            - "min_date": Earliest date in the cleaned data.
            - "max_date": Latest date in the cleaned data.
            - "num_data_points": Number of data points (days) used in the backtest.
            - "data_retention_pct": Percentage of original data retained (after cleaning),
                                    or None if price_data is provided.
            - "max_drawdown": Maximum portfolio drawdown (as a positive fraction).
            - "average_correlation": Average pairwise correlation among portfolio constituents.
    """

    # ensure that allocations sum to 1; if not, normalize them
    total_alloc = sum(model_portfolio.values())
    if not np.isclose(total_alloc, 1.0):
        if verbose:
            print(f"Allocations sum to {total_alloc}, normalizing to 1.")
        model_portfolio = {ticker: alloc / total_alloc for ticker, alloc in model_portfolio.items()}

    # get the tickers included in the model portfolio
    tickers = list(model_portfolio.keys())

    # use provided price_data if available; otherwise, retrieve it (and its stats)
    if price_data is None:
        if verbose:
            print(f"Retrieving historical price data for tickers: {', '.join(tickers)}")
        price_data, price_data_stats = get_tickers_data(tickers,
                                                        start_date=start_date,
                                                        end_date=end_date,
                                                        price_type="Adj Close")
    else:
        price_data_stats = None  # Statistics unavailable when providing price_data directly.

    # only show price data statistics if available.
    if verbose and price_data_stats is not None:
        print("Price data statistics:")
        print("-" * 21)
        print("Pre-clean stats:")
        print("  row count: ", price_data_stats["pre-clean stats"]["row count"])
        print("  min date: ", price_data_stats["pre-clean stats"]["min date"])
        print("  max date: ", price_data_stats["pre-clean stats"]["max date"])
        print("Post-clean stats:")
        print("  row count: ", price_data_stats["post-clean stats"]["row count"])
        print("  min date: ", price_data_stats["post-clean stats"]["min date"])
        print("  max date: ", price_data_stats["post-clean stats"]["max date"])
        print(f"Data retention: {price_data_stats['data retention']:.3f}%")

    # sort by date for proper time series order.
    price_data.sort_index(inplace=True)

    # identify rebalancing dates
    # if rebalancing is daily then simulate daily rebalancing, otherwise use resampling
    if rebalance_freq == "daily":
        rebalance_dates = price_data.index
    else:
        freq_aliases = {
            "weekly": "W-MON",
            "monthly": "MS",
            "quarterly": "QS",
            "annually": "AS"
        }
        rule = freq_aliases.get(rebalance_freq)
        if rule is None:
            raise ValueError(f"Unsupported rebalance frequency: {rebalance_freq}")
        # get the first day of each period as a rebalancing date
        rebalance_dates = price_data.resample(rule).first().dropna().index

    # simulation setup
    dates = price_data.index
    weights = np.array([model_portfolio[ticker] for ticker in tickers])
    # simulate using an initial total portfolio value of $1.0
    portfolio_value = 1.0
    # get initial prices for all tickers
    initial_prices = price_data.loc[dates[0], tickers].values
    # calculate initial holdings (shares) according to target weights
    holdings = (portfolio_value * weights) / initial_prices
    # initialize a list to store the simulated daily returns
    simulated_returns = []

    # simulate model portfolio returns - starting on second day
    for current_date in dates[1:]:
        # get the current prices for all tickers
        current_prices = price_data.loc[current_date, tickers].values

        # on rebalance days, adjust holdings to re-establish target allocations.
        if current_date in rebalance_dates:
            holdings = (portfolio_value * weights) / current_prices

        # calculate the new portfolio value based on current prices.
        new_portfolio_value = (holdings * current_prices).sum()

        # compute the daily return for the portfolio.
        daily_ret = (new_portfolio_value / portfolio_value) - 1
        simulated_returns.append(daily_ret)

        # update the portfolio value for the next iteration.
        portfolio_value = new_portfolio_value

    # convert the simulated daily returns to a pandas Series for convenience.
    portfolio_daily_returns = pd.Series(simulated_returns, index=dates[1:])

    # compute daily summary statistics.
    daily_avg_return = portfolio_daily_returns.mean()
    daily_sample_variance = portfolio_daily_returns.var(ddof=1)

    # annualize the statistics (assuming 252 trading days per year).
    annualized_return = daily_avg_return * 252
    annualized_variance = daily_sample_variance * 252
    annualized_volatility = np.sqrt(annualized_variance)

    # compute the Sharpe ratio (assume risk-free rate is 0).
    sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else np.nan

    # calculate maximum drawdown.
    cumulative_returns = (1 + portfolio_daily_returns).cumprod()
    rolling_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    max_drawdown = abs(drawdown.min())  # Represented as a positive fraction

    # measure correlation among portfolio constituents using asset daily returns
    asset_daily_returns = price_data[tickers].pct_change().dropna()
    corr_matrix = asset_daily_returns.corr()
    # extract the upper triangle (excluding the diagonal) and compute the mean
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    average_correlation = corr_matrix.where(mask).stack().mean()

    if verbose:
        print("Backtest results:")
        print(f"Daily Average Return: {daily_avg_return:.3%}")
        print(f"Daily Sample Variance: {daily_sample_variance:.6f}")
        print(f"Annualized Return: {annualized_return:.3%}")
        print(f"Annualized Variance: {annualized_variance:.6f}")
        print(f"Sharpe Ratio: {sharpe_ratio:.6f}")
        print(f"Date Range: {price_data.index.min().date()} to {price_data.index.max().date()}")
        print(f"Number of Data Points: {price_data.shape[0]}")
        if price_data_stats is not None:
            print(f"Data Retention: {price_data_stats['data retention']:.3f}%")
        print(f"Maximum Drawdown: {max_drawdown:.3%}")
        print(f"Average Pairwise Correlation: {average_correlation:.4f}")
        print(f"Rebalancing Frequency: {rebalance_freq}")

    return {
        "daily_sample_variance": daily_sample_variance,
        "daily_average_return": daily_avg_return,
        "annualized_variance": annualized_variance,
        "annualized_return": annualized_return,
        "sharpe_ratio": sharpe_ratio,
        "min_date": price_data.index.min(),
        "max_date": price_data.index.max(),
        "num_data_points": price_data.shape[0],
        "data_retention_pct": price_data_stats["data retention"] if price_data_stats is not None else None,
        "max_drawdown": max_drawdown,
        "average_correlation": average_correlation
    }

def simulate_model_portfolio(model_portfolio: dict[str, float],
                             start_date: str,
                             end_date: str | None = None,
                             rebalance_freq: str = "quarterly",
                             price_data: pd.DataFrame | None = None,
                             verbose: bool = False) -> pd.DataFrame:
    """
    Simulate a model portfolio to generate a synthetic asset's daily value
    time series.

    This function returns a DataFrame indexed by date with a single column
    "Synthetic Value" representing the daily portfolio value.

    Args:
        model_portfolio: Dict mapping ticker symbols to allocation percentages.
        start_date: Start date for historical price data retrieval.
        end_date: End date for historical price data retrieval (default: None, meaning today).
        rebalance_freq: Frequency for rebalancing the portfolio. Supported options are "daily",
                        "weekly", "monthly", "quarterly", "annually" (default is "quarterly").
        price_data: Optional DataFrame with historical price data. If provided, it should be in a
                    format similar to that returned by get_tickers_data.
        verbose: If True, prints additional status messages.

    Returns:
        DataFrame indexed by date with a single column "Synthetic Value" that contains the daily portfolio value.

    Example:
        portfolio = {'AAPL': 0.5, 'MSFT': 0.5}
        synthetic_df = simulate_model_portfolio(portfolio, start_date="2000-01-01", end_date="2020-01-01")
    """
    import numpy as np
    import pandas as pd
    from market_data import get_tickers_data  # Ensure correct import

    # Normalize allocations if they do not sum exactly to 1.
    total_alloc = sum(model_portfolio.values())
    if not np.isclose(total_alloc, 1.0):
        if verbose:
            print(f"Allocations sum to {total_alloc}, normalizing to 1.")
        model_portfolio = {ticker: alloc / total_alloc for ticker, alloc in model_portfolio.items()}

    tickers = list(model_portfolio.keys())

    # Retrieve historical price data if not provided.
    if price_data is None:
        if verbose:
            print(f"Retrieving historical price data for tickers: {', '.join(tickers)}")
        price_data, _ = get_tickers_data(tickers, start_date=start_date, end_date=end_date, price_type="Adj Close")
    if price_data.empty:
        raise ValueError("No historical price data retrieved.")

    # Ensure the price data is sorted by date.
    price_data.sort_index(inplace=True)

    # Determine rebalancing dates.
    if rebalance_freq == "daily":
        rebalance_dates = set(price_data.index)
    else:
        freq_aliases = {
            "weekly": "W-MON",
            "monthly": "MS",
            "quarterly": "QS",
            "annually": "AS"
        }
        rule = freq_aliases.get(rebalance_freq)
        if rule is None:
            raise ValueError(f"Unsupported rebalance frequency: {rebalance_freq}")
        rebalance_dates = set(price_data.resample(rule).first().dropna().index)

    # Simulation setup: get the weights and initialize the portfolio value.
    weights = np.array([model_portfolio[ticker] for ticker in tickers])
    portfolio_value = 1.0  # starting portfolio value (e.g., $1 or 100%)
    holdings = None  # Will be initialized on first iteration

    # Create an empty DataFrame for synthetic portfolio values.
    synthetic_df = pd.DataFrame(index=price_data.index, columns=["Synthetic Value"], dtype=float)

    # Iterate over each row (date) in price_data.
    for current_date, row in price_data.iterrows():
        current_prices = row[tickers].values
        # If current_date is a rebalance day or holdings have not been initialized, re-calc holdings.
        if (current_date in rebalance_dates) or (holdings is None):
            holdings = (portfolio_value * weights) / current_prices
        # Calculate the new portfolio value.
        portfolio_value = (holdings * current_prices).sum()
        synthetic_df.loc[current_date, "Synthetic Value"] = portfolio_value

    return synthetic_df

def simulate_model_portfolio_bt(model_portfolio: dict[str, float],
                                start_date: str,
                                end_date: str | None = None,
                                rebalance_freq: str = "quarterly",
                                price_data: pd.DataFrame | None = None,
                                verbose: bool = False):
    """
    Simulate a model portfolio using the bt package.

    This function leverages bt to perform a backtest for a portfolio that holds fixed
    target weights defined by `model_portfolio`. bt's built-in algorithms handle data
    alignment, rebalancing, and performance aggregation.

    Args:
        model_portfolio: Dict mapping ticker symbols to allocation percentages.
                         If they do not sum to 1, they will be normalized.
        start_date: The start date for the backtest (e.g., "2000-01-01").
        end_date: The end date for the backtest; if None, bt.get() will fetch data until today.
        rebalance_freq: The rebalancing frequency. Options include "daily", "weekly", "monthly",
                        "quarterly", "annually".
        price_data: Optional DataFrame of historical price data; if not provided, it will be fetched using bt.get.
        verbose: If True, prints additional status messages.

    Returns:
        A bt.Backtest result that contains the simulated portfolio's equity curve and performance metrics.
    """

    # Normalize allocations if they do not sum close to 1.
    total_alloc = sum(model_portfolio.values())
    if not np.isclose(total_alloc, 1.0):
        if verbose:
            print(f"Allocations sum to {total_alloc}, normalizing to 1.")
        model_portfolio = {ticker: alloc / total_alloc for ticker, alloc in model_portfolio.items()}

    # Retrieve historical price data if not provided.
    if price_data is None:
        tickers = list(model_portfolio.keys())
        if verbose:
            print(f"Retrieving historical price data for tickers: {', '.join(tickers)}")
        price_data, _ = get_tickers_data(tickers, start_date=start_date, end_date=end_date, price_type="Adj Close")
    if price_data.empty:
        raise ValueError("No historical price data retrieved.")

    # Ensure the price data is sorted by date.
    price_data.sort_index(inplace=True)

    # Map the rebalancing frequency string to a bt algorithm.
    frequency_map = {
        "daily": bt.algos.RunDaily(),
        "weekly": bt.algos.RunWeekly(),
        "monthly": bt.algos.RunMonthly(),
        "quarterly": bt.algos.RunQuarterly(),
        "annually": bt.algos.RunYearly(),
    }
    if rebalance_freq not in frequency_map:
        raise ValueError(f"Unsupported rebalance frequency: {rebalance_freq}")

    # Define the strategy:
    # - run on the specified rebalancing frequency,
    # - select all securities in the universe,
    # - allocate weights as in the model portfolio,
    # - and rebalance accordingly.
    strategy = bt.Strategy("ModelPortfolio",
                           [
                               frequency_map[rebalance_freq],
                               bt.algos.SelectAll(),
                               bt.algos.WeighSpecified(**model_portfolio),
                               bt.algos.Rebalance()
                           ])

    # Create the backtest using the strategy and price data.
    portfolio = bt.Backtest(strategy, price_data)

    # Run the backtest.
    result = bt.run(portfolio)

    if verbose:
        result.display()

    return result