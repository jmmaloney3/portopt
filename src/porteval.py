# this module contains utility functions that can be used to evaluate
# and compare portfolios.

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import pandas as pd
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