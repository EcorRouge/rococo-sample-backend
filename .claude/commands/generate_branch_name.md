# /generate_branch_name - Generate Git Branch Name

Generate a standardized git branch name for a GitHub issue.

## Usage

```
/generate_branch_name <issue_type> <adw_id> <issue_json>
```

## Arguments

- `issue_type`: Type of issue (chore, bug, or feature)
- `adw_id`: ADW workflow ID
- `issue_json`: JSON object containing issue number, title, and body

## Output

Returns a branch name following the pattern:
```
{type}-issue-{issue_number}-adw-{adw_id}-{slug}
```

Example: `feat-issue-123-adw-abc12345-add-user-authentication`

## Guidelines

- Use lowercase
- Replace spaces with hyphens
- Keep slug concise but descriptive
- Follow the pattern exactly

