---
# Metadata (remove this section in actual entries)
entry_id: "{YYYYMMDD-xxx-brief-description}"
agent: "{agent-name or 'human' - for AI agents, verify model name from UI since agents cannot self-identify reliably}"
human: "{git-user-name or human-identifier}"
session_id: "{unique-session-identifier - AI agents cannot retrieve this automatically, human must provide}"
timestamp: "{ISO8601 format: YYYY-MM-DDTHH:MM:SSZ - AI agents can get current UTC time by web searching 'current time UTC'}"
---

# {Brief Description of Changes}

## Context
{REQUIRED: 1-2 sentences describing what prompted these changes. What problem was being solved or what feature was being implemented?}

## Changes Made
{REQUIRED: Include only the subsections that apply to your changes}

### Code Changes
- {List specific files modified, created, or deleted with brief descriptions}
- {Include code quality improvements like refactoring, separation of concerns, etc.}

### Bug Fixes
- {List bugs that were fixed with brief descriptions}

### Automated Test Changes
- {List new test files or test cases added/modified/removed}
- {Describe test coverage improvements}

### Documentation Changes
- {List documentation files updated}

### Configuration Changes
- {List config files, environment variables, or settings modified}

### Dependency Changes
- {List packages added, updated, or removed with version changes}

## Testing Performed
{REQUIRED: Describe testing that was performed to verify the change.  At a bare minimum, the automated test suite should ALWAYS be executed.}
- {Describe manual testing steps taken to verify the changes work}
- {Include any edge cases tested}
- {Include automated test execution results if relevant}

## Impact Assessment
{OPTIONAL: Include this section only if there are notable impacts}

### Breaking Changes
- {List breaking changes with migration steps if needed}

### Performance Impact
- {Describe any performance improvements or regressions}
- {Include benchmark results if available}

### Security Considerations
- {Note security implications or vulnerability fixes}

## Deployment Notes
{OPTIONAL: Include this section only if special deployment considerations exist}

### Prerequisites
- {List any setup steps required before deployment}
- {Include environment variable changes}

### Rollback Plan
- {Describe how to rollback these changes if needed}
- {Include any data migration rollback steps}

## Follow-up Actions
{OPTIONAL: Include this section only if there are specific follow-up tasks}

### Immediate
- {List immediate follow-up tasks}

### Future
- {List future improvements or technical debt created}

## Related Issues/PRs
{OPTIONAL: Include this section only if there are related issues or PRs}

### Issues Resolved
- {Link to GitHub issues closed by these changes}

### Related Work
- {Link to related PRs or commits}

## Technical Details
{OPTIONAL: Include this section only for complex implementations or architectural changes}

### Architecture Changes
- {Describe architectural decisions made, reference ADRs if applicable}

### Implementation Notes
- {Include tricky implementation details or design decisions}