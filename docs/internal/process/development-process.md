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

## Roles & Responsibilities

This process involves multiple stakeholders with distinct areas of authority and responsibility. Clear role definition ensures proper governance while enabling efficient decision-making.

### Document Ownership & Approval Authority

Each document type in the development process has a designated owner who must approve changes to maintain consistency and system integrity:

| Document Type | Template | Owner | Approval Authority | Scope of Responsibility |
|---------------|----------|-------|-------------------|------------------------|
| **Requirements Document** | [Requirements Template](../templates/requirements-template.md) | **Product Manager** | Business requirements, functional specifications, acceptance criteria | Owns the "what" needs to be built and business value |
| **Feature Decomposition** | [Feature Decomposition Specification](../templates/feature-decomposition-specification.md) | **Architecture Lead** | System-level design, increment boundaries, interfaces, dependencies | Owns system architecture and integration coherence |
| **Technical Design Document** | [Technical Design Template](../templates/technical-design-template.md) | **Technical Lead** | Implementation approach, detailed technical design, development patterns | Owns "how" the increment will be technically implemented |
| **Architecture Decision Records** | [ADR Template](../adr/000-adr-template.md) | **Architecture Lead** | Architectural choices, technology decisions, system-level patterns | Owns architectural decisions that impact system design |
| **Implementation Learning** | [Implementation Learning Capture](../templates/implementation-learning-capture.md) | **Development Team** | Knowledge capture, lessons learned, development insights | No approval needed - knowledge sharing activity |

### Role Definitions

#### **Product Manager**
- **Primary Focus**: Business value, user needs, and functional requirements
- **Key Responsibilities**:
  - Defines and maintains business requirements and acceptance criteria
  - Approves changes to functional specifications and scope
  - Negotiates requirement changes with technical teams
  - Ensures business alignment throughout development process

#### **Architecture Lead** 
- **Primary Focus**: System-level design coherence and architectural integrity
- **Key Responsibilities**:
  - Defines system architecture and integration patterns
  - Approves feature decomposition and increment boundaries
  - Validates architectural decisions and technology choices
  - Ensures system-level consistency across increments
  - Maintains architectural decision records (ADRs)

#### **Technical Lead**
- **Primary Focus**: Detailed implementation approach and technical execution
- **Key Responsibilities**:
  - Creates and maintains technical design documents
  - Defines implementation approach and development patterns
  - Approves technical design changes during implementation
  - Ensures technical quality and consistency within increments
  - May be the same person as the implementing developer

#### **Development Team**
- **Primary Focus**: Implementation execution and knowledge capture
- **Key Responsibilities**:
  - Implements code, tests, and documentation following standards
  - Identifies issues during design and implementation phases
  - Captures implementation lessons and insights
  - Follows established technical designs and architectural decisions

### Decision-Making Authority

#### **Requirements & Scope Changes**
- **Authority**: Product Manager
- **When**: Requirements discoveries during design (Step 2.2) or implementation (Step 3.2)
- **Process**: Negotiate → Approve → Update requirements document → Adjust approach

#### **System Design & Architecture Changes**  
- **Authority**: Architecture Lead
- **When**: Decomposition issues or architectural decisions during design (Step 2.2) or implementation (Step 3.2)
- **Process**: Negotiate → Approve → Update decomposition/create ADR → Adjust approach

#### **Technical Implementation Changes**
- **Authority**: Technical Lead  
- **When**: Technical design modifications needed during implementation (Step 3.2)
- **Process**: Negotiate → Approve → Update technical design → Adjust implementation

### Escalation & Conflict Resolution

**Cross-Role Conflicts**: When decisions span multiple areas of authority (e.g., business requirements vs. technical constraints), stakeholders should collaborate to find solutions that satisfy both business and technical needs.

**Approval Rejection**: If document owners reject proposed changes, the requesting team must either:
- Modify their approach to work within existing constraints, or  
- Accept technical debt and document it for future resolution, or
- Escalate to higher-level decision makers for resolution

**Role Clarity**: When unclear which role has authority, default to the most restrictive interpretation and involve all potentially affected stakeholders in the decision.

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

**For Major Features (New Functionality)**:
1. **Create initial requirements document** conforming to the [Requirements Template](../templates/requirements-template.md)
   - **Recommended approach**: Use the [Requirements Gathering Prompt](../prompts/requirements-gathering-prompt.md) with an AI agent to conduct a structured interview
2. **Share for stakeholder review** and gather feedback on clarity, completeness, and feasibility
3. **Iterate on requirements** based on feedback until stakeholders agree requirements are clear and complete

**For Bug Fixes & Minor Enhancements**:
1. **Review existing acceptance criteria** in the ticket/issue 
2. **Clarify ambiguous criteria** with stakeholders if needed
3. **Ensure acceptance criteria are testable** and clearly define "done"

**Validation Activities** (All Work Types):
- **Verify requirements clarity**: Can someone else understand what needs to be built?
- **Confirm acceptance criteria**: Are success criteria specific and testable?
- **Validate scope boundaries**: Is it clear what's in scope vs out of scope?
- **Check for completeness**: Are all requirement types addressed (functional, DX, non-functional, constraints)?

**Deliverables**: 
- [ ] **Accepted requirements**: Requirements are agreed upon by both requirement providers and implementers
  - **For major features**: Requirements document following template format
  - **For minor work**: Acceptance criteria documented in ticket/issue

### 1.2 Determine Design Approach (System-Wide Activity)

**What to do**: Decide whether this requires monolithic or iterative design approach.

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

**Deliverables**:
- [ ] Design approach decided (iterative vs monolithic)

### 1.3 Plan Feature Decomposition (System-Wide Activity - Iterative Only)

**What to do**: Create feature decomposition document that breaks complex requirements into implementable increments using the [Feature Decomposition Specification](../templates/feature-decomposition-specification.md).

**Instructions**:
- **For Iterative Approach**: Create feature decomposition document conforming to the [Feature Decomposition Specification](../templates/feature-decomposition-specification.md)
- **Recommended approach**: Use the [Feature Decomposition Prompt](../prompts/feature-decomposition-prompt.md) with an AI agent to conduct a structured systems engineering interview
- **For Monolithic Approach**: Skip this section

**Deliverables**:
- [ ] **For Iterative**: Feature decomposition document created with defined increments, dependencies, and interfaces
- [ ] **For Monolithic**: N/A (skip to Step 2)

---

## Step 2: Increment Design Phase (Per-Increment Activity)

*This phase contains increment-specific design activities that are performed once for each increment (1x for monolithic approach, Nx for iterative approach).*

### 2.1 Review Design Context

**What to do**: Review all relevant context from previous work to understand the current increment design scope and constraints.

**Context Review** (All Increments):
1. **Review current requirements document** - Focus on sections relevant to current increment scope
2. **Review current feature decomposition** - Understand increment boundaries, interfaces, and dependencies
3. **Review relevant ADRs** - Understand architectural decisions that may impact current increment
4. **Review implementation learning documents** - Learn from previous increment patterns and lessons (may include learnings from previous projects for first increment)

**Deliverables**:
- [ ] All relevant context reviewed and understood (requirements, decomposition, ADRs, learning documents)
- [ ] Design scope and constraints clearly understood

### 2.2 Create Technical Design

**What to do**: Create detailed technical design document for the current increment, updating requirements or decomposition as design discoveries are made.

**Design Process**:
- **Create technical design document** conforming to the [Technical Design Template](../templates/technical-design-template.md)
- **Recommended approach**: Use the [Technical Design Prompt](../prompts/technical-design-prompt.md) with an AI agent to conduct a structured design interview
- **For Iterative**: Focus on current increment scope and interfaces to other increments
- **For Monolithic**: Design the complete feature

**Design-Time Discovery Process**:
As design progresses, you may discover issues that require immediate attention:

1. **Requirements issues discovered** - If design reveals missing, incorrect, or infeasible requirements:
   - **Negotiate with product manager** to resolve requirements issues
   - **Obtain approval** from product manager for requirements changes
   - **Update requirements document** with approved changes

2. **Decomposition issues discovered** - If design reveals interface conflicts, dependency problems, or scope boundary issues:
   - **Negotiate with architecture lead** to resolve decomposition issues  
   - **Obtain approval** from architecture lead for feature decomposition changes
   - **Update feature decomposition document** with approved changes

3. **Architectural decisions required** - If significant architectural or technology choices are made during design:
   - **Negotiate with architecture lead** to validate architectural decisions
   - **Obtain approval** from architecture lead for architectural decisions  
   - **Document as ADRs** using [ADR Template](../adr/000-adr-template.md)

**Note**: Design-time discoveries should be resolved immediately rather than waiting until Step 5.1, as they represent fundamental feasibility and scope issues that affect the validity of the current design approach. Requirements and decomposition changes require approval from document owners before implementation begins. If approval is not granted, the design approach must be modified to work within the existing constraints.

**Deliverables**:
- [ ] Technical design document created for current increment/feature following template structure
- [ ] Requirements document updated with approved changes if design discoveries revealed issues (if applicable)
- [ ] Feature decomposition updated with approved changes if design discoveries revealed issues (if applicable)
- [ ] ADRs created with architecture lead approval for significant technical decisions made during design (if applicable)

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

**What to do**: Implement the increment functionality by developing code, tests, and documentation together, resolving any implementation-discovered issues through proper approval channels.

**Implementation Process**:
1. Follow [Implementation Standards](design-principles-and-standards.md#implementation-standards) from Design Principles & Standards
2. **For Iterative Approach**: Implement one increment at a time

**Implementation-Time Discovery Process**:
As implementation progresses, you may discover issues that require immediate resolution:

1. **Requirements issues discovered** - If implementation reveals additional missing/incorrect requirements beyond those found during design:
   - **Negotiate with product manager** to resolve requirements issues
   - **Obtain approval** from product manager for requirements changes
   - **Update requirements document** with approved changes
   - **Adjust implementation** based on approved requirements

2. **Decomposition issues discovered** - If implementation reveals interface, scope, or dependency issues not identified during design:
   - **Negotiate with architecture lead** to resolve decomposition issues
   - **Obtain approval** from architecture lead for feature decomposition changes
   - **Update feature decomposition document** with approved changes
   - **Adjust implementation** based on approved decomposition

3. **Technical design changes needed** - If implementation reveals that the technical design approach needs modification:
   - **Negotiate with technical lead** (design document author) to resolve technical design issues
   - **Obtain approval** from technical lead for technical design changes
   - **Update technical design document** with approved changes
   - **Adjust implementation** based on approved technical design

4. **Architectural decisions required** - If additional architectural or technology choices need to be made during implementation (beyond those documented during design):
   - **Negotiate with architecture lead** to validate architectural decisions
   - **Obtain approval** from architecture lead for architectural decisions
   - **Document as ADRs** using [ADR Template](../adr/000-adr-template.md)
   - **Continue implementation** using approved technical approach

**Note**: Implementation-time discoveries should be resolved immediately to prevent implementing against known-incorrect requirements, decomposition, or design approaches. If approval is not granted, implementation approach must be modified to work within existing constraints or technical debt must be accepted and documented.

**Implementation Deliverables**:
- [ ] **Implementation standards met** - Follow [Implementation Standards](design-principles-and-standards.md#implementation-standards) (code quality, testing, documentation, repository practices, module organization)
- [ ] **All tests pass locally** - No regressions in existing functionality
- [ ] **Requirements document updated** with approved implementation-discovered changes (if applicable)
- [ ] **Feature decomposition updated** with approved implementation-discovered changes (if applicable)
- [ ] **Technical design document updated** with approved implementation-discovered changes (if applicable)
- [ ] **ADRs created** with architecture lead approval for implementation-time architectural decisions (if applicable)

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

### 5.1 Capture Implementation Lessons

**What to do**: Document implementation insights, patterns, and lessons learned for future reference.

**Knowledge Capture Process**:
Document implementation lessons using [Implementation Learning Capture](../templates/implementation-learning-capture.md):

1. **Development patterns and techniques** - What coding approaches worked well or poorly
2. **Technical insights and gotchas** - Unexpected discoveries about libraries, frameworks, or system behavior  
3. **Performance learnings** - Insights about system performance, bottlenecks, or optimizations
4. **Integration lessons** - What worked or didn't work when integrating with existing systems
5. **Testing approaches** - Effective testing strategies and patterns discovered during implementation
6. **Tooling and workflow insights** - Development tools, processes, or workflows that enhanced or hindered productivity

**Note**: All requirements, decomposition, and architectural decision issues should have already been resolved during Step 3.2 (Implement Increment) through proper approval channels. This step focuses purely on knowledge capture that will benefit future development efforts.

**Knowledge Capture Deliverables**:
- [ ] Implementation lessons documented for future reference using the learning capture template

### 5.2 Merge and Deploy

**What to do**: Merge your changes and deploy to integration environment.

**Instructions**:
1. Merge pull request using project's preferred merge strategy
2. Verify integration tests pass in integration environment
3. Validate system-level coherence following System Integration Standards
4. Monitor for any immediate issues
5. Clean up feature branch after successful merge

**Integration Checklist**:
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

**Release Checklist**:
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