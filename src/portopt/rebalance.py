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
from typing import Dict, Union
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

    def getCanonicalFactorWeightsMatrix(self, verbose: bool = False) -> pd.DataFrame:
        """Create a factor weights matrix with canonically ordered rows (factors)
           and columns (tickers).

        The matrix will:
        1. Include all possible factors and tickers from factor weights
        2. Sort factors (rows) and tickers (columns) lexicographically
        3. Fill any missing values with 0
        4. Include 'Factor' as a named index (to facillitate debugging), when converting
           the matrix to a NumPy array, the index will be dropped

        Args:
            verbose: If True, print information about the matrix construction

        Returns:
            DataFrame with factors as rows (indexed by 'Factor') and tickers as columns, sorted in canonical order

        Raises:
            AssertionError: If factors or tickers are not in lexicographical order
        """
        if verbose:
            print("\nCreating canonical factor weights matrix...")

        # Get raw factor weights
        factor_weights = self.getFactorWeights()

        # Get unique factors and tickers in sorted order
        factors = sorted(factor_weights.index.get_level_values('Factor').unique())
        tickers = sorted(factor_weights.index.get_level_values('Ticker').unique())

        if verbose:
            print(f"Number of factors: {len(factors)}")
            print(f"Number of tickers: {len(tickers)}")

        # Create pivot table with canonical ordering
        F = pd.pivot_table(
            factor_weights,
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Reindex to ensure all factors and tickers are included in sorted order
        F = F.reindex(index=factors, columns=tickers, fill_value=0)

        # Explicitly name the index
        F.index.name = 'Factor'

        # Validate ordering
        assert list(F.index) == sorted(F.index), "Factors are not in lexicographical order"
        assert list(F.columns) == sorted(F.columns), "Tickers are not in lexicographical order"

        if verbose:
            print("\nCanonical factor weights matrix F:")
            print(f"Shape: {F.shape}")
            self._write_weights(F)

        return F

    def _create_variable_vectors(self, canonical_matrix: pd.DataFrame, account: str = None, verbose: bool = False) -> Dict[str, cp.Variable]:
        """Create variable vectors compatible with the canonical factor weights matrix.

        Args:
            canonical_matrix: Factor weights matrix from getCanonicalFactorWeightsMatrix()
            account: Optional account name to include in variable names
            verbose: If True, print information about the variables created

        Returns:
            Dictionary containing:
                'x': Vstack of allocation variables
                'z': Vstack of binary selection variables
            Variables are ordered to match columns of canonical_matrix

        Raises:
            AssertionError: If variable ordering doesn't match canonical matrix columns
        """
        # Get tickers from canonical matrix columns
        tickers = canonical_matrix.columns

        # Create variable name pattern based on whether account is provided
        if account:
            x_pattern = lambda ticker: f"x_{account}_{ticker}"
            z_pattern = lambda ticker: f"z_{account}_{ticker}"
        else:
            x_pattern = lambda ticker: f"x_{ticker}"
            z_pattern = lambda ticker: f"z_{ticker}"

        # Create variables with appropriate names
        x_vars = [cp.Variable(name=x_pattern(ticker)) for ticker in tickers]
        z_vars = [cp.Variable(boolean=True, name=z_pattern(ticker)) for ticker in tickers]

        # Validate variable alignment with canonical matrix
        assert all(x_vars[i].name().split('_')[-1] == ticker
                  for i, ticker in enumerate(canonical_matrix.columns)), \
            "Variable order does not match canonical matrix columns"

        # Stack variables into vectors
        variables = {
            'x': cp.vstack(x_vars),  # Allocation percentages
            'z': cp.vstack(z_vars)   # Binary selection variables
        }

        if verbose:
            print("\nCreated variable vectors:")
            print(f"Number of variables: {len(tickers)}")
            print("\nAllocation variables (x):")
            print([var.name() for var in x_vars])
            print("\nSelection variables (z):")
            print([var.name() for var in z_vars])

        return variables

    def _create_target_factor_allocations_vector(
        self,
        target_allocations: pd.Series,
        canonical_matrix: pd.DataFrame,
        account: str = None,
        verbose: bool = False
    ) -> pd.Series:
        """Create a target factor allocations vector compatible with the canonical
           factor weights matrix and, when requested, scaled by the account's
           proportion of the total portfolio.

        Args:
            target_allocations: Series indexed by Factor containing target allocation
                percentages for the entire portfolio
            canonical_matrix: Factor weights matrix from getCanonicalFactorWeightsMatrix()
            account: If provided, scale target allocations by account's proportion
                of portfolio
            verbose: If True, print information about the vector creation

        Returns:
            Series indexed by Factor containing target allocations, aligned with canonical
            matrix rows. If account is provided, values are scaled to represent that
            account's portion of the total portfolio.

        Raises:
            ValueError: If target allocations don't sum to 100%
            ValueError: If target allocations contain factors not present in canonical matrix
            AssertionError: If resulting series is not aligned with canonical matrix
        """
        if verbose:
            print("\nCreating target factor vector...")
            print(f"Original target allocations shape: {target_allocations.shape}")
            self._write_weights(target_allocations, "Original target allocations:")

        # Validate original allocations sum to 100%
        total_allocation = target_allocations.sum()
        if not np.isclose(total_allocation, 1.0, rtol=1e-5):
            raise ValueError(
                f"Target allocations must sum to 100%, got {total_allocation:.2%}"
            )

        # Check for extra factors in target allocations
        extra_factors = set(target_allocations.index) - set(canonical_matrix.index)
        if extra_factors:
            raise ValueError(
                f"Target allocations contain factors not present in canonical matrix: {extra_factors}"
            )

        # Create new series with all factors from canonical matrix
        canonical_factors = canonical_matrix.index
        result = pd.Series(
            0.0, 
            index=canonical_factors,
            name=target_allocations.name  # Preserve original Series name
        )
        result.index.name = 'Factor'  # Set name for the index

        # Fill in provided target allocations
        result.update(target_allocations)

        # If account is provided, scale allocations by account's proportion of portfolio
        if account is not None:
            # Get account's current allocation as percentage of total portfolio
            account_metrics = self.getMetrics('Account', portfolio_allocation=True)
            account_proportion = account_metrics.loc[account, 'Allocation']

            if verbose:
                print(f"\nScaling target allocations for account: {account}")
                print(f"Account proportion of portfolio: {account_proportion:.2%}")

            # Scale all allocations by account proportion
            result *= account_proportion

        # Validate resulting allocations sum appropriately
        total_allocation = result.sum()
        expected_total = 1.0 if account is None else account_metrics.loc[account, 'Allocation']
        if not np.isclose(total_allocation, expected_total, rtol=1e-5):
            raise ValueError(
                f"Resulting allocations must sum to {expected_total:.2%}, got {total_allocation:.2%}"
            )

        # Validate alignment with canonical matrix
        assert result.index.equals(canonical_matrix.index), \
            "Result factors not aligned with canonical matrix"
        assert list(result.index) == list(canonical_matrix.index), \
            "Result factors not in same order as canonical matrix"

        if verbose:
            print(f"\nResulting target allocations shape: {result.shape}")
            self._write_weights(result, "Resulting target allocations:")

            # Show added factors
            added_factors = set(result.index) - set(target_allocations.index)
            if added_factors:
                print("\nFactors added with zero allocation:")
                print(added_factors)

        return result

    def _create_account_optimization_components(
        self,
        account: str,
        target_factor_allocations: pd.Series,
        min_ticker_alloc: float = 0.0,
        verbose: bool = False
    ) -> Dict[str, any]:
        """Create optimization components (variables, objectives, constraints) for
        a single account.

        This creates components that will be used to define an optimization problem
        that finds the ticker allocations for each account-ticker pair that achieves
        the optimization goals.  The resulting optimized values are percentages of
        the entire portfolio, not just the account.

        Args:
            account: Account identifier
            target_factor_allocations: Series indexed by Factor containing target
                allocation percentages
            min_ticker_alloc: Minimum non-zero allocation for any fund
            verbose: If True, print optimization details

        Returns:
            Dictionary containing:
            - variables: Dict of optimization variables (x: allocations, z: binary selection)
            - objectives: Dict of objective expressions (factor, turnover, complexity)
            - constraints: List of account-level constraints
            - factor_allocations: Expression for account's factor allocations (F @ x)

        Raises:
            ValueError: If account is not found in portfolio
        """
        if verbose:
            print(f"\nCreating optimization components for account: {account}")

        # Verify account exists
        account_tickers = self.getAccountTickers()
        if account not in account_tickers.index.get_level_values('Account').unique():
            raise ValueError(f"Account '{account}' not found in portfolio. Available accounts: "
                            f"{account_tickers.index.get_level_values('Account').unique().tolist()}")

        # Get current ticker allocations for this account
        # - this is the current allocation of each ticker in the context of
        #   the entire portfolio - not just the account
        current_ticker_allocations = self.getMetrics('Ticker',
                                                     filters={'Account': account},
                                                     portfolio_allocation=True
                                                     )['Allocation']

        if verbose:
            print("\nCurrent ticker allocations:")
            print(current_ticker_allocations)
            print(f"Current ticker allocations sum: {current_ticker_allocations.sum():.2%}")

        # Get canonical factor weights matrix
        F = self.getCanonicalFactorWeightsMatrix(verbose=verbose)

        # Create target allocations vector aligned with canonical matrix
        # - this is the target allocation for each factor in the context of the
        #   entire portfolio - not just the account
        target_vector = self._create_target_factor_allocations_vector(
            target_allocations=target_factor_allocations,
            canonical_matrix=F,
            account=account,
            verbose=verbose
        )

        # Create variable vectors aligned with canonical matrix
        # - these variables represent the allocation percentages for each
        #   ticker in the context of the entire portfolio - not just the
        #   account
        # - they will be optimized to achieve the target factor allocations
        variables = self._create_variable_vectors(
            canonical_matrix=F,
            account=account,
            verbose=verbose
        )

        # Calculate account's factor allocations using canonical matrix
        account_factor_allocations = F.to_numpy() @ variables['x']

        if verbose:
            print("\nCreating objective components...")

        # Create objective components
        objectives = {
            # factor objective: minimize difference between account factor allocations and target factor allocations
            'factor': cp.sum_squares(account_factor_allocations - target_vector.to_numpy()),
            # turnover objective: minimize difference between current and new ticker allocations
            'turnover': cp.sum_squares(variables['x'] - current_ticker_allocations.to_numpy()),
            # complexity objective: minimize number of funds used
            'complexity': cp.sum(variables['z'])
        }

        if verbose:
            print("\nCreating constraints...")

        # Get account's current allocation as percentage of total portfolio
        account_metrics = self.getMetrics('Account', portfolio_allocation=True)
        account_proportion = account_metrics.loc[account, 'Allocation']

        # Create the constraints list
        constraints = [
            # Sum of allocations equals account's proportion of portfolio
            cp.sum(variables['x']) == account_proportion,
            variables['x'] >= 0,                                 # No negative allocations
            variables['x'] <= variables['z'],                    # Link x and z
            variables['x'] >= min_ticker_alloc * variables['z']  # Minimum allocation
        ]

        if verbose:
            print(f"\nAccount constraints:")
            print(f"- Sum of allocations = {account_proportion:.2%} (account's portfolio proportion)")

        return {
            'variables': variables,
            'objectives': objectives,
            'constraints': constraints,
            'factor_allocations': account_factor_allocations,
        }

    def rebalance_portfolio(
        self,
        target_factor_allocations: pd.Series,
        turnover_penalty: float = 1.0,
        complexity_penalty: float = 0.0,
        account_align_penalty: float = 1.0,
        min_ticker_alloc: float = 0.0,
        verbose: bool = False
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Rebalance a multi-account portfolio to match target factor allocations as
        closely as possible.

        NOTE: This method is a work in progress and is not yet ready for use.

        Args:
            target_factor_allocations: Series indexed by Factor containing target
                allocation percentages
            turnover_penalty: Weight for penalizing changes from current allocations
                (default: 1.0)
            complexity_penalty: Weight for penalizing the number of funds used
                (default: 0.0)
            account_align_penalty: Weight for penalizing account-level factor
                misalignment (default: 1.0)
            min_ticker_alloc: Minimum non-zero allocation for any fund (default: 0.0)
            verbose: If True, print optimization details

        Returns:
            Tuple containing:
            - DataFrame with ticker-level details (original and new allocations)
            - DataFrame with factor-level details (original, new, and target allocations)
        """
        # Validate inputs
        if not np.isclose(target_factor_allocations.sum(), 1.0, rtol=1e-5):
            raise ValueError(f"Target factor allocations must sum to 100%, sum is {target_factor_allocations.sum():.2%}")
        if any(p < 0 for p in [turnover_penalty, complexity_penalty, account_align_penalty]):
            raise ValueError("Penalty parameters must be non-negative")

        if verbose:
            self._write_weights(target_factor_allocations, "Input target allocations:")

        # Get canonical factor weights matrix (will be used for all accounts)
        F = self.getCanonicalFactorWeightsMatrix(verbose=verbose)

        # Align target allocations with canonical matrix
        target_factor_allocations = self._create_target_factor_allocations_vector(
            target_allocations=target_factor_allocations,
            canonical_matrix=F,
            account=None,  # No account scaling needed here
            verbose=verbose
        )

        # Get list of accounts
        accounts = self.getAccountTickers().index.get_level_values('Account').unique()
        if verbose:
            print(f"\nOptimizing allocations for {len(accounts)} accounts")

        # Find tickers with non-zero allocations
        # TODO: use this to simplify the optimization problem
        active_tickers = self.getMetrics('Ticker')['Allocation']
        active_tickers = active_tickers[active_tickers > 0].index

        if verbose:
            print("\nActive tickers:")
            print(f"Found {len(active_tickers)} tickers with non-zero allocations")
            print("\n".join(sorted(active_tickers)))

        # Create optimization components for each account
        account_components = {}
        for account in accounts:
            try:
                components = self._create_account_optimization_components(
                    account=account,
                    target_factor_allocations=target_factor_allocations,
                    min_ticker_alloc=min_ticker_alloc,
                    verbose=verbose
                )
                account_components[account] = components
            except Exception as e:
                raise RuntimeError(f"Failed to create optimization components for account {account}: {str(e)}")

        # Create sub-objectives
        account_factor_objective = sum(
            components['objectives']['factor']
            for components in account_components.values()
        )
        account_turnover_objective = sum(
            components['objectives']['turnover']
            for components in account_components.values()
        )
        account_complexity_objective = sum(
            components['objectives']['complexity']
            for components in account_components.values()
        )

        # Create portfolio-level factor objective
        portfolio_factor_allocations = sum(
            components['factor_allocations']
            for components in account_components.values()
        )
        portfolio_factor_objective = cp.sum_squares(
            portfolio_factor_allocations - target_factor_allocations.to_numpy()
        )

        # Combine objectives with penalties
        objective = cp.Minimize(
            portfolio_factor_objective +
            account_align_penalty * account_factor_objective +
            turnover_penalty * account_turnover_objective +
            complexity_penalty * account_complexity_objective
        )

        # Combine all account constraints
        constraints = []
        for components in account_components.values():
            constraints.extend(components['constraints'])

        # Add portfolio-level constraint: sum of all allocations equals 100%
        portfolio_sum = sum(
            cp.sum(components['variables']['x'])
            for components in account_components.values()
        )
        constraints.append(portfolio_sum == 1.0)

        # Create and solve the optimization problem
        problem = cp.Problem(objective, constraints)
        try:
            problem.solve(solver=cp.SCIP, verbose=verbose)
        except Exception as e:
            raise RuntimeError(f"Optimization failed: {str(e)}")

        if problem.status != 'optimal':
            raise RuntimeError(f"Optimization failed with status: {problem.status}")

        # Extract results and create DataFrames

        # Sum allocations across accounts using pandas concat
        account_allocations = pd.concat([
            pd.Series(components['variables']['x'].value.flatten(), index=F.columns)
            for components in account_components.values()
        ], axis=1, keys=account_components.keys())

        if verbose:
            print("\nAccount allocations:")
            # Add a totals row and column properly
            with_totals = account_allocations.copy()
            # Add totals column
            with_totals['Total'] = with_totals.sum(axis=1)
            # Add totals row
            with_totals.loc['Total'] = with_totals.sum()
            print(with_totals.to_string(float_format=lambda x: f"{x:.2%}"))

        # Sum account allocations (columns) to get portfolio allocations
        new_allocations = account_allocations.sum(axis=1)

        # Create ticker results DataFrame aligned with canonical matrix
        ticker_results = pd.DataFrame(index=F.columns)
        ticker_results['Original Allocation'] = pd.Series(
            self.getMetrics('Ticker', portfolio_allocation=True)['Allocation']
        ).reindex(index=F.columns, fill_value=0.0)
        ticker_results['New Allocation'] = new_allocations
        ticker_results['Allocation Diff'] = ticker_results['New Allocation'] - ticker_results['Original Allocation']

        # Create factor results DataFrame aligned with canonical matrix
        factor_results = pd.DataFrame(index=F.index)
        factor_results['Original Allocation'] = pd.Series(
            self.getMetrics('Factor')['Allocation']
        ).reindex(index=F.index, fill_value=0.0)
        factor_results['New Allocation'] = F @ new_allocations
        factor_results['Target Allocation'] = target_factor_allocations
        factor_results['Allocation Diff'] = factor_results['New Allocation'] - factor_results['Target Allocation']

        if verbose:
            print("\nOptimization complete")
            print(f"Objective value: {problem.value:.6f}")
            print(f"Status: {problem.status}")

        return ticker_results, factor_results

    def _write_weights(self, weights: Union[pd.DataFrame, pd.Series], title: str = None):
        """Display weights (factor matrix or allocation vector) in a formatted table.

        Args:
            weights: Either a factor weights DataFrame from getCanonicalFactorWeightsMatrix()
                    or an allocation Series
            title: Optional title to display above the table
        """
        if title:
            print(f"\n{title}")

        # Create column formats dictionary
        column_formats = {
            'Factor': {'width': 30}  # Format for index column
        }

        # Get columns to format (either DataFrame columns or Series name)
        value_columns = weights.columns if isinstance(weights, pd.DataFrame) else [weights.name]

        # Add formats for all value columns
        column_formats.update({
            col: {'width': 8, 'type': '%', 'decimal': 2}
            for col in value_columns
        })

        # Write the formatted table
        write_table(weights, columns=column_formats)