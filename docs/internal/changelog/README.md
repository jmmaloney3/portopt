# Changelog System

This directory contains a structured changelog system for tracking changes made by both AI agents and human contributors to the Portfolio Optimization project.

## Philosophy

Unlike traditional changelogs that aggregate changes by version, this system tracks individual change sessions to provide:
- **Granular tracking**: Each development session is documented separately
- **Agent accountability**: Clear attribution of changes to specific agents or humans
- **Context preservation**: Rich context about why changes were made
- **Debugging support**: Detailed technical information for troubleshooting
- **Knowledge continuity**: Future agents can understand the evolution of the codebase

## File Structure

### Directory Organization
```
docs/internal/changelog/
├── README.md                           # This file
├── 000-changelog-template.md           # Template for new entries
├── YYYY/                               # Year directories
│   ├── MM/                             # Month directories  
│   │   ├── YYYYMMDD-001-brief-description.md
│   │   ├── YYYYMMDD-002-another-change.md
│   │   └── ...
│   └── ...
└── index/                              # Optional indexing files (Future)
    ├── by-agent.md                     # Changes grouped by agent
    ├── by-component.md                 # Changes grouped by system component
    └── by-type.md                      # Changes grouped by type (feature, bugfix, etc.)
```

### Scalability Benefits
- **Hierarchical organization**: Year/month structure prevents directory bloat
- **Chronological ordering**: Natural time-based organization
- **Easy navigation**: Clear structure for finding specific time periods
- **Automated tooling**: Structure supports automated indexing and reporting

## Naming Convention

### File Naming Format
```
YYYYMMDD-xxx-brief-description.md
```

### Components
- **YYYYMMDD**: ISO date format (no hyphens) for chronological sorting
- **xxx**: Three-digit sequential number (001, 002, 003, etc.) for uniqueness within a day
- **brief-description**: Kebab-case description (2-4 words max)

### Examples
```
20250614-001-metrics-double-counting-fix.md
20250622-001-adr-documentation-creation.md
20250623-001-test-suite-enhancement.md
```

### Naming Guidelines
- Use YYYYMMDD date format (no hyphens in date portion)
- Sequential numbering starts at 001 each day
- Keep descriptions brief but descriptive
- Use kebab-case (lowercase with hyphens) for descriptions
- Avoid special characters except hyphens in descriptions
- Focus on the primary change, not implementation details

### Determining Sequential Numbers
To find the next sequential number for a given date:
```bash
# List existing files for today (replace with current date)
ls docs/internal/changelog/2025/06/20250622-*.md | wc -l

# Or use find to search across all directories
find docs/internal/changelog -name "20250622-*.md" | wc -l
```
The next number would be the count + 1, formatted as a three-digit number (e.g., 001, 002, 003).

## Entry Template

Use the template at `000-changelog-template.md` for all new entries. The template includes:

- **Clear section guidelines** - Each section is marked as REQUIRED or OPTIONAL
- **Content-only approach** - Omit sections that don't apply rather than including empty sections
- **Detailed instructions** - Specific guidance for what to include in each section

Follow the template's guidelines exactly to ensure consistency and completeness across all changelog entries.

## Agent Integration

### For AI Agents
When making changes, create a changelog entry with:
```yaml
agent: "claude-3-sonnet" # or your agent identifier
human: "git-user-name" # from git config user.name
session_id: "session-name-provided-by-human" # AI agents cannot retrieve this automatically
```

### For Human Contributors  
When making changes, create a changelog entry with:
```yaml
agent: "human"
human: "git-user-name" # from git config user.name
session_id: "descriptive-session-name" # or git-commit-hash
```

### Session ID Guidelines
- **AI agents cannot automatically retrieve session IDs** - The human must provide the session name/identifier
- **Use descriptive names** when possible (e.g., "metrics-refactor-session", "bug-fix-debugging")
- **Multiple sessions** can be listed if work spans multiple AI sessions
- **Consistency** - Use the same session ID format within your team/project

## Workflow

### 1. Before Making Changes
- Plan the work and identify the scope
- Note any related issues or requirements

### 2. During Development
- Keep notes of significant decisions
- Document any unexpected issues or solutions

### 3. After Completing Changes
- Copy the template to create a new entry
- Fill in all relevant sections
- Save with the proper naming convention
- Consider updating index files if they exist

## Maintenance

### Regular Tasks
- **Monthly**: Review entries for completeness
- **Quarterly**: Update index files if maintained
- **Yearly**: Archive old directories if needed

### Cleanup Guidelines
- Keep all entries (don't delete historical records)
- Compress very old directories if storage becomes an issue
- Maintain index files to help with navigation

## Integration with Other Systems

### ADRs (Architecture Decision Records)
- Reference relevant ADRs in the "Technical Details" section
- Create new ADRs for significant architectural changes
- Link between changelog entries and ADRs bidirectionally

### Git Integration
- Include git commit hashes in changelog entries
- Reference changelog entries in commit messages
- Use changelog entries to write better commit messages

### Issue Tracking
- Link to GitHub issues in the "Related Issues/PRs" section
- Use changelog entries to provide detailed closure notes
- Reference changelog entries in issue comments

## Tools and Automation

### Potential Automation
- **Entry Creation**: Scripts to generate entries from templates
- **Index Generation**: Automated index file creation
- **Validation**: Checks for required sections and proper formatting
- **Reporting**: Summary reports for time periods or agents

### Manual Tools
- **Search**: Use grep/ripgrep to search across entries
- **Navigation**: File explorer or command-line tools for browsing
- **Aggregation**: Manual compilation for release notes or reports

## Best Practices

### Writing Quality
- Be specific and detailed
- Use clear, professional language
- Include code examples where helpful
- Focus on the "why" not just the "what"

### Technical Accuracy
- Include exact file paths and line numbers
- Document configuration changes precisely
- Provide complete test instructions
- Include rollback procedures for risky changes

### Future-Proofing
- Write for someone unfamiliar with the current context
- Explain acronyms and project-specific terminology
- Include links to external documentation
- Assume the reader is debugging an issue months later

## Examples

See the following entries:
- `20250614-001-metrics-double-counting-fix.md` - MetricsMixin refactor and double-counting bug fix (actual entry)
- `20250622-001-adr-documentation-creation.md` - ADR creation and METRICS.md refactoring (actual entry)
- `20250623-001-test-suite-enhancement.md` - Test infrastructure improvement (example) 