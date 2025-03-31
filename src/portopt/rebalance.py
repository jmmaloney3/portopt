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
        source_filter: Dict[str, str],
        dest_filter: Dict[str, str],
        transfer: float,
        verbose: bool = False
    ) -> pd.DataFrame:
        """Adjust factor allocations by transferring allocation between two sets of factors.

        Args:
            source_filter: Dictionary of filters to identify source factors
            dest_filter: Dictionary of filters to identify destination factors
            transfer: Percentage points to transfer from source to destination (e.g., 0.05 for 5%)
            verbose: If True, print detailed information about the changes

        Returns:
            DataFrame with original and new allocations
        """
        # Get current allocations to use as base
        base_allocations = self.getMetrics('Factor', portfolio_allocation=True)['Allocation']

        # Get the current metrics for source and destination factors
        source_metrics = self.getMetrics('Factor', filters=source_filter, portfolio_allocation=True)
        dest_metrics = self.getMetrics('Factor', filters=dest_filter, portfolio_allocation=True)

        source_total = source_metrics['Allocation'].sum()
        dest_total = dest_metrics['Allocation'].sum()

        if verbose:
            print(f"\nSource factors total: {source_total:.2%}")
            print(f"Destination factors total: {dest_total:.2%}")
            print(f"Transfer amount: {transfer:.2%}")

        # Create target allocations starting from current allocations
        target_allocations = base_allocations.copy()

        # Get source and destination factors
        source_factors = source_metrics.index
        dest_factors = dest_metrics.index

        # Scale down source factors proportionally
        source_scale = (source_total - transfer) / source_total
        target_allocations[source_factors] *= source_scale

        # Scale up destination factors proportionally
        dest_scale = (dest_total + transfer) / dest_total
        target_allocations[dest_factors] *= dest_scale

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

            # Verify the total changes
            print(f"\nSource factors (Original): {source_metrics['Allocation'].sum():.2%}")
            print(f"Source factors (New): {results.loc[source_factors, 'New Allocation'].sum():.2%}")
            print(f"Destination factors (Original): {dest_metrics['Allocation'].sum():.2%}")
            print(f"Destination factors (New): {results.loc[dest_factors, 'New Allocation'].sum():.2%}")

        return results

    def rebalance(
        self,
        target_factor_allocations: pd.Series,
        turnover_penalty: float = 1.0,
        complexity_penalty: float = 0.0,
        min_ticker_alloc: float = 0.0,
        verbose: bool = False
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Rebalance the portfolio to match target factor allocations as closely as possible.

        Args:
            target_factor_allocations: Series indexed by Factor containing target allocation percentages
            turnover_penalty: Weight for penalizing changes from current allocations (default: 1.0)
                            Higher values mean prefer keeping current allocations
                            0.0 means ignore current allocations
            complexity_penalty: Weight for penalizing the number of funds used (default: 0.0)
                            Higher values favor solutions with fewer funds
                            0.0 means ignore portfolio complexity
            min_ticker_alloc: Minimum non-zero allocation for any fund (default: 0.0)
                      Fund allocation will either be 0 or >= min_ticker_alloc
            verbose: If True, print optimization details. Default is False.

        Returns:
            Tuple containing:
            - DataFrame with ticker-level details (original and new allocations)
            - DataFrame with factor-level details (original, new, and target allocations)

        Note: This initial implementation treats all accounts as one portfolio and
              assumes all tickers are available for allocation.
        """
        # Get current portfolio data
        current_ticker_allocations = self.getMetrics('Ticker')['Allocation']
        account_tickers = self.getAccountTickers()
        factor_weights = self.getFactorWeights()

        # Prepare optimization inputs
        tickers = account_tickers.index.get_level_values('Ticker').unique()
        factors = target_factor_allocations.index

        # Create factor weights matrix (factors x tickers)
        F = pd.pivot_table(
            factor_weights,
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Reindex F to match exactly:
        # - rows (factors): 
        #   1. Keep only factors that are in target_factor_allocations
        #   2. Add rows with zeros for any target factors not in factor_weights
        #   3. Ensure factors are in same order as target_factor_allocations
        # - columns (tickers):
        #   1. Keep only tickers that are in our account_tickers DataFrame
        #   2. Ensure tickers are in same order as the unique tickers list
        #
        # This is crucial for the optimization to work correctly because:
        # 1. Allows element-wise comparison in the objective function:
        #    portfolio_factor_allocations = F @ x
        #    minimize: sum_squares(portfolio_factor_allocations - target_factor_allocations)
        # 2. Ensures matrix dimensions are compatible for optimization
        F = F.reindex(index=factors, columns=tickers, fill_value=0)

        if verbose:
            print("\nFactor weights matrix F:")
            print(F)
            print("\nTarget allocations:")
            print(target_factor_allocations)

        # Set up optimization problem
        x = cp.Variable(len(tickers))  # Allocation percentages to each ticker
        z = cp.Variable(len(tickers), boolean=True)  # Binary selection variables

        # Objective: Minimize weighted sum of:
        # 1. Squared differences between target and actual factor allocations
        # 2. Squared differences between current and new ticker allocations
        # 3. Number of funds used (complexity penalty)

        # 1. Set up factor objective
        portfolio_factor_allocations = F.to_numpy() @ x
        factor_objective = cp.sum_squares(portfolio_factor_allocations - target_factor_allocations.to_numpy())

        # 2. Set up turnover objective
        turnover_objective = cp.sum_squares(x - current_ticker_allocations.to_numpy())

        # 3. Set up complexity objective
        complexity_objective = cp.sum(z)  # Count number of funds used

        # Define objective
        objective = cp.Minimize(
            factor_objective +
            turnover_penalty * turnover_objective +
            complexity_penalty * complexity_objective
        )

        # Define constraints
        constraints = [
            cp.sum(x) == 1,            # Allocations must sum to 100%
            x >= 0,                    # No negative allocations
            x <= z,                    # Link x and z (if z=0, x=0)
            x >= min_ticker_alloc * z  # Minimum allocation when fund is selected
        ]

        # Solve optimization problem
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.SCIP, verbose=verbose)

        if problem.status != 'optimal':
            raise RuntimeError(f"Optimization failed with status: {problem.status}")

        # Create new allocations series
        new_ticker_allocations = pd.Series(x.value, index=tickers)

        # Ticker results
        ticker_results = pd.DataFrame(index=tickers)
        ticker_results['Original Allocation'] = current_ticker_allocations
        ticker_results['New Allocation'] = new_ticker_allocations
        ticker_results['Allocation Diff'] = ticker_results['New Allocation'] - ticker_results['Original Allocation']

        # Factor results
        factor_results = pd.DataFrame(index=factors)
        factor_results['Original Allocation'] = self.getMetrics('Factor')['Allocation']
        factor_results['New Allocation'] = F @ new_ticker_allocations
        factor_results['Target Allocation'] = target_factor_allocations
        factor_results['Allocation Diff'] = factor_results['New Allocation'] - factor_results['Target Allocation']

        return ticker_results, factor_results

    def _create_account_optimization_components(
        self,
        account: str,
        target_factor_allocations: pd.Series,
        min_ticker_alloc: float = 0.0,
        verbose: bool = False
    ) -> Dict[str, any]:
        """Create optimization components (variables, objectives, constraints) for a single account.

        Args:
            account: Account identifier
            target_factor_allocations: Series indexed by Factor containing target allocation percentages
            min_ticker_alloc: Minimum non-zero allocation for any fund
            verbose: If True, print optimization details

        Returns:
            Dictionary containing:
            - variables: Dict of optimization variables (x: allocations, z: binary selection)
            - objectives: Dict of objective expressions (factor, turnover, complexity)
            - constraints: List of account-level constraints
            - factor_allocations: Expression for account's factor allocations (F @ x)
            - tickers: List of tickers for this account
            - factors: List of factors for this account
        """
        # Get account-specific data
        account_tickers = self.getAccountTickers()
        tickers = account_tickers.xs(account, level='Account').index

        current_ticker_allocations = self.getMetrics('Ticker', filters={'Account': account})['Allocation']

        factor_weights = self.getFactorWeights()
        factors = target_factor_allocations.index

        # Create factor weights matrix F
        F = pd.pivot_table(
            factor_weights,
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Reindex F to match exactly:
        # - rows (factors):
        #   1. Keep only factors that are in target_factor_allocations
        #   2. Add rows with zeros for any target factors not in factor_weights
        #   3. Ensure factors are in same order as target_factor_allocations
        # - columns (tickers):
        #   1. Keep only tickers that are in our account_tickers DataFrame
        #   2. Ensure tickers are in same order as the unique tickers list
        #
        # This is crucial for the optimization to work correctly because:
        # 1. Allows element-wise comparison in the objective function:
        #    portfolio_factor_allocations = F @ x
        #    minimize: sum_squares(portfolio_factor_allocations - target_factor_allocations)
        # 2. Ensures matrix dimensions are compatible for optimization
        F = F.reindex(index=factors, columns=tickers, fill_value=0)

        if verbose:
            print(f"\nAccount: {account}")
            print(f"Number of tickers: {len(tickers)}")
            print("Tickers:", tickers.tolist())
            print("\nFactor weights matrix F:")
            print(F)

        # Create variables with meaningful names
        x_vars = [cp.Variable(name=f"x_{account}_{ticker}") for ticker in tickers]
        z_vars = [cp.Variable(boolean=True, name=f"z_{account}_{ticker}") for ticker in tickers]

        variables = {
            'x': cp.vstack(x_vars),  # Stack into column vector
            'z': cp.vstack(z_vars),  # Stack into column vector
            'x_dict': {var.name: var for var in x_vars},  # For easier lookup
            'z_dict': {var.name: var for var in z_vars}   # For easier lookup
        }

        # Calculate account's factor allocations
        account_factor_allocations = F.to_numpy() @ variables['x']

        # Create objective components
        objectives = {
            # factor objective: minimize difference between account factor allocations and target factor allocations
            'factor': cp.sum_squares(account_factor_allocations - target_factor_allocations.to_numpy()),
            # turnover objective: minimize difference between current and new ticker allocations
            'turnover': cp.sum_squares(variables['x'] - current_ticker_allocations.to_numpy()),
            # complexity objective: minimize number of funds used
            'complexity': cp.sum(variables['z'])
        }

        # Create constraints
        constraints = [
            cp.sum(variables['x']) == 1,                         # Allocations sum to 100%
            variables['x'] >= 0,                                 # No negative allocations
            variables['x'] <= variables['z'],                    # Link x and z
            variables['x'] >= min_ticker_alloc * variables['z']  # Minimum allocation
        ]

        if verbose:
            print("\nCreated variables:")
            print("Allocation variables (x):", [var.name for var in x_vars])
            print("Selection variables (z):", [var.name for var in z_vars])
            print("\nFactor alignment:")
            print("Factors:", factors.tolist())

        return {
            'variables': variables,
            'objectives': objectives,
            'constraints': constraints,
            'factor_allocations': account_factor_allocations,
            'tickers': tickers,
            'factors': factors
        }
