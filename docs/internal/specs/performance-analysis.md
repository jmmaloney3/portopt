# Performance Analysis Requirements Specification

## Document Information

- **Requirement ID**: REQ-2025-001
- **Title**: Portfolio Performance Analysis & Attribution System
- **Author**: Portfolio Requirements Interview Process
- **Date Created**: 2025-07-25
- **Last Updated**: 2025-09-22
- **Version**: v1.2
- **Status**: Approved
- **Priority**: Critical
- **Target Release**: TBD

## Executive Summary

This requirement addresses the critical "flying blind" problem where portfolio managers lack objective performance metrics to evaluate investment decisions. The system will provide comprehensive performance analysis including time-weighted and money-weighted returns, factor attribution, risk metrics, and comparison capabilities against alternative investment strategies.

## Requirements Overview

This document organizes requirements into four interconnected types that work together to ensure complete coverage from business need to system requirements:

### **Personas** → **WHO**
Define the key user archetypes and their characteristics that drive design decisions and user experience requirements.
- **Primary Personas**: Main user types whose needs must be satisfied for success
- **Secondary Personas**: Supporting user types with specific needs or constraints
- **Anti-Personas**: User types explicitly not targeted or supported

### **Business Requirements** → **WHY**
Define the fundamental problems and user value that justify this development effort.
- **Problem Statements**: Core challenges and pain points that need solving
- **User Stories**: Specific user-centered solutions that deliver business value

### **Functional Requirements** → **WHAT**
Define the core capabilities and behaviors the system must provide, independent of how users access them.
- System capabilities, business logic, data processing, and computational features
- Focus on what the system does, not how developers interact with it

### **Non-Functional Requirements** → **HOW WELL**
Define quality attributes and performance characteristics the system must exhibit.
- Performance, reliability, security requirements that apply to system behavior
- Measurable quality standards independent of specific functionality

### **Technical Constraints** → **WITHIN WHAT LIMITS**
Define environmental limitations and compatibility requirements the system must operate within.
- Platform support, dependency constraints, compatibility requirements
- External factors that constrain implementation choices

### **Requirements Flow**
Adopt a simplified hierarchical traceability model that reduces redundancy while preserving clarity:
- Personas → Problem Statements → User Stories → Functional Requirements
- Keep only immediate parent-child links; derive longer chains when needed
- Retain targeted cross-links only where they add unique value (e.g., FR "Impacts" for FR-to-FR dependencies)

**User Foundation:**
- **Personas** → Define who we're building for

**Business Foundation:**
- **Problem Statements** → Identify core challenges
- **User Stories** → Translate into user-centered solutions

**System Requirements:**
- **Functional Requirements** → Define system capabilities (WHAT)
- **Non-Functional Requirements** → Define quality attributes (HOW WELL)

**Constraints:** All technical requirements operate within **Technical Constraints** (platform, compatibility, dependencies)

*Note: For developer-facing libraries, Functional requirements define the system capabilities that developers will use. For end-user facing applications, Functional requirements define the system capabilities that support user interactions. All trace back to the same User Stories and address the core system capabilities needed to deliver value.*

## Personas

*Personas are detailed, semi-fictional representations of key user archetypes that help ensure requirements remain user-centered and realistic. They provide context for understanding user needs, behaviors, goals, and constraints. Well-defined personas help validate that business requirements, user stories, and technical requirements all address real user needs and create meaningful value. For developer-facing libraries, personas should focus on different types of developers, analysts, and technical users.*

### Primary Personas

**P-1**: Technical Individual Investor - Self-directed investor with programming skills managing personal portfolio

**Demographics & Background:**
- **Role**: Individual investor managing personal retirement and investment accounts across multiple institutions
- **Experience Level**: Beginner to intermediate quantitative finance knowledge, with access to experts for guidance; intermediate to advanced Python programming skills
- **Technical Skills**: Python (pandas, numpy, matplotlib, bt), Jupyter notebooks, command-line tools, *nix systems, JSON/YAML/CSV file formats
- **Work Environment**: Personal development environment (MacBook Air), uses Jupyter notebooks for analysis, command-line for automation
- **Goals**: Optimize personal portfolio performance, make data-driven investment decisions, automate routine analysis tasks

**Behaviors & Workflows:**
- **Primary Tasks**: Monthly/quarterly portfolio analysis, performance evaluation, rebalancing decisions, factor exposure monitoring
- **Decision Making**: Data-driven approach, values transparency in calculations, needs to understand methodology and assumptions
- **Information Sources**: Financial research, academic papers, quantitative finance experts, personal analysis using quantitative tools
- **Pain Points**: No historical performance tracking, can't compare against alternatives, relies on memory/spreadsheets for performance analysis, no factor analysis to support risk and return attribution to factors
- **Success Metrics**: Portfolio performance vs benchmarks, risk-adjusted returns, factor allocation effectiveness, automation of routine tasks

**Technical Context:**
- **Current Tools**: Brokerage websites, Excel/Google Sheets spreadsheets, Python libraries (pandas, bt), manual calculations, portopt library for current state analysis
- **Integration Needs**: Works with CSV data from multiple brokerages, needs to export results for further analysis or reporting
- **Performance Expectations**: Most operations complete in a few seconds; complex operations (e.g., long-term backtests) complete within 30 seconds for typical portfolio (50 tickers, 10 accounts)
- **Learning Preferences**: Prefers working examples, clear documentation, gradual complexity progression, values understanding of underlying methodology

**Traceability:**
- **Primary Problems**: PS-1 (lack of objective performance metrics), PS-2 (limited factor attribution), PS-3 (no benchmark comparison)
- **Related Personas**: P-2 (Application Developer - may build tools for P-1)

**P-2**: Backend Developer - Developer building financial services and data processing applications using portopt

**Demographics & Background:**
- **Role**: Backend developer or data engineer building financial applications, APIs, or data processing systems
- **Experience Level**: Expert in Python development, basic to intermediate quantitative finance knowledge (sufficient to understand requirements from product managers with quantitative finance expertise)
- **Technical Skills**: Python (pandas, numpy, FastAPI/Flask), SQL, data processing libraries, API development, testing frameworks
- **Work Environment**: Development team with product managers providing quantitative finance requirements, uses version control, testing, CI/CD
- **Goals**: Build robust financial data processing systems, create reliable APIs for portfolio analysis, implement complex financial calculations efficiently

**Behaviors & Workflows:**
- **Primary Tasks**: API development, data pipeline implementation, financial calculation integration, performance optimization, testing and deployment
- **Decision Making**: Architecture-focused, values maintainable and testable code, needs clear APIs with good documentation, prioritizes performance and reliability
- **Information Sources**: API documentation, product manager requirements, software engineering best practices, financial data provider documentation
- **Pain Points**: Complex financial calculation requirements, data quality and consistency issues, API design for financial use cases, performance optimization
- **Success Metrics**: API performance, code maintainability, feature completeness, system reliability, integration success

**Technical Context:**
- **Current Tools**: Python development stack, financial data providers, databases, API frameworks, testing tools, deployment platforms
- **Integration Needs**: Clean, well-documented APIs for portfolio analysis, consistent data formats, extensible architecture, comprehensive error handling
- **Performance Expectations**: Sub-second response times for API calls, efficient memory usage, scalable data processing, reliable error handling
- **Learning Preferences**: Comprehensive API documentation, code examples, clear architectural patterns, detailed error messages and debugging information

**Traceability:**
- **Primary Problems**: PS-1 (need robust performance analysis APIs), PS-2 (require flexible factor analysis capabilities), PS-3 (need benchmark comparison APIs)
- **Related Personas**: P-1 (Technical Individual Investor - may use applications built by P-2), P-3 
(Sophisticated Individual Investor - end users of applications)

**P-3**: Sophisticated Individual Investor - Non-technical investor with intermediate financial knowledge who will use future web applications

**Demographics & Background:**
- **Role**: Individual investor with significant assets, intermediate to advanced understanding of portfolio theory and factor investing, no programming skills
- **Experience Level**: Intermediate to advanced investment knowledge, basic to intermediate quantitative finance concepts (web application democratizes access to advanced tools)
- **Technical Skills**: Basic computer skills, comfortable with web applications, Excel/Google Sheets, financial analysis tools
- **Work Environment**: Personal computer, uses web browsers and financial software, may work with financial advisors
- **Goals**: Optimize portfolio performance using sophisticated quantitative tools, make data-driven investment decisions, understand factor attribution and risk

**Behaviors & Workflows:**
- **Primary Tasks**: Portfolio analysis and optimization, performance evaluation, factor exposure monitoring, rebalancing decisions, benchmark comparisons
- **Decision Making**: Data-driven approach, values transparency in calculations, needs to understand methodology but not implementation details
- **Information Sources**: Financial research, academic papers, financial advisors, quantitative finance experts, web-based financial tools and tutorials
- **Pain Points**: Limited access to sophisticated portfolio analysis tools, difficulty comparing performance against alternatives, lack of factor attribution analysis
- **Success Metrics**: Portfolio performance vs benchmarks, risk-adjusted returns, factor allocation effectiveness, achievement of financial goals

**Technical Context:**
- **Current Tools**: Brokerage websites, Excel/Google Sheets, financial advisor tools, basic portfolio analysis software, web-based investment platforms
- **Integration Needs**: Web-based interface, export capabilities for further analysis, integration with existing brokerage accounts, clear visualizations
- **Performance Expectations**: Immediate response for most operations; delays only acceptable for operations understood to require significant computation
- **Learning Preferences**: Guided tutorials, clear explanations of financial concepts, visual examples, step-by-step workflows, educational content that builds quantitative finance knowledge

**Traceability:**
- **Primary Problems**: PS-1 (lack of objective performance metrics), PS-2 (limited factor attribution), PS-3 (no benchmark comparison)
- **Related Personas**: P-1 (Technical Individual Investor - may provide guidance), P-2 (Backend 
Developer - builds applications for P-3)

### Secondary Personas

**P-4**: Financial Advisor/Wealth Manager - Professional who uses portopt-based tools to serve clients

**Demographics & Background:**
- **Role**: Financial advisor or wealth manager serving individual clients with sophisticated portfolio needs
- **Experience Level**: Expert in investment management, intermediate to advanced quantitative finance knowledge, basic to intermediate technical skills
- **Technical Skills**: Comfortable with financial software, may have basic programming skills, uses portfolio management tools
- **Work Environment**: Financial services firm or independent practice, works with multiple clients, regulatory compliance requirements
- **Goals**: Provide sophisticated portfolio analysis to clients, differentiate services through advanced quantitative tools, scale client management efficiently

**Specific Needs & Constraints:**
- **Unique Requirements**: Multi-client portfolio management, regulatory compliance, client reporting, professional-grade analysis tools
- **Constraints**: Must work within regulatory frameworks, needs audit trails, requires detailed documentation for client communications
- **Integration Points**: Uses applications built by P-2 (Backend Developer), serves clients similar to P-3 (Sophisticated Individual Investor)

**Traceability:**
- **Related Problems**: PS-1 (need performance analysis for client portfolios), PS-2 (require factor attribution for client reporting), PS-3 (need benchmark comparisons for client presentations)
- **Supporting User Stories**: US-6 (benchmark comparison), US-8 (quarterly rebalancing decisions)
- **Specific Requirements**: FR-10 (benchmark comparison), enhanced reporting capabilities

### Anti-Personas

**AP-1**: Basic Individual Investors - Not targeted due to financial sophistication requirements

**Why Not Targeted:**
- **Scope Mismatch**: Library and future web application are designed for investors who understand quantitative finance concepts (factor investing, risk attribution, etc.); basic investors need fundamental investment education and different analytical approaches
- **Alternative Solutions**: Should use retail-focused investment platforms, robo-advisors, or traditional financial advisors for basic portfolio management
- **Impact on Design**: Allows focus on sophisticated quantitative analysis without needing to provide basic investment education

**Traceability:**
- **Scope Boundaries**: No basic investment education, no simplified factor models, no fundamental portfolio theory explanations
- **Design Constraints**: Can assume intermediate to advanced financial knowledge, focus on sophisticated analysis capabilities

**AP-2**: Enterprise IT Administrators - Not targeted due to deployment and integration requirements

**Why Not Targeted:**
- **Scope Mismatch**: Library and web application are designed for individual use and small-scale applications; enterprise users need advanced integration, deployment, and administrative features
- **Alternative Solutions**: Should use enterprise-grade portfolio management platforms with IT administration features, multi-tenant architectures, and enterprise integrations
- **Impact on Design**: Allows focus on individual investor needs without enterprise deployment complexity

**Traceability:**
- **Scope Boundaries**: No enterprise deployment options, no multi-tenant architecture, no enterprise integrations (SSO, LDAP, etc.)
- **Design Constraints**: Can focus on individual portfolio management, assume standard web application security requirements

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
- **Primary Personas**: P-1 (Technical Individual Investor), P-2 (Backend Developer), P-3 (Sophisticated Individual Investor)
- **Addresses**: None (primary problem statement)
- **Addressed By**: US-1, US-2, US-3, US-4, US-5, US-6, US-7, US-8 (performance analysis user stories)
- **Related Problems**: PS-2 (Limited factor attribution capabilities), PS-3 (No benchmark comparison capabilities)

#### Secondary Problems

**PS-2**: Current portfolio analysis lacks comprehensive factor analysis capabilities

- **Who**: Portfolio managers analyzing factor-based investment strategies and managing portfolio risk
- **What**: Need bidirectional factor analysis: (1) understand which factors contribute to portfolio performance, and (2) understand which tickers contribute to portfolio's exposure to each factor
- **Why**: To evaluate factor allocation decisions, identify sources of performance, and manage factor concentration risk
- **Current State**: Factor weights are defined but no attribution analysis or exposure analysis is available
- **Impact**: Cannot identify which factor allocations are contributing positively or negatively to returns, and cannot identify concentration risk or unintended factor exposure through specific holdings

**Traceability:**
- **Primary Personas**: P-1 (Technical Individual Investor), P-2 (Backend Developer), P-3 (Sophisticated Individual Investor)
- **Addresses**: PS-1 (lack of objective performance metrics)
- **Addressed By**: US-4, US-5 (factor attribution user stories)
- **Related Problems**: PS-1 (primary problem), PS-3 (benchmark comparison)

**PS-3**: No capability to compare actual portfolio performance against alternative strategies

- **Who**: Portfolio managers evaluating investment strategy effectiveness
- **What**: Need to compare actual portfolio returns against alternative allocation strategies (e.g., 60/40, 80/20, custom factor allocations)
- **Why**: To validate current strategy effectiveness and identify potentially better approaches
- **Current State**: No systematic way to backtest alternative strategies against actual performance
- **Impact**: Cannot determine if current investment strategy outperforms standard benchmarks or alternative approaches

**Traceability:**
- **Primary Personas**: P-1 (Technical Individual Investor), P-2 (Backend Developer), P-3 (Sophisticated Individual Investor)
- **Addresses**: PS-1 (lack of objective performance metrics)
- **Addressed By**: US-6, US-7 (benchmark comparison user stories)
- **Related Problems**: PS-1 (primary problem), PS-2 (factor attribution)

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
- **Addresses Problem**: PS-3 (no benchmark comparison capabilities)
- **Implemented By**: FR-10 (benchmark comparison engine), FR-9 (alternative portfolio calculation)
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
- **Addresses Problem**: PS-3 (no benchmark comparison capabilities)
- **Implemented By**: FR-9 (alternative portfolio calculation), FR-10 (benchmark comparison)
- **Related Stories**: US-6 (benchmark comparison), US-1 (TWR), US-2 (MWR)

**US-8**: As a portfolio manager,
I want to use performance analysis data to make quarterly rebalancing decisions,
So that I can make data-driven allocation adjustments based on objective performance metrics rather than subjective assessment.

**Acceptance Criteria:**
- [ ] Can access performance metrics (returns, risk, factor attribution) for the current quarter and previous quarters
- [ ] Can compare current portfolio performance against target allocations and benchmarks
- [ ] Can identify underperforming or overperforming asset classes and factors
- [ ] Results provide clear guidance on which allocations should be adjusted and by how much
- [ ] Integrates with existing portopt rebalancing workflow and optimization capabilities

**Traceability:**
- **Addresses Problem**: PS-1 (lack of objective performance metrics for decision-making)
- **Implemented By**: FR-1 (TWR calculation), FR-4 (risk metrics), FR-5 (factor attribution)
- **Related Stories**: US-1 (TWR), US-3 (risk metrics), US-4 (factor attribution)

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
- **User Story**: US-1 - Calculate time-weighted returns for any time period
- **Impacts**: FR-4 (risk metrics), FR-5 (factor attribution), FR-10 (benchmark comparison)

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
- **User Story**: US-2 - Calculate money-weighted returns for actual dollar experience
- **Impacts**: FR-10 (benchmark comparison), FR-9 (alternative portfolio calculation)

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
- **User Story**: US-3 - Calculate risk metrics for risk-adjusted performance evaluation
- **Impacts**: FR-10 (benchmark comparison), FR-9 (alternative portfolio calculation)

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
- **User Story**: US-4 - Analyze factor attribution for portfolio performance, US-5 - Identify holdings driving factor exposure
- **Impacts**: FR-7 (factor concentration), FR-10 (benchmark comparison)

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
- **User Story**: US-6 - Compare actual portfolio performance against benchmarks
- **Impacts**: None (leaf requirement)


## Non-Functional Requirements

*These specify quality attributes that the implemented system must meet.*

### Performance Requirements

**Response Time**: Performance calculations must complete within acceptable time limits for interactive use and decision-making
- **Basic Calculations**: Portfolio-level TWR, volatility, and Sharpe ratio for YTD period must complete within 10 seconds (target) or 30 seconds (acceptable) to support timely investment decisions
- **Complex Analysis**: Factor attribution across 4-level hierarchy for custom time periods must complete within 60 seconds for typical portfolio (50 tickers, 10 accounts, 25 factors)
- **Alternative Portfolio Analysis**: Backtesting alternative strategies should perform comparably to bt framework benchmarks
- **Decision Support**: Performance metrics must be available quickly enough to reduce decision-making uncertainty and enable data-driven portfolio management

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
*This matrix provides a high-level overview of traceability relationships. Detailed traceability information is maintained in each individual item's "Traceability" section.*

*Note: For developer-facing libraries, user stories typically generate functional requirements that define system capabilities. The relationships between requirements are flexible - not every user story needs multiple functional requirements, and some functional requirements may span multiple user stories.*

| Problem Statement | User Story | Requirements Generated | Primary Personas | Status |
|-------------------|------------|----------------------|-------------------|---------|
| PS-1 | US-1 | FR-1, FR-2, FR-8 | P-1, P-2, P-3 | Not Started |
| PS-1 | US-2 | FR-3, FR-2 | P-1, P-2, P-3 | Not Started |
| PS-1 | US-3 | FR-4 | P-1, P-2, P-3 | Not Started |
| PS-2 | US-4 | FR-5, FR-6 | P-1, P-2, P-3 | Not Started |
| PS-2 | US-5 | FR-7, FR-5 | P-1, P-2, P-3 | Not Started |
| PS-3 | US-6 | FR-10, FR-9 | P-1, P-2, P-3 | Not Started |
| PS-3 | US-7 | FR-9, FR-10 | P-1, P-2, P-3 | Not Started |
| PS-1 | US-8 | FR-1, FR-4, FR-5 | P-1, P-2, P-3 | Not Started |

*Example interpretations:*
- *US-1 generates multiple functional capabilities (FR-1, FR-2, FR-8) for portfolio performance analysis*
- *US-2 generates internal functionality (FR-3, FR-2) for money-weighted return calculations*
- *US-3 generates functional capabilities (FR-4) for risk metrics calculation*

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

### Traceability Validation Checklist
*Use this checklist to ensure traceability is complete and accurate while avoiding redundant links.*

Required forward links:
- [x] Persona → Problem Statement(s) (Primary Problems)
- [x] Problem Statement → User Story(ies) (Addressed By)
- [x] User Story → Functional Requirement(s) (Implemented By)

Required backward links:
- [x] Functional Requirement → User Story (User Story)
- [x] User Story → Problem Statement (Addresses Problem)
- [x] Problem Statement → Persona(s) (Primary Personas)

Optional/contextual links:
- [x] Problem Statement → Parent Problem (Addresses) when a true hierarchy exists
- [x] Functional Requirement → FR (Impacts) for FR-to-FR dependencies
- [x] Persona → Related Personas for collaboration/hand-offs (does not affect required chain)

General rules:
- [x] No orphans: Every FR traces to a US; every US traces to a PS; every PS links to at least one Persona
- [x] Immediate links only in bodies; derive longer chains when needed
- [x] Cross-links are targeted and add unique value

## Appendices

### A. Glossary
- **TWR (Time-Weighted Return)**: A measure of investment performance that eliminates the impact of cash flows
- **MWR (Money-Weighted Return)**: A measure of investment performance that accounts for the timing and size of cash flows
- **Factor Attribution**: Analysis of how different factors contribute to portfolio performance
- **Factor Concentration**: The degree to which portfolio exposure to specific factors is concentrated in particular holdings
- **bt/ffn Framework**: Backtesting and financial analysis frameworks used for standardized performance calculations

### B. References
- [Design Principles](../design-principles-and-standards.md)
- [requirements template](../templates/requirements-template.md)
- bt framework documentation
- ffn framework documentation
- CFA Institute performance measurement standards

### C. Examples
*[To be populated during implementation with concrete examples of the expected functionality]*

---

*This requirements specification provides the foundation for implementing comprehensive portfolio performance analysis capabilities in the portopt library, addressing the critical "flying blind" problem while maintaining consistency with existing portopt design principles and patterns.*
