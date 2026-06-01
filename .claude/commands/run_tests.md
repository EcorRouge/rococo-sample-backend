# /run_tests - Run Test Suite

Execute the test suite and report results.

## Usage

```
/run_tests [test_path]
```

## Arguments

- Optional: `test_path` - Specific test file or test function to run (e.g., `tests/test_person.py` or `tests/test_person.py::test_create_person`)

## Behavior

1. Run pytest with appropriate PYTHONPATH configuration
2. Execute all tests or specific test if path provided
3. Report test results with pass/fail status
4. Show coverage if available

## Execution Command

For all tests with full coverage:
```bash
PYTHONPATH=.:common:flask pytest tests/ \
  --cov \
  --cov-report=term-missing \
  --cov-report=term \
  --cov-branch \
  -v
```

For specific test file:
```bash
PYTHONPATH=.:common:flask pytest <test_path> -v
```

For specific test function:
```bash
PYTHONPATH=.:common:flask pytest <test_path>::<test_function> -v
```

## Output Format

Return a summary of test execution results:
- Total tests run
- Passed count
- Failed count
- Skipped count (if any)
- List of failed tests with error messages (if any)
- Coverage summary if available

## Guidelines

- Set PYTHONPATH to include `.`, `common`, and `flask` directories
- Use `-v` flag for verbose output
- Include coverage reporting with `--cov`, `--cov-report`, and `--cov-branch` flags
- Report any test failures with clear error messages
- If tests fail, suggest using `/resolve_failed_test` command to fix them

## Examples

Run all tests:
```
/run_tests
```

Run specific test file:
```
/run_tests tests/test_person.py
```

Run specific test function:
```
/run_tests tests/test_person.py::test_create_person
```

