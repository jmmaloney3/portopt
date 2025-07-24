---
# Metadata (remove this section in actual entries)
entry_id: "20250727-001-requirements-gathering-prompt-creation"
agent: "claude-sonnet-4" 
human: "john"
session_id: "Creating a prompt for requirements gathering"
timestamp: "2025-07-24T03:37:33Z"
---

# Requirements Gathering Prompt Creation

## Context
Created a comprehensive AI agent prompt to facilitate structured requirements gathering interviews for new portopt features. This addresses the need for consistent, thorough requirements documentation that follows the established requirements template and ensures all requirement types are properly captured.

## Changes Made

### Documentation Changes
- Created `docs/internal/process/requirements-gathering-prompt.md` - comprehensive prompt for AI agents to conduct structured requirements interviews
- Updated `docs/internal/specs/requirements-template.md` to incorporate MoSCoW prioritization method and explicit functional requirement format
- Enhanced requirements template with clearer priority definitions and format requirements
- Added credential handling and security considerations to the requirements gathering process
- Updated `docs/internal/changelog/000-changelog-template.md` to use ISO8601 timestamp format and provide guidance for AI agents to obtain current UTC time via web search

### Configuration Changes
- Updated functional requirements template to mandate "The system must..." format for consistency
- Replaced Critical/High/Medium/Low priority system with MoSCoW method (Must have/Should have/Could have/Won't have)
- Updated all example requirements in template to demonstrate new prioritization approach
- Consolidated changelog template date/time fields into single ISO8601 timestamp field for standardization

## Testing Performed
- Reviewed both documents for consistency and completeness
- Verified that the requirements gathering prompt references the correct template location
- Ensured all requirement types are covered in the interview structure
- Validated that the prompt includes portopt-specific considerations for developer-facing libraries

## Impact Assessment

### Documentation Impact
- Provides standardized approach for requirements gathering across all portopt features
- Improves consistency and thoroughness of requirements documentation
- Better alignment with agile development practices through MoSCoW prioritization
- Enhanced focus on Developer Experience requirements for library use cases

### Process Improvement
- Enables systematic requirements discovery through structured interview phases
- Reduces risk of missing critical requirement types during feature planning
- Supports better prioritization and scope management through MoSCoW method
- Includes specific guidance for financial software security considerations (credentials, brokerage access)
- Improved changelog template standardization with ISO8601 timestamps and web search guidance for AI agents

## Follow-up Actions

### Immediate
- Test the requirements gathering prompt with a sample feature to validate effectiveness

### Future
- Consider creating requirement gathering templates for different feature types (API integrations, optimization algorithms, data analysis features)
- Develop training materials for using the requirements gathering process
- Create examples of completed requirements documents generated using this process

## Technical Details

### Process Design
- Four-phase interview structure: Business Context → Functional Capabilities → Developer Experience → Quality & Constraints
- Comprehensive traceability framework linking problems to objectives to user stories to technical requirements
- Quality checklist ensuring completeness and portopt-specific considerations
- Built-in guidance for avoiding common requirements gathering pitfalls

### Security Enhancements
- Added specific credential handling discovery questions for financial integrations
- Included compliance considerations (SOC 2, PCI DSS) relevant to portfolio management software
- Enhanced security requirement gathering for brokerage and data provider integrations

### Template Standardization
- Simplified changelog metadata format by consolidating separate date/time fields into single ISO8601 timestamp
- Added explicit guidance for AI agents to obtain current UTC time via web search ("current time UTC")
- Improved consistency and machine-readability of changelog timestamps 