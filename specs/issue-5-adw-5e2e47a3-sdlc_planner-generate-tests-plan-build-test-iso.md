# Chore: Generate Tests for adw_plan_build_test_iso.py

## Metadata
issue_number: `5`
adw_id: `5e2e47a3`
issue_json: `{"number": 5, "title": "Generate tests", "body": "adw_plan_build_test_iso.py\n\nGenerate test for uncovered code. The coverage must reach 100%."}`

## Chore Description
This chore focuses on generating comprehensive test coverage for the `adw_plan_build_test_iso.py` script located in the main repository's `adws/` directory (not in the trees worktree). The script is a compositional ADW workflow that orchestrates three separate workflows: planning (adw_plan_iso.py), building (adw_build_iso.py), and testing (adw_test_iso.py).

The script:
- Accepts issue number and optional ADW ID as command-line arguments
- Executes three workflow steps sequentially using subprocess
- Extracts ADW ID from state files if not provided
- Handles error codes and provides clear user feedback
- Uses environment variables loaded via dotenv

The goal is to achieve 100% test coverage by creating unit tests that cover all code paths, including:
- Successful execution paths for all three workflow steps
- Error handling for missing arguments, failed workflows, and missing state files
- ADW ID extraction logic from state files
- Edge cases like partial failures and warning scenarios

## Relevant Files
Use these files to resolve the chore:

- `/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py` - The main script that needs test coverage. This is a compositional workflow script that orchestrates planning, building, and testing workflows in sequence.

- `/Users/Bek/Downloads/rococo-sample-backend/tests/conftest.py` - Contains pytest fixtures and configuration. We'll need to review this to understand existing test patterns and potentially add fixtures for testing ADW scripts.

- `/Users/Bek/Downloads/rococo-sample-backend/tests/test_*.py` - Existing test files that demonstrate the project's testing patterns, structure, and conventions. These will guide the style and approach for the new tests.

- `/Users/Bek/Downloads/rococo-sample-backend/adws/README.md` - Documentation for the ADW system architecture, workflow dependencies, and usage patterns. Essential for understanding how the script should behave.

- `/Users/Bek/Downloads/rococo-sample-backend/adws/adw_modules/sonarqube.py` - SonarQube integration module that may be referenced in coverage validation.

- `/Users/Bek/Downloads/rococo-sample-backend/pyproject.toml` - Project configuration including test dependencies and pytest configuration.

### New Files
- `/Users/Bek/Downloads/rococo-sample-backend/tests/test_adw_plan_build_test_iso.py` - New comprehensive test file for adw_plan_build_test_iso.py

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyze the target script and existing test patterns
- Read and understand the complete implementation of `adw_plan_build_test_iso.py`
- Identify all code paths, branches, and edge cases that need coverage
- Review existing test files to understand:
  - Testing patterns and conventions used in the project
  - Fixture usage and mocking strategies
  - Test organization and naming conventions
  - Assertion styles and error handling tests
- Review `conftest.py` to understand available fixtures
- Document all functions, branches, and scenarios that need test coverage

### Step 2: Design comprehensive test cases
- Create a test plan covering:
  - Successful execution with all three workflow steps passing
  - Successful execution with ADW ID provided as argument
  - Successful execution with ADW ID auto-detected from state files
  - Planning step failure (exit code != 0)
  - Building step failure (exit code != 0)
  - Testing step failure with warning (exit code != 0)
  - Missing required arguments (no issue number)
  - State file not found after planning step
  - Invalid JSON in state files
  - Missing issue_number in state data
  - Empty agents directory
  - Non-existent agents directory
  - All subprocess calls and their return codes
  - Environment variable loading via dotenv
  - Script directory path resolution
- Ensure every line of code is covered by at least one test case
- Design tests to be isolated, repeatable, and not dependent on external services

### Step 3: Create test fixtures and mocking infrastructure
- Add necessary fixtures to support ADW script testing (either in conftest.py or in the test file itself)
- Set up mocking for:
  - `subprocess.run` calls to avoid actual workflow execution
  - File system operations (reading state files, checking directory existence)
  - `os.path` operations for script directory resolution
  - `dotenv.load_dotenv` to avoid environment dependencies
  - `sys.argv` for command-line argument testing
- Create helper fixtures for:
  - Mock state file data with valid JSON structure
  - Mock directory structures (agents directory, state files)
  - Temporary directory creation if needed

### Step 4: Implement comprehensive unit tests
- Create `/Users/Bek/Downloads/rococo-sample-backend/tests/test_adw_plan_build_test_iso.py`
- Implement test cases following the test plan from Step 2
- Organize tests into logical test classes/groups
- Use descriptive test names that clearly indicate what is being tested
- Include docstrings for complex test scenarios
- Mock all external dependencies (subprocess, file I/O, environment)
- Test all conditional branches and error paths
- Verify:
  - Correct subprocess commands are constructed with proper arguments
  - Exit codes are properly checked and handled
  - Error messages are displayed correctly
  - ADW ID extraction logic works correctly
  - State file parsing handles edge cases
  - Script exits with appropriate exit codes for different scenarios

### Step 5: Run tests and verify 100% coverage
- Execute the test suite: `pytest tests/test_adw_plan_build_test_iso.py -v`
- Run coverage analysis specifically for the target script: `pytest tests/test_adw_plan_build_test_iso.py --cov=adws/adw_plan_build_test_iso.py --cov-report=term-missing`
- Review coverage report to identify any uncovered lines
- Add additional test cases for any uncovered code paths
- Iterate until 100% coverage is achieved
- Ensure all tests pass with zero failures

### Step 6: Validate with full test suite and validation commands
- Run the complete test suite to ensure new tests don't break existing functionality
- Execute all validation commands listed in the "Validation Commands" section
- Fix any regressions or test failures
- Verify that the new tests are stable and don't introduce flakiness
- Confirm that 100% coverage is maintained for `adw_plan_build_test_iso.py`

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `pytest tests/test_adw_plan_build_test_iso.py -v` - Run the new test file to ensure all tests pass
- `pytest tests/test_adw_plan_build_test_iso.py --cov=adws --cov-report=term-missing --cov-report=html` - Verify 100% coverage for adw_plan_build_test_iso.py
- `pytest tests/ -v` - Run full test suite to validate zero regressions

## Notes
- The target script is located in the main repository at `/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py`, NOT in the trees worktree
- The script uses `subprocess.run` to execute other Python scripts, so all subprocess calls should be mocked
- The script reads state files from the `agents/` directory, so file I/O operations need to be mocked
- The ADW ID extraction logic involves finding the most recent state file matching the issue number, which requires careful mocking of directory structure
- Test isolation is critical - tests should not depend on actual state files, worktrees, or external processes
- The script uses `sys.exit()` for error handling, so tests need to catch `SystemExit` exceptions
- Coverage should be measured against the original script in the main repository, not the worktree copy
- Follow the existing test patterns in the `tests/` directory for consistency
- The script is a single-file Python script that can be run with `uv run` or directly with Python, so tests should not depend on the execution method
