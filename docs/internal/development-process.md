# Development Process SOP for portopt

## Document Information

- **Title**: Development Process Standard Operating Procedure (SOP)
- **Author**: [Author name]
- **Date Created**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]
- **Version**: 1.0
- **Status**: [Draft | Active | Deprecated]

## How to Use This SOP

**For New Development Work**: Follow Steps 1-5 sequentially from start to finish.

**For Quick Reference**: Use the [Quick Reference Index](#quick-reference-index) to jump to specific standards and policies.

**For Code Reviews**: Skip to [Step 4: Review & Approval Phase](#step-4-review--approval-phase) for reviewer instructions.

**For Troubleshooting**: Check the [Reference Materials](#reference-materials) section for detailed policies and procedures.

## Overview

This Standard Operating Procedure (SOP) defines the step-by-step process for all software development work within the portopt project. Follow these instructions sequentially to ensure consistent quality, maintainability, and reliability. Each step includes just-in-time guidance, checklists, and references to detailed procedures.

## Development Workflow Overview

All development work follows this five-phase process:

1. **Planning & Setup** - Define requirements, create branches, set up environment
2. **Development** - Implement functionality with tests and documentation  
3. **Pre-Review Validation** - Self-check and automated validation before peer review
4. **Review & Approval** - Peer review, approvals, and final validation
5. **Integration & Release** - Merge, deploy, and monitor changes

*Each phase is detailed with step-by-step instructions below.*

---

## Step 1: Planning & Setup Phase

### 1.1 Define Requirements
**What to do**: Create or review requirements documentation for your feature/task.

**Instructions**:
1. If this is new functionality, create requirements using the [Requirements Template](specs/requirements-template.md)
2. If this is a bug fix or a minor enhancement, ensure you understand the acceptance criteria
3. Identify dependencies on other features or systems
4. Clarify any ambiguous requirements with stakeholders

**Deliverables**: 
- [ ] Requirements clearly defined and understood
- [ ] Acceptance criteria identified
- [ ] Dependencies documented

### 1.2 Plan Technical Approach
**What to do**: Design your implementation approach and identify risks.

**Instructions**:
1. Review existing code and architecture patterns
2. Identify which modules need to be modified or created
3. Plan your testing strategy (unit, integration, manual)
4. Identify risks and mitigation strategies:
   - **Security risks**: Authentication, authorization, data validation, injection attacks
   - **Performance risks**: Scalability, memory usage, computational complexity
   - **Technical risks**: Integration points, dependency conflicts, compatibility issues
   - **Operational risks**: Deployment complexity, monitoring, rollback procedures
5. For significant changes, discuss approach with team lead

**Deliverables**:
- [ ] Implementation approach planned
- [ ] Testing strategy identified
- [ ] Security, performance, technical, and operational risks assessed

### 1.3 Set Up Development Environment
**What to do**: Prepare your development environment and create your feature branch.

**Instructions**:
1. Ensure your local environment matches [Development Tools](#development-tools) requirements
2. Pull latest changes from main branch
3. Create feature branch following naming conventions: `feature/brief-description` or `bugfix/brief-description`
4. Verify development environment is working (run existing tests)

**Commands**:
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

**Deliverables**:
- [ ] Development environment configured
- [ ] Feature branch created
- [ ] Existing tests pass locally

---

## Step 2: Development Phase

### 2.1 Implement Core Functionality
**What to do**: Write the main code for your feature following project standards.

**Instructions**:
1. Follow [Repository Standards](#repository-standards) for code organization
2. Implement functionality incrementally with frequent commits
3. Follow Python code style guidelines (PEP 8, meaningful names, type hints)
4. Add docstrings for public functions and classes
5. Add code comments explaining complex logic ("why" not "what")

**Code Quality Checklist**:
- [ ] **Style guidelines met** - Follows PEP 8, lines under 100 characters
- [ ] **Meaningful names used** - Variables, functions, and classes have clear, descriptive names
- [ ] **Type hints added** - Public APIs and complex functions include appropriate type hints
- [ ] **Code comments added** - Complex logic explained with "why" not just "what"

### 2.2 Write Tests Alongside Implementation
**What to do**: Create comprehensive tests for your functionality.

**Instructions**:
1. Follow [Testing Standards](#testing-standards) for test structure and organization
2. Write unit tests for individual functions/methods
3. Create integration tests for module interactions
4. Test edge cases, error conditions, and boundary scenarios
5. Ensure test coverage meets >90% threshold
6. Run tests frequently during development

**Testing Checklist**:
- [ ] **Unit tests added** - Individual functions/methods tested in isolation
- [ ] **Integration tests added** - Module interactions tested (if applicable)
- [ ] **Edge cases tested** - Error conditions, boundary cases, and invalid inputs covered
- [ ] **Test coverage >90%** - Automated test suite maintains coverage thresholds
- [ ] **All tests pass locally** - No regressions in existing functionality

### 2.3 Update Documentation
**What to do**: Create or update documentation alongside your implementation.

**Instructions**:
1. Update API documentation (docstrings) for any new or modified public interfaces
2. Update user guides if functionality affects end-user workflows
3. Update architecture documentation for significant structural changes
4. Create usage examples for new functionality
5. Ensure documentation is clear and includes practical examples

**Documentation Checklist**:
- [ ] **API documentation updated** - Public APIs have complete docstrings with examples
- [ ] **User documentation updated** - Guides updated for user-facing changes
- [ ] **Architecture docs updated** - Structural changes documented (if applicable)
- [ ] **Changelog updated** - Significant changes documented for release notes

### 2.4 Perform Self-Review
**What to do**: Review your own code using the same criteria that peer reviewers will apply.

**Instructions**:
1. Review your code changes line by line using the [Code Review Checklist](#code-review-checklist) from Code Review Standards
2. Focus especially on areas where you can objectively self-assess:
   - Requirements fulfillment and logic correctness
   - Code readability and maintainability  
   - Error handling and security considerations
3. For areas requiring external perspective (design fit, integration impact), prepare context for reviewers
4. Fix any issues you identify before requesting peer review

**Self-Review Checklist**: 
Use the [Code Review Checklist](#code-review-checklist) from Code Review Standards - the same criteria reviewers will apply.

---

## Step 3: Pre-Review Validation Phase

### 3.1 Complete Developer Validation
**What to do**: Run all automated checks and ensure your code meets quality standards.

**Instructions**:
1. Run full test suite locally: `pytest`
2. Check test coverage: `pytest --cov`
3. Run linting: `flake8` or configured linter
4. Ensure CI/CD pipeline passes (push to feature branch and check status)
5. Fix any issues found by automated checks

**Automated Validation Checklist**:
- [ ] **All automated tests pass** - Full test suite passes without errors
- [ ] **CI/CD pipeline passes** - All automated quality checks and builds succeed
- [ ] **Linting passes** - Code style meets project standards
- [ ] **Test coverage maintained** - Coverage thresholds met

### 3.2 Perform Manual Testing
**What to do**: Test your functionality manually to catch issues automation might miss.

**Instructions**:
1. Test the happy path with typical inputs
2. Test error scenarios and edge cases
3. Test integration with related functionality
4. For UI changes, test across different environments
5. Document any manual testing performed

**Manual Testing Checklist**:
- [ ] **Happy path tested** - Core functionality works with typical inputs
- [ ] **Error scenarios tested** - System handles invalid inputs gracefully
- [ ] **Integration tested** - Works correctly with related functionality

### 3.3 Ensure Backward Compatibility
**What to do**: Verify your changes don't break existing functionality.

**Instructions**:
1. Review [API Compatibility Policy](#api-compatibility-policy)
2. If making breaking changes, follow deprecation process
3. Test against existing code that uses your modified APIs

**Compatibility Checklist**:
- [ ] **Backward compatibility maintained** - Existing APIs continue to work (unless deprecation followed)
- [ ] **Breaking changes documented** - Deprecation process followed if needed

### 3.4 Create Pull Request
**What to do**: Create a clear, well-documented pull request.

**Instructions**:
1. Write clear PR title and description
2. Link to relevant issues or requirements
3. Describe what was implemented and why
4. Include testing notes and any special considerations
5. Request appropriate reviewers based on code areas affected

**Pull Request Checklist**:
- [ ] **Clear title and description** - PR purpose and changes clearly explained  
- [ ] **Requirements linked** - Connected to relevant issues or requirements
- [ ] **Testing described** - Manual testing performed documented
- [ ] **Reviewers assigned** - Appropriate team members requested for review

---

## Step 4: Review & Approval Phase

### 4.1 Code Reviewer Instructions
**What to do** (for reviewers): Conduct thorough review focusing on aspects that require human judgment.

**Review Focus Areas**:
- **Design & Architecture** - Does solution fit well with existing patterns?
- **Code Quality & Maintainability** - Is code readable and well-structured?
- **Testing & Documentation** - Are tests appropriate and documentation clear?

**Feedback Guidelines**:
- **Constructive & Actionable** - Provide specific suggestions, not just criticism
- **Educational** - Explain the "why" behind feedback to help developer learning
- **Respectful** - Focus on code, not person; acknowledge good practices too
- **Clear & Specific** - Point to exact lines and provide concrete improvement suggestions

**Code Review Checklist**: 
Use the [Code Review Checklist](#code-review-checklist) from Code Review Standards to ensure comprehensive review.

### 4.2 Support Code Review Process
**What to do**: Respond to reviewer feedback and iterate on your implementation.

**Instructions**:
1. Respond to reviewer comments promptly and professionally
2. Make requested changes or explain why alternatives are better
3. Re-request review after making significant changes
4. Ensure all reviewer concerns are addressed

### 4.3 Obtain Required Approvals
**What to do**: Ensure all necessary approvals are obtained before merge.

**Instructions**:
1. At least one peer code review approval required
2. Security review required for security-sensitive changes
3. Architecture review required for significant design changes
4. All automated checks must pass

**Approval Checklist**:
- [ ] **Code review approved** - At least one peer approval received
- [ ] **Security review completed** - For security-sensitive changes
- [ ] **Architecture review completed** - For significant design changes
- [ ] **All automated checks pass** - CI/CD pipeline is green

---

## Step 5: Integration & Release Phase

### 5.1 Merge and Deploy
**What to do**: Merge your changes and deploy to integration environment.

**Instructions**:
1. Merge pull request using project's preferred merge strategy
2. Verify integration tests pass in integration environment
3. Monitor for any immediate issues
4. Clean up feature branch after successful merge

**Integration Checklist**:
- [ ] **Code merged** - Pull request successfully merged to main
- [ ] **Integration tests pass** - Full test suite passes in integration environment
- [ ] **No immediate issues** - No obvious problems detected post-merge

### 5.2 Release Preparation (If Applicable)
**What to do**: Prepare for release if your changes are part of a release.

**Instructions**:
1. Update version numbers following [Release Process](#release-process)
2. Update release notes with your changes
3. Verify API compatibility requirements are met
4. Coordinate with release manager if needed

**Release Checklist**:
- [ ] **Version updated** - Version numbers updated per semantic versioning
- [ ] **Release notes updated** - Changes documented for users
- [ ] **Compatibility verified** - API compatibility policy followed

### 5.3 Post-Deployment Monitoring
**What to do**: Monitor your changes after deployment to catch any issues.

**Instructions**:
1. Monitor system health for first 24 hours after deployment
2. Watch for error rates or performance regressions
3. Be available to respond to any issues
4. Document any lessons learned

**Monitoring Checklist**:
- [ ] **System health monitored** - No unusual errors or performance issues
- [ ] **Ready to respond** - Available to address any issues that arise
- [ ] **Lessons documented** - Any insights captured for future improvements

---

## Reference Materials

The following sections provide detailed standards, policies, and procedures referenced in the step-by-step instructions above. Use these as reference when you need specific guidance on implementation details.

### Quick Reference Index
- **Development Standards**: [Repository Standards](#repository-standards), [Testing Standards](#testing-standards), [Manual Testing](#manual-testing--validation)
- **Quality Assurance**: [Continuous Integration](#continuous-integration), [API Compatibility Policy](#api-compatibility-policy), [Code Review Standards](#code-review-standards)
- **Process Management**: [Release Process](#release-process)
- **Organizational Support**: [Tools and Infrastructure](#tools-and-infrastructure)
- **Governance**: [Compliance and Standards](#compliance-and-standards), [Process Improvement](#process-improvement)

## Repository Standards

### Branch Management
- **Main Branch**: Always deployable, protected from direct pushes
- **Feature Branches**: Created for each user story or task
- **Branch Naming**: Use descriptive names (e.g., `feature/risk-calculation`, `bugfix/portfolio-loading`)

### Commit Standards
- **Commit Messages**: Use clear, descriptive commit messages
- **Atomic Commits**: Each commit should represent a single logical change
- **Commit Frequency**: Commit often with meaningful checkpoints

## Testing Standards

### Test Implementation
- **Test Structure**: Follow Arrange-Act-Assert pattern
- **Test Naming**: Use descriptive test names that explain what is being tested
- **Mocking**: Use appropriate mocking for external dependencies
- **Test Data**: Use representative test data sets in isolated environments

### Test Types
- **Unit Testing**: Test individual components in isolation
- **Integration Testing**: Test module interactions and end-to-end workflows
- **Performance Testing**: Establish baselines and monitor for regressions

## Manual Testing & Validation

- **Test Plans**: Create test plans for complex features
- **User Acceptance**: Verify functionality meets user requirements
- **Edge Case Testing**: Test boundary conditions and error scenarios

## Continuous Integration

### Automation Requirements
- **Quality Gate Automation**: All checklist criteria must be enforced through automated checks where possible
- **Pull Request Validation**: Automated checks must pass before human review
- **Build Pipeline**: Automated linting, testing, security scanning, and dependency checking

### Build & Deployment Standards
- **Reproducible Builds**: Ensure builds are consistent and reproducible
- **Artifact Management**: Manage build artifacts and dependencies
- **Environment Consistency**: Maintain consistent development and production environments

## Code Review Standards

### Code Review Checklist

The following checklist is used for both self-review (Step 2.4) and peer review (Step 4.1) to ensure consistent quality standards:

- [ ] **Requirements met** - Implementation fulfills acceptance criteria
- [ ] **Design principles followed** - Adheres to [portopt Design Principles](design-principles.md)
- [ ] **Logic is sound and efficient** - Implementation is correct and reasonably optimized
- [ ] **Code is readable and maintainable** - Future developers can understand and modify
- [ ] **Test strategy is appropriate** - Tests cover the right scenarios at the right level
- [ ] **Documentation quality is good** - Clear, accurate, and helpful documentation
- [ ] **Error handling appropriate** - Proper error handling and edge case management
- [ ] **Security implications considered** - No obvious security vulnerabilities
- [ ] **Performance considered** - No obvious performance issues introduced
- [ ] **Integration considerations reviewed** - Impacts on other components considered

## Release Process

### Version Management
- **Semantic Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)
- **Release Notes**: Document all changes, fixes, and new features
- **Changelog**: Maintain detailed changelog for all releases

### Deployment
- **Staging**: Test in staging environment before production
- **Rollback Plan**: Have rollback procedures for all deployments
- **Monitoring**: Monitor system health after deployments

## API Compatibility Policy

### Backwards Compatibility Standards

All changes to public APIs must follow these compatibility standards:

#### **Semantic Versioning**
- **MAJOR version**: Breaking changes that require user code modifications
- **MINOR version**: New functionality that is backwards compatible
- **PATCH version**: Backwards compatible bug fixes

#### **Breaking Change Definition**
Breaking changes include but are not limited to:
- Removing public functions, classes, or methods
- Changing function signatures (parameters, return types)
- Changing public class interfaces
- Modifying expected behavior of existing functionality
- Changing import paths or module organization

#### **Non-Breaking Changes**
These changes are allowed in MINOR releases:
- Adding new public functions, classes, or methods
- Adding new optional parameters with default values
- Adding new return fields to existing functions (where applicable)
- Internal implementation improvements that don't affect public behavior

#### **Deprecation Process**
- **Warning Phase**: Mark as deprecated with clear warnings and migration guidance
- **Timeline**: Minimum 6 months deprecation period before removal
- **Documentation**: Update all documentation to reflect deprecation
- **Migration Guide**: Provide clear migration path to new functionality

#### **API Stability Guarantees**
- **Public API**: Covered by backwards compatibility guarantees
- **Private/Internal**: Marked with leading underscore, no compatibility guarantees
- **Experimental**: Clearly marked, may change without notice

### API Documentation Requirements
- All public APIs must have complete docstrings
- Breaking changes must be documented in changelog with migration instructions
- Deprecations must include timeline and recommended alternatives

## Compliance and Standards

### Security Standards
- **Vulnerability Scanning**: Regular security scans of dependencies
- **Secure Coding**: Follow secure coding practices
- **Access Control**: Implement appropriate access controls
- **Data Protection**: Protect sensitive data appropriately

### Regulatory Compliance
- **License Compliance**: Ensure all dependencies have compatible licenses
- **Documentation**: Maintain required documentation for compliance
- **Audit Trail**: Maintain audit trails for changes and deployments

## Process Improvement

### Metrics and Monitoring
- **Development Metrics**: Track cycle time, defect rates, and test coverage
- **Quality Metrics**: Monitor code quality and technical debt
- **Performance Metrics**: Track system performance and reliability

### Retrospectives
- **Regular Reviews**: Conduct regular process retrospectives
- **Continuous Improvement**: Implement process improvements based on feedback
- **Knowledge Sharing**: Share lessons learned across the team

## Tools and Infrastructure

### Development Tools
- **IDE/Editor**: [Specify preferred development environment]
- **Version Control**: Git with GitHub/GitLab
- **Package Management**: `pipenv` for Python dependencies
- **Testing**: `pytest` for Python testing

### CI/CD Tools
- **Build System**: [Specify CI/CD platform]
- **Deployment**: [Specify deployment tools]
- **Monitoring**: [Specify monitoring and alerting tools]

---

## Document Maintenance

This document should be reviewed and updated regularly to reflect:
- Changes in development practices
- New tools and technologies
- Lessons learned from retrospectives
- Industry best practices evolution

**Review Schedule**: Quarterly review and update as needed
**Owner**: [Development Team Lead]
**Approval**: [Technical Lead/CTO]

## Related Documents

- [portopt Design Principles](design-principles.md)
- [Requirements Template](specs/requirements-template.md)
- [ADR Templates](adr/000-adr-template.md)
- [Changelog Guidelines](changelog/README.md) 