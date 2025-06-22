---
status: "accepted"
date: 2024-12-27
decision-makers: [Portfolio Optimization Team, LLM Agent]
consulted: [Portfolio Analytics Domain Experts]
informed: [Development Team]
---

# Factor Weight Pre-Aggregation to Prevent Double Counting

## Context and Problem Statement

In portfolio metrics calculations, when securities have multiple factor exposures with fractional weights, naive SQL aggregation leads to systematic double-counting of position values. For example, if AAPL has exposures to both "US_Large_Growth" (weight: 0.7) and "US_Large_Tech" (weight: 0.3), a simple `SUM(Quantity * Price)` grouped by factor levels would count the full $15,000 position twice, resulting in $30,000 total value instead of the correct $15,000.

**Naive Aggregation Example:**
```sql
-- Naive aggregation double-counts the position:
SELECT Level_0, SUM(Quantity * Price) AS Value
FROM base_query
GROUP BY Level_0
-- Results in: Equity = $30,000 (should be $15,000)
```

This problem manifests when:
- Tickers have multiple factor exposures with fractional weights (summing to 1.0)
- Users request metrics grouped by factor hierarchy levels (Level_0, Level_1, etc.)
- Factor weights table JOIN creates multiple rows for the same position

## Decision Drivers

* **Data Accuracy**: Portfolio metrics must reflect true position values, not inflated double-counted values
* **Performance**: Solution must handle large portfolios efficiently without degrading query performance
* **Maintainability**: Implementation should be transparent and debuggable for future developers
* **Flexibility**: Must work across different factor hierarchies and aggregation levels

## Considered Options

* **Option 1: Python-based post-processing** - Handle aggregation in pandas after SQL query
* **Option 2: Complex SQL with window functions** - Use SQL analytics functions to weight positions
* **Option 3: Pre-aggregate factor weights** - Consolidate weights before final metrics calculation
* **Option 4: Separate queries per factor level** - Execute individual queries and combine results

## Decision Outcome

Chosen option: "Pre-aggregate factor weights", because it provides the most accurate, efficient, and maintainable solution while leveraging SQL's strengths for aggregation operations.

### Consequences

* Good, because it eliminates double-counting at the SQL level, ensuring accuracy
* Good, because it leverages DuckDB's optimized aggregation engine for performance
* Good, because the solution is transparent and debuggable with verbose SQL output
* Good, because it handles arbitrary factor hierarchies without code changes
* Bad, because it adds complexity to the query pipeline with an additional aggregation step
* Bad, because it requires careful understanding of when to apply the pre-aggregation

### Confirmation

The implementation is confirmed through:
1. **Regression test**: `test_original_double_counting_bug_with_factor_filters()` validates the fix
2. **Mathematical verification**: Tests compare SQL results against manual calculations
3. **Verbose SQL output**: Developers can inspect generated queries to verify correct logic
4. **Integration testing**: All existing portfolio metrics tests continue to pass

## Pros and Cons of the Options

### Pre-aggregate factor weights

The chosen approach creates an intermediate aggregation step that consolidates fractional factor weights before final metrics calculation:

```sql
-- Step 1: Pre-aggregate weights
SELECT Ticker, Account, Quantity, Price, Level_0, Level_1, SUM(Weight) AS Weight
FROM base_query_with_factor_joins
GROUP BY Ticker, Account, Quantity, Price, Level_0, Level_1

-- Step 2: Calculate metrics with aggregated weights  
SELECT Level_0, SUM(Quantity * Price * Weight) AS Value
FROM pre_aggregated_query
GROUP BY Level_0
```

* Good, because it mathematically eliminates double-counting at the source
* Good, because it maintains full SQL pipeline efficiency 
* Good, because it's transparent and debuggable
* Good, because it scales to any number of factor levels
* Neutral, because it requires developers to understand the aggregation concept
* Bad, because it adds one additional query step to the pipeline

### Python-based post-processing

Handle weight aggregation in pandas after executing SQL query.

* Good, because it keeps SQL queries simpler
* Good, because Python logic might be more familiar to some developers
* Bad, because it moves business logic out of the optimized SQL engine
* Bad, because it requires loading more data into memory for processing
* Bad, because it makes the overall pipeline less efficient

### Complex SQL with window functions

Use SQL analytics functions like `ROW_NUMBER()` and `PARTITION BY` to handle weights.

* Good, because it keeps everything in SQL
* Neutral, because window functions are powerful but complex
* Bad, because the resulting SQL is difficult to understand and maintain
* Bad, because it's harder to verify correctness of complex window function logic
* Bad, because it may not perform as well as simple aggregations

### Separate queries per factor level

Execute individual SQL queries for each factor level and combine results.

* Good, because each individual query is simple and easy to understand
* Bad, because it requires multiple database round-trips
* Bad, because it doesn't scale to dynamic factor hierarchies
* Bad, because it complicates the code with query result merging logic
* Bad, because it's less efficient than a single optimized query

## More Information

The implementation is located in `src/portopt/metrics.py` in the `_aggregate_factor_weights()` method. This method is automatically called whenever factor tables are joined to the base query, ensuring consistent behavior across all metrics calculations.

The original bug was discovered during portfolio allocation calculations where filtered results (e.g., `filters={'Level_0': ['Equity']}`) showed 50% higher values than expected. The pre-aggregation solution was validated to produce mathematically correct results matching manual calculations.

Related implementation details:
- `_requires_factor_tables()`: Determines when factor weight aggregation is needed
- `_handle_undefined_factor_weights()`: Handles tickers without factor weights (see ADR-002)
- Comprehensive test suite in `tests/test_metrics.py` validates the solution 