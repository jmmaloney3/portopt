"""
Metrics mixin for portfolio analysis.

This module provides a MetricsMixin class that adds metrics calculation capabilities
to the Portfolio class. It uses ibis to implement efficient and maintainable
metrics calculations across various portfolio dimensions.

The mixin supports:
- Calculating metrics like Quantity, Value and Allocation
- Aggregating by different dimensions (Ticker, Factor, Account, etc.)
- Filtering by dimension values
- Handling factor weights for factor-based analysis

Dependencies:
    - ibis: Analytics framework for expressing complex queries
    - duckdb: Backend engine for query execution
"""

import ibis
from ibis import _
import pandas as pd
from typing import List, Dict, Optional, Union


class MetricsMixin:
    """Mixin class that adds metrics calculation capabilities to Portfolio class.

    This mixin uses ibis to implement portfolio metrics calculations in a maintainable
    and efficient way. It handles the complexity of joining multiple dimensions and
    calculating metrics while providing a clean interface.
    """

    def _requires_factor_tables(self,
                               dimensions: List[str],
                               filters: Optional[Dict[str, Union[str, List[str]]]] = None) -> tuple[bool, bool]:
        """Determine if factor tables are required based on dimensions and filters.

        This centralizes the logic for determining when to join factor_weights and factors tables.

        Args:
            dimensions: List of dimensions for the query
            filters: Dictionary of filters to apply

        Returns:
            Tuple of (requires_factor_weights, requires_factor_levels)
            - requires_factor_weights: True if factor_weights table is needed
            - requires_factor_levels: True if factors table is needed (for Level_* columns)
        """
        requires_factor_weights = False
        requires_factor_levels = False

        # Check dimensions
        if dimensions:
            requires_factor_weights = any(d.startswith('Level_') or d == 'Factor' for d in dimensions)
            requires_factor_levels = any(d.startswith('Level_') for d in dimensions)

        # Check filters if they exist
        if filters:
            requires_factor_weights = requires_factor_weights or \
                                      any(d.startswith('Level_') or d == 'Factor' for d in filters.keys())
            requires_factor_levels = requires_factor_levels or \
                                     any(d.startswith('Level_') for d in filters.keys())

        return requires_factor_weights, requires_factor_levels

    def _get_base_tables(self,
                        dimensions: List[str] = None,
                        filters: Optional[Dict[str, Union[str, List[str]]]] = None) -> Dict[str, ibis.Table]:
        """Get the base tables needed for metrics calculations.

        Args:
            dimensions: List of dimensions (optional, for optimization)
            filters: Dictionary of filters (optional, for optimization)

        Returns:
            Dict mapping table names to ibis Table objects
        """
        # Create DuckDB connection
        con = ibis.duckdb.connect()

        # Register dataframes as tables
        tables = {}

        # Holdings table - core fact table (always needed)
        holdings_df = self.getHoldings().reset_index()
        tables['holdings'] = con.create_table('holdings', holdings_df)

        # Prices table - for calculating values (always needed)
        prices_df = self.getPrices().reset_index()
        tables['prices'] = con.create_table('prices', prices_df)

        # Optional dimension tables
        try:
            # Accounts dimension
            accounts_df = self.getAccounts().reset_index()
            tables['accounts'] = con.create_table('accounts', accounts_df)
        except:
            pass

        # Factor tables - only load if needed
        if dimensions is not None and filters is not None:
            requires_factor_weights, requires_factor_levels = self._requires_factor_tables(dimensions, filters)

            if requires_factor_weights:
                try:
                    # Factor weights fact table
                    weights_df = self.getFactorWeights().reset_index()
                    tables['factor_weights'] = con.create_table('factor_weights', weights_df)
                except:
                    pass

                if requires_factor_levels:
                    try:
                        # Factors dimension
                        factors_df = self.getFactors().reset_index()
                        tables['factors'] = con.create_table('factors', factors_df)
                    except:
                        pass
        else:
            # Fallback: load all factor tables if dimensions/filters not provided
            try:
                # Factors dimension
                factors_df = self.getFactors().reset_index()
                tables['factors'] = con.create_table('factors', factors_df)

                # Factor weights fact table
                weights_df = self.getFactorWeights().reset_index()
                tables['factor_weights'] = con.create_table('factor_weights', weights_df)
            except:
                pass

        try:
            # Tickers dimension
            tickers_df = self.getTickers().reset_index()
            tables['tickers'] = con.create_table('tickers', tickers_df)
        except:
            pass

        return tables

    def _handle_undefined_factor_weights(self,
                                       query: ibis.Table,
                                       requires_factor_levels: bool) -> ibis.Table:
        """Handle tickers that don't have factor weights defined.

        This method creates an "UNDEFINED" factor that matches the structure of the
        user's factor hierarchy, ensuring tickers without factor weights are included
        exactly once in factor-based calculations.

        This adds the UNDEFINED factor to the query, and sets the Weight to 1.0
        resulting the Factor, Weight, and facrtor hierarchy columns being replaced
        with COALESCE expressions like the following:
            ```
            COALESCE("t8"."Factor", 'UNDEFINED') AS "Factor",
            COALESCE("t8"."Weight", 1.0) AS "Weight",
            COALESCE("t8"."Level_0", 'UNDEFINED') AS "Level_0",
            COALESCE("t8"."Level_1", 'N/A') AS "Level_1",
            COALESCE("t8"."Level_2", 'N/A') AS "Level_2"
            ```
        Args:
            query: The current query with LEFT JOINed factor tables
            requires_factor_levels: Whether factor level columns are needed

        Returns:
            Query with undefined factor weights handled appropriately
        """
        # Set default values for missing factor weights
        mutate_exprs = {
            'Factor': query.Factor.coalesce('UNDEFINED'),
            'Weight': query.Weight.coalesce(1.0)
        }

        # If factor levels are required, we need to determine the appropriate
        # default values based on the actual factor hierarchy structure
        if requires_factor_levels:
            # Get the level column names from the query columns (they're already joined)
            level_columns = [col for col in query.columns if col.startswith('Level_')]

            # For each level column, set undefined tickers to "UNDEFINED" at Level_0
            # and "N/A" for all other levels (following common convention)
            for level_col in level_columns:
                if level_col == 'Level_0':
                    mutate_exprs[level_col] = getattr(query, level_col).coalesce('UNDEFINED')
                else:
                    mutate_exprs[level_col] = getattr(query, level_col).coalesce('N/A')

        return query.mutate(**mutate_exprs)

    def _aggregate_factor_weights(self,
                                  query: ibis.Table,
                                  dimensions: List[str],
                                  requires_factor_levels: bool,
                                  verbose: bool = False) -> ibis.Table:
        """Pre-aggregate factor weights to prevent double-counting in metrics calculations.

        This method is CRITICAL for correct portfolio metrics when factor weights are
        involved but the query does not have a GROUP BY on the Factors associated with
        the weights. It solves the fundamental double-counting problem that occurs when
        tickers have multiple factor exposures with fractional weights resulting in
        multiple rows for the same position.

        THE PROBLEM:
        When a ticker (e.g., AAPL) has multiple factor exposures:
        - AAPL → US_Large_Growth (weight: 0.5)
        - AAPL → US_Large_Tech (weight: 0.2)
        - AAPL → Intl_Large (weight: 0.2)
        - AAPL → Intl_Tech (weight: 0.1)

        The factor weight JOIN creates multiple rows for the same position:
        | Ticker | Account | Quantity | Price | Factor         | Weight | Level_0 | Level_1 |
        |--------|---------|----------|-------|----------------|--------|---------|---------|
        | AAPL   | IRA     | 100      | 150   | US_Large_Growth| 0.5    | Equity  | US      |
        | AAPL   | IRA     | 100      | 150   | US_Large_Tech  | 0.2    | Equity  | US      |
        | AAPL   | IRA     | 100      | 150   | Intl_Large     | 0.2    | Equity  | Intl    |
        | AAPL   | IRA     | 100      | 150   | Intl_Tech      | 0.1    | Equity  | Intl    |

        Note that neither the Quantity nor the Price columns account for the factor weights.
        These are the amounts for the entire position, not the fractional position allocated
        to each Factor.

        Assume that we are aggregating by dimensions other than the individual Factors.
        For example, assume we are aggregating by Account, Level_0, and Level_1. The
        naive approach is to generate a query like the following:

        ```sql
        SELECT Account, Level_0, Level_1, SUM(Quantity * Price) AS Value
        FROM <base_query>
        GROUP BY Account, Level_0, Level_1
        ```

        This produces the following INCORRECT result because it counts each row separately:

        For (IRA, Equity, US): (100 * 150) + (100 * 150) = 30,000 ✗ WRONG (2x too high)
        For (IRA, Equity, Intl): (100 * 150) + (100 * 150) = 30,000 ✗ WRONG (2x too high)
        Total: 60,000 ✗ WRONG (4x the actual $15,000 position value)

        THE SOLUTION:
        The solution is to pre-aggregate the weights to combine the fractional positions
        into a single row for each unique combination of position and factor levels,
        resulting in an intermediate result like the following where the Weight column
        is the sum of the fractional weights:

        | Ticker | Account | Quantity | Price | Level_0 | Level_1 | Weight |
        |--------|---------|----------|-------|---------|---------|--------|
        | AAPL   | IRA     | 100      | 150   | Equity  | US      | 0.7    |
        | AAPL   | IRA     | 100      | 150   | Equity  | Intl    | 0.3    |

        Then include the pre-aggregated weights in the final calculation:

        ```sql
        SELECT Account, Level_0, Level_1, SUM(Quantity * Price * Weight) AS Value
        FROM <pre_aggregated_query>
        GROUP BY Account, Level_0, Level_1
        ```

        This produces the following CORRECT result:

        For (IRA, Equity, US): 100 * 150 * 0.7 = 10,500 ✓ CORRECT
        For (IRA, Equity, Intl): 100 * 150 * 0.3 = 4,500 ✓ CORRECT
        Total: 15,000 ✓ CORRECT (matches the actual position value)

        WHEN THIS IS NEEDED:
        - Factor weights table is joined (creates duplicate rows)
        - Tickers have multiple factor exposures (fractional weights)
        - Using factor filters but not factor dimensions (the original bug scenario)

        REAL-WORLD EXAMPLE:
        Original bug scenario: portfolio.getMetrics('Account',
                                                   filters={'Level_0': ['Equity']},
                                                   portfolio_allocation=True)
        - Without this method: $67,500 (50% too high due to double-counting)
        - With this method: $45,000 (correct value)

        Args:
            query: Query with factor weights joined (contains duplicate rows)
            dimensions: List of dimensions for the final query
            requires_factor_levels: Whether factor level columns are needed
            verbose: If True, print the generated SQL query

        Returns:
            Query with weights properly aggregated (one row per position)
        """
        # Determine grouping columns for weight aggregation
        # Create list of all columns that should be considered for grouping
        base_cols = ['Ticker', 'Account', 'Quantity', 'Price']
        candidate_cols = base_cols + ['Factor'] + list(dimensions)

        # Add columns that exist in the query (avoiding duplicates)
        group_cols = []
        for col in candidate_cols:
            if col in query.columns and col not in group_cols:
                group_cols.append(col)

        # Handle Level_* columns separately (using "starts with" logic)
        # This ensures we maintain the factor hierarchy and prevents incorrect aggregation
        for col in query.columns:
            if col.startswith('Level_') and col not in group_cols:
                group_cols.append(col)

        # Collect column expressions for the GROUP BY clause
        # All columns in group_cols are guaranteed to exist in query.columns
        group_exprs = [getattr(query, col) for col in group_cols]

        # Create aggregation expression for weights
        # SUM(Weight) handles fractional weights correctly (e.g., 0.5 + 0.2 = 0.7 for US factors)
        if 'Weight' not in query.columns:
            raise ValueError("Weight column not found in query - this method should only be called when factor weights are present")
        agg_exprs = [query.Weight.sum().name('Weight')]

        # Group and aggregate to get one row per position with summed weights
        aggregated_query = query.group_by(group_exprs).aggregate(agg_exprs)

        if verbose:
            print("Pre-aggregated Weights Query --------------------------------")
            print(ibis.to_sql(aggregated_query))

        return aggregated_query

    def _build_base_query(self,
                          tables: Dict[str, ibis.Table],
                          dimensions: List[str],
                          filters: Optional[Dict[str, Union[str, List[str]]]] = None,
                          verbose = False) -> ibis.Table:
        """Join together the base tables required for metrics calculations.

        Args:
            tables: Dict of ibis tables
            dimensions: List of dimensions to include in query
            filters: Dict of filters to apply to the query
            verbose: If True, print the generated SQL query. Default is False.

        Returns:
            ibis Table with base joined data
        """
        # Determine if factor tables are needed based on dimensions and filters
        requires_factor_weights, requires_factor_levels = self._requires_factor_tables(dimensions, filters)

        # Start with holdings and join with prices
        query = tables['holdings'].join(tables['prices'], 'Ticker')

        # Add factor tables if needed - use LEFT JOINs to include all tickers
        # If factor tables are added ensure that:
        # - all tickers have a factor weights
        # - factor weights are properly aggregated (no double-counting)
        if requires_factor_weights:
            if 'factor_weights' not in tables:
                raise ValueError("Factor weights are required for the requested dimensions/filters, "
                               "but factor_weights table is not available")
            query = query.left_join(tables['factor_weights'], 'Ticker')
            if requires_factor_levels:
                if 'factors' not in tables:
                    raise ValueError("Factor levels are required for the requested dimensions/filters, "
                                   "but factors table is not available")
                query = query.left_join(tables['factors'], 'Factor')

            # Handle tickers without factor weights by assigning them to an "UNDEFINED" factor
            # This prevents them from being counted multiple times across all factors
            query = self._handle_undefined_factor_weights(query, requires_factor_levels)

            # CRITICAL: Pre-aggregate factor weights to prevent double-counting
            query = self._aggregate_factor_weights(
                query, dimensions, requires_factor_levels, verbose
            )

        if verbose and not requires_factor_weights:
            print("Base Query --------------------------------")
            print(ibis.to_sql(query))

        return query

    def _apply_filters(
        self,
        query: ibis.Table,
        filters: Optional[Dict[str, Union[str, List[str]]]] = None,
        verbose = False
    ) -> ibis.Table:
        """Apply dimension filters to the query.

        Args:
            query: Query to filter
            filters: Dict of filters to apply

        Returns:
            Filtered query
        """
        if not filters:
            if verbose:
                print("No filters specified, returning unfiltered query")
            return query

        for dim, values in filters.items():
            # Convert single values to list
            if isinstance(values, str):
                values = [values]

            # Apply filter
            query = query.filter(getattr(query, dim).isin(values))

        if verbose:
            print("Filtered Query --------------------------------")
            print(ibis.to_sql(query))

        return query

    def _build_total_value_subquery(
        self,
        unfiltered_query: ibis.Table,
        filtered_query: ibis.Table,
        portfolio_allocation: bool,
        verbose = False
    ) -> ibis.Table:
        """Calculate total value used to calculate Allocation metric.

        Args:
            unfiltered_query: Query used to calculate total value when portfolio_allocation is True
            filtered_query: Query used to calculate total value when portfolio_allocation is False
            portfolio_allocation: Whether to calculate total value for entire portfolio or filtered portfolio
            verbose: If True, print the generated SQL query. Default is False.
        """
        # Identify correct total_value query - unfiltered or filtered
        if portfolio_allocation:
            # Use UNFILTERED query to calculate total value used to calculate Allocation
            if verbose:
                print("Using UNFILTERED query to calculate total value used to calculate Allocation")
            base_query = unfiltered_query
        else:
            # Use FILTERED query to calculate total value used to calculate Allocation
            if verbose:
                print("Using FILTERED query to calculate total value used to calculate Allocation")
            base_query = filtered_query

        # Build total value expression - used to calculate Allocation
        # With the new approach, Weight is always available when factor weights are involved
        # and the weights are already properly aggregated
        if 'Weight' in base_query.columns:
            total_value_expr = (base_query.Quantity * base_query.Price * base_query.Weight).sum().name("Total")
        else:
            total_value_expr = (base_query.Quantity * base_query.Price).sum().name("Total")

        total_value_subquery = total_value_expr.as_scalar()

        if verbose:
            print("Total Value Query --------------------------------")
            print(ibis.to_sql(total_value_subquery))

        return total_value_subquery  # Not executed yet, will be used in expression

    def _add_aggregates(
        self,
        query: ibis.Table,
        dimensions: List[str],
        metrics: List[str],
        verbose = False
    ) -> ibis.Table:
        """Add aggregate expressions to the query using a GROUP BY if required.

        Args:
            query: Query to add aggregates to
            dimensions: List of dimensions to group by
            metrics: List of metrics to add aggregates for
            verbose: If True, print the generated SQL query. Default is False.
        """
        agg_exprs = []
        if 'Quantity' in metrics:
            # Always sum quantities - whether factor weights are involved or not
            agg_exprs.append(query.Quantity.sum().name("Quantity"))

        if 'Value' in metrics or 'Allocation' in metrics:
            # Use Weight if it's available (means factor weights were pre-aggregated)
            if 'Weight' in query.columns:
                agg_exprs.append((query.Quantity * query.Price * query.Weight).sum().name("Value"))
            else:
                agg_exprs.append((query.Quantity * query.Price).sum().name("Value"))

        # If no dimensions, just apply aggregates directly
        if not dimensions:
            query = query.aggregate(agg_exprs)
            if verbose:
                print("Grouped Query --------------------------------")
                print("   No dimensions specified, no GROUP BY")
                print(ibis.to_sql(query))
            return query

        # Otherwise group by dimensions first
        # Validate that all requested dimensions exist in the query
        missing_dims = [dim for dim in dimensions if dim not in query.columns]
        if missing_dims:
            raise ValueError(f"Requested dimensions not found in query: {missing_dims}. "
                           f"Available columns: {list(query.columns)}")

        group_exprs = [getattr(query, dim) for dim in dimensions]
        # Don't overwrite query with grouped table -
        # grouped table can't be used for other query building operations
        grouped = query.group_by(group_exprs)

        # Add aggregates to grouped table - returns a query
        grouped_query = grouped.aggregate(agg_exprs)

        if verbose:
            print("Grouped Query --------------------------------")
            print(ibis.to_sql(grouped_query))

        return grouped_query

    def _add_allocation(
        self,
        query: ibis.Table,
        total_value_subquery: ibis.Table,
        verbose = False
    ) -> ibis.Table:
        """Add allocation metric to the query.

        Args:
            query: The query (with aggregations) to add allocation metric to
            total_value_subquery: Subquery that provides the total value used for allocation calculation
            verbose: If True, print the generated SQL query. Default is False.
        """
        # Get value column from final query
        value_col = query.Value.name('Value')

        # Build allocation expression
        # - total_value_query is a scalar subquery, so we can divide directly
        # - we need to use a subquery to ensure the total value is calculated once
        allocation_expr = (value_col / total_value_subquery).name("Allocation")

        final_query = query.mutate(Allocation=allocation_expr)

        if verbose:
            print("Allocation Query --------------------------------")
            print(ibis.to_sql(final_query))

        return final_query

    def getMetrics(
        self,
        *dimensions: str,
        metrics: Optional[List[str]] = None,
        filters: Optional[Dict[str, Union[str, List[str]]]] = None,
        portfolio_allocation: bool = False,
        verbose: bool = False
    ) -> pd.DataFrame:
        """Get portfolio metrics grouped by specified dimensions.

        Args:
            *dimensions: Variable number of dimension names ('Ticker', 'Factor', 'Level_0', etc.)
            metrics: List of metrics to include ('Quantity', 'Value', 'Allocation').
                    If None, includes all metrics.
            filters: Dictionary of filters to apply. Keys are dimension names, values are
                    lists of values to include (single values should be in a list).
                    Example: {'Account': ['IRA', '401k'], 'Level_0': ['Equity']}
            portfolio_allocation: If True, calculate allocations relative to total portfolio value
                                If False, calculate relative to filtered portfolio value (default)
            verbose: If True, print the generated SQL query. Default is False.

        Returns:
            DataFrame indexed by the specified dimensions with requested metrics as columns
        """
        # Default metrics if no metrics provided
        if not metrics:
            if verbose:
                print("No metrics specified, using default metrics: Quantity, Value, Allocation")
            metrics = ['Quantity', 'Value', 'Allocation']

        # Get base tables
        tables = self._get_base_tables(dimensions, filters)

        # Build base query
        # - save this to be used for allocation calculation
        unfiltered_query = self._build_base_query(tables, dimensions, filters, verbose)

        # Apply filters to get filtered query (before aggregation)
        # - save this to be used for allocation calculation
        filtered_query = self._apply_filters(unfiltered_query, filters, verbose)

        # Add aggregates to get metrics
        metrics_query = self._add_aggregates(filtered_query, dimensions, metrics, verbose)

        # Add allocation if requested
        if 'Allocation' in metrics:
            # Build total value query for allocation calculation
            # - filtered_query and unfiltered_query have the Price column
            # - which is required to build the total value query for the allocation calculation
            total_value_subquery = self._build_total_value_subquery(
                unfiltered_query,
                filtered_query,
                portfolio_allocation,
                verbose
            )

            # Add allocation metrics to final query
            metrics_query = self._add_allocation(
                query=metrics_query,
                total_value_subquery=total_value_subquery,
                verbose=verbose
            )

        if verbose:
            print("Final Metrics Query --------------------------------")
            print(ibis.to_sql(metrics_query))

        # Execute query
        result = metrics_query.execute()

        # Set index based on dimensions if any were specified
        if dimensions:
            result.set_index(list(dimensions), inplace=True)

        return result
