# /commit - Generate Git Commit Message

Generate a properly formatted git commit message for changes.

## Usage

```
/commit <agent_name> <issue_type> <issue_json>
```

## Arguments

- `agent_name`: Name of the agent making the commit (e.g., "sdlc_planner", "sdlc_implementor")
- `issue_type`: Type of issue (chore, bug, or feature)
- `issue_json`: JSON object containing issue number, title, and body

## Output

Returns a commit message following conventional commits format:

```
<type>(<scope>): <subject>

<body>

Closes #<issue_number>
```

## Guidelines

- Use conventional commit format
- Include issue number in footer
- Be descriptive but concise
- Reference the ADW ID if relevant

