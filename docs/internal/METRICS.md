# MetricsMixin Architecture Documentation

> A high‑level technical map for human contributors *and* LLM coding agents.

## Overview

The `MetricsMixin` class provides portfolio metrics calculation capabilities through a mixin architecture pattern. It uses [ibis](https://ibis-project.org/) as the query engine with DuckDB as the backend to implement efficient, maintainable SQL-based analytics for portfolio data.

## Design Philosophy

### Mixin Architecture
The metrics functionality is implemented as a mixin class that can be composed with the main `Portfolio` class. This design provides:
- **Separation of Concerns**: Metrics logic is isolated from core portfolio data management
- **Modularity**: Can be easily tested in isolation and reused across different portfolio implementations
- **Maintainability**: Changes to metrics calculations don't affect other portfolio functionality

### Query-Based Approach
Rather than implementing metrics calculations in pure Python/pandas, the module uses ibis to generate optimized SQL queries:
- **Performance**: Leverages DuckDB's columnar engine for fast aggregations
- **Expressiveness**: Complex multi-dimensional queries are easier to reason about
- **Maintainability**: Single algorithm handles all metric combinations rather than multiple code paths
- **Flexibility**: Supports potential future migration to a database such as *BigQuery*

## Core Architecture

### Data Model
The metrics system operates on a star schema with the following tables:

**Fact Tables:**
- `holdings`: Core position data (Ticker, Account, Quantity)
- `factor_weights`: Factor exposure weights (Ticker, Factor, Weight)

**Dimension Tables:**
- `prices`: Current market prices (Ticker, Price)
- `factors`: Factor hierarchy (Factor, Level_0, Level_1, Level_2, ...)
- `accounts`: Account metadata (Account, Type, Institution)
- `tickers`: Security metadata (Ticker, Name, Category)

### Query Pipeline
The metrics calculation follows a structured pipeline:

```
1. Table Loading → 2. Base Query → 3. Filtering → 4. Aggregation → 5. Allocation
```

1. **Table Loading** (`_get_base_tables`): Dynamically loads only required tables based on requested dimensions/filters
2. **Base Query** (`_build_base_query`): Joins tables and handles factor weight aggregation
3. **Filtering** (`_apply_filters`): Applies dimension filters to narrow results
4. **Aggregation** (`_add_aggregates`): Groups by dimensions and calculates metrics
5. **Allocation** (`_add_allocation`): Adds percentage allocation calculations

## Critical Implementation Details

### Double-Counting Prevention
Portfolio metrics calculations face a critical challenge when securities have multiple factor exposures with fractional weights. The solution involves pre-aggregating factor weights before final metrics calculation to prevent systematic double-counting of position values.

**Implementation**: See [ADR-001: Factor Weight Pre-Aggregation to Prevent Double Counting](adr/001-double-counting-prevention.md) for detailed analysis of the problem, considered alternatives, and the chosen solution.

**Key Method**: `_aggregate_factor_weights()` automatically handles this whenever factor tables are joined.

### Factor Table Requirements Logic
The system intelligently determines which tables to load based on requested dimensions and filters:

```python
def _requires_factor_tables(dimensions, filters):
    # Check if any dimension/filter references factors
    requires_factor_weights = any(d.startswith('Level_') or d == 'Factor' 
                                 for d in dimensions + list(filters.keys()))
    requires_factor_levels = any(d.startswith('Level_') 
                                for d in dimensions + list(filters.keys()))
    return requires_factor_weights, requires_factor_levels
```

This optimization prevents unnecessary table joins and improves performance.

### Undefined Factor Handling
Portfolio analytics must handle securities that lack factor weight definitions while maintaining complete portfolio coverage and consistent total values across different grouping methods.

**Implementation**: See [ADR-002: UNDEFINED Factor Category for Tickers Without Factor Weights](adr/002-undefined-factor-handling.md) for detailed analysis of the problem, considered alternatives, and the chosen solution.

**Key Method**: `_handle_undefined_factor_weights()` assigns undefined tickers to a structured "UNDEFINED" category that integrates seamlessly with factor hierarchy aggregations.

## Public Interface

### Main Method: `getMetrics()`
```python
def getMetrics(
    *dimensions: str,                                    # Variable dimensions to group by
    metrics: Optional[List[str]] = None,                 # ['Quantity', 'Value', 'Allocation']
    filters: Optional[Dict[str, Union[str, List[str]]]] = None,  # Dimension filters
    portfolio_allocation: bool = False,                  # Allocation calculation method
    verbose: bool = False                               # SQL query debugging
) -> pd.DataFrame
```

**Supported Dimensions:**
- `Ticker`: Individual securities
- `Account`: Portfolio accounts (IRA, 401k, etc.)
- `Factor`: Individual factor names
- `Level_0`, `Level_1`, `Level_2`, etc.: Factor hierarchy levels

**Supported Metrics:**
- `Quantity`: Sum of position quantities
- `Value`: Market value (Quantity × Price × Weight)
- `Allocation`: Percentage allocation

**Filter Examples:**
```python
# Single value filter
filters={'Account': 'IRA'}

# Multiple value filter  
filters={'Level_0': ['Equity', 'Fixed Income']}

# Multiple dimension filters
filters={'Account': ['IRA', '401k'], 'Level_0': 'Equity'}
```

**Allocation Methods:**
- `portfolio_allocation=False`: Allocations relative to filtered results (sum to 100%)
- `portfolio_allocation=True`: Allocations relative to total portfolio (may sum to <100%)

## Error Handling

### Dimension Validation
The system validates that all requested dimensions exist in the final query:
```python
missing_dims = [dim for dim in dimensions if dim not in query.columns]
if missing_dims:
    raise ValueError(f"Requested dimensions not found: {missing_dims}. "
                    f"Available columns: {list(query.columns)}")
```

### Missing Table Handling
When factor dimensions are requested but factor tables aren't available:
```python
if requires_factor_weights and 'factor_weights' not in tables:
    raise ValueError("Factor weights are required for the requested dimensions/filters, "
                    "but factor_weights table is not available")
```

## Performance Considerations

### Lazy Table Loading
Tables are only loaded when needed based on the query requirements:
- Holdings and prices are always loaded (core data)
- Factor tables are loaded only when factor dimensions/filters are used
- Other dimension tables are loaded opportunistically

### Query Optimization
- Uses LEFT JOINs to preserve all positions
- Pre-aggregates factor weights to minimize final aggregation complexity
- Leverages DuckDB's columnar engine for efficient aggregations

### Memory Management
- Creates temporary DuckDB tables in memory
- Tables are automatically cleaned up when the connection closes
- Uses pandas DataFrame interchange for efficient data transfer

## Testing Strategy

The module includes comprehensive tests covering:
- **Basic functionality**: Individual metrics, dimensions, filters
- **Edge cases**: Missing factor weights, invalid dimensions, empty results
- **Mathematical accuracy**: Verification against manual calculations
- **Regression tests**: Specific test for the original double-counting bug
- **Performance tests**: Large dimension combinations

Key test categories:
- `test_original_double_counting_bug_with_factor_filters()`: Regression test for the critical bug
- `test_invalid_dimension_validation()`: Error handling validation
- `test_total_value_consistency_*()`: Ensures consistent totals across different groupings

## Dependencies

### Core Dependencies
- **ibis**: Query expression framework
- **duckdb**: SQL analytics engine (via ibis backend)
- **pandas**: Data interchange and result formatting
- **typing**: Type hints for better code documentation

### Integration Dependencies
The mixin expects the host class to provide these methods:
- `getHoldings()`: Returns holdings DataFrame
- `getPrices()`: Returns prices DataFrame  
- `getFactors()`: Returns factors DataFrame (optional)
- `getFactorWeights()`: Returns factor weights DataFrame (optional)
- `getAccounts()`: Returns accounts DataFrame (optional)
- `getTickers()`: Returns tickers DataFrame (optional)

## Future Enhancements

### Potential Improvements
1. **Caching**: Cache table creation for repeated queries
2. **Streaming**: Support for larger-than-memory datasets
3. **Additional Metrics**: Risk metrics, performance attribution
4. **Query Optimization**: More sophisticated join optimization
5. **Parallel Processing**: Multi-threaded query execution

### Architectural Considerations
- The mixin pattern allows for easy extension with additional mixins
- The ibis abstraction makes it possible to switch backends (PostgreSQL, BigQuery, etc.)
- The query pipeline is extensible for additional processing steps

## Debugging

### Verbose Mode
Set `verbose=True` to see generated SQL queries:
```python
result = portfolio.getMetrics('Level_0', 'Level_1', verbose=True)
```

This prints the SQL for each pipeline stage:
- Base Query
- Pre-aggregated Weights Query  
- Filtered Query
- Grouped Query
- Total Value Query
- Final Metrics Query

### Common Issues
1. **Double-counting**: Usually indicates factor weight aggregation isn't working
2. **Missing data**: Check that required tables are available
3. **Dimension errors**: Verify dimension names match available columns
4. **Allocation issues**: Check portfolio_allocation setting and filter logic
