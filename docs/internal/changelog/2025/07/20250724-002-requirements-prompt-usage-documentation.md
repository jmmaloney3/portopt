---
# Metadata (remove this section in actual entries)
entry_id: "20250724-002-requirements-prompt-usage-documentation"
agent: "claude-4-sonnet" 
human: "john"
session_id: "Creating a prompt for requirements gathering"
timestamp: "2025-07-24T18:11:00Z"
---

# Requirements Gathering Prompt Usage Documentation

## Context
Enhanced the requirements gathering prompt document to include comprehensive usage instructions for humans while maintaining clear separation from AI agent instructions. This addresses the need for self-documenting processes that can be easily discovered and properly used by team members.

## Changes Made

### Documentation Changes
- Added "How to Use This Prompt" section to `docs/internal/process/requirements-gathering-prompt.md`
- Created clear separation between human instructions and AI agent instructions using horizontal dividers
- Added explicit notes directing AI agents to ignore human-focused sections
- Included quick start command with Cursor `@` file reference syntax
- Documented 4-phase interview process overview for users
- Added practical tips for successful requirements gathering sessions

### Content Improvements
- Enhanced Quick Start section with tool compatibility clarification (Cursor and other AI tools with file references)
- Added specific placeholder identification for users (`[brief description of what you want to build]`)
- Set realistic time expectations (30-60 minutes for complete process)
- Included guidance on preparation and success criteria

## Testing Performed
- Reviewed document structure to ensure clear separation between human and AI instructions
- Verified that file references work correctly in the quick start command
- Confirmed that AI agent instructions remain unmodified and focused
- Validated that usage instructions are comprehensive and actionable

## Impact Assessment

### Documentation Impact
- Self-documenting process - new users can understand usage without external training
- Reduced barrier to adoption through clear quick start instructions
- Improved discoverability of requirements gathering capabilities
- Standardized invocation method across different AI tools

### Process Improvement
- Eliminates need to copy/paste large prompt content
- Maintains single source of truth for requirements gathering process
- Provides realistic expectations about time commitment and preparation needed
- Reduces risk of improper usage through clear guidance

## Follow-up Actions

### Future
- Consider creating video tutorial or walkthrough example showing the process in action
- Gather feedback from first users to refine instructions
- Add examples of well-formed feature descriptions for the quick start command

## Technical Details

### Document Structure Design
- Clear visual separation using horizontal dividers (`---`)
- Explicit audience targeting with "NOTE FOR AI AGENTS" and "NOTE FOR HUMANS" 
- Defensive design preventing AI confusion about role boundaries
- Maintains full prompt functionality while adding user guidance

### Usage Pattern Optimization
- Leverages Cursor's `@` file reference capability for clean invocation
- Supports any AI tool with file reference or upload capability
- Provides template command that users can customize with their feature ideas
- Sets appropriate expectations for interview depth and time commitment 