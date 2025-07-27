# Performance Analysis Requirements Specification

## Document Information

- **Requirement ID**: REQ-2025-001
- **Title**: Portfolio Performance Analysis & Attribution System
- **Author**: Portfolio Requirements Interview Process
- **Date Created**: 2025-07-25
- **Last Updated**: 2025-07-27
- **Status**: Approved
- **Priority**: Critical
- **Target Release**: v0.2.0

## Executive Summary

This requirement addresses the critical "flying blind" problem where portfolio managers lack objective performance metrics to evaluate investment decisions. The system will provide comprehensive performance analysis including time-weighted and money-weighted returns, factor attribution, risk metrics, and comparison capabilities against alternative investment strategies.

## Requirements Overview

This document organizes requirements into five interconnected types that work together to ensure complete coverage from business need to system requirements:

### **Business Requirements** → **WHY**
Define the fundamental problems, strategic goals, and user value that justify this development effort.

### **Functional Requirements** → **WHAT**
Define the core capabilities and behaviors the system must provide for performance calculation, transaction integration, and attribution analysis.

### **Developer Experience (DX) Requirements** → **HOW** 
Define how developers discover, access, and successfully use the performance analysis capabilities following existing portopt patterns.

### **Non-Functional Requirements** → **HOW WELL**
Define performance, reliability, and resource constraints the system must meet.

### **Technical Constraints** → **WITHIN WHAT LIMITS**
Define platform requirements, dependency constraints, and compatibility requirements.

## Business Requirements

*Business requirements capture the WHY behind developing performance analysis capabilities - the fundamental problems that need solving, the strategic goals to achieve, and the user value to deliver.*

### Problem Statements

#### Primary Problem

**PS-1**: Portfolio managers using portopt lack objective performance metrics to evaluate investment decisions

- **Who**: Portfolio managers and individual investors using the portopt library for portfolio management
- **What**: Need objective, quantitative performance analysis to evaluate investment decisions and portfolio performance
- **Why**: To replace subjective assessment with data-driven decision making for portfolio optimization and rebalancing
- **Current State**: Relying on brokerage websites and subjective assessment of daily returns without comprehensive performance metrics, factor attribution, or benchmark comparisons
- **Impact**: Suboptimal investment decisions, inability to evaluate strategy effectiveness, missed opportunities for portfolio improvement, uncertainty about retirement readiness

**Traceability:**
- **Addresses**: None (primary problem statement)
- **Addressed By**: OBJ-1 (Enable data-driven portfolio performance analysis)
- **Related Problems**: PS-2 (Limited factor attribution capabilities), PS-3 (No benchmark comparison capabilities)

#### Secondary Problems

**PS-2**: Current portfolio analysis lacks comprehensive factor analysis capabilities

- **Who**: Portfolio managers analyzing factor-based investment strategies and managing portfolio risk
- **What**: Need bidirectional factor analysis: (1) understand which factors contribute to portfolio performance, and (2) understand which tickers contribute to portfolio's exposure to each factor
- **Why**: To evaluate factor allocation decisions, identify sources of performance, and manage factor concentration risk
- **Current State**: Factor weights are defined but no attribution analysis or exposure analysis is available
- **Impact**: Cannot identify which factor allocations are contributing positively or negatively to returns, and cannot identify concentration risk or unintended factor exposure through specific holdings

**Traceability:**
- **Addresses**: PS-1 (lack of objective performance metrics)
- **Addressed By**: OBJ-2 (Provide comprehensive factor attribution analysis)
- **Related Problems**: PS-1 (primary problem), PS-3 (benchmark comparison)

**PS-3**: No capability to compare actual portfolio performance against alternative strategies

- **Who**: Portfolio managers evaluating investment strategy effectiveness
- **What**: Need to compare actual portfolio returns against alternative allocation strategies (e.g., 60/40, 80/20, custom factor allocations)
- **Why**: To validate current strategy effectiveness and identify potentially better approaches
- **Current State**: No systematic way to backtest alternative strategies against actual performance
- **Impact**: Cannot determine if current investment strategy outperforms standard benchmarks or alternative approaches

**Traceability:**
- **Addresses**: PS-1 (lack of objective performance metrics)
- **Addressed By**: OBJ-1 (data-driven analysis), OBJ-3 (strategy comparison capabilities)
- **Related Problems**: PS-1 (primary problem), PS-2 (factor attribution)

### Objectives & Key Results (OKRs)

#### Primary OKR

**OBJ-1**: Enable data-driven portfolio performance analysis to replace subjective assessment with objective metrics

**Key Results:**
- **KR1**: Reduce decision-making uncertainty by providing objective performance metrics within 30 seconds for any time period
- **KR2**: Enable quarterly rebalancing decisions based on quantitative performance data rather than subjective assessment
- **KR3**: Achieve comprehensive performance visibility across portfolio, account, ticker, and factor dimensions

**Traceability:**
- **Addresses Problems**: PS-1 (lack of objective performance metrics)
- **Supported By**: US-1 (time-weighted returns), US-2 (money-weighted returns), US-3 (risk metrics), US-4 (factor attribution)
- **Related Objectives**: OBJ-2 (factor attribution), OBJ-3 (strategy comparison)

#### Supporting OKRs

**OBJ-2**: Provide comprehensive factor attribution analysis for portfolio performance evaluation

**Key Results:**
- **KR1**: Enable factor-level performance attribution across 4-level factor hierarchy with 25 leaf factors
- **KR2**: Support bidirectional attribution analysis (factors→tickers and tickers→factors)  
- **KR3**: Provide time-based attribution analysis for any custom time period

**Traceability:**
- **Addresses Problems**: PS-2 (limited factor attribution)
- **Supported By**: US-4 (factor attribution), US-5 (factor contribution analysis)
- **Related Objectives**: OBJ-1 (data-driven analysis), OBJ-3 (strategy comparison)

**OBJ-3**: Enable comparison of actual portfolio performance against alternative investment strategies

**Key Results:**
- **KR1**: Support comparison against standard benchmark portfolios (60/40, 80/20, S&P 500)
- **KR2**: Enable custom alternative portfolio definition and backtesting
- **KR3**: Provide standardized performance comparison metrics using bt/ffn framework formats

**Traceability:**
- **Addresses Problems**: PS-3 (no benchmark comparison)
- **Supported By**: US-6 (benchmark comparison), US-7 (alternative strategy analysis)
- **Related Objectives**: OBJ-1 (data-driven analysis), OBJ-2 (factor attribution)

### User Stories

#### Core User Stories

**US-1**: As a portfolio manager,
I want to calculate time-weighted returns for my portfolio over any time period,
So that I can evaluate investment performance isolated from cash flow timing.

**Acceptance Criteria:**
- [ ] **Flexible Asset Grouping**: Can calculate TWR for:
  - [ ] Entire portfolio
  - [ ] One or more accounts
  - [ ] One or more tickers
  - [ ] One or more factors
- [ ] Supports predefined time periods (YTD, last quarter, last year) and custom date ranges
- [ ] Handles contributions and withdrawals properly without affecting performance measurement
- [ ] Returns results within 30 seconds for typical portfolio (50 tickers, 10 accounts)
- [ ] Provides clear warnings when data is incomplete for requested time period

**Traceability:**
- **Supports Objective**: OBJ-1 (Enable data-driven portfolio performance analysis)
- **Addresses Problem**: PS-1 (lack of objective performance metrics)
- **Implemented By**: FR-1 (TWR calculation engine), FR-2 (time period handling)
- **Related Stories**: US-2 (money-weighted returns), US-3 (risk metrics)

**US-2**: As a portfolio manager,
I want to calculate money-weighted returns for my portfolio,
So that I can understand the actual return experience on my invested dollars.

**Acceptance Criteria:**
- [ ] Can calculate MWR using Internal Rate of Return methodology
- [ ] **Flexible Asset Grouping**: Supports same asset grouping options as TWR:
  - [ ] Entire portfolio, one or more accounts, one or more tickers, one or more factors
- [ ] Accounts for timing and size of all contributions and withdrawals
- [ ] Supports same time period options as TWR calculations
- [ ] Provides clear explanation of when to use MWR vs TWR
- [ ] Handles complex cash flow patterns (irregular contributions, withdrawals)

**Traceability:**
- **Supports Objective**: OBJ-1 (Enable data-driven portfolio performance analysis)
- **Addresses Problem**: PS-1 (lack of objective performance metrics)
- **Implemented By**: FR-3 (MWR calculation engine), FR-2 (time period handling)
- **Related Stories**: US-1 (time-weighted returns), US-3 (risk metrics)

**US-3**: As a portfolio manager,
I want to calculate risk metrics (volatility, Sharpe ratio, maximum drawdown) for my portfolio,
So that I can evaluate risk-adjusted performance and drawdown characteristics.

**Acceptance Criteria:**
- [ ] Calculates portfolio volatility (standard deviation of returns)
- [ ] Calculates Sharpe ratio with configurable risk-free rate
- [ ] Calculates maximum drawdown over the analysis period
- [ ] **Flexible Asset Grouping**: Supports risk metric calculation for:
  - [ ] Entire portfolio, one or more accounts, one or more tickers, one or more factors
- [ ] Risk metrics calculated over same time periods as return metrics

**Traceability:**
- **Supports Objective**: OBJ-1 (Enable data-driven portfolio performance analysis)
- **Addresses Problem**: PS-1 (lack of objective performance metrics)
- **Implemented By**: FR-4 (risk metrics calculation engine)
- **Related Stories**: US-1 (TWR), US-2 (MWR), US-4 (factor attribution)

**US-4**: As a portfolio manager,
I want to analyze factor attribution for my portfolio performance,
So that I can understand which factors contributed positively or negatively to returns.

**Acceptance Criteria:**
- [ ] Provides factor-level return attribution across 4-level factor hierarchy
- [ ] Shows factor contribution to total portfolio returns with specific percentages
- [ ] **Flexible Asset Grouping**: Supports factor attribution analysis for:
  - [ ] Entire portfolio, one or more accounts, one or more tickers, one or more factors
- [ ] Handles missing factor weights using existing portopt UNDEFINED factor logic
- [ ] Results formatted as "Factor X contributed +2.3% to total returns"

**Traceability:**
- **Supports Objective**: OBJ-2 (Provide comprehensive factor attribution analysis)
- **Addresses Problem**: PS-2 (limited factor attribution capabilities)
- **Implemented By**: FR-5 (factor attribution engine), FR-6 (factor weight handling)
- **Related Stories**: US-5 (factor contribution), US-1 (TWR), US-3 (risk metrics)

**US-5**: As a portfolio manager,
I want to identify which holdings are driving my exposure to particular factors,
So that I can understand factor concentration and make informed rebalancing decisions.

**Acceptance Criteria:**
- [ ] Shows which tickers contribute to specific factor exposures
- [ ] Identifies holdings with highest factor concentrations
- [ ] **Flexible Asset Grouping**: Supports bidirectional analysis for:
  - [ ] Entire portfolio, one or more accounts, one or more tickers, one or more factors
  - [ ] Factors→tickers analysis and tickers→factors analysis
- [ ] Provides factor concentration warnings above configurable thresholds
- [ ] Results help identify diversification opportunities

**Traceability:**
- **Supports Objective**: OBJ-2 (Provide comprehensive factor attribution analysis)
- **Addresses Problem**: PS-2 (limited factor attribution capabilities)
- **Implemented By**: FR-5 (factor attribution engine), FR-7 (factor concentration analysis)
- **Related Stories**: US-4 (factor attribution), US-6 (benchmark comparison)

**US-6**: As a portfolio manager,
I want to compare my actual portfolio performance against benchmark strategies,
So that I can evaluate whether my investment approach is outperforming standard alternatives.

**Acceptance Criteria:**
- [ ] Can compare against S&P 500 benchmark over any time period
- [ ] Supports comparison against standard portfolios (60/40, 80/20 allocations)
- [ ] Can define custom benchmark portfolios with specific ticker or factor allocations
- [ ] Shows side-by-side performance metrics (returns, risk, Sharpe ratio)
- [ ] Results use standardized bt/ffn framework formats for consistency

**Traceability:**
- **Supports Objective**: OBJ-3 (Enable comparison against alternative strategies)
- **Addresses Problem**: PS-3 (no benchmark comparison capabilities)
- **Implemented By**: FR-8 (benchmark comparison engine), FR-9 (alternative portfolio calculation)
- **Related Stories**: US-7 (alternative strategies), US-1 (TWR), US-3 (risk metrics)

**US-7**: As a portfolio manager,
I want to backtest alternative investment strategies against my actual portfolio performance,
So that I can identify potentially better allocation approaches.

**Acceptance Criteria:**
- [ ] Can define alternative portfolios with custom factor or ticker allocations
- [ ] Supports different rebalancing frequencies for alternative strategies
- [ ] Backtests alternative strategies over same time periods as actual portfolio
- [ ] Accounts for actual contributions and market timing in comparisons
- [ ] Integrates with existing bt framework for sophisticated backtesting

**Traceability:**
- **Supports Objective**: OBJ-3 (Enable comparison against alternative strategies)
- **Addresses Problem**: PS-3 (no benchmark comparison capabilities)
- **Implemented By**: FR-9 (alternative portfolio calculation), FR-10 (backtesting integration)
- **Related Stories**: US-6 (benchmark comparison), US-1 (TWR), US-2 (MWR)

## Functional Requirements

*This section defines what the system must do - the core capabilities and behaviors that fulfill business requirements.*

### Performance Calculation Engine

**FR-1**: The system must calculate time-weighted returns (TWR) for portfolios, accounts, tickers, and factors

**Priority**: Must have
**User Role**: Portfolio Manager
**Preconditions**: Historical price data and transaction data are available for the requested time period
**Postconditions**: TWR calculated and cached, methodology metadata stored
**Dependencies**: None

**Completion Criteria:**
- [ ] TWR calculation engine implemented following industry standard methodology
- [ ] Handles cash flows (contributions, withdrawals) without affecting performance measurement
- [ ] **Flexible Asset Grouping**: Supports calculation for multiple asset groupings:
  - [ ] Entire portfolio
  - [ ] One or more accounts
  - [ ] One or more tickers
  - [ ] One or more factors
- [ ] Performance: Completes within 30 seconds for typical portfolio (50 tickers, 10 accounts)
- [ ] Integration: Works with existing portopt factor weight and holdings systems
- [ ] Documentation: Clear explanation of TWR methodology and when to use it

**Traceability:**
- **Problem Statement**: PS-1 - Portfolio managers lack objective performance metrics
- **Objective**: OBJ-1 - Enable data-driven portfolio performance analysis
- **User Story**: US-1 - Calculate time-weighted returns for any time period
- **Impacts**: FR-4 (risk metrics), FR-5 (factor attribution), FR-8 (benchmark comparison)

**FR-2**: The system must support flexible time period specification for all performance calculations

**Priority**: Must have
**User Role**: Portfolio Manager, Developer
**Preconditions**: Performance calculation engine is available
**Postconditions**: Time periods properly parsed and validated for calculation requests
**Dependencies**: FR-1 (TWR calculation)

**Completion Criteria:**
- [ ] Supports predefined periods ('YTD', 'last_quarter', 'last_year', 'last_month', 'last_week')
- [ ] Supports custom date ranges using start_date and end_date parameters
- [ ] Validates time period availability against transaction and price data
- [ ] Provides clear error messages for invalid or unavailable time periods
- [ ] Incompatible parameter combinations (time_period + start_date) raise appropriate errors

**Traceability:**
- **Problem Statement**: PS-1 - Portfolio managers lack objective performance metrics
- **Objective**: OBJ-1 - Enable data-driven portfolio performance analysis
- **User Story**: US-1 - Calculate TWR for any time period
- **Impacts**: FR-3 (MWR calculation), FR-4 (risk metrics), FR-5 (factor attribution)

**FR-3**: The system must calculate money-weighted returns (MWR) using Internal Rate of Return methodology

**Priority**: Should have
**User Role**: Portfolio Manager
**Preconditions**: Complete transaction history including cash flows for the requested period
**Postconditions**: MWR calculated accounting for cash flow timing and amounts
**Dependencies**: FR-2 (time period handling)

**Completion Criteria:**
- [ ] MWR calculation using IRR methodology for actual dollar return experience
- [ ] Handles complex cash flow patterns (irregular contributions, multiple withdrawals)
- [ ] **Flexible Asset Grouping**: Supports same asset groupings as TWR calculations:
  - [ ] Entire portfolio, one or more accounts, one or more tickers, one or more factors
- [ ] Supports same time period options as TWR calculations
- [ ] Performance: Completes within reasonable time for complex cash flow scenarios
- [ ] Documentation: Clear explanation of MWR vs TWR and when to use each

**Traceability:**
- **Problem Statement**: PS-1 - Portfolio managers lack objective performance metrics
- **Objective**: OBJ-1 - Enable data-driven portfolio performance analysis
- **User Story**: US-2 - Calculate money-weighted returns for actual dollar experience
- **Impacts**: FR-8 (benchmark comparison), FR-9 (alternative portfolio calculation)

**FR-4**: The system must calculate risk metrics (volatility, Sharpe ratio, maximum drawdown) for performance evaluation

**Priority**: Must have
**User Role**: Portfolio Manager, Risk Analyst
**Preconditions**: Return series calculated for the requested time period and scope
**Postconditions**: Risk metrics calculated and available for analysis and comparison
**Dependencies**: FR-1 (TWR calculation), FR-2 (time period handling)

**Completion Criteria:**
- [ ] Portfolio volatility calculation (standard deviation of returns)
- [ ] Sharpe ratio calculation with configurable risk-free rate (default: 2%)
- [ ] Maximum drawdown calculation over analysis period
- [ ] **Flexible Asset Grouping**: Risk metrics calculated for multiple asset groupings:
  - [ ] Entire portfolio
  - [ ] One or more accounts
  - [ ] One or more tickers
  - [ ] One or more factors
- [ ] Performance: Risk calculations complete within performance targets for return calculations

**Traceability:**
- **Problem Statement**: PS-1 - Portfolio managers lack objective performance metrics
- **Objective**: OBJ-1 - Enable data-driven portfolio performance analysis
- **User Story**: US-3 - Calculate risk metrics for risk-adjusted performance evaluation
- **Impacts**: FR-8 (benchmark comparison), FR-9 (alternative portfolio calculation)

### Factor Attribution & Analysis

**FR-5**: The system must provide comprehensive factor attribution analysis for portfolio performance and risk management

**Priority**: Must have
**User Role**: Portfolio Manager, Quantitative Analyst
**Preconditions**: Factor weights are defined for portfolio holdings, return data available
**Postconditions**: Factor attribution calculated showing contribution of each factor to total returns and ticker contributions to factor exposures
**Dependencies**: FR-1 (TWR calculation), FR-6 (factor weight handling)

**Completion Criteria:**
- [ ] Factor-level return attribution across 4-level factor hierarchy (25 leaf factors)
- [ ] Bidirectional analysis: (1) factors→performance attribution and (2) tickers→factor exposure contribution
- [ ] Time-based attribution analysis for any supported time period
- [ ] Results format: "Factor X contributed +2.3% to total returns" and "Ticker Y contributes 15% of Factor X exposure"
- [ ] Integration: Uses existing portopt factor weights and UNDEFINED factor handling
- [ ] **Flexible Asset Grouping**: Supports factor attribution analysis for multiple asset groupings:
  - [ ] Entire portfolio, one or more accounts, one or more tickers, one or more factors

**Traceability:**
- **Problem Statement**: PS-2 - Current portfolio analysis lacks comprehensive factor analysis capabilities
- **Objective**: OBJ-2 - Provide comprehensive factor attribution analysis
- **User Story**: US-4 - Analyze factor attribution for portfolio performance, US-5 - Identify holdings driving factor exposure
- **Impacts**: FR-7 (factor concentration), FR-8 (benchmark comparison)

**FR-6**: The system must handle factor weights consistently with existing portopt factor handling logic

**Priority**: Must have
**User Role**: Developer, Portfolio Manager
**Preconditions**: Factor weights matrix is available, tickers may have missing or inconsistent factor weights
**Postconditions**: Factor weight handling provides consistent results with existing metrics module
**Dependencies**: None (integrates with existing system)

**Completion Criteria:**
- [ ] Reuses existing portopt factor weight normalization and UNDEFINED factor logic
- [ ] Handles missing factor weights by assigning to UNDEFINED factor category
- [ ] Normalizes factor weights that don't sum to 100%
- [ ] Maintains consistency with metrics.py module approach
- [ ] Documentation: References existing factor weight handling documentation

**Traceability:**
- **Problem Statement**: PS-2 - Current portfolio analysis lacks comprehensive factor analysis capabilities
- **Objective**: OBJ-2 - Provide comprehensive factor attribution analysis
- **User Story**: US-4 - Analyze factor attribution for portfolio performance
- **Impacts**: FR-5 (factor attribution), FR-7 (factor concentration analysis)

**FR-7**: The system must identify factor concentration risks, unintended exposures, and factor overlap patterns

**Priority**: Should have
**User Role**: Portfolio Manager, Risk Manager
**Preconditions**: Factor attribution analysis completed, factor exposure data available
**Postconditions**: Comprehensive factor risk analysis showing concentration, unintended exposures, and overlap issues
**Dependencies**: FR-5 (factor attribution analysis)

**Completion Criteria:**
- [ ] **Concentration Risk Analysis**: Identifies holdings with highest contribution to specific factor exposures and flags concentration above configurable thresholds
- [ ] **Unintended Exposure Detection**: Shows unexpected factor exposures (e.g., emerging market exposure in "US equity" holdings)
- [ ] **Factor Overlap Analysis**: Identifies multiple holdings providing redundant exposure to the same factors
- [ ] **Ticker-to-Factor Mapping**: Shows which tickers drive exposure to particular factors with percentage contributions
- [ ] **Cross-Account Analysis**: Supports concentration analysis at both account and portfolio levels
- [ ] **Actionable Results**: Provides specific recommendations for addressing concentration risks and improving diversification

**Traceability:**
- **Problem Statement**: PS-2 - Current portfolio analysis lacks comprehensive factor analysis capabilities
- **Objective**: OBJ-2 - Provide comprehensive factor attribution analysis
- **User Story**: US-5 - Identify holdings driving factor exposure
- **Impacts**: None (leaf requirement)

### Transaction Data Integration

**FR-8**: The system must load and process transaction data following the existing portopt holdings pattern

**Priority**: Must have
**User Role**: Developer, Portfolio Manager
**Preconditions**: Transaction CSV files available in supported brokerage formats
**Postconditions**: Transaction data loaded, classified, and available for performance calculations
**Dependencies**: None

**Completion Criteria:**
- [ ] Extends Portfolio class constructor to accept transactions_path parameter
- [ ] Implements TransactionsMixin following existing RebalanceMixin and MetricsMixin patterns
- [ ] Supports multiple brokerage CSV formats similar to holdings.py approach
- [ ] Automatically detects and classifies transaction types (buy, sell, contribution, withdrawal, dividend)
- [ ] Validates transaction data against current holdings with warn-and-continue on reconciliation failures

**Traceability:**
- **Problem Statement**: PS-1 - Portfolio managers lack objective performance metrics
- **Objective**: OBJ-1 - Enable data-driven portfolio performance analysis
- **User Story**: US-1 - Calculate time-weighted returns (requires transaction data)
- **Impacts**: FR-1 (TWR calculation), FR-3 (MWR calculation), FR-9 (alternative portfolio calculation)

### Benchmark & Alternative Portfolio Analysis

**FR-9**: The system must support alternative portfolio definition and performance calculation

**Priority**: Must have
**User Role**: Portfolio Manager, Quantitative Analyst
**Preconditions**: Price data available for alternative portfolio components
**Postconditions**: Alternative portfolio performance calculated using same methodology as actual portfolio
**Dependencies**: FR-1 (TWR calculation), FR-4 (risk metrics)

**Completion Criteria:**
- [ ] Supports custom alternative portfolio definition with ticker or factor allocations
- [ ] Calculates performance metrics for alternative portfolios over same time periods
- [ ] Supports different rebalancing frequencies for alternative strategies
- [ ] Returns results in standardized bt/ffn framework formats for consistency
- [ ] Performance: Alternative portfolio calculations complete within reasonable time for backtesting scenarios

**Traceability:**
- **Problem Statement**: PS-3 - No capability to compare against alternative strategies
- **Objective**: OBJ-3 - Enable comparison against alternative investment strategies
- **User Story**: US-7 - Backtest alternative investment strategies
- **Impacts**: FR-10 (benchmark comparison engine)

**FR-10**: The system must provide benchmark comparison capabilities

**Priority**: Must have
**User Role**: Portfolio Manager
**Preconditions**: Actual portfolio performance calculated, benchmark/alternative performance calculated
**Postconditions**: Side-by-side comparison metrics available for analysis
**Dependencies**: FR-1 (TWR calculation), FR-4 (risk metrics), FR-9 (alternative portfolio calculation)

**Completion Criteria:**
- [ ] Supports comparison against S&P 500 and other market benchmarks
- [ ] Supports comparison against standard allocation portfolios (60/40, 80/20)
- [ ] Shows side-by-side performance metrics (returns, risk, Sharpe ratio, max drawdown)
- [ ] Results formatted for easy interpretation and decision-making
- [ ] Integration: Uses standardized performance calculation methodology for fair comparison

**Traceability:**
- **Problem Statement**: PS-3 - No benchmark comparison capabilities
- **Objective**: OBJ-3 - Enable comparison against alternative investment strategies
- **User Story**: US-6 - Compare actual portfolio performance against benchmarks
- **Impacts**: None (leaf requirement)

## Developer Experience (DX) Requirements

*For developer-facing libraries like portopt, developer experience IS the product experience. This section defines how developers will discover, access, and successfully use the performance analysis capabilities.*

### Expected Module Integration

**Primary Module**: New `performance.py` module will house the main performance analysis functionality
**Supporting Modules**: 
- `portfolio.py` - Extended to support transaction data loading and performance method access
- `metrics.py` - Performance calculations will follow similar patterns and reuse factor handling logic
- `holdings.py` - Transaction loading will extend existing CSV parsing patterns

**New Modules**: 
- `performance.py` - Main performance analysis engine with PerformanceMixin
- `transactions.py` - Transaction data loading and processing (following holdings.py pattern)

### API Design Considerations

*This implementation must follow the [portopt Design Principles](../design-principles.md). Document any requirement-specific design constraints that will impact how developers interact with the functionality.*

**Parameter Naming Consistency**: Performance methods must follow existing portopt parameter conventions
- **Type**: Consistency
- **Rationale**: Developers expect consistent parameter names across similar functions
- **Impact**: Method signatures must use established patterns from metrics.py (dimensions, filters, metrics parameters)
- **Validation**: API review confirms naming matches existing portfolio analysis methods

**Return Format Standardization**: Performance results should use bt/ffn framework formats where applicable
- **Type**: Integration
- **Rationale**: Leverages established financial analysis infrastructure and enables interoperability
- **Impact**: Return objects should be compatible with bt.Result and ffn.GroupStats patterns
- **Validation**: Results can be consumed by existing bt/ffn analysis and visualization tools

**Transaction Data Integration**: Transaction loading should follow holdings.py patterns
- **Type**: Consistency
- **Rationale**: Developers familiar with holdings loading expect similar transaction loading patterns
- **Impact**: Portfolio class constructor extended with transactions_path parameter, TransactionsMixin follows RebalanceMixin pattern
- **Validation**: Transaction loading API matches holdings loading API patterns and documentation

### Error Handling & Developer Messaging

**Missing Data Strategy Parameters**: Clear parameter options for handling incomplete data
- **Error Message Clarity**: Method parameters should clearly document available missing data strategies
- **Exception Types**: Use ValueError for invalid missing data strategy options, provide clear list of valid options
- **Recovery Guidance**: Error messages should suggest appropriate missing data strategies based on data availability
- **Validation Feedback**: Warnings should clearly indicate what data is missing and impact on calculations

**Time Period Validation**: Clear guidance for invalid or unavailable time periods
- **Error Message Clarity**: Specific error messages indicating why a time period is invalid or unavailable
- **Exception Types**: Use ValueError for invalid time periods, provide suggested alternatives
- **Recovery Guidance**: Error messages should suggest valid time periods based on available transaction and price data
- **Validation Feedback**: Clear warnings when requested time period exceeds available data

### Documentation Requirements

**API Reference**: Complete docstrings following NumPy/SciPy conventions
- **Method Documentation**: All public methods must have comprehensive docstrings with parameters, returns, examples
- **Financial Concepts**: Brief explanations of TWR vs MWR, when to use each, interpretation of results
- **Performance Considerations**: Document expected response times and data scale limitations

**Usage Examples**: Jupyter notebook demonstrating end-to-end performance analysis workflow
- **Basic Usage**: Simple examples for calculating portfolio returns and risk metrics
- **Advanced Usage**: Factor attribution analysis, benchmark comparison, alternative strategy evaluation
- **Integration Examples**: How to use results with existing portopt optimization and analysis workflows

**Migration Guides**: Documentation for integrating performance analysis with existing portfolios
- **Transaction Data Setup**: How to prepare and load transaction data from different brokerages
- **Factor Integration**: How performance analysis works with existing factor weight configurations
- **Troubleshooting**: Common data issues and solutions for performance calculation problems

### Learning Curve & Usability

**Financial Terminology**: Use standard financial terms (TWR, MWR, Sharpe, attribution) in method names and documentation
- **Discoverability**: Methods should be discoverable through logical naming that matches industry terminology
- **Learning Curve**: Assume basic financial knowledge; provide brief explanations in docstrings for complex concepts
- **Integration Effort**: Should integrate naturally with existing Portfolio class usage patterns
- **Cognitive Load**: Method complexity should match complexity of underlying financial concepts

**API Integration**: Performance analysis should feel like natural extension of existing portopt capabilities
- **Method Discovery**: Performance methods accessible through Portfolio class following metrics.py pattern
- **Parameter Consistency**: Similar aggregation and filtering patterns as existing getMetrics() method
- **Result Interpretation**: Results should be clearly formatted and include metadata about calculation methods used
- **Progressive Disclosure**: Simple use cases should be simple, advanced features should be discoverable

## Non-Functional Requirements

*These specify quality attributes that the implemented system must meet.*

### Performance Requirements

**Response Time**: Performance calculations must complete within acceptable time limits for interactive use
- **Basic Calculations**: Portfolio-level TWR, volatility, and Sharpe ratio for YTD period must complete within 10 seconds (target) or 30 seconds (acceptable)
- **Complex Analysis**: Factor attribution across 4-level hierarchy for custom time periods must complete within 60 seconds for typical portfolio (50 tickers, 10 accounts, 25 factors)
- **Alternative Portfolio Analysis**: Backtesting alternative strategies should perform comparably to bt framework benchmarks

**Memory Usage**: System must operate within resource constraints of development environment
- **Memory Limit**: Total memory usage must not exceed 8GB (50% of MacBook Air 16GB RAM)
- **Data Loading**: Efficient loading and processing of 5 years of transaction data (~430 transactions) and corresponding price history
- **Calculation Efficiency**: Use vectorized pandas/numpy operations for performance calculations to minimize memory footprint

**Scalability**: System should handle expected data volumes efficiently
- **Portfolio Scale**: Must efficiently handle 50 tickers across 10 accounts with 25 factors
- **Time Series Data**: Should handle 5+ years of daily price data for performance and risk calculations
- **Transaction Volume**: Must process 5 years of transaction history (~430 transactions) efficiently

### Reliability Requirements

**Data Validation**: Input validation and data consistency requirements
- **Transaction Reconciliation**: When transaction data doesn't reconcile with current holdings, system must warn and continue (not halt calculations)
- **Price Data Gaps**: Support configurable missing data strategies (forward-fill, interpolation, skip gaps, require complete data, calculate only complete periods)
- **Factor Weight Consistency**: Handle missing factor weights using existing portopt UNDEFINED factor logic

**Error Recovery**: How errors should be handled and recovered from
- **External Data Failures**: Handle Yahoo Finance outages using same approach as existing market_data.py module
- **Partial Data Availability**: Provide meaningful results when complete data is not available, with appropriate warnings
- **Calculation Failures**: Graceful degradation when specific calculations fail (e.g., continue with available metrics when one metric fails)

**Edge Cases**: Known edge cases to handle gracefully
- **Empty Portfolios**: Handle portfolios with no holdings or minimal transaction history
- **Short Time Periods**: Handle performance calculations for very short time periods (less than 1 month)
- **Corporate Actions**: Basic handling of stock splits and mergers in historical performance calculations

### Security Requirements

**Data Protection**: Handle financial data appropriately
- **Local File Storage**: Transaction and holdings data stored in local files with standard OS permissions (sufficient for initial release)
- **External API Access**: Yahoo Finance API calls should respect rate limits to avoid being blocked
- **Sensitive Information**: No special encryption requirements for local development use case

## Technical Constraints

*Technical constraints define limitations or requirements that the system must operate within.*

### Platform Requirements

**Operating System Support**: Must support macOS development environment
- **Primary Platform**: macOS (MacBook Air development environment)
- **Python Version**: Python 3.12.7 or later
- **Development Tools**: Must work seamlessly in Cursor IDE with Jupyter notebooks

**Package Management**: Must integrate with existing dependency management
- **Package Manager**: pipenv for dependency management
- **Testing Framework**: pytest for automated testing
- **Documentation**: Jupyter notebook examples and comprehensive docstrings

### Dependency Constraints

**Required Compatibility**: Must work with existing portopt dependencies
- **Core Dependencies**: pandas, numpy, cvxpy, statsmodel, duckdb, ibis-framework, pyyaml (maintain existing version compatibility)
- **Financial Libraries**: bt, ffn frameworks for backtesting and performance analysis (bt already in use)
- **Market Data**: Continue using yfinance for price data (consistent with existing market_data.py)

**New Dependencies**: New dependencies should be added judiciously
- **Approval Process**: New dependencies require explicit approval
- **Justification**: Each new dependency must provide significant value that cannot be achieved with existing tools
- **Lightweight Preference**: Prefer lightweight, well-maintained packages with minimal sub-dependencies

**Version Constraints**: Maintain compatibility with existing portopt ecosystem
- **Backward Compatibility**: Performance analysis should not break existing portopt functionality
- **API Evolution**: Lax backward compatibility acceptable for performance analysis APIs (early development phase)
- **Integration Testing**: Ensure performance module works with existing portfolio optimization and analysis workflows

## Traceability Summary

### Quick Reference Matrix

| Problem Statement | Objective | User Story | Requirements Generated | Status |
|-------------------|-----------|------------|----------------------|---------|
| PS-1 | OBJ-1 | US-1 | FR-1, FR-2, FR-8 | Not Started |
| PS-1 | OBJ-1 | US-2 | FR-3, FR-2 | Not Started |
| PS-1 | OBJ-1 | US-3 | FR-4 | Not Started |
| PS-2 | OBJ-2 | US-4 | FR-5, FR-6 | Not Started |
| PS-2 | OBJ-2 | US-5 | FR-7, FR-5 | Not Started |
| PS-3 | OBJ-3 | US-6 | FR-10, FR-9 | Not Started |
| PS-3 | OBJ-3 | US-7 | FR-9, FR-10 | Not Started |

### Implementation Priority

**Phase 1 - Core Performance Analysis (Must Have)**
- FR-1: TWR calculation engine
- FR-2: Time period handling
- FR-4: Basic risk metrics
- FR-8: Transaction data integration

**Phase 2 - Factor Attribution (Must Have)**
- FR-5: Factor attribution analysis
- FR-6: Factor weight handling integration
- FR-10: Basic benchmark comparison

**Phase 3 - Advanced Analysis (Should Have)**
- FR-3: MWR calculation engine
- FR-7: Factor concentration analysis
- FR-9: Alternative portfolio calculation

## Dependencies and Assumptions

### Prerequisites
- Existing portopt library with metrics.py, holdings.py, and factor weight capabilities
- Transaction data available in CSV format from supported brokerages
- Historical price data accessible via Yahoo Finance API

### Assumptions
- Factor weights remain static over time for initial release (dynamic factor weights deferred)
- Transaction volume remains modest (<100 transactions per year) for performance requirements
- Users have basic financial knowledge of performance metrics and attribution concepts
- bt/ffn framework integration provides sufficient backtesting capabilities

### Related Requirements
- Future requirement for dynamic factor weight handling over time
- Future requirement for database storage of transactions and performance calculations
- Future requirement for more sophisticated factor analysis (factor loadings vs percentage allocations)

---

*This requirements specification provides the foundation for implementing comprehensive portfolio performance analysis capabilities in the portopt library, addressing the critical "flying blind" problem while maintaining consistency with existing portopt design principles and patterns.*
