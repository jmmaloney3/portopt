---
status: "accepted"
date: 2024-12-27
decision-makers: [Portfolio Optimization Team, LLM Agent]
consulted: [Portfolio Analytics Domain Experts]
informed: [Development Team]
---

# UNDEFINED Factor Category for Tickers Without Factor Weights

## Context and Problem Statement

In portfolio analytics, not all securities have factor exposures defined in the factor weights table. When calculating portfolio metrics grouped by factor dimensions (e.g., Level_0, Level_1), these tickers would be excluded from results because they cannot be joined with the factor tables. This creates incomplete portfolio views and potential allocation discrepancies.

The problem occurs when:
- Factor-based grouping or filtering is requested (Level_0, Level_1, Factor dimensions)
- Some tickers exist in holdings but not in factor_weights table
- LEFT JOIN operations result in NULL values for factor dimensions
- Standard GROUP BY operations exclude NULL values, losing positions

Without proper handling, a $100,000 portfolio might only show $85,000 in factor-based metrics if $15,000 worth of positions lack factor definitions.

## Decision Drivers

* **Completeness**: All portfolio positions must be included in metrics, regardless of factor coverage
* **Accuracy**: Total portfolio values must be consistent across different grouping methods
* **Transparency**: Users should clearly see which positions lack factor definitions
* **Flexibility**: Solution must work across different factor hierarchy structures
* **Consistency**: Undefined tickers should be counted exactly once, not zero times or multiple times

## Considered Options

* **Option 1: Exclude undefined tickers** - Only include positions with factor weights in results
* **Option 2: Default factor assignment** - Assign all undefined tickers to a single default factor
* **Option 3: UNDEFINED category with structured hierarchy** - Create "UNDEFINED" factor matching hierarchy structure
* **Option 4: Separate undefined metrics** - Report defined and undefined positions separately
* **Option 5: Throw exception on missing factors** - Fail fast when undefined factor assignments are discovered

## Decision Outcome

Chosen option: "UNDEFINED category with structured hierarchy", because it provides complete portfolio coverage while maintaining clear distinction between defined and undefined factor exposures, and integrates seamlessly with existing aggregation logic.

### Consequences

* Good, because all portfolio positions are included in metrics calculations
* Good, because total values are consistent regardless of grouping method
* Good, because undefined positions are clearly labeled and identifiable
* Good, because it integrates seamlessly with existing SQL aggregation logic
* Good, because it scales to any factor hierarchy depth (Level_0, Level_1, Level_2, etc.)
* Neutral, because it requires users to understand the "UNDEFINED" category meaning
* Bad, because it adds slight complexity to factor hierarchy interpretation

### Confirmation

The implementation is confirmed through:
1. **Integration tests**: All portfolio positions appear in factor-based metrics
2. **Consistency tests**: Total values match between ticker-based and factor-based groupings
3. **Hierarchy tests**: UNDEFINED category appears correctly at all factor levels
4. **Edge case tests**: Portfolios with 100% undefined tickers produce correct results

## Pros and Cons of the Options

### UNDEFINED category with structured hierarchy

The chosen approach uses SQL COALESCE functions to assign default values matching the factor hierarchy structure:

```sql
COALESCE(Factor, 'UNDEFINED') AS Factor,
COALESCE(Weight, 1.0) AS Weight,
COALESCE(Level_0, 'UNDEFINED') AS Level_0,
COALESCE(Level_1, 'N/A') AS Level_1,
COALESCE(Level_2, 'N/A') AS Level_2
```

* Good, because it ensures 100% portfolio coverage in all metrics
* Good, because undefined positions have Weight=1.0, preventing fractional counting
* Good, because the hierarchy structure is maintained (UNDEFINED at Level_0, N/A at deeper levels)
* Good, because it integrates transparently with existing aggregation logic
* Good, because users can easily filter out or focus on UNDEFINED positions
* Neutral, because it requires documentation for users to understand the convention
* Bad, because it slightly complicates the factor hierarchy interpretation

### Exclude undefined tickers

Simply omit tickers without factor weights from factor-based metrics.

* Good, because it keeps factor-based results "pure" with only defined factors
* Good, because it requires no special handling logic
* Bad, because it creates incomplete portfolio views with missing positions
* Bad, because total values become inconsistent across different grouping methods
* Bad, because users lose visibility into which positions lack factor definitions
* Bad, because it can lead to significant portfolio coverage gaps

### Default factor assignment

Assign all undefined tickers to an existing factor (e.g., first factor alphabetically).

* Good, because all positions remain in the results
* Neutral, because it maintains total value consistency
* Bad, because it misrepresents the true factor exposure of undefined tickers
* Bad, because it inflates the apparent size of the chosen default factor
* Bad, because it makes it impossible to identify which positions lack proper factor definitions
* Bad, because it can lead to misleading factor-based analysis

### Separate undefined metrics

Report defined and undefined positions in separate result sets or columns.

* Good, because it clearly separates defined from undefined positions
* Good, because it preserves the purity of factor-based analysis
* Neutral, because it maintains complete portfolio coverage
* Bad, because it complicates the API with multiple return values or result structures
* Bad, because it makes aggregation and comparison more difficult for users
* Bad, because it doesn't integrate well with existing single-result metrics workflows

### Throw exception on missing factors

Immediately raise an exception when any ticker lacks factor weight definitions, forcing users to address data completeness issues.

* Good, because it enforces complete factor coverage and data quality
* Good, because it prevents silent data omissions that could lead to incorrect analysis
* Good, because it's simple to implement and understand
* Good, because it forces explicit handling of data completeness issues
* Neutral, because it requires users to maintain complete factor weight coverage
* Bad, because it makes the system brittle when factor coverage is naturally incomplete
* Bad, because it prevents any analysis when even a small portion of positions lack factors
* Bad, because it doesn't accommodate real-world scenarios where some securities inherently lack factor classifications
* Bad, because it blocks legitimate use cases where partial factor coverage is acceptable

## More Information

The implementation is located in `src/portopt/metrics.py` in the `_handle_undefined_factor_weights()` method. This method is automatically called after LEFT JOINing factor tables, ensuring that all positions are properly categorized.

The UNDEFINED category follows these conventions:
- **Factor**: Set to 'UNDEFINED'
- **Weight**: Set to 1.0 (full position weight, no fractional allocation)
- **Level_0**: Set to 'UNDEFINED' (primary categorization)
- **Level_1, Level_2, etc.**: Set to 'N/A' (not applicable for deeper hierarchy levels)

This approach was chosen after analyzing real portfolio data where 10-15% of positions typically lack factor definitions, making exclusion impractical for complete portfolio analysis.

Related implementation details:
- `_requires_factor_tables()`: Determines when undefined factor handling is needed
- `_aggregate_factor_weights()`: Processes UNDEFINED factors alongside defined factors (see ADR-001)
- LEFT JOIN strategy ensures all tickers are preserved in the query pipeline 