# /classify_issue - Classify GitHub Issue Type

Classify a GitHub issue to determine if it's a chore, bug, or feature.

## Usage

```
/classify_issue <issue_json>
```

## Arguments

- `issue_json`: JSON object containing issue number, title, and body

## Output

Returns one of:
- `/chore` - Maintenance, documentation, refactoring
- `/bug` - Bug fixes and corrections
- `/feature` - New features and enhancements
- `0` - Cannot be classified

## Guidelines

- Analyze the issue title and body
- Consider the nature of the change requested
- Default to `/feature` if unclear
- Use `/chore` for non-functional changes
- Use `/bug` for fixing incorrect behavior

