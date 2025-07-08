# portopt Library Design Principles & Standards

## Document Information
- **Last Updated**: 2025-07-07
- **Status**: Living Document
- **Scope**: Entire portopt library

## Overview

This document defines the design principles, coding standards, and development conventions for the `portopt` Python library. These guidelines ensure consistency, maintainability, and usability across all modules and features.

## Core Philosophy

These design principles are derived from the principles followed by the [scikit-learn project](https://arxiv.org/pdf/1309.0238). The `portopt` project provides an open source portfolio management & optimization library for the Python programming language. The ambition of the project is to provide efficient and well-established portfolio management & optimization tools within a programming environment that is accessible to non-finance experts and reusable to support various investing strategies. The project is not a novel domain-specific language, but a library that provides portfolio management & optimization idioms to a general-purpose high-level language.

`portopt` is a library, a collection of classes and functions that users import into Python programs. Using `portopt` therefore requires basic Python programming knowledge. The library has been designed to tie in with the set of numeric and scientific packages centered around the NumPy, SciPy and Pandas libraries. No command-line interface, let alone a graphical user interface, is offered for non-programmer users. Instead, interactive use is made possible by the Python interactive interpreter, its enhanced replacement IPython, as well as Jupyter notebooks.

Our rule of thumb is that user code should not be tied to `portopt`—which is a library, and not a framework. This principle avoids the well-known problem with object-oriented design, where users wanting a "banana" should not get "a gorilla holding the banana and the entire jungle". Programs using `portopt` should not be intimately tied to it, so that their code can be reused with other toolkits or in other contexts.

## API Design Principles

### The Four Core Principles (Scikit-learn Inspired)

As much as possible, design choices should be guided so as to avoid the proliferation of framework code. Simple conventions should be adopted to limit to a minimum the number of methods an object must implement. The API design should adhere to the following four broad principles:

#### 1. Consistency
All objects (basic or composite) share a consistent interface composed of a limited set of methods. This interface is documented in a consistent manner for all objects.

**In Practice:**
- **Naming Conventions**: Use clear, descriptive names that follow Python conventions (PEP 8)
- **Parameter Patterns**: Similar functions should have similar parameter names and ordering
- **Return Types**: Consistent return types for similar operations
- **Interface Uniformity**: Portfolio optimizers, risk models, and return models follow consistent patterns
- **Error Handling**: Use consistent exception types and error message formats across all modules

#### 2. Inspection
Constructor parameters and parameter values determined by algorithms are stored and exposed as public attributes.

**In Practice:**
- **Parameter Transparency**: Optimization parameters, model settings, and results are easily accessible
- **Result Introspection**: Make it easy to inspect optimization results, risk decompositions, and performance metrics
- **Computed Attributes**: Results from optimization and analysis are exposed as public attributes with trailing underscore (e.g., `weights_`, `expected_return_`, `risk_`)
- **Intermediate Results**: Provide access to intermediate calculations for debugging and analysis

#### 3. Non-proliferation of Classes
Datasets are represented as NumPy arrays, SciPy sparse matrices, or Pandas data frames. Other parameter names and values are represented as standard Python strings or numbers whenever possible.

**In Practice:**
- **Standard Data Types**: Use pandas DataFrames for financial time series, numpy arrays for matrices
- **Simple Parameters**: Configuration uses standard Python types (strings, numbers, dictionaries) where possible
- **Minimal Custom Classes**: Only create custom classes when they provide clear value over standard types
- **Familiar Interfaces**: Leverage patterns familiar to users of pandas, numpy, and the broader Python ecosystem

#### 4. Composition
Many tasks are expressible as sequences or combinations of transformations to data. Some algorithms are also naturally viewed as meta-algorithms parametrized on other algorithms.

**In Practice:**
- **Modular Components**: Portfolio optimization workflows should be expressible as combinations of risk models, return models, constraints, and optimizers
- **Interchangeable Parts**: Users should be able to easily swap different risk models or optimizers without changing other parts of their workflow
- **Complex from Simple**: Enable building sophisticated optimization strategies from simple, well-tested components
- **Pipeline Support**: Support chaining of data preprocessing, optimization, and post-processing steps
- **Module Integration**: New functionality should integrate seamlessly with existing modules
- **Data Flow**: Functions should accept and return standard data types (pandas DataFrames, numpy arrays)
- **Chaining**: Enable method chaining where appropriate for fluent interfaces
- **Functional Style**: Prefer pure functions when possible; avoid side effects

### Additional Design Principles

#### Sensible Defaults
Whenever an operation requires a user-defined parameter, if possible, an appropriate default value is defined by the library. The default value should cause the operation to be performed in a sensible way (giving a baseline solution for the task at hand).

**In Practice:**
- **Out-of-box Functionality**: Provide reasonable default parameters that work for common portfolio optimization problems
- **Progressive Disclosure**: Make simple cases simple while enabling complex cases
- **Practical Defaults**: Default values should reflect industry best practices and produce meaningful baseline results

#### Flexibility & Extensibility
- **Input Formats**: Support multiple input formats where reasonable (DataFrame, dict, file paths)
- **Optional Parameters**: Provide sensible defaults while allowing customization
- **Configuration**: Support both programmatic and configuration-file-based setup
- **Extensibility**: Design for future extension without breaking existing code

#### Duck Typing
To ease code reuse, simplify implementation and skip the introduction of superfluous classes, the Python principle of duck typing is exploited throughout the codebase. This means that objects and classes are defined by interface, not by inheritance, where the interface is entirely implicit as far as the programming language is concerned. Duck typing allows both for extensibility and flexibility: as long as an object or class follows the API and conventions defined by the library, then it can be used in lieu of a built-in class and external developers are not forced to inherit from any `portopt` class.

### Data Representation Philosophy
The `portopt` project represents data using NumPy multidimensional arrays, SciPy sparse matrices, and Pandas data frames. While these may seem rather unsophisticated data representations when compared to more object-oriented constructs, they bring the prime advantage of leveraging efficient NumPy, SciPy, and Pandas data operations while keeping the code short and readable. This design choice has also been motivated by the fact that, given their pervasiveness in many other Python packages, many users of Python are already familiar with NumPy, SciPy, and Pandas.

## Architectural Patterns

### Mixin Pattern
The `portopt` library uses the mixin pattern extensively to create focused, testable, and cohesive units of functionality that can be composed to create more complex behavior.

#### Mixin Design Principles
- **Single Responsibility**: Each mixin should have one clear, focused purpose
- **Composability**: Mixins should be designed to work together seamlessly
- **Testability**: Each mixin should be independently testable
- **Reusability**: Mixins should be reusable across different classes and contexts

#### Common Mixin Patterns
- **Validation Mixins**: Provide input validation for specific data types or constraints
- **Calculation Mixins**: Implement specific mathematical or financial calculations
- **Formatting Mixins**: Handle data transformation and output formatting
- **Persistence Mixins**: Manage data loading, saving, and serialization
- **Metrics Mixins**: Provide standardized calculation of performance metrics

#### Mixin Implementation Guidelines
- **Clear Interfaces**: Define clear methods and attributes that the mixin provides
- **Dependency Declaration**: Clearly document any methods or attributes the mixin expects from the host class
- **Naming Conventions**: Use descriptive names that indicate the mixin's purpose
- **Method Resolution**: Be aware of method resolution order (MRO) when combining multiple mixins
- **Documentation**: Document the mixin's purpose, expected usage, and any requirements

#### Example Mixin Structure
```python
class ValidationMixin:
    """Mixin providing portfolio validation functionality."""
    
    def validate_weights(self, weights: pd.Series) -> bool:
        """Validate that portfolio weights sum to 1.0."""
        return abs(weights.sum() - 1.0) < 1e-6
    
    def validate_returns(self, returns: pd.DataFrame) -> bool:
        """Validate return data format and completeness."""
        # Implementation here
        pass

class MetricsMixin:
    """Mixin providing portfolio performance metrics."""
    
    def sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio for given returns."""
        # Implementation here
        pass
    
    def max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown for given returns."""
        # Implementation here
        pass

class Portfolio(ValidationMixin, MetricsMixin):
    """Portfolio class with validation and metrics capabilities."""
    
    def __init__(self, weights: pd.Series):
        if not self.validate_weights(weights):
            raise ValueError("Invalid portfolio weights")
        self.weights = weights
```

## Implementation Standards

### Code Quality

#### Python Style
- **PEP 8 Compliance**: Follow PEP 8 style guidelines
- **Line Length**: Keep lines under 100 characters when practical
- **Imports**: Organize imports (standard library, third-party, local)
- **Naming**: Use descriptive names; avoid abbreviations unless they're domain standard

#### Type Safety
- **Type Hints**: Use type hints for function signatures and class attributes
- **Optional Types**: Use `Optional[T]` for parameters that can be None
- **Generic Types**: Use appropriate generic types for containers
- **Protocol Types**: Use Protocol for duck typing where appropriate

#### Testing Standards
- **Coverage**: Maintain >90% test coverage for new code
- **Test Organization**: Mirror source structure in test directory
- **Test Naming**: Use descriptive test names that explain what is being tested
- **Edge Cases**: Include tests for edge cases and error conditions
- **Integration Tests**: Test module interactions, not just individual functions

### Documentation Standards
- **Public APIs**: All public functions and classes must have comprehensive docstrings
- **Docstring Standards**: Follow NumPy/SciPy docstring conventions
- **Type Hints**: Use type hints for all public APIs
- **Examples**: Include examples in docstrings for complex functions
- **Complex Logic**: Comment complex algorithms and business logic
- **API Stability**: Clearly mark experimental vs. stable APIs
- **Changelog**: Document breaking changes and new features

### Module Organization

#### Separation of Concerns
- **Single Responsibility**: Each module should have a clear, focused purpose
- **Domain Boundaries**: Separate financial concepts, data processing, and optimization logic
- **Utility Functions**: Place reusable utilities in appropriate shared modules

#### Dependencies
- **Minimal Dependencies**: Avoid adding dependencies unless they provide significant value
- **Optional Dependencies**: Make specialized dependencies optional where possible
- **Version Pinning**: Be conservative with dependency version requirements
- **Import Strategy**: Use explicit imports; avoid `import *`

#### File Structure
- **Logical Grouping**: Group related functionality in the same module
- **Size Management**: Keep modules reasonably sized (typically <1000 lines)
- **Public Interfaces**: Use `__all__` to define public APIs
- **Private Functions**: Use leading underscore for internal functions

## Data Handling Standards

### Data Types & Validation
- **Primary Types**: Use pandas DataFrames for tabular data, numpy arrays for numerical data
- **Index Standards**: Use meaningful index names and types
- **Column Naming**: Use consistent, descriptive column names
- **Missing Data**: Handle NaN values explicitly and document behavior
- **Input Validation**: Validate all inputs at function entry points
- **Data Integrity**: Check for data consistency (e.g., portfolio weights sum to 1)
- **Range Checks**: Validate numerical ranges where appropriate
- **Format Validation**: Ensure data formats match expectations

### Performance Considerations
- **Vectorization**: Use pandas/numpy vectorized operations over loops
- **Memory Management**: Be conscious of memory usage with large datasets
- **Copying**: Minimize unnecessary data copying
- **Indexing**: Use efficient indexing strategies
- **Memory Efficiency**: Consider memory usage for large portfolios and datasets
- **Computational Efficiency**: Optimize critical paths; use vectorized operations
- **Lazy Evaluation**: Compute results only when needed where appropriate
- **Caching**: Cache expensive computations when safe and beneficial

## Error Handling & Reliability

### Exception Types
- **ValueError**: For invalid parameter values or data
- **TypeError**: For incorrect parameter types
- **KeyError**: For missing required keys/columns
- **FileNotFoundError**: For missing data files
- **Custom Exceptions**: Create custom exceptions for domain-specific errors

### Error Messages & Handling
- **Clear Messages**: Provide actionable error messages with context
- **Early Validation**: Validate inputs early and fail fast
- **Graceful Degradation**: Handle missing data gracefully when possible
- **Context**: Include relevant context in error messages
- **Suggestions**: Provide suggestions for fixing the error when possible
- **Available Options**: List available options when input is invalid
- **Data Information**: Include information about the problematic data

## Configuration & Compatibility

### Configuration Management
- **Environment Variables**: Support environment variable configuration
- **Config Files**: Support YAML/JSON configuration files
- **Programmatic**: Allow full programmatic configuration
- **Defaults**: Provide sensible defaults for all configuration options
- **Hierarchical**: Organize configuration in logical hierarchies
- **Validation**: Validate configuration at startup
- **Documentation**: Document all configuration options
- **Examples**: Provide example configuration files

### Backward Compatibility
- **Semantic Versioning**: Follow semantic versioning for releases
- **Deprecation Policy**: Provide deprecation warnings before removing features
- **Migration Guides**: Provide clear migration paths for breaking changes
- **Feature Flags**: Use feature flags for experimental functionality
- **Impact Assessment**: Assess impact of changes on existing users
- **Testing**: Test backward compatibility with existing usage patterns
- **Communication**: Communicate changes through appropriate channels

## Performance Guidelines

### Optimization Priorities
1. **Correctness**: Never sacrifice correctness for performance
2. **Clarity**: Prefer clear code over micro-optimizations
3. **Measurement**: Profile before optimizing
4. **Algorithmic**: Focus on algorithmic improvements first

### Resource Management
- **Memory**: Monitor memory usage patterns
- **CPU**: Identify and optimize computational bottlenecks
- **I/O**: Minimize file I/O operations
- **Network**: Cache remote data appropriately

### Implementation Guidelines
The library implementation guidelines emphasize writing efficient but readable code. In particular, the codebase should be easily maintainable and understandable in order to favor external contributions. Whenever practicable, algorithms implemented in `portopt` are written in Python, using NumPy or Pandas operations for data processing. This allows for the code to remain concise, readable and efficient.

To facilitate the installation and thus adoption of `portopt`, the set of external dependencies is kept to a bare minimum.

## Contributing Guidelines

### Code Reviews
- **Standards Compliance**: Ensure code follows these principles
- **Testing**: Verify adequate testing coverage
- **Documentation**: Check documentation completeness
- **Performance**: Consider performance implications

### Pull Request Requirements
- **Description**: Clear description of changes and rationale
- **Tests**: Include tests for new functionality
- **Documentation**: Update documentation as needed
- **Breaking Changes**: Clearly mark any breaking changes

---

## References

- [API design for machine learning software: experiences from the scikit-learn project](https://arxiv.org/pdf/1309.0238)
- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [NumPy Docstring Standard](https://numpydoc.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Updates and Maintenance

This document should be updated when:
- New design patterns are established
- Significant architectural decisions are made
- Community feedback suggests improvements
- Tool or dependency changes affect guidelines

All updates should be reviewed and approved by the project maintainers. 