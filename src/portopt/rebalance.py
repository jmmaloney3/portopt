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
from .utils import write_table, write_weights

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

    def _create_factor_weights_matrix(
        self,
        factors: pd.Index,
        tickers: Union[list, pd.Index],
        verbose: bool = False
    ) -> pd.DataFrame:
        """Create a factor weights matrix for a specific account using reference lists.

        The matrix will:
        1. Include only the specified factors and tickers
        2. Sort factors and tickers according to the reference lists
        3. Fill any missing values with 0
        4. Include 'Factor' as a named index

        Args:
            factors: Index of factors to include in canonical order (must be pre-sorted)
            tickers: List or Index of tickers to include in canonical order (must be pre-sorted)
            verbose: If True, print information about the matrix construction

        Returns:
            DataFrame with factors as rows (indexed by 'Factor') and tickers as columns,
            ordered according to the reference lists

        Raises:
            AssertionError: If factors or tickers are not in the specified order
        """
        if verbose:
            print("\n==> _create_factor_weights_matrix()")

        if verbose:
            print(f" - Number of factors: {len(factors)}")
            print(f" - Number of tickers: {len(tickers)}")

        # Convert tickers to Index if it's a list
        if isinstance(tickers, list):
            tickers = pd.Index(tickers)

        # Get raw factor weights
        factor_weights = self.getFactorWeights()

        # Create pivot table with specified ordering
        F = pd.pivot_table(
            factor_weights,
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Reindex to include only specified factors and tickers in specified order
        F = F.reindex(index=factors, columns=tickers, fill_value=0)

        # Explicitly name the index
        F.index.name = 'Factor'

        # Validate ordering
        assert F.index.equals(factors), "Factors are not in specified order"
        assert F.columns.equals(tickers), "Tickers are not in specified order"

        if verbose:
            print("\nAccount-specific factor weights matrix F:")
            print(f" - Shape: {F.shape}")
            write_weights(F)
            print("\n<== _create_factor_weights_matrix()")

        return F

    def _create_variable_vectors(
        self,
        tickers: list,
        account: str = None,
        verbose: bool = False
    ) -> Dict[str, cp.Variable]:
        """Create variable vectors for a specific account.

        Args:
            tickers: List of tickers in canonical order
            account: Optional account name to include in variable names
            verbose: If True, print information about the variables created

        Returns:
            Dictionary containing:
                'x': Vstack of allocation variables
                'z': Vstack of binary selection variables
            Variables are ordered to match the reference ticker list

        Raises:
            AssertionError: If variable ordering doesn't match reference ticker list
        """
        if verbose:
            print("\n==> _create_variable_vectors()")

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

        # Validate variable alignment with reference ticker list
        assert all(x_vars[i].name().split('_')[-1] == ticker
                  for i, ticker in enumerate(tickers)), \
            "Variable order does not match reference ticker list"

        # Stack variables into vectors
        variables = {
            'x': cp.vstack(x_vars),  # Allocation percentages
            'z': cp.vstack(z_vars)   # Binary selection variables
        }

        if verbose:
            # Create a DataFrame with two columns for allocation and selection variables
            variable_df = pd.DataFrame({
                'Allocation Variables (x)': [var.name() for var in x_vars],
                'Selection Variables (z)': [var.name() for var in z_vars]
            })

            # Define column formats for write_table
            column_formats = {
                'Allocation Variables (x)': {'width': 30},
                'Selection Variables (z)': {'width': 30}
            }

            # Print the table using write_table
            print("\nVariables:")
            write_table(variable_df, columns=column_formats)
            print("\n<== _create_variable_vectors()")

        return variables

    def _create_target_factor_allocations_vector(
        self,
        target_allocations: pd.Series,
        account_proportion: float = 1.0,
        verbose: bool = False
    ) -> pd.Series:
        """Create a target factor allocations vector aligned with the reference factor list.

        Args:
            target_allocations: Series indexed by Factor containing target allocation
                percentages for the entire portfolio
            account_proportion: The proportion of the portfolio that the account represents
            verbose: If True, print information about the vector creation

        Returns:
            Series indexed by Factor containing target allocations, aligned with
            reference factor list. Values are scaled to represent the account's
            portion of the total portfolio.

        Raises:
            ValueError: If target allocations don't sum to 100%
            AssertionError: If resulting series is not aligned with reference list
        """
        if verbose:
            print("\n==> _create_target_factor_allocations_vector()")

        # Validate original allocations sum to 100%
        total_allocation = target_allocations.sum()
        if not np.isclose(total_allocation, 1.0, rtol=1e-5):
            raise ValueError(
                f"Target allocations must sum to 100%, got {total_allocation:.2%}"
            )

        # Create new series with all factors from reference list
        result = pd.Series(
            0.0, 
            index=target_allocations.index,
            name=target_allocations.name  # Preserve original Series name
        )
        result.index.name = 'Factor'  # Set name for the index

        # Fill in provided target allocations
        result.update(target_allocations)

        # Scale allocations by account proportion
        if account_proportion != 1.0:
            if verbose:
                print(f"\nScaling target allocations")
                print(f" - Account proportion of portfolio: {account_proportion:.2%}")

            # Scale all allocations by account proportion
            result *= account_proportion

        # Validate resulting allocations sum appropriately
        total_allocation = result.sum()
        if not np.isclose(total_allocation, account_proportion, rtol=1e-5):
            raise ValueError(
                f"Resulting allocations must sum to {account_proportion:.2%}, got {total_allocation:.2%}"
            )

        # Validate alignment with reference list
        assert result.index.equals(target_allocations.index), \
            "Result factors not aligned with reference list"
        assert list(result.index) == list(target_allocations.index), \
            "Result factors not in same order as reference list"

        if verbose:
            # Create DataFrame to display allocations
            allocation_df = pd.DataFrame({
                'Factor': result.index,
                'Orig Alloc': target_allocations,
                'New Alloc': result,
                'Diff': result - target_allocations,
            })
            allocation_df.set_index('Factor', inplace=True)

            # Define column formats for write_table
            column_formats = {
                'Factor': {'width': 30},
                'Orig Alloc': {'width': 10, 'type': '%', 'decimal': 2},
                'New Alloc': {'width': 10, 'type': '%', 'decimal': 2},
                'Diff': {'width': 10, 'type': '%', 'decimal': 2},
            }

            print("\nTarget Allocation Changes:")
            write_table(allocation_df, columns=column_formats)

            print("\n<== _create_target_factor_allocations_vector()")

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
                allocation percentages - defines the canonical order of factors
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
            print(f"\n==> _create_account_optimization_components()")
            print(f" - Account: {account}")

        # Verify account exists
        account_tickers = self.getAccountTickers()
        if account not in account_tickers.index.get_level_values('Account').unique():
            raise ValueError(f"Account '{account}' not found in portfolio. Available accounts: "
                            f"{account_tickers.index.get_level_values('Account').unique().tolist()}")

        # Get account-specific tickers in canonical order
        account_tickers = account_tickers[account_tickers.index.get_level_values('Account') == account]
        account_tickers = account_tickers.index.get_level_values('Ticker').unique()
        account_tickers = pd.Index(sorted(account_tickers))

        # Get current ticker allocations aligned with account tickers
        current_ticker_allocations = self._create_current_allocations_vector(
            account=account,
            tickers=account_tickers,
            verbose=verbose
        )

        # Create account-specific factor weights matrix
        F = self._create_factor_weights_matrix(
            factors=target_factor_allocations.index,
            tickers=account_tickers,
            verbose=verbose
        )

        # Get account's current allocation as percentage of total portfolio
        account_metrics = self.getMetrics('Account', portfolio_allocation=True)
        account_proportion = account_metrics.loc[account, 'Allocation']

        # Create target allocations vector aligned with factors
        target_factor_allocations = self._create_target_factor_allocations_vector(
            target_allocations=target_factor_allocations,
            account_proportion=account_proportion,
            verbose=verbose
        )

        # Create variable vectors
        variables = self._create_variable_vectors(
            account=account,
            tickers=account_tickers,
            verbose=verbose
        )

        # Calculate account's factor allocations using factor weights matrix
        account_factor_allocations = F.to_numpy() @ variables['x']

        if verbose:
            print("\nCreating objectives...")

        # Create objective components
        objectives = {
            # factor objective: minimize difference between account factor allocations and target factor allocations
            'factor': cp.sum_squares(account_factor_allocations - target_factor_allocations.to_numpy()),
            # turnover objective: minimize difference between current and new ticker allocations
            'turnover': cp.sum_squares(variables['x'] - current_ticker_allocations.to_numpy()),
            # complexity objective: minimize number of funds used
            'complexity': cp.sum(variables['z'])
        }

        if verbose:
            print(f"\nFactor objective for account {account}:")
            self._write_objective(objectives['factor'], target_factor_allocations=target_factor_allocations)

            # For turnover objective, just print the expression
            print(f"\nTurnover objective for account {account}:")
            print(" - Minimize difference between current and new ticker allocations")
            # - this verbose output does not yet work
            # self._write_turnover_objective(objectives['turnover'], current_allocations=current_ticker_allocations)

            # For complexity objective, just print the expression
            print(f"\nComplexity objective for account {account}:")
            print(" - Minimize number of funds used")

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
            print(f"<== _create_account_optimization_components()")

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
                allocation percentages - defines the canonical order of factors
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
            write_weights(target_factor_allocations, "Input target allocations:")
            print(f"\nOptimizing allocations for {len(accounts)} accounts")

        # Get list of accounts
        accounts = self.getAccountTickers().index.get_level_values('Account').unique()
        if verbose:
            print(f"\nOptimizing allocations for {len(accounts)} accounts")

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

        if verbose:
            self._write_objective(
                portfolio_factor_objective,
                target_factor_allocations=target_factor_allocations,
                title="Portfolio-level factor objective:"
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

        # Get original ticker allocations by account
        original_ticker_allocations = self.getMetrics(
            'Account', 'Ticker',
            metrics=['Allocation'],
            portfolio_allocation=True
        )['Allocation']

        # Get original factor allocations by account
        original_factor_allocations = self.getMetrics(
            'Account', 'Factor',
            metrics=['Allocation'],
            portfolio_allocation=True
        )['Allocation']

        # Create ticker results DataFrame
        ticker_results = []
        for account, components in account_components.items():
            # Get account-specific tickers in canonical order
            account_tickers = components['variables']['x'].name().split('_')[1:]

            # Get original allocations for this account's tickers
            # - reindex with account_tickers so that the original allocations
            #   are in the same order as the variables
            account_original_allocations = original_ticker_allocations.loc[account].reindex(account_tickers, fill_value=0.0)

            # Get new allocations from optimizer
            # - account_tickers were extracted from the variable names and therefore
            #   the tickers and variables values are in the same order
            account_new_allocations = pd.Series(
                components['variables']['x'].value.flatten(),
                index=account_tickers
            )

            # Create DataFrame for this account's tickers
            account_df = pd.DataFrame({
                'Account': account,
                'Ticker': account_tickers,
                'Original Allocation': account_original_allocations,
                'New Allocation': account_new_allocations,
            })
            ticker_results.append(account_df)

        # Combine all account ticker results
        ticker_results = pd.concat(ticker_results, ignore_index=True)
        ticker_results['Difference'] = ticker_results['New Allocation'] - ticker_results['Original Allocation']

        # Create factor results DataFrame
        factor_results = []
        for account, components in account_components.items():
            # Get original allocations for this account's factors
            account_original_allocations = original_factor_allocations.loc[account].reindex(
                target_factor_allocations.index,
                fill_value=0.0
            )

            # Get new allocations from optimizer
            # - target_factor_allocations.index was used to create the factor weights matrix
            #   that was used to create the factor allocations, therefore the factor allocations
            #   are in the same order as the target_factor_allocations index
            account_new_allocations = pd.Series(
                components['factor_allocations'].value.flatten(),
                index=target_factor_allocations.index
            )

            # Create DataFrame for this account's factors
            account_df = pd.DataFrame({
                'Account': account,
                'Factor': target_factor_allocations.index,
                'Original Allocation': account_original_allocations,
                'New Allocation': account_new_allocations,
            })
            factor_results.append(account_df)

        # Combine all account factor results
        factor_results = pd.concat(factor_results, ignore_index=True)
        factor_results['Difference'] = factor_results['New Allocation'] - factor_results['Original Allocation']

        if verbose:
            # Define column formats for both DataFrames
            column_formats = {
                'Account': {'width': 20},
                'Ticker': {'width': 20},
                'Factor': {'width': 30},
                'Original Allocation': {'width': 15, 'type': '%', 'decimal': 2},
                'New Allocation': {'width': 15, 'type': '%', 'decimal': 2},
                'Difference': {'width': 15, 'type': '%', 'decimal': 2}
            }

            print("\nTicker Allocations:")
            write_table(ticker_results, columns=column_formats)

            print("\nFactor Allocations:")
            write_table(factor_results, columns=column_formats)

            print("\nOptimization complete")
            print(f"Objective value: {problem.value:.6f}")
            print(f"Status: {problem.status}")

        return ticker_results, factor_results

    def _write_objective(self, objective: cp.atoms.quad_over_lin, target_factor_allocations: pd.Series = None, title: str = None):
        """Display components of a sum_squares objective function in a table.

        Args:
            objective: CVXPY sum_squares expression (typically F @ x - target)
            target_factor_allocations: Series containing target allocations with factor names as index
            title: Optional title to display above the table

        Example output for F @ x - target:
        Factor                           AAPL     MSFT     GOOGL    Target
        US Large Cap Growth             0.95%    0.92%    0.88%    25.00%
        Technology                      0.85%    0.90%    0.75%    30.00%
        Momentum                        0.45%    0.38%    0.42%    15.00%
        """
        if title:
            print(f"\n{title}")

        # Extract the expression inside sum_squares
        expr = objective.args[0]  # This is the AddExpression (F @ x - target)

        # Get components from matrix multiplication
        matrix_mult = expr.args[0].args[0]
        F = matrix_mult.args[0]  # Get F matrix
        x = matrix_mult.args[1]  # Get x vector (Vstack of variables)

        # Extract variable names from the Vstack
        var_names = [v.name().split('_')[-1] for v in x.args]

        # Create DataFrame with factor weights, using factor names from target allocations
        df = pd.DataFrame(
            F.value,
            columns=var_names,
            index=target_factor_allocations.index
        )
        df.index.name = 'Factor'

        # Second argument contains -target (broadcast_to)
        target = -expr.args[1].args[0]  # Get target vector and negate it
        df['Target'] = target.value

        # Create column formats
        column_formats = {
            'Factor': {'width': 30},  # Index column
            **{col: {'width': 8, 'type': '%', 'decimal': 2}
               for col in df.columns}  # All value columns as percentages
        }

        # Write the table
        write_table(df, columns=column_formats)

    def _write_turnover_objective(self, objective: cp.atoms.quad_over_lin, current_allocations: pd.Series, title: str = None):
        """Display components of a turnover objective function in a table.

        NOTE: This method is a work in progress and is not yet ready for use.

        Args:
            objective: CVXPY sum_squares expression (typically x - current_allocations)
            current_allocations: Series containing current allocations with ticker names as index
            title: Optional title to display above the table

        Example output:
        Ticker    Variable Ticker    Current Allocation
        ACWX     ACWX              18.54%
        AMAXX    AMAXX             25.83%
        FSMDX    FSMDX              2.92%
        """
        if title:
            print(f"\n{title}")

        # Extract the expression inside sum_squares
        expr = objective.args[0]  # This is the AddExpression

        # Get components
        x = expr.args[0].args[0]  # Variable vector (Vstack inside broadcast_to)
        current = expr.args[1].args[0]  # Current allocations vector (NegExpression inside broadcast_to)

        # Extract variable tickers from the Vstack
        var_tickers = [v.name().split('_')[-1] for v in x.args]

        # Get current values (negated because it's a NegExpression)
        current_values = -current.value

        # Validate length matches
        if len(current_values) != len(current_allocations):
            raise ValueError(f"Mismatch between number of current values ({len(current_values)}) "
                           f"and current allocations ({len(current_allocations)})")

        # Create DataFrame showing alignment
        df = pd.DataFrame({
            'Variable Ticker': var_tickers,
            'Current Allocation': current_values
        }, index=current_allocations.index)
        df.index.name = 'Ticker'

        # Define column formats
        column_formats = {
            'Ticker': {'width': 20, 'type': 's'},  # Index column
            'Variable Ticker': {'width': 20, 'type': 's'},
            'Current Allocation': {'width': 15, 'type': '%', 'decimal': 2}
        }

        # Write the table
        write_table(df, columns=column_formats)

    def _create_current_allocations_vector(
        self,
        account: str,
        tickers: list,
        verbose: bool = False
    ) -> pd.Series:
        """Create a current allocations vector aligned with the reference ticker list.

        Args:
            account: Account identifier
            tickers: List of tickers in canonical order
            verbose: If True, print information about the vector creation

        Returns:
            Series indexed by Ticker containing current allocations, aligned with
            the reference ticker list. Missing tickers are filled with 0.

        Raises:
            ValueError: If account is not found in portfolio
        """
        if verbose:
            print("\n==> _create_current_allocations_vector()")

        # Verify account exists
        account_tickers = self.getAccountTickers()
        if account not in account_tickers.index.get_level_values('Account').unique():
            raise ValueError(f"Account '{account}' not found in portfolio. Available accounts: "
                            f"{account_tickers.index.get_level_values('Account').unique().tolist()}")

        # Get current ticker allocations for this account
        current_allocations = self.getMetrics('Ticker',
                                            filters={'Account': account},
                                            portfolio_allocation=True
                                            )['Allocation']

        # Create new series with all tickers from reference list
        result = pd.Series(
            0.0,
            index=tickers,
            name=current_allocations.name  # Preserve original Series name
        )
        result.index.name = 'Ticker'  # Set name for the index

        # Fill in current allocations
        result.update(current_allocations)

        if verbose:
            print("\nCurrent allocations:")
            print(f" - Number of tickers: {len(tickers)}")
            print(f" - Number of non-zero allocations: {(result > 0).sum()}")
            print(f" - Total allocation: {result.sum():.2%}")

            # Create DataFrame to display allocations
            allocation_df = pd.DataFrame({
                'Ticker': result.index,
                'Current Allocation': result,
            })
            allocation_df.set_index('Ticker', inplace=True)

            # Define column formats for write_table
            column_formats = {
                'Ticker': {'width': 20},
                'Current Allocation': {'width': 15, 'type': '%', 'decimal': 2},
            }

            print("\nCurrent Allocations:")
            write_table(allocation_df, columns=column_formats)
            print("\n<== _create_current_allocations_vector()")

        return result

class PortfolioRebalancer:
    """
    Helper class for managing portfolio rebalancing optimization components.

    This class maintains the portfolio-level components needed for rebalancing,
    including the factor weights matrix and target allocations. It ensures
    consistent ordering of factors and tickers across all operations.

    Attributes:
        target_factor_allocations: Series containing target factor allocations
        factor_weights: DataFrame containing factor weights for all tickers
        min_ticker_alloc: Minimum allocation for any ticker (default: 0.0)
    """

    def __init__(
        self,
        target_factor_allocations: pd.Series,
        factor_weights: pd.DataFrame,
        min_ticker_alloc: float = 0.0,
        verbose: bool = False
    ):
        """
        Initialize the PortfolioRebalancer.

        Args:
            target_factor_allocations: Series indexed by Factor containing target
                allocation percentages - defines the canonical order of factors
            factor_weights: DataFrame with hierarchical index [Ticker, Factor]
                containing factor weights for each ticker
            min_ticker_alloc: Minimum non-zero allocation for any fund (default: 0.0)
            verbose: If True, print detailed information about initialization

        Raises:
            ValueError: If target allocations don't sum to 100%
            ValueError: If any target factors are missing from factor weights
        """
        if verbose:
            print("\n==> PortfolioRebalancer.__init__()")

        # Validate target allocations sum to 100%
        if not np.isclose(target_factor_allocations.sum(), 1.0, rtol=1e-5):
            raise ValueError(
                f"Target factor allocations must sum to 100%, got {target_factor_allocations.sum():.2%}"
            )

        # Store inputs
        self.target_factor_allocations = target_factor_allocations
        self.min_ticker_alloc = min_ticker_alloc

        if verbose:
            write_weights(target_factor_allocations, title="Target Factor Allocations")
            print(f"\nMinimum Ticker Allocation: {min_ticker_alloc:.2%}")

        # Create master factor weights matrix:
        # 1. Pivot factor weights to get matrix form (factors x tickers)
        # 2. Reindex to match target factor order and include all tickers
        # 3. Fill missing values with 0
        self.factor_weights = pd.pivot_table(
            factor_weights,
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Verify all target factors exist in factor weights
        missing_factors = set(target_factor_allocations.index) - set(self.factor_weights.index)
        if missing_factors:
            raise ValueError(
                f"Target factors not found in factor weights: {sorted(missing_factors)}"
            )

        # Reindex to ensure:
        # - rows (factors): match target_factor_allocations order exactly
        # - columns (tickers): include all tickers from factor_weights
        self.factor_weights = self.factor_weights.reindex(
            index=target_factor_allocations.index,  # Use target factor order
            columns=factor_weights.index.get_level_values('Ticker').unique(),
            fill_value=0
        )

        if verbose:
            write_weights(self.factor_weights, title="Factor Weights Matrix")

        # Validate matrix shape
        assert self.factor_weights.shape[0] == len(target_factor_allocations), \
            "Factor weights matrix rows don't match target factor count"
        assert self.factor_weights.shape[1] > 0, \
            "Factor weights matrix has no tickers"

        if verbose:
            print("\n<== PortfolioRebalancer.__init__()")