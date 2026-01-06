# /pull_request - Create Pull Request

Generate pull request title and description.

## Usage

```
/pull_request <branch_name> <issue_json> <plan_file> <adw_id>
```

## Arguments

- `branch_name`: Name of the feature branch
- `issue_json`: JSON object containing issue number, title, and body
- `plan_file`: Path to the implementation plan file
- `adw_id`: ADW workflow ID

## Output

Returns the URL of the created pull request.

## Behavior

1. Create a pull request from the branch to main
2. Use issue title and body for PR description
3. Reference the implementation plan
4. Include ADW tracking information
5. Link to the original issue

## Guidelines

- Use clear, descriptive PR title
- Include implementation summary
- Reference the plan file
- Add ADW tracking information
- Link to the GitHub issue

