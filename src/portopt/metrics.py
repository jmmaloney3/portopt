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

    def _get_base_tables(self) -> Dict[str, ibis.Table]:
        """Get the base tables needed for metrics calculations.
        
        Returns:
            Dict mapping table names to ibis Table objects
        """
        # Create DuckDB connection
        con = ibis.duckdb.connect()

        # Register dataframes as tables
        tables = {}
        
        # Holdings table - core fact table
        holdings_df = self.getHoldings().reset_index()
        tables['holdings'] = con.create_table('holdings', holdings_df)
        
        # Prices table - for calculating values
        prices_df = self.getPrices().reset_index()
        tables['prices'] = con.create_table('prices', prices_df)

        # Optional dimension tables
        try:
            # Accounts dimension
            accounts_df = self.getAccounts().reset_index()
            tables['accounts'] = con.create_table('accounts', accounts_df)
        except:
            pass

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
        
        # Start with holdings and join with prices
        query = tables['holdings'].join(tables['prices'], 'Ticker')
        
        # Add factor tables if needed
        if requires_factor_weights:
            query = query.join(tables['factor_weights'], 'Ticker')
            if requires_factor_levels:
                query = query.join(tables['factors'], 'Factor')
                
        if verbose:
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
        agg_by_factors: bool,
        verbose = False
    ) -> ibis.Table:
        """Calculate total value used to calculate Allocation metric.
        
        Args:
            unfiltered_query: Query used to calculate total value when portfolio_allocation is True
            filtered_query: Query used to calculate total value when portfolio_allocation is False
            portfolio_allocation: Whether to calculate total value for entire portfolio or filtered portfolio
            agg_by_factors: Whether metrics are aggregated by factors
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
        if agg_by_factors:
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
        agg_by_factors: bool,
        verbose = False
    ) -> ibis.Table:
        """Add aggregate expressions to the query using a GROUP BY if required.
        
        Args:
            query: Query to add aggregates to
            dimensions: List of dimensions to group by
            metrics: List of metrics to add aggregates for
            agg_by_factors: Whether metrics are aggregated by factors
            verbose: If True, print the generated SQL query. Default is False.
        """
        agg_exprs = []
        if 'Quantity' in metrics:
            agg_exprs.append(query.Quantity.sum().name("Quantity"))

        if 'Value' in metrics or 'Allocation' in metrics:
            if agg_by_factors:
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

        # Do metrics need to be aggregated by factors?
        agg_by_factors = (('Allocation' in metrics) or ('Value' in metrics)) and \
                        any(d.startswith('Level_') or d == 'Factor' for d in dimensions)

        # Get base tables
        tables = self._get_base_tables()
        
        # Build base query
        # - save this to be used for allocation calculation
        unfiltered_query = self._build_base_query(tables, dimensions, filters, verbose)
        
        # Apply filters to get filtered query (before aggregation)
        # - save this to be used for allocation calculation
        filtered_query = self._apply_filters(unfiltered_query, filters, verbose)
        
        # Add aggregates to get metrics
        metrics_query = self._add_aggregates(filtered_query, dimensions, metrics, agg_by_factors, verbose)
        
        # Add allocation if requested
        if 'Allocation' in metrics:
            # Build total value query for allocation calculation
            # - filtered_query and unfiltered_query have the Price column
            # - which is required to build the total value query for the allocation calculation
            total_value_subquery = self._build_total_value_subquery(
                unfiltered_query, 
                filtered_query, 
                portfolio_allocation, 
                agg_by_factors, 
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
