# Development Process SOP for portopt

## Document Information

- **Title**: Development Process Standard Operating Procedure (SOP)
- **Author**: john and claude-4-sonnet
- **Date Created**: 2025-07-19
- **Last Updated**: 2025-07-31
- **Version**: 1.1
- **Status**: Draft

## How to Use This SOP

**For New Development Work**: Follow Steps 1-5 sequentially from start to finish.

**For Quick Reference**: Use the [Quick Reference Index](#quick-reference-index) to jump to specific standards and policies.

**For Code Reviews**: Skip to [Step 4: Review & Approval Phase](#step-4-review--approval-phase) for reviewer instructions.

**For Troubleshooting**: Check the [Reference Materials](#reference-materials) section for detailed policies and procedures.

## Overview

This Standard Operating Procedure (SOP) defines the step-by-step process for all software development work within the portopt project. Follow these instructions sequentially to ensure consistent quality, maintainability, and reliability. Each step includes just-in-time guidance, checklists, and references to detailed procedures.

## Development Workflow Overview

All development work follows this five-phase process:

1. **Feature Analysis & Design** - Define requirements, determine implementation approach, create feature decomposition (system-wide activities)
2. **Increment Design** - Plan technical approach for current increment (per-increment activity)
3. **Development** - Set up environment, implement functionality with tests and documentation, perform self-review (per-increment activity)
4. **Review & Approval** - Peer review, approvals, and final validation (per-increment activity)
5. **Integration & Release** - Merge, deploy, and monitor changes (per-increment activity)

*Phase 1 contains system-wide activities (done once per feature). Phases 2-5 contain per-increment activities (repeated for each increment: 1x for monolithic, Nx for iterative).*

---

## Step 1: Feature Analysis & Design Phase (System-Wide Activities)

*This phase contains system-wide activities that are performed once per feature, regardless of whether the implementation uses a single increment (monolithic) or multiple increments (iterative).*

### 1.1 Define Requirements (System-Wide Activity)

**What to do**: Create or review requirements documentation for your feature/task using the [Requirements Template](../templates/requirements-template.md).

**Process Decision**: We use structured requirements gathering to ensure comprehensive coverage of business needs, functional capabilities, and developer experience.

**Instructions**:
- **For new functionality**: Create requirements document conforming to the [Requirements Template](../templates/requirements-template.md)
- **Recommended approach**: Use the [Requirements Gathering Prompt](../prompts/requirements-gathering-prompt.md) with an AI agent to conduct a structured interview
- **For bug fixes or minor enhancements**: Ensure you understand the acceptance criteria
- **Identify dependencies** on other features or systems
- **Clarify ambiguous requirements** with stakeholders

**Benefits of Structured Requirements**:
- **Complete Coverage**: Ensures all requirement types are addressed (business, functional, DX, non-functional, constraints)
- **Traceability**: Clear linkage from business problems to implementation details
- **Developer Focus**: Special attention to Developer Experience for library-focused projects
- **Early Risk Identification**: Surface dependencies and constraints before implementation

**Deliverables**: 
- [ ] Requirements clearly defined and understood
- [ ] Acceptance criteria identified
- [ ] Dependencies documented

### 1.2 Determine Design Approach (System-Wide Activity)

**What to do**: Decide whether this requires monolithic or iterative design approach.

**Process Decision**: We treat iterative design as the norm and monolithic design as a special case (single increment). This enables early value delivery, rapid feedback, and risk mitigation for complex features.

#### Iterative vs Monolithic Design Decision

**Use Iterative Design When:**
- Requirements span >3 major functional areas
- High technical uncertainty or risk
- Implementation estimated >4 weeks
- Natural increment boundaries exist  
- Early value delivery and user feedback are important
- Feature has multiple distinct capabilities that could provide standalone value

**Use Monolithic Design When:**
- Single cohesive functional area
- Well-understood technical approach
- Implementation estimated <3 weeks
- No meaningful increment boundaries
- Tight coupling between components makes separation impractical

**Benefits of Iterative Design**:
- **Risk Mitigation**: Fail fast on infeasible approaches with minimal investment
- **Better Designs**: Implementation learning improves subsequent design decisions
- **Early Value Delivery**: Users get working functionality sooner
- **Rapid Feedback**: Get user feedback early to prevent building the wrong thing
- **Manageable Complexity**: Smaller design sessions are less overwhelming and more focused
- **Adaptability**: Can pivot based on implementation discoveries and user feedback

**Acceptable Trade-offs**:
- **Early Delivery Philosophy**: Accept risk of some interface rework to deliver value sooner and get feedback before investing too heavily in any direction
- **Process Overhead**: Multiple design sessions vs single comprehensive session
- **Interface Evolution**: May need to refactor interfaces between increments based on learnings
- **Coordination Complexity**: Managing dependencies and sequencing between increments

**Deliverables**:
- [ ] Design approach decided (iterative vs monolithic)

### 1.3 Plan Feature Decomposition (System-Wide Activity - Iterative Only)

**What to do**: Create feature decomposition document that breaks complex requirements into implementable increments using the [Feature Decomposition Specification](../templates/feature-decomposition-specification.md).

**Instructions**:
- **For Iterative Approach**: Create feature decomposition document conforming to the [Feature Decomposition Specification](../templates/feature-decomposition-specification.md)
- **Recommended approach**: Use the [Feature Decomposition Prompt](../prompts/feature-decomposition-prompt.md) with an AI agent to conduct a structured systems engineering interview
- **Plan learning integration** between increments and define increment interfaces
- **For Monolithic Approach**: Skip this section

**Deliverables**:
- [ ] **For Iterative**: Feature decomposition document created with defined increments, dependencies, and interfaces
- [ ] **For Monolithic**: N/A (skip to Step 2)
- [ ] Existing tests pass locally

---

## Step 2: Increment Design Phase (Per-Increment Activity)

*This phase contains increment-specific design activities that are performed once for each increment (1x for monolithic approach, Nx for iterative approach).*

### 2.1 Plan Technical Approach

**What to do**: Create detailed technical design document for the current increment (or complete feature if monolithic) using the [Technical Design Template](../templates/technical-design-template.md).

**Instructions**:
- **For Iterative Approach - Before Designing Subsequent Increments**: Complete Learning Integration preparation (see Learning Integration Checklist)
- **Create technical design document** conforming to the [Technical Design Template](../templates/technical-design-template.md)
- **Recommended approach**: Use the [Technical Design Prompt](../prompts/technical-design-prompt.md) with an AI agent to conduct a structured design interview
- **For Iterative**: Focus on current increment scope and interfaces to other increments, incorporating learnings from previous increments
- **For Monolithic**: Design the complete feature

**Learning Integration Checklist** (for subsequent increments in iterative approach):
- [ ] **Implementation Learning Captured** - Previous increment learnings documented using [Implementation Learning Capture](../templates/implementation-learning-capture.md)
- [ ] **Interface Refinements Identified** - Needed changes to interfaces documented
- [ ] **Design Adaptations Planned** - Next increment design adapted based on learnings
- [ ] **Risk Updates** - Risk assessment updated based on implementation experience

**Deliverables**:
- [ ] **For Iterative - Subsequent Increments**: Learning integration preparation completed
- [ ] Technical design document created for current increment/feature following template structure

---

## Step 3: Development Phase (Per-Increment Activity)

*This phase contains all development and pre-review validation activities that are performed once for each increment (1x for monolithic approach, Nx for iterative approach).*

### 3.1 Set Up Development Environment

**What to do**: Prepare your development environment and create your feature branch.

**Instructions**:
1. Ensure your local environment matches [Development Tools](design-principles-and-standards.md#process--infrastructure-standards) requirements
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

### 3.2 Implement Increment

**What to do**: Implement the increment functionality by developing code, tests, and documentation together following all implementation standards.

**Process Decision**: We implement incrementally with frequent commits, developing code, tests, and documentation in parallel following established standards.

**Instructions**:
1. Follow [Implementation Standards](design-principles-and-standards.md#implementation-standards) from Design Principles & Standards
2. **For Iterative Approach**: Implement one increment at a time, capturing learnings using [Implementation Learning Capture](../templates/implementation-learning-capture.md)

**Implementation Checklist**:
- [ ] **Implementation standards met** - Follow [Implementation Standards](design-principles-and-standards.md#implementation-standards) (code quality, testing, documentation, repository practices, module organization)
- [ ] **All tests pass locally** - No regressions in existing functionality

### 3.3 Complete Development Validation

**What to do**: Perform comprehensive validation including self-review, automated validation, manual testing, and compatibility checks before requesting peer review.

#### Self-Review
**Instructions**:
1. Review your code changes line by line using the [Code Review Checklist](design-principles-and-standards.md#code-review-checklist) from Design Principles & Standards
2. Focus especially on areas where you can objectively self-assess:
   - Requirements fulfillment and logic correctness
   - Code readability and maintainability  
   - Error handling and security considerations
3. For areas requiring external perspective (design fit, integration impact), prepare context for reviewers
4. Fix any issues you identify before requesting peer review

#### Automated Validation
**Instructions**:
1. Run full test suite locally: `pytest`
2. Check test coverage: `pytest --cov`
3. Run linting: `flake8` or configured linter
4. Ensure CI/CD pipeline passes (push to feature branch and check status)
5. Fix any issues found by automated checks

#### Manual Testing
**Instructions**:
1. Test the happy path with typical inputs
2. Test error scenarios and edge cases
3. Test integration with related functionality
4. For UI changes, test across different environments
5. Document any manual testing performed

#### Compatibility Validation
**Instructions**:
1. Follow [Backward Compatibility Standards](design-principles-and-standards.md#backward-compatibility) from Design Principles & Standards

**Development Validation Checklist**:
- [ ] **Self-review completed** - Code reviewed using [Code Review Checklist](design-principles-and-standards.md#code-review-checklist)
- [ ] **All automated tests pass** - Full test suite passes without errors
- [ ] **CI/CD pipeline passes** - All automated quality checks and builds succeed
- [ ] **Linting passes** - Code style meets project standards
- [ ] **Test coverage maintained** - Coverage thresholds met
- [ ] **Manual testing completed** - Happy path, error scenarios, and integration tested
- [ ] **Compatibility standards met** - [Backward Compatibility Standards](design-principles-and-standards.md#backward-compatibility) followed

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
Use the [Code Review Checklist](design-principles-and-standards.md#code-review-checklist) from Design Principles & Standards to ensure comprehensive review.

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
3. **For Iterative Approach**: After each increment, capture implementation learnings and plan next increment design session
4. Validate system-level coherence following System Integration Standards
5. Monitor for any immediate issues
6. Clean up feature branch after successful merge

**Integration Checklist**:
- [ ] **Code merged** - Pull request successfully merged to main
- [ ] **Integration tests pass** - Full test suite passes in integration environment
- [ ] **System integration standards met** - Follow [System Integration Standards](design-principles-and-standards.md#system-integration-standards) (API coherence, end-to-end workflows, performance, documentation)
- [ ] **Implementation learnings captured** - For iterative approach, document learnings from completed increment
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
- [ ] **Compatibility verified** - [Backward Compatibility Standards](design-principles-and-standards.md#backward-compatibility) followed

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

All development standards have been consolidated into the [Design Principles & Development Standards](design-principles-and-standards.md) document to serve as a single source of truth.

### Quick Reference to Standards
- **All Development Standards**: [Design Principles & Development Standards](design-principles-and-standards.md)
  - Implementation Standards (code quality, testing, documentation, repository practices, module organization)
  - Code Review Standards
  - Build & Deployment Standards
  - Security & Compliance Standards
  - Process & Infrastructure Standards

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

- [portopt Design Principles & Standards](design-principles-and-standards.md)
- [Requirements Template](../templates/requirements-template.md)
- [Requirements Gathering Prompt](../prompts/requirements-gathering-prompt.md)
- [Feature Decomposition Prompt](../prompts/feature-decomposition-prompt.md)
- [Technical Design Prompt](../prompts/technical-design-prompt.md)
- [ADR Templates](adr/000-adr-template.md)  
- [Changelog Guidelines](changelog/README.md) 