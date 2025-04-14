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
        account_ticker_allocations: DataFrame with hierarchical index [Account, Ticker]
            containing current allocation percentages for each account-ticker pair
        target_factor_allocations: Series containing target factor allocations
        factor_weights: DataFrame containing factor weights for all tickers
        min_ticker_alloc: Minimum allocation for any ticker (default: 0.0)
        accounts: DataFrame indexed by Account and containing the proportion
            of the portfolio held in each account
    """

    def __init__(
        self,
        account_ticker_allocations: pd.DataFrame,
        target_factor_allocations: pd.Series,
        factor_weights: pd.DataFrame,
        min_ticker_alloc: float = 0.0,
        turnover_penalty: float = 1.0,
        complexity_penalty: float = 0.0,
        account_align_penalty: float = 1.0,
        verbose: bool = False
    ):
        """
        Initialize the PortfolioRebalancer.

        Args:
            account_ticker_allocations: DataFrame with hierarchical index [Account, Ticker]
                containing current allocation percentages for each account-ticker pair
            target_factor_allocations: Series indexed by Factor containing target
                allocation percentages - defines the canonical order of factors
            factor_weights: DataFrame with hierarchical index [Ticker, Factor]
                containing factor weights for each ticker
            min_ticker_alloc: Minimum non-zero allocation for any fund (default: 0.0)
            account_align_penalty: Weight for penalizing account-level factor
                misalignment - applied to factor objective (default: 1.0)
            turnover_penalty: Weight for penalizing changes from current allocations
                (default: 1.0)
            complexity_penalty: Weight for penalizing the number of funds used
                (default: 0.0)
            verbose: If True, print detailed information about initialization

        Raises:
            ValueError: If target allocations don't sum to 100%
            ValueError: If any target factors are missing from factor weights
            ValueError: If account_ticker_allocations doesn't have the correct index structure
            ValueError: If account_ticker_allocations doesn't sum to 100% across all account-ticker pairs
        """
        if verbose:
            print("\n==> PortfolioRebalancer.__init__()")

        # Validate account_ticker_allocations structure
        if not isinstance(account_ticker_allocations.index, pd.MultiIndex):
            raise ValueError(
                "account_ticker_allocations must have a MultiIndex with levels [Account, Ticker]"
            )
        if account_ticker_allocations.index.names != ['Account', 'Ticker']:
            raise ValueError(
                "account_ticker_allocations index names must be ['Account', 'Ticker']"
            )

        # Validate account_ticker_allocations sum to 100%
        total_allocation = account_ticker_allocations.sum()
        if not np.isclose(total_allocation, 1.0, rtol=1e-5):
            raise ValueError(
                f"Account ticker allocations must sum to 100%, got {total_allocation:.2%}"
            )

        # Validate target allocations sum to 100%
        if not np.isclose(target_factor_allocations.sum(), 1.0, rtol=1e-5):
            raise ValueError(
                f"Target factor allocations must sum to 100%, got {target_factor_allocations.sum():.2%}"
            )

        # Store inputs
        self.account_ticker_allocations = account_ticker_allocations
        self._target_factor_allocations = target_factor_allocations
        self.min_ticker_alloc = min_ticker_alloc
        self._turnover_penalty = turnover_penalty
        self._complexity_penalty = complexity_penalty
        self._account_align_penalty = account_align_penalty

        if verbose:
            write_weights(self.account_ticker_allocations, title="Account Ticker Allocations")
            write_weights(self._target_factor_allocations, title="Target Factor Allocations")
            print(f"\nMinimum Ticker Allocation: {min_ticker_alloc:.2%}")
            print(f"Turnover Penalty: {self._turnover_penalty}")
            print(f"Complexity Penalty: {self._complexity_penalty}")
            print(f"Account Align Penalty: {self._account_align_penalty}")

        # Initialize factor weights matrix
        self._init_factor_weights_matrix(factor_weights=factor_weights, verbose=verbose)

        # Initialize account registry
        self._init_account_registry(verbose=verbose)

        if verbose:
            print("\n<== PortfolioRebalancer.__init__()")

    def _init_factor_weights_matrix(self,
                                    factor_weights: pd.DataFrame,
                                    verbose: bool = False) -> None:
        """Initialize the factor weights matrix.

        Creates a master factor weights matrix from the input factor weights DataFrame.
        This matrix is used to map factor allocations to ticker allocations.  The
        columns in this matrix provide the canonical order for the tickers.
        """
        # Create master factor weights matrix:
        # 1. Pivot factor weights to get matrix form (factors x tickers)
        # 2. Reindex to match target factor order and include all tickers
        # 3. Fill missing values with 0
        self._factor_weights = pd.pivot_table(
            factor_weights,
            values='Weight',
            index='Factor',
            columns='Ticker',
            fill_value=0
        )

        # Verify all target factors exist in factor weights
        missing_factors = set(self.getPortfolioFactors()) - set(self._factor_weights.index)
        if missing_factors:
            raise ValueError(
                f"Target factors not found in factor weights: {sorted(missing_factors)}"
            )

        # Reindex to ensure:
        # - rows (factors): match self._target_factor_allocations order exactly
        # - columns (tickers): include all tickers from factor_weights
        self._factor_weights = self._factor_weights.reindex(
            index=self.getPortfolioFactors(),  # Use target factor order
            columns=factor_weights.index.get_level_values('Ticker').unique(),
            fill_value=0
        )

        if verbose:
            write_weights(self._factor_weights, title="Factor Weights Matrix")

        # Validate matrix shape
        assert self._factor_weights.shape[0] == len(self._target_factor_allocations), \
            "Factor weights matrix rows don't match target factor count"
        assert self._factor_weights.shape[1] > 0, \
            "Factor weights matrix has no tickers"

    def _init_account_registry(self, verbose: bool = False) -> None:
        """Initialize the account registry.

        Creates a DataFrame that serves as the master registry for all accounts,
        containing their proportions and AccountRebalancer instances.

        Args:
            verbose: If True, print detailed information about initialization

        Returns:
            None
        """
        if verbose:
            print("\n==> _init_account_registry()\n")

        # Create DataFrame indexed by Account with account proportions
        proportions = self.account_ticker_allocations.groupby(level='Account').sum()
        proportions.name = 'Proportion'

        # Create empty DataFrame with account names as index
        self._account_registry = pd.DataFrame(index=proportions.index)
        self._account_registry.index.name = 'Account'

        # Add proportion column
        self._account_registry['Proportion'] = proportions

        # Create AccountRebalancer instances and store them
        self._account_registry['Rebalancer'] = [
            AccountRebalancer(
                port_rebalancer=self,
                account=account,
                verbose=verbose
            )
            for account in self._account_registry.index
        ]

        if verbose:
            print(f"\nAccount Registry:")
            print(f" - Number of accounts: {len(self._account_registry)}")
            print(f" - Total proportion: {self._account_registry['Proportion'].sum():.2%}")
            write_weights(self._account_registry['Proportion'])
            print("\n<== _init_account_registry()")

    def getAccountProportion(self, account: str) -> float:
        """Get the proportion of the portfolio held in a specific account.

        Args:
            account: Name of the account to get the proportion for

        Returns:
            float: The proportion of the portfolio held in the specified account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        if account not in self.getAccounts():
            raise ValueError(
                f"Account '{account}' not found in portfolio. Available accounts: "
                f"{self.getAccounts()}"
            )
        return self._account_registry.loc[account, 'Proportion']

    def getAccounts(self) -> list[str]:
        """Get the list of accounts being rebalanced.

        Returns:
            list[str]: List of account names in the portfolio
        """
        return self._account_registry.index

    def getAccountRebalancer(self, account: str) -> 'AccountRebalancer':
        """Get the AccountRebalancer instance for a specific account.

        Args:
            account: Name of the account to get the rebalancer for

        Returns:
            AccountRebalancer: The AccountRebalancer instance for the specified account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        if account not in self.getAccounts():
            raise ValueError(
                f"Account '{account}' not found in portfolio. Available accounts: "
                f"{self.getAccounts()}"
            )
        return self._account_registry.loc[account, 'Rebalancer']

    def getPortfolioTickers(self, verbose: bool = False) -> pd.Index:
        """Get all tickers in the portfolio in canonical order.

        The canonical order is determined by the order of tickers in the factor weights
        matrix. This ensures consistent ordering between:
        - Factor weights matrix columns
        - Optimization variables
        - Current allocation vectors

        Args:
            verbose: If True, print detailed information about the tickers

        Returns:
            pd.Index: Index containing all tickers in canonical order
        """
        tickers = self.getPortfolioFactorWeights(verbose=verbose).columns

        if verbose:
            print("\nPortfolio tickers:")
            print(f" - Number of tickers: {len(tickers)}")
            print(f" - Tickers: {sorted(tickers.tolist())}")

        return tickers

    def getAccountTickers(self, account: str) -> pd.Index:
        """Get the tickers for a specific account in canonical order.

        The canonical order is determined by the order of tickers in the factor weights
        matrix. This ensures consistent ordering between:
        - Factor weights matrix columns
        - Optimization variables
        - Current allocation vectors

        Args:
            account: Name of the account to get tickers for

        Returns:
            pd.Index: Index containing tickers in canonical order that exist in the account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        if account not in self.getAccounts():
            raise ValueError(
                f"Account '{account}' not found in portfolio. Available accounts: "
                f"{self.getAccounts()}"
            )

        # Get all tickers in canonical order from factor weights matrix
        canonical_tickers = self.getPortfolioTickers()

        # Get tickers that exist in this account
        account_tickers = self.account_ticker_allocations.xs(
            account, level='Account'
        ).index

        # Filter canonical tickers to only include those in the account
        # This preserves the canonical order while only including relevant tickers
        return pd.Index([ticker for ticker in canonical_tickers if ticker in account_tickers])

    def getAccountTickerResults(self, account: str) -> pd.DataFrame:
        """Get the ticker allocation results for a specific account.

        Delegates to the AccountRebalancer instance for the specified account.

        Args:
            account: Name of the account to get results for

        Returns:
            pd.DataFrame: DataFrame indexed by ticker (in canonical order) containing:
                - Original Allocation: Current allocation percentages

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        if account not in self.getAccounts():
            raise ValueError(
                f"Account '{account}' not found in portfolio. Available accounts: "
                f"{self.getAccounts()}"
            )

        return self.getAccountRebalancer(account).getTickerResults()

    def getAccountTickerAllocation(self, account: str) -> pd.Series:
        """Get the current ticker allocations for an account in canonical order.

        Args:
            account: Name of the account to get allocations for

        Returns:
            pd.Series: Series indexed by ticker containing current allocation percentages,
                      ordered according to the canonical ticker order

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        if account not in self.getAccounts():
            raise ValueError(
                f"Account '{account}' not found in portfolio. Available accounts: "
                f"{self.getAccounts()}"
            )

        # Get current allocations for this account
        account_allocations = self.account_ticker_allocations.xs(
            account, level='Account'
        )['Allocation']  # Extract the Allocation column as a Series

        # Get tickers in canonical order
        canonical_tickers = self.getAccountTickers(account)

        # Create new series with canonical ordering
        result = pd.Series(
            0.0,  # Default to 0 for any missing tickers
            index=canonical_tickers,
            name='Allocation'  # Use consistent name for the allocation column
        )

        # Fill in current allocations
        result.update(account_allocations)

        return result

    def getAccountVariables(self, account: str, verbose: bool = False) -> Dict[str, cp.Variable]:
        """Get optimization variables for a specific account.

        Delegates to the AccountRebalancer instance for the specified account.

        Args:
            account: Name of the account to get variables for
            verbose: If True, print detailed information about the variables created

        Returns:
            Dict[str, cp.Variable]: Dictionary containing:
                'x': Vstack of allocation variables
                'z': Vstack of binary selection variables
            Variables are ordered to match the canonical ticker order

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getVariables(verbose=verbose)

    def getAccountFactorWeights(self, account: str, verbose: bool = False) -> pd.DataFrame:
        """Get the factor weights matrix for a specific account.

        Delegates to the AccountRebalancer instance for the specified account.

        Args:
            account: Name of the account to get factor weights for
            verbose: If True, print detailed information about the matrix

        Returns:
            pd.DataFrame: Factor weights matrix with:
                - Rows: Factors (in same order as parent portfolio)
                - Columns: Tickers (in canonical order for this account)
                - Values: Factor weights

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getFactorWeights(verbose=verbose)

    def getPortfolioTargetFactorAllocations(self, verbose: bool = False) -> pd.Series:
        """Get the portfolio's target factor allocations.

        Returns the target factor allocations for the entire portfolio, ensuring
        they are in canonical order and sum to 100%.

        Args:
            verbose: If True, print detailed information about the allocations

        Returns:
            pd.Series: Series indexed by Factor containing target allocation percentages,
                      ordered according to the canonical factor order

        Raises:
            ValueError: If target allocations don't sum to 100%
        """
        # Validate allocations sum to 100%
        total_allocation = self._target_factor_allocations.sum()
        if not np.isclose(total_allocation, 1.0, rtol=1e-5):
            raise ValueError(
                f"Target factor allocations must sum to 100%, got {total_allocation:.2%}"
            )

        if verbose:
            print("\nPortfolio target factor allocations:")
            print(f" - Number of factors: {len(self._target_factor_allocations)}")
            print(f" - Total allocation: {total_allocation:.2%}")
            write_weights(self._target_factor_allocations)

        # The target factor allocations supplied to the constructor defines the
        # canonical order of the factors.
        return self._target_factor_allocations

    def getPortfolioFactors(self) -> pd.Index:
        """Get the factors in canonical order.

        The canonical order is determined by the order of factors in the target
        factor allocations. This ensures consistent ordering between:
        - Factor weights matrix rows
        - Target factor allocations
        - Factor allocation vectors

        Returns:
            pd.Index: Index containing factors in canonical order
        """
        return self._target_factor_allocations.index

    def getPortfolioFactorWeights(self, verbose: bool = False) -> pd.DataFrame:
        """Get the master factor weights matrix for the entire portfolio.

        Returns the complete factor weights matrix that:
        1. Contains all factors in canonical order (from getPortfolioFactors)
        2. Contains all tickers in canonical order
        3. Has zeros for any missing factor-ticker combinations

        Args:
            verbose: If True, print detailed information about the matrix

        Returns:
            pd.DataFrame: Factor weights matrix with:
                - Rows: Factors (in canonical order)
                - Columns: Tickers (in canonical order)
                - Values: Factor weights
        """
        if verbose:
            print("\nPortfolio factor weights matrix:")
            print(f" - Shape: {self._factor_weights.shape}")
            print(f" - Factors: {len(self._factor_weights.index)}")
            print(f" - Tickers: {len(self._factor_weights.columns)}")
            write_weights(self._factor_weights)

        return self._factor_weights

    def getAccountTargetFactorAllocations(self, account: str, verbose: bool = False) -> pd.Series:
        """Get the target factor allocations for a specific account.

        Delegates to the AccountRebalancer instance for the specified account.

        Args:
            account: Name of the account to get target allocations for
            verbose: If True, print detailed information about the allocations

        Returns:
            pd.Series: Series indexed by Factor containing target allocation percentages,
                      ordered according to the canonical factor order and scaled to
                      the account's proportion of the portfolio

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getTargetFactorAllocations(verbose=verbose)

    def getAccountFactorObjective(self, account: str, verbose: bool = False) -> cp.Expression:
        """Get the factor objective for a specific account.

        Delegates to the AccountRebalancer instance for the specified account.

        Args:
            account: Name of the account to get factor objective for
            verbose: If True, print detailed information about the objective

        Returns:
            cp.Expression: CVXPY expression representing the factor objective
                for the specified account.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getFactorObjective(verbose=verbose)

    def getAccountTurnoverObjective(self, account: str, verbose: bool = False) -> cp.Expression:
        """Get the turnover objective for a specific account.

        Delegates to the AccountRebalancer instance for the specified account.

        Args:
            account: Name of the account to get turnover objective for
            verbose: If True, print detailed information about the objective

        Returns:
            cp.Expression: CVXPY expression representing the turnover objective
                for the specified account.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getTurnoverObjective(verbose=verbose)

    def getAccountComplexityObjective(self, account: str, verbose: bool = False) -> cp.Expression:
        """Get the complexity objective for a specific account.

        Args:
            account: Name of the account to get complexity objective for
            verbose: If True, print detailed information about the objective

        Returns:
            cp.Expression: CVXPY expression representing the complexity objective
                for the specified account.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getComplexityObjective(verbose=verbose)

    def getAccountConstraints(self, account: str, verbose: bool = False) -> list[cp.Constraint]:
        """Get the optimization constraints for a specific account.

        Args:
            account: Name of the account to get constraints for
            verbose: If True, print detailed information about the constraints

        Returns:
            list[cp.Constraint]: List of CVXPY constraints for the specified account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.getAccountRebalancer(account).getConstraints(verbose=verbose)

    def getTurnoverPenalty(self) -> float:
        """Get the turnover penalty parameter.

        Returns:
            float: The weight for penalizing changes from current allocations
        """
        return self._turnover_penalty

    def getComplexityPenalty(self) -> float:
        """Get the complexity penalty parameter.

        Returns:
            float: The weight for penalizing the number of funds used
        """
        return self._complexity_penalty

    def getAccountAlignPenalty(self) -> float:
        """Get the account alignment penalty parameter.

        Returns:
            float: The weight for penalizing account-level factor misalignment
        """
        return self._account_align_penalty

class AccountRebalancer:
    """
    Helper class for managing account-level rebalancing optimization components.

    This class maintains the account-specific components needed for rebalancing,
    including the factor weights matrix and target allocations. It ensures
    consistent ordering of factors and tickers across all operations.

    Attributes:
        port_rebalancer: Parent PortfolioRebalancer object
        account: Name of the account being rebalanced
    """

    def __init__(
        self,
        port_rebalancer: PortfolioRebalancer,
        account: str,
        verbose: bool = False
    ):
        """
        Initialize the AccountRebalancer.

        Args:
            port_rebalancer: Parent PortfolioRebalancer object
            account: Name of the account being rebalanced
            verbose: If True, print detailed information about initialization
        """
        if verbose:
            print(f"\n==> AccountRebalancer.__init__()")
            print(f" - Account: {account}")

        # Store inputs
        self.port_rebalancer = port_rebalancer
        self.account = account

        # Initialize cache for optimization variables
        self._variables = None
        # Initialize cache for factor allocations expression
        self._factor_allocations = None
        # Initialize cache for factor weights matrix
        self._factor_weights = None
        # Initialize cache for factor objective
        self._factor_objective = None
        # Initialize cache for turnover objective
        self._turnover_objective = None
        # Initialize cache for target factor allocations
        self._target_factor_allocations = None
        # Initialize cache for complexity objective
        self._complexity_objective = None
        # Initialize cache for constraints
        self._constraints = None

        if verbose:
            print("\n<== AccountRebalancer.__init__()")

    def getAccountProportion(self) -> float:
        """Get the proportion of the portfolio held in this account.

        Returns:
            float: The proportion of the portfolio held in this account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.port_rebalancer.getAccountProportion(self.account)

    def getTickers(self) -> pd.Index:
        """Get the tickers for this account in canonical order.

        Returns:
            pd.Index: Index containing tickers in canonical order that exist in this account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.port_rebalancer.getAccountTickers(self.account)

    def getTickerAllocations(self) -> pd.Series:
        """Get the current ticker allocations for this account in canonical order.

        Returns:
            pd.Series: Series indexed by ticker containing current allocation percentages,
                      ordered according to the canonical ticker order

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        return self.port_rebalancer.getAccountTickerAllocation(self.account)

    def getTickerResults(self) -> pd.DataFrame:
        """Get the ticker allocation results for this account.

        Currently returns a DataFrame with original allocations. This will be extended
        to include optimized/rebalanced allocations in the future.

        Returns:
            pd.DataFrame: DataFrame indexed by ticker (in canonical order) containing:
                - Original Allocation: Current allocation percentages

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Get original allocations
        original_allocations = self.getTickerAllocations()

        # Create DataFrame with original allocations
        results = pd.DataFrame({
            'Original Allocation': original_allocations
        })

        # Set index name
        results.index.name = 'Ticker'

        return results

    def getVariables(self, verbose: bool = False) -> Dict[str, cp.Variable]:
        """Create optimization variables for this account.

        Creates two sets of variables:
        - x: Allocation percentages for each ticker
        - z: Binary selection variables for each ticker

        Variables are created in canonical order to ensure consistent ordering with
        other components (factor weights matrix, current allocations, etc.).

        Variables are cached after first creation to ensure they are not recreated
        in subsequent calls.

        Args:
            verbose: If True, print detailed information about the variables created

        Returns:
            Dict[str, cp.Variable]: Dictionary containing:
                'x': Vstack of allocation variables
                'z': Vstack of binary selection variables
            Variables are ordered to match the canonical ticker order

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached variables if they exist
        if self._variables is not None:
            if verbose:
                print(f"\nUsing cached variables for account {self.account}")
            return self._variables

        # Get tickers in canonical order
        tickers = self.getTickers()

        # Create variable name patterns
        x_pattern = lambda ticker: f"x_{self.account}_{ticker}"
        z_pattern = lambda ticker: f"z_{self.account}_{ticker}"

        # Create variables with appropriate names
        x_vars = [cp.Variable(name=x_pattern(ticker)) for ticker in tickers]
        z_vars = [cp.Variable(boolean=True, name=z_pattern(ticker)) for ticker in tickers]

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
            print(f"\nVariables for account {self.account}:")
            write_table(variable_df, columns=column_formats)

        # Stack variables into vectors and cache them
        self._variables = {
            'x': cp.vstack(x_vars),  # Allocation percentages
            'z': cp.vstack(z_vars)   # Binary selection variables
        }

        return self._variables

    def getFactorWeights(self, verbose: bool = False) -> pd.DataFrame:
        """Get the factor weights matrix for this account.

        Returns a factor weights matrix that:
        1. Contains only columns for tickers that are valid for this account
        2. Orders tickers according to the canonical order (from getTickers)
        3. Maintains the same factor ordering as the parent portfolio

        The matrix is cached after first creation to ensure it is not recreated
        in subsequent calls.

        Args:
            verbose: If True, print detailed information about the matrix

        Returns:
            pd.DataFrame: Factor weights matrix with:
                - Rows: Factors (in same order as parent portfolio)
                - Columns: Tickers (in canonical order for this account)
                - Values: Factor weights

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached matrix if it exists
        if self._factor_weights is not None:
            if verbose:
                print(f"\nUsing cached factor weights matrix for account {self.account}")
            return self._factor_weights

        # Get tickers in canonical order
        tickers = self.getTickers()

        # Get factor weights matrix from parent portfolio and filter
        # columns to match account's tickers
        self._factor_weights = self.port_rebalancer.getPortfolioFactorWeights(verbose=verbose)[tickers]

        if verbose:
            print(f"\nFactor weights matrix for account {self.account}:")
            print(f" - Shape: {self._factor_weights.shape}")
            print(f" - Factors: {len(self._factor_weights.index)}")
            print(f" - Tickers: {len(self._factor_weights.columns)}")
            write_weights(self._factor_weights)

        return self._factor_weights

    def getOptimizedFactorAllocations(self, verbose: bool = False) -> cp.Expression:
        """Calculate the optimized factor allocations for this account.

        This is calculated by multiplying the factor weights matrix by the allocation
        variables vector: F @ x

        The expression is cached after first creation to ensure it is not recreated
        in subsequent calls.

        Args:
            verbose: If True, print detailed information about the calculation

        Returns:
            cp.Expression: CVXPY expression representing the optimized factor allocations
                for this account. The expression is a vector with one element per factor,
                ordered according to the parent portfolio's factor order.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached expression if it exists
        if self._factor_allocations is not None:
            if verbose:
                print(f"\nUsing cached factor allocations expression for account {self.account}")
            return self._factor_allocations

        # Get factor weights matrix and variables
        F = self.getFactorWeights(verbose=verbose)
        variables = self.getVariables(verbose=verbose)

        # Calculate factor allocations: F @ x
        self._factor_allocations = F.to_numpy() @ variables['x']

        if verbose:
            print(f"\nOptimized factor allocations for account {self.account}:")
            print(f" - Shape: {self._factor_allocations.shape}")
            # TODO: fix this (len doesn't work)
            #print(f" - Factors: {len(self._factor_allocations)}")
            print(f" - Expression: F @ x")

        return self._factor_allocations

    def getTargetFactorAllocations(self, verbose: bool = False) -> pd.Series:
        """Get the target factor allocations for this account.

        Returns the target factor allocations scaled to this account's proportion
        of the portfolio, ensuring they are in canonical order.

        The allocations are cached after first creation to ensure they are not
        recreated in subsequent calls.

        Args:
            verbose: If True, print detailed information about the allocations

        Returns:
            pd.Series: Series indexed by Factor containing target allocation percentages,
                      ordered according to the canonical factor order and scaled to
                      this account's proportion of the portfolio

        Raises:
            ValueError: If target allocations don't sum to 100%
        """
        # Return cached allocations if they exist
        if self._target_factor_allocations is not None:
            if verbose:
                print(f"\nUsing cached target factor allocations for account {self.account}")
            return self._target_factor_allocations

        # Get portfolio target allocations and account proportion
        portfolio_targets = self.port_rebalancer.getPortfolioTargetFactorAllocations(verbose=verbose)
        account_proportion = self.getAccountProportion()

        # Scale target allocations by account proportion
        self._target_factor_allocations = portfolio_targets * account_proportion

        if verbose:
            print(f"\nTarget factor allocations for account {self.account}:")
            print(f" - Account proportion: {account_proportion:.2%}")
            print(f" - Number of factors: {len(self._target_factor_allocations)}")
            print(f" - Total allocation: {self._target_factor_allocations.sum():.2%}")
            write_weights(self._target_factor_allocations)

        return self._target_factor_allocations

    def getFactorObjective(self, verbose: bool = False) -> cp.Expression:
        """Calculate the factor objective for this account.

        This is calculated as the sum of squares of the difference between the
        optimized factor allocations and the target factor allocations:
        sum_squares(F @ x - target)

        The expression is cached after first creation to ensure it is not recreated
        in subsequent calls.

        Args:
            verbose: If True, print detailed information about the calculation

        Returns:
            cp.Expression: CVXPY expression representing the factor objective
                for this account.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached expression if it exists
        if self._factor_objective is not None:
            if verbose:
                print(f"\nUsing cached factor objective for account {self.account}")
            return self._factor_objective

        # Get factor allocations and target allocations
        factor_allocations = self.getOptimizedFactorAllocations(verbose=verbose)
        target_allocations = self.getTargetFactorAllocations(verbose=verbose)

        # Calculate factor objective: sum_squares(F @ x - target)
        self._factor_objective = cp.sum_squares(
            factor_allocations - target_allocations.to_numpy()
        )

        if verbose:
            print(f"\nFactor objective for account {self.account}:")
            print(f" - Expression: sum_squares(F @ x - target)")
            print(f" - Target allocations:")
            write_weights(target_allocations)

        return self._factor_objective

    def getTurnoverObjective(self, verbose: bool = False) -> cp.Expression:
        """Calculate the turnover objective for this account.

        This is calculated as the sum of squares of the difference between the
        current ticker allocations and the new allocation variables:
        sum_squares(x - current_allocations)

        The expression is cached after first creation to ensure it is not recreated
        in subsequent calls.

        Args:
            verbose: If True, print detailed information about the calculation

        Returns:
            cp.Expression: CVXPY expression representing the turnover objective
                for this account.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached expression if it exists
        if self._turnover_objective is not None:
            if verbose:
                print(f"\nUsing cached turnover objective for account {self.account}")
            return self._turnover_objective

        # Get variables and current allocations
        variables = self.getVariables(verbose=verbose)
        current_allocations = self.getTickerAllocations()

        # Calculate turnover objective: sum_squares(x - current_allocations)
        self._turnover_objective = cp.sum_squares(
            variables['x'] - current_allocations.to_numpy()
        )

        if verbose:
            print(f"\nTurnover objective for account {self.account}:")
            print(f" - Expression: sum_squares(x - current_allocations)")
            print(f" - Current allocations:")
            write_weights(current_allocations)

        return self._turnover_objective

    def getComplexityObjective(self, verbose: bool = False) -> cp.Expression:
        """Calculate the complexity objective for this account.

        This is calculated as the sum of binary selection variables (z), which
        minimizes the number of funds used in the account.

        The expression is cached after first creation to ensure it is not recreated
        in subsequent calls.

        Args:
            verbose: If True, print detailed information about the calculation

        Returns:
            cp.Expression: CVXPY expression representing the complexity objective
                for this account.

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached expression if it exists
        if self._complexity_objective is not None:
            if verbose:
                print(f"\nUsing cached complexity objective for account {self.account}")
            return self._complexity_objective

        # Get variables
        variables = self.getVariables(verbose=verbose)

        # Calculate complexity objective: sum(z)
        self._complexity_objective = cp.sum(variables['z'])

        if verbose:
            print(f"\nComplexity objective for account {self.account}:")
            print(f" - Expression: sum(z)")
            print(f" - Number of tickers: {variables['z'].size}")

        return self._complexity_objective

    def getConstraints(self, verbose: bool = False) -> list[cp.Constraint]:
        """Get the optimization constraints for this account.

        The constraints include:
        1. Sum of allocations equals account's proportion of portfolio
        2. No negative allocations
        3. Link between allocation variables (x) and selection variables (z)
        4. Minimum allocation when a fund is selected

        The constraints are cached after first creation to ensure they are not
        recreated in subsequent calls.

        Args:
            verbose: If True, print detailed information about the constraints

        Returns:
            list[cp.Constraint]: List of CVXPY constraints for the account

        Raises:
            ValueError: If the account is not found in the portfolio
        """
        # Return cached constraints if they exist
        if self._constraints is not None:
            if verbose:
                print(f"\nUsing cached constraints for account {self.account}")
            return self._constraints

        # Get variables and account proportion
        variables = self.getVariables(verbose=verbose)
        account_proportion = self.getAccountProportion()
        min_ticker_alloc = self.port_rebalancer.min_ticker_alloc

        # Create the constraints list
        self._constraints = [
            # Sum of allocations equals account's proportion of portfolio
            cp.sum(variables['x']) == account_proportion,
            variables['x'] >= 0,                                 # No negative allocations
            variables['x'] <= variables['z'],                    # Link x and z
            variables['x'] >= min_ticker_alloc * variables['z']  # Minimum allocation
        ]

        if verbose:
            print(f"\nConstraints for account {self.account}:")
            print(f" - Account proportion: {account_proportion:.2%}")
            print(f" - Minimum ticker allocation: {min_ticker_alloc:.2%}")
            print(f" - Number of constraints: {len(self._constraints)}")
            print(f" - Constraint types:")
            print(f"   1. Sum of allocations = {account_proportion:.2%}")
            print(f"   2. No negative allocations")
            print(f"   3. Link x and z variables")
            print(f"   4. Minimum allocation when selected: {min_ticker_alloc:.2%}")

        return self._constraints

    def validate(self, verbose: bool = False) -> None:
        """Validate that all ticker-related and factor-related components are properly aligned.

        This method checks that:
        1. The following components have the same tickers in the exact same order:
           - Account tickers from getTickers()
           - Current ticker allocations from getTickerAllocations()
           - Ticker results index from getTickerResults()
           - Optimization variables from getVariables()
           - Factor weights matrix columns from getFactorWeights()

        2. The following components have the same factors in the exact same order:
           - Target factor allocations from getTargetFactorAllocations()
           - Factor weights matrix index from getFactorWeights()

        Args:
            verbose: If True, print detailed information about the validation

        Raises:
            ValueError: If any components are misaligned
        """
        if verbose:
            print(f"\n==> AccountRebalancer.validate()")
            print(f" - Account: {self.account}")

        # Get all components to validate
        tickers = self.getTickers()
        current_allocations = self.getTickerAllocations()
        ticker_results = self.getTickerResults()
        variables = self.getVariables()
        factor_weights = self.getFactorWeights()
        target_factor_allocations = self.getTargetFactorAllocations()

        # Create a list of component names and their ticker indices
        ticker_components = [
            ("Account Tickers", tickers),
            ("Current Allocations", current_allocations.index),
            ("Ticker Results", ticker_results.index),
            ("Variables", pd.Index([var.name().split('_')[-1] for var in variables['x'].args])),
            ("Factor Weights", factor_weights.columns)
        ]

        # Create a list of component names and their factor indices
        factor_components = [
            ("Target Factor Allocations", target_factor_allocations.index),
            ("Factor Weights", factor_weights.index)
        ]

        # Validate each ticker component against the reference (Account Tickers)
        reference_name, reference_index = ticker_components[0]
        for name, index in ticker_components[1:]:
            if not index.equals(reference_index):
                raise ValueError(
                    f"Ticker misalignment detected:\n"
                    f" - {reference_name} tickers: {list(reference_index)}\n"
                    f" - {name} tickers: {list(index)}\n"
                    f" - Mismatch at positions: {[i for i, (t1, t2) in enumerate(zip(reference_index, index)) if t1 != t2]}"
                )

        # Validate each factor component against the reference (Target Factor Allocations)
        reference_name, reference_index = factor_components[0]
        for name, index in factor_components[1:]:
            if not index.equals(reference_index):
                raise ValueError(
                    f"Factor misalignment detected:\n"
                    f" - {reference_name} factors: {list(reference_index)}\n"
                    f" - {name} factors: {list(index)}\n"
                    f" - Mismatch at positions: {[i for i, (t1, t2) in enumerate(zip(reference_index, index)) if t1 != t2]}"
                )

        if verbose:
            print("\nValidation complete:")
            print(f" - All ticker components aligned with {ticker_components[0][0]}")
            print(f" - Number of tickers: {len(ticker_components[0][1])}")
            print(f" - Tickers: {list(ticker_components[0][1])}")
            print(f" - All factor components aligned with {factor_components[0][0]}")
            print(f" - Number of factors: {len(factor_components[0][1])}")
            print(f" - Factors: {list(factor_components[0][1])}")
            print(f"<== AccountRebalancer.validate()")

    def rebalance(self, verbose: bool = False) -> None:
        """Construct and solve the optimization problem for this account.

        The optimization problem minimizes a weighted sum of:
        1. Factor misalignment (account_align_penalty * factor_objective)
        2. Turnover (turnover_penalty * turnover_objective)
        3. Complexity (complexity_penalty * complexity_objective)

        The constraints are provided by getConstraints().

        Args:
            verbose: If True, print detailed information about the optimization

        Returns:
            None

        Raises:
            RuntimeError: If optimization fails
        """
        if verbose:
            print(f"\n==> AccountRebalancer.rebalance()")
            print(f" - Account: {self.account}")

        # Validate all components are properly aligned
        self.validate(verbose=verbose)

        # Get penalty parameters from parent portfolio
        account_align_penalty = self.port_rebalancer.getAccountAlignPenalty()
        turnover_penalty = self.port_rebalancer.getTurnoverPenalty()
        complexity_penalty = self.port_rebalancer.getComplexityPenalty()

        if verbose:
            print(f"\nPenalty parameters:")
            print(f" - Account align penalty: {account_align_penalty}")
            print(f" - Turnover penalty: {turnover_penalty}")
            print(f" - Complexity penalty: {complexity_penalty}")

        # Get objectives
        factor_objective = self.getFactorObjective(verbose=verbose)
        turnover_objective = self.getTurnoverObjective(verbose=verbose)
        complexity_objective = self.getComplexityObjective(verbose=verbose)

        # Construct the objective function
        objective = cp.Minimize(
            account_align_penalty * factor_objective +
            turnover_penalty * turnover_objective +
            complexity_penalty * complexity_objective
        )

        # Get constraints
        constraints = self.getConstraints(verbose=verbose)

        # Create and solve the optimization problem
        problem = cp.Problem(objective, constraints)
        try:
            problem.solve(solver=cp.SCIP, verbose=verbose)
        except Exception as e:
            raise RuntimeError(f"Optimization failed: {str(e)}")

        if problem.status != 'optimal':
            raise RuntimeError(f"Optimization failed with status: {problem.status}")

        if verbose:
            print(f"\nOptimization complete:")
            print(f" - Status: {problem.status}")
            print(f" - Objective value: {problem.value:.6f}")
            print(f"<== AccountRebalancer.rebalance()")