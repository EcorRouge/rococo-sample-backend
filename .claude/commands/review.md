# Review

Follow the `Instructions` below to **review work done against a specification file** (specs/*.md) to ensure implemented features match requirements. Use the spec file to understand the requirements and then use the git diff if available to understand the changes made. If there are issues, report them if not then report success.

## Variables

adw_id: $1
spec_file: $2
agent_name: $3 if provided, otherwise use 'review_agent'

## Instructions

- Check current git branch using `git branch` to understand context
- Run `git diff origin/main` to see all changes made in current branch. Continue even if there are no changes related to the spec file.
- Find the spec file by looking for specs/*.md files in the diff that match the current branch name
- Read the identified spec file to understand requirements
- IMPORTANT: Review the implementation against the spec to ensure it matches requirements
  - Compare implemented changes with spec requirements to verify correctness
  - Check that all acceptance criteria are met
  - Verify that validation commands pass
  - Ensure code follows existing patterns and conventions
- IMPORTANT: Issue Severity Guidelines
  - Think hard about the impact of the issue on the feature and the user
  - Guidelines:
    - `skippable` - the issue is non-blocker for the work to be released but is still a problem
    - `tech_debt` - the issue is non-blocker for the work to be released but will create technical debt that should be addressed in the future
    - `blocker` - the issue is a blocker for the work to be released and should be addressed immediately. It will harm the user experience or will not function as expected.
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Output your result in JSON format based on the `Report` section below.
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- Ultra think as you work through the review process. Focus on the critical functionality paths and the user experience. Don't report issues if they are not critical to the feature.

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- `success` should be `true` if there are NO BLOCKING issues (implementation matches spec for critical functionality)
- `success` should be `false` ONLY if there are BLOCKING issues that prevent the work from being released
- `review_issues` can contain issues of any severity (skippable, tech_debt, or blocker)
- This allows subsequent agents to quickly identify and resolve blocking errors while documenting all issues

### Output Structure

{
    "success": "boolean - true if there are NO BLOCKING issues (can have skippable/tech_debt issues), false if there are BLOCKING issues",
    "review_summary": "string - 2-4 sentences describing what was built and whether it matches the spec. Written as if reporting during a standup meeting.",
    "review_issues": [
        {
            "review_issue_number": "number - the issue number based on the index of this issue",
            "issue_description": "string - description of the issue",
            "issue_resolution": "string - description of the resolution",
            "issue_severity": "string - severity of the issue between 'skippable', 'tech_debt', 'blocker'"
        },
        ...
    ]
}