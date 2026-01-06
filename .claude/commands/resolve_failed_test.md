# /resolve_failed_test - Resolve Failed Test Cases

Analyze failed test cases and fix them by either updating the test or fixing the code.

## Usage

```
/resolve_failed_test <failed_tests_json>
```

## Arguments

- `failed_tests_json`: JSON array of failed test results with error information

## Behavior

1. Analyze the failed test cases and their error messages
2. Determine if the issue is in the test code or the implementation
3. Fix the test or implementation as appropriate
4. Re-run the tests to verify the fix
5. Return updated test results

## Output Format

Return a JSON array of updated test results:

```json
[
  {
    "test_name": "test_person_repository_create",
    "passed": true,
    "execution_command": "pytest tests/test_person_repository.py::test_person_repository_create -v",
    "test_purpose": "Test creating a new person in the repository",
    "error": null
  }
]
```

## Guidelines

- Fix the root cause, not just the symptoms
- If the test is wrong, fix the test
- If the implementation is wrong, fix the implementation
- Ensure all fixes maintain backward compatibility
- Add appropriate error handling if missing
- Update related tests if implementation changes affect them

