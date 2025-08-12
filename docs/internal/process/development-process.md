# Development Process SOP for portopt

## Document Information

- **Title**: Development Process Standard Operating Procedure (SOP)
- **Author**: john and claude-4-sonnet
- **Date Created**: 2025-07-19
- **Last Updated**: 2025-08-07
- **Version**: 1.1.2
- **Status**: Draft

## How to Use This SOP

**For New Development Work**: Follow Steps 1-5 sequentially from start to finish.

**For Quick Reference**: Use the [Quick Reference Index](#quick-reference-index) to jump to specific standards and policies.

**For Code Reviews**: Skip to [Step 4: Review & Approval Phase](#step-4-review--approval-phase) for reviewer instructions.

**For Troubleshooting**: Check the [Reference Materials](#reference-materials) section for detailed policies and procedures.

## Overview

This Standard Operating Procedure (SOP) defines the step-by-step process for all software development work within the portopt project. Follow these instructions sequentially to ensure consistent quality, maintainability, and reliability. Each step includes just-in-time guidance, checklists, and references to detailed procedures.

## Roles & Responsibilities

This process involves multiple stakeholders with distinct areas of authority and responsibility. Clear role definition ensures proper governance while enabling efficient decision-making.

### Role Authority Matrix

| Role | Primary Focus | Document Ownership | Decision Authority | Key Activities |
|------|---------------|-------------------|-------------------|----------------|
| **Product Manager** | Business value and user needs | Requirements Document | Business requirements, functional specifications, acceptance criteria | Define requirements, approve scope changes, ensure business alignment |
| **Architecture Lead** | System-level design coherence | Feature Decomposition, ADRs | System architecture, increment boundaries, technology choices | Define system architecture, approve decomposition changes, maintain ADRs |
| **Technical Lead** | Implementation approach | Technical Design Document | Implementation approach, technical design patterns | Create technical designs, approve design changes, ensure design quality and adherence to design principles |
| **Development Team** | Implementation execution | Implementation Learning | N/A (knowledge sharing) | Implement code/tests/docs following development standards, identify issues, capture lessons learned |

### Decision-Making & Conflict Resolution

**Standard Decision Process**: When issues arise during design or implementation that require changes to established documents:

1. **Negotiate** with the appropriate document owner (see Role Authority Matrix above)
2. **Obtain approval** from the document owner for proposed changes
3. **If approved**: Update the relevant document with approved changes and adjust approach accordingly
4. **If not approved**: Choose one of the following options:
   - Modify your approach to work within existing constraints
   - Accept technical debt and document it for future resolution
   - Escalate to higher-level decision makers for resolution

**Special Cases**:
- **Cross-Role Conflicts**: When decisions span multiple authority areas, stakeholders collaborate to find solutions satisfying both business and technical needs
- **Role Clarity**: When authority is unclear, involve all potentially affected stakeholders and default to the most restrictive interpretation

## Process Principles

These core principles guide our development approach and inform the specific procedures outlined in this SOP:

### Structured Requirements Gathering

**Process Decision**: We use structured requirements gathering to ensure comprehensive coverage of business needs, functional capabilities, and developer experience.

This approach provides complete coverage of all requirement types (business, functional, DX, non-functional, constraints), maintains clear traceability from business problems to implementation details, gives special attention to Developer Experience for our library-focused project, and enables early risk identification by surfacing dependencies and constraints before implementation begins.

### Iterative Design as Default

**Process Decision**: We treat iterative design as the norm and monolithic design as a special case (single increment). This enables early value delivery, rapid feedback, and risk mitigation for complex features.

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

### Incremental Implementation

**Process Decision**: We implement incrementally with frequent commits, developing code, tests, and documentation in parallel following established standards.

This parallel development approach ensures quality is built in from the start rather than added later, provides continuous validation through testing, and maintains comprehensive documentation throughout the development process.

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

### 1.1 Requirements Definition & Validation (System-Wide Activity)

**What to do**: Establish clear, validated requirements for your work through an iterative process of creation, review, and refinement.

**Process Flow**: Requirements work is inherently collaborative and iterative. This step involves cycles of definition, review, clarification, and refinement until requirements are clear and agreed upon.

**Instructions**:
- **For Major Features (New Functionality)**:
  1. **Create initial requirements document** conforming to the [Requirements Template](../templates/requirements-template.md)
     - **Recommended approach**: Use the [Requirements Gathering Prompt](../prompts/requirements-gathering-prompt.md) with an AI agent to conduct a structured interview
  2. **Share for stakeholder review** and gather feedback on clarity, completeness, and feasibility
  3. **Iterate on requirements** based on feedback until stakeholders agree requirements are clear and complete
- **For Bug Fixes & Minor Enhancements**:
  1. **Review existing acceptance criteria** in the ticket/issue
  2. **Clarify ambiguous criteria** with stakeholders if needed
  3. **Ensure acceptance criteria are testable** and clearly define "done"

**Validation Activities** (All Work Types):
- **Verify requirements clarity**: Can someone else understand what needs to be built?
- **Confirm acceptance criteria**: Are success criteria specific and testable?
- **Validate scope boundaries**: Is it clear what's in scope vs out of scope?
- **Check for completeness**: Are all requirement types addressed (functional, DX, non-functional, constraints)?

**Completion Criteria**:
- [ ] **Accepted requirements**: Requirements are agreed upon by both requirement providers and implementers
  - **For major features**: Requirements document following template format
  - **For minor work**: Acceptance criteria documented in ticket/issue

### 1.2 Determine Design Approach (System-Wide Activity)

**What to do**: Decide whether this requires monolithic or iterative design approach.

**Instructions**:

- **Use Iterative Design When:**
  - Requirements span >3 major functional areas
  - High technical uncertainty or risk
  - Implementation estimated >4 weeks
  - Natural increment boundaries exist
  - Early value delivery and user feedback are important
  - Feature has multiple distinct capabilities that could provide standalone value

- **Use Monolithic Design When:**
  - Single cohesive functional area
  - Well-understood technical approach
  - Implementation estimated <3 weeks
  - No meaningful increment boundaries
  - Tight coupling between components makes separation impractical

**Completion Criteria**:
- [ ] Design approach decided (iterative vs monolithic)

### 1.3 Plan Feature Decomposition (System-Wide Activity - Iterative Only)

**What to do**: Create and validate feature decomposition document that breaks complex requirements into implementable increments through an iterative process of creation, review, and refinement.

**Process Flow**: Feature decomposition work is inherently collaborative and requires validation from technical stakeholders. This step involves cycles of definition, review, clarification, and refinement until the decomposition is clear and agreed upon.

**Instructions**:
- **For Iterative Approach**:
  1. **Create initial feature decomposition document** conforming to the [Feature Decomposition Specification](../templates/feature-decomposition-specification.md)
     - **Recommended approach**: Use the [Feature Decomposition Prompt](../prompts/feature-decomposition-prompt.md) with an AI agent to conduct a structured systems engineering interview
  2. **Share for technical stakeholder review** with technical leads from affected product areas and gather feedback on architectural coherence, increment boundaries, interfaces, and dependencies
  3. **Iterate on decomposition** based on feedback until technical stakeholders agree the decomposition is architecturally sound and implementable
- **For Monolithic Approach**: Skip this section

**Validation Activities** (Iterative Approach):
- **Verify increment coherence**: Does each increment deliver standalone value and have clear boundaries?
- **Confirm interface clarity**: Are interfaces between increments well-defined and implementable?
- **Validate dependency management**: Are dependencies between increments properly sequenced and manageable?
- **Check architectural consistency**: Does the decomposition align with existing system architecture and design principles?

**Completion Criteria**:
- [ ] **For Iterative**: Accepted feature decomposition with technical stakeholder agreement on increment boundaries, interfaces, and dependencies
- [ ] **For Monolithic**: N/A (skip to Step 2)

---

## Step 2: Increment Design Phase (Per-Increment Activity)

*This phase contains increment-specific design activities that are performed once for each increment (1x for monolithic approach, Nx for iterative approach).*

### 2.1 Review Design Context

**What to do**: Review all relevant context from previous work to understand the current increment design scope and constraints.

**Instructions**:
1. **Review current requirements document** - Focus on sections relevant to current increment scope
2. **Review current feature decomposition** - Understand increment boundaries, interfaces, and dependencies
3. **Review relevant ADRs** - Understand architectural decisions that may impact current increment
4. **Review implementation learning documents** - Learn from previous increment patterns and lessons (may include learnings from previous projects for first increment)

**Completion Criteria**:
- [ ] All relevant context reviewed and understood (requirements, decomposition, ADRs, learning documents)
- [ ] Design scope and constraints clearly understood

### 2.2 Create Technical Design

**What to do**: Create and validate detailed technical design document for the current increment through an iterative process of creation, review, and refinement, updating requirements or decomposition as design discoveries are made.

**Process Flow**: Technical design work is inherently collaborative and requires validation from implementation stakeholders. This step involves cycles of definition, review, clarification, and refinement until the design is clear and agreed upon.

**Instructions**:
1. **Create initial technical design document** conforming to the [Technical Design Template](../templates/technical-design-template.md)
   - **Recommended approach**: Use the [Technical Design Prompt](../prompts/technical-design-prompt.md) with an AI agent to conduct a structured design interview
   - **For Iterative**: Focus on current increment scope and interfaces to other increments
   - **For Monolithic**: Design the complete feature
2. **Share for implementation stakeholder review** with team(s) charged with implementing the design and gather feedback on technical feasibility, implementation approach, and design clarity
3. **Iterate on technical design** based on feedback until implementation stakeholders agree the design is technically sound and implementable

**Validation Activities**:
- **Verify technical feasibility**: Can the proposed approach be implemented with available resources and constraints?
- **Confirm implementation clarity**: Do implementers understand the technical approach and can estimate effort accurately?
- **Validate design soundness**: Does the design follow established patterns and architectural principles?
- **Check integration compatibility**: Will the design work well with existing system components and future increments?

**Completion Criteria**:
- [ ] **Accepted technical design**: Technical design agreed upon by both design creators and implementation stakeholders

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

**Completion Criteria**:
- [ ] Development environment configured
- [ ] Feature branch created
- [ ] Existing tests pass locally

### 3.2 Implement Increment

**What to do**: Implement the increment functionality by developing code, tests, and documentation together, resolving any implementation-discovered issues through proper approval channels.

**Instructions**:
1. Follow [Implementation Standards](design-principles-and-standards.md#implementation-standards) from Design Principles & Standards
2. **For Iterative Approach**: Implement one increment at a time

**Completion Criteria**:
- [ ] **Implementation standards met** - Follow [Implementation Standards](design-principles-and-standards.md#implementation-standards) (code quality, testing, documentation, repository practices, module organization)
- [ ] **All tests pass locally** - No regressions in existing functionality

### 3.3 Complete Development Validation

**What to do**: Perform comprehensive validation including self-review, automated validation, manual testing, and compatibility checks before requesting peer review.

**Instructions**:

- Self-Review
  1. Review your code changes line by line using the [Code Review Checklist](design-principles-and-standards.md#code-review-checklist) from Design Principles & Standards
  2. Focus especially on areas where you can objectively self-assess:
     - Requirements fulfillment and logic correctness
     - Code readability and maintainability
     - Error handling and security considerations
  3. For areas requiring external perspective (design fit, integration impact), prepare context for reviewers
  4. Fix any issues you identify before requesting peer review

- Automated Validation
  1. Run full test suite locally: `pytest`
  2. Check test coverage: `pytest --cov`
  3. Run linting: `flake8` or configured linter
  4. Ensure CI/CD pipeline passes (push to feature branch and check status)
  5. Fix any issues found by automated checks

- Manual Testing
  1. Test the happy path with typical inputs
  2. Test error scenarios and edge cases
  3. Test integration with related functionality
  4. For UI changes, test across different environments
  5. Document any manual testing performed

- Compatibility Validation
  1. Follow [Backward Compatibility Standards](design-principles-and-standards.md#backward-compatibility) from Design Principles & Standards

**Completion Criteria**:
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

**Completion Criteria**:
- [ ] **Clear title and description** - PR purpose and changes clearly explained
- [ ] **Requirements linked** - Connected to relevant issues or requirements
- [ ] **Testing described** - Manual testing performed documented
- [ ] **Reviewers assigned** - Appropriate team members requested for review

---

## Step 4: Review & Approval Phase

### 4.1 Code Reviewer Instructions

**What to do** (for reviewers): Conduct thorough review focusing on aspects that require human judgment.

**Instructions**:
- Use the [Code Review Checklist](design-principles-and-standards.md#code-review-checklist) from Design Principles & Standards to perform comprehensive code review
- Follow the [Code Review Focus Areas](design-principles-and-standards.md#code-review-focus-areas) and [Feedback Guidelines](design-principles-and-standards.md#code-review-feedback-guidelines) for effective reviews

**Completion Criteria**:
- [ ] **Code review completed** - Code has been reviewed against the [Code Review Checklist](design-principles-and-standards.md#code-review-checklist) with feedback provided

### 4.2 Support Code Review Process

**What to do**: Respond to reviewer feedback and iterate on your implementation.

**Instructions**:
1. Respond to reviewer comments promptly and professionally
2. Make requested changes or explain why alternatives are better
3. Re-request review after making significant changes

**Completion Criteria**:
- [ ] **All reviewer comments addressed** - Every review comment has been responded to with either implementation changes or explanations
- [ ] **Changes implemented** - Requested code changes have been made and committed
- [ ] **Re-review requested** - Each code change made in response to a review comment has been reviewed
- [ ] **No outstanding concerns** - All reviewer concerns have been resolved to their satisfaction

### 4.3 Obtain Required Approvals

**What to do**: Ensure all necessary approvals are obtained before merge.

**Instructions**:
1. At least one peer code review approval required
2. Security review required for security-sensitive changes
3. Architecture review required for significant design changes
4. All automated checks must pass

**Completion Criteria**:
- [ ] **Code review approved** - At least one peer approval received
- [ ] **Security review completed** - For security-sensitive changes
- [ ] **Architecture review completed** - For significant design changes
- [ ] **All automated checks pass** - CI/CD pipeline is green

---

## Step 5: Integration & Release Phase

### 5.1 Capture Implementation Lessons

**What to do**: Document implementation insights, patterns, and lessons learned for future reference.

**Instructions**:
Document implementation lessons using [Implementation Learning Capture](../templates/implementation-learning-capture.md):

1. **Development patterns and techniques** - What coding approaches worked well or poorly
2. **Technical insights and gotchas** - Unexpected discoveries about libraries, frameworks, or system behavior
3. **Performance learnings** - Insights about system performance, bottlenecks, or optimizations
4. **Integration lessons** - What worked or didn't work when integrating with existing systems
5. **Testing approaches** - Effective testing strategies and patterns discovered during implementation
6. **Tooling and workflow insights** - Development tools, processes, or workflows that enhanced or hindered productivity

**Note**: All requirements, decomposition, and architectural decision issues should have already been resolved during Step 3.2 (Implement Increment) through proper approval channels. This step focuses purely on knowledge capture that will benefit future development efforts.

**Completion Criteria**:
- [ ] Implementation lessons documented for future reference using the learning capture template

### 5.2 Merge and Deploy

**What to do**: Merge your changes and deploy to integration environment.

**Instructions**:
1. Merge pull request using project's preferred merge strategy
2. Verify integration tests pass in integration environment
3. Validate system-level coherence following System Integration Standards
4. Monitor for any immediate issues
5. Clean up feature branch after successful merge

**Completion Criteria**:
- [ ] **Code merged** - Pull request successfully merged to main
- [ ] **Integration tests pass** - Full test suite passes in integration environment
- [ ] **System integration standards met** - Follow [System Integration Standards](design-principles-and-standards.md#system-integration-standards) (API coherence, end-to-end workflows, performance, documentation)
- [ ] **No immediate issues** - No obvious problems detected post-merge

### 5.3 Release Preparation (If Applicable)

**What to do**: Prepare for release if your changes are part of a release.

**Instructions**:
1. Update version numbers following [Release Process](#release-process)
2. Update release notes with your changes
3. Verify API compatibility requirements are met
4. Coordinate with release manager if needed

**Completion Criteria**:
- [ ] **Version updated** - Version numbers updated per semantic versioning
- [ ] **Release notes updated** - Changes documented for users
- [ ] **Compatibility verified** - [Backward Compatibility Standards](design-principles-and-standards.md#backward-compatibility) followed

### 5.4 Post-Deployment Monitoring

**What to do**: Monitor your changes after deployment to catch any issues.

**Instructions**:
1. Monitor system health for first 24 hours after deployment
2. Watch for error rates or performance regressions
3. Be available to respond to any issues
4. Document any lessons learned

**Completion Criteria**:
- [ ] **System health monitored** - No unusual errors or performance issues
- [ ] **Ready to respond** - Available to address any issues that arise
- [ ] **Lessons documented** - Any insights captured for future improvements

---

## Reference Materials

### Standards
All development standards have been consolidated into the [Design Principles & Development Standards](design-principles-and-standards.md) document to serve as a single source of truth.  This document includes the following standards:
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

**Review Details**:
- **Review Schedule**: Quarterly review and update as needed
- **Owner**: [Development Team Lead]
- **Approval**: Any role impacted by the process change

## Related Documents

- [Design Principles & Standards](design-principles-and-standards.md)
- [Requirements Template](../templates/requirements-template.md)
- [Requirements Gathering Prompt](../prompts/requirements-gathering-prompt.md)
- [Feature Decomposition Specification](../templates/feature-decomposition-specification.md)
- [Feature Decomposition Prompt](../prompts/feature-decomposition-prompt.md)
- [Technical Design Template](../templates/technical-design-template.md)
- [Technical Design Prompt](../prompts/technical-design-prompt.md)
- [Implementation Learning Capture](../templates/implementation-learning-capture.md)
- [ADR Template](adr/000-adr-template.md)
- [Changelog Guidelines](changelog/README.md)
- [Changelog Template](changelog/000-changelog-template.md)