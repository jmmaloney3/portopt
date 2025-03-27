"""
Rebalancing functionality for portfolio optimization.

This module provides the RebalanceMixin class that adds portfolio rebalancing
capabilities to the Portfolio class. It uses convex optimization to determine
optimal fund allocations that achieve target factor weights while respecting
specified constraints.

Classes:
    RebalanceMixin: Mixin class providing portfolio rebalancing methods

Dependencies:
    - pandas: Data manipulation and analysis
    - cvxpy: Convex optimization
    - numpy: Numerical computing
"""

import pandas as pd
import numpy as np
import cvxpy as cp
from typing import Dict
from .utils import write_table

class RebalanceMixin:
    """
    Mixin class that adds portfolio rebalancing capabilities to Portfolio class.
    """

    def adjust_factor_allocations(
        self,
        filters: Dict[str, str],
        reduction: float,
        verbose: bool = False
    ) -> pd.DataFrame:
        """Adjust factor allocations by reducing specified factors by a percentage.

        Args:
            filters: Dictionary of filters to apply (e.g., {'Level_0': ['Equity'], 'Level_1': ['US']})
            reduction: Percentage points to reduce the filtered factors by (e.g., 5.0 for 5%)
            verbose: If True, print detailed information about the changes

        Returns:
            DataFrame with original and new allocations
        """
        # Get current allocations to use as base
        base_allocations = self.getMetrics('Factor', portfolio_allocation=True)['Allocation']

        # Get the current metrics for filtered factors
        filtered_metrics = self.getMetrics('Factor', filters=filters, portfolio_allocation=True)
        current_total = filtered_metrics['Allocation'].sum()
        target_total = current_total - reduction  # reduction is already in decimal form
        reduction_amount = reduction  # reduction is already in decimal form

        if verbose:
            print(f"\nCurrent total for filtered factors: {current_total:.2%}")
            print(f"Target total: {target_total:.2%}")
            print(f"Reduction amount: {reduction_amount:.2%}")

        # Create target allocations starting from current allocations
        target_allocations = base_allocations.copy()

        # Get filtered factors
        filtered_factors = filtered_metrics.index

        # Scale down each filtered factor proportionally
        scale_factor = target_total / current_total
        target_allocations[filtered_factors] *= scale_factor

        # Add the reduction to Cash
        target_allocations['Cash'] += reduction_amount

        # Create DataFrame with original and new allocations
        results = pd.DataFrame({
            'Original Allocation': base_allocations,
            'New Allocation': target_allocations,
        })

        # Display the changes
        if verbose:
            print("\nTarget Allocation Changes:")
            print("=========================")
            # Filter for factors that changed significantly
            changed_factors = results[abs(results['New Allocation'] - results['Original Allocation']) > 0.0001]
            if not changed_factors.empty:
                column_formats = {
                    'Factor': {'width': 30},
                    'Original Allocation': {'width': 15, 'type': '%', 'decimal': 2},
                    'New Allocation': {'width': 15, 'type': '%', 'decimal': 2}
                }
                write_table(changed_factors, columns=column_formats)

            # Verify the total change
            print(f"\nTotal filtered factors (Original): {filtered_metrics['Allocation'].sum():.2%}")
            print(f"Total filtered factors (New): {results.loc[filtered_factors, 'New Allocation'].sum():.2%}")

        return results

    def rebalance(self, target_allocations: pd.Series, turnover_penalty: float = 1.0, verbose: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Rebalance the portfolio to match target factor allocations as closely as possible.

        Args:
            target_allocations: Series indexed by Factor containing target allocation percentages
            turnover_penalty: Weight for penalizing changes from current allocations (default: 1.0)
                            Higher values mean prefer keeping current allocations
                            0.0 means ignore current allocations
            verbose: If True, print optimization details. Default is False.

        Returns:
            Tuple containing:
            - DataFrame with ticker-level details (original and new allocations)
            - DataFrame with factor-level details (original, new, and target allocations)

        Note: This initial implementation treats all accounts as one portfolio and
              assumes all tickers are available for allocation.
        """
        # Get current portfolio data
        current_values = self.getMetrics('Ticker')
        prices = self.getPrices()
        factor_weights = self.getFactorWeights()
        
        # Get total portfolio value
        total_value = current_values['Total Value'].sum()

        # Prepare optimization inputs
        tickers = prices.index
        factors = target_allocations.index

        # Create factor weights matrix (factors x tickers)
        F = pd.pivot_table(
            factor_weights.reset_index(),
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Reindex F to match exactly:
        # - rows (factors): 
        #   1. Keep only factors that are in target_allocations
        #   2. Add rows with zeros for any target factors not in factor_weights
        #   3. Ensure factors are in same order as target_allocations
        # - columns (tickers):
        #   1. Keep only tickers that are in our prices DataFrame
        #   2. Ensure tickers are in same order as prices
        # 
        # This is crucial for the optimization to work correctly because:
        # 1. Allows element-wise comparison in the objective function:
        #    portfolio_allocations = F @ x
        #    minimize: sum_squares(portfolio_allocations - target_allocations)
        # 2. Ensures matrix dimensions are compatible for optimization
        F = F.reindex(index=factors, columns=tickers, fill_value=0)

        if verbose:
            print("\nFactor weights matrix F:")
            print(F)
            print("\nTarget allocations:")
            print(target_allocations)

        # Set up optimization problem
        x = cp.Variable(len(tickers))  # Allocation percentages to each ticker

        # Objective: Minimize weighted sum of:
        # 1. Squared differences between target and actual factor allocations
        # 2. Squared differences between current and new ticker allocations
        portfolio_allocations = F.to_numpy() @ x
        factor_objective = cp.sum_squares(portfolio_allocations - target_allocations.to_numpy())

        # Create vector of current allocations (0 for tickers not in current portfolio)
        current_allocations = pd.Series(0, index=tickers)
        current_allocations.update(current_values['Allocation'])

        turnover_objective = cp.sum_squares(x - current_allocations.to_numpy())

        objective = cp.Minimize(factor_objective + turnover_penalty * turnover_objective)

        # Constraints
        constraints = [
            cp.sum(x) == 1,     # Allocations must sum to 100%
            x >= 0,             # No negative allocations
            x <= 1,             # No allocations over 100%
        ]

        # Solve optimization problem
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.SCIP, verbose=verbose)

        if problem.status != 'optimal':
            raise RuntimeError(f"Optimization failed with status: {problem.status}")

        # Create results DataFrames
        ticker_results = pd.DataFrame(index=tickers)
        ticker_results['Original Value'] = current_values['Total Value']
        ticker_results['Original Allocation'] = current_values['Allocation']

        # Calculate new values
        new_allocations = pd.Series(x.value, index=tickers)
        new_values = new_allocations * total_value

        ticker_results['New Value'] = new_values
        ticker_results['New Allocation'] = new_allocations

        # Calculate difference between new and original values
        ticker_results['Value Diff'] = ticker_results['New Value'] - ticker_results['Original Value']
        ticker_results['Allocation Diff'] = ticker_results['New Allocation'] - ticker_results['Original Allocation']

        # Calculate factor allocations
        factor_results = pd.DataFrame(index=factors)
        factor_results['Original Value'] = F @ current_values['Total Value']
        factor_results['Original Allocation'] = factor_results['Original Value'] / total_value
        factor_results['New Value'] = F @ new_values
        factor_results['New Allocation'] = F @ new_allocations
        factor_results['Target Allocation'] = target_allocations
        factor_results['Value Diff'] = factor_results['New Value'] - factor_results['Original Value']
        factor_results['Allocation Diff'] = factor_results['New Allocation'] - factor_results['Target Allocation']

        return ticker_results, factor_results
