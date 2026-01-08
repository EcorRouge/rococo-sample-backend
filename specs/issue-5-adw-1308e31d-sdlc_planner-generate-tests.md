# Chore: Generate tests for adw_plan_build_test_iso.py

## Metadata
issue_number: `5`
adw_id: `1308e31d`
issue_json: `{"number": 5, "title": "Generate tests", "body": "adw_plan_build_test_iso.py\n\nGenerate test for uncovered code. The coverage must reach 100%."}`

## Chore Description
Generate comprehensive unit tests for the `adw_plan_build_test_iso.py` script to achieve 100% code coverage. This script is a compositional workflow orchestrator that runs three ADW workflows in sequence: planning (`adw_plan_iso.py`), building (`adw_build_iso.py`), and testing (`adw_test_iso.py`). The tests need to verify all code paths including:

1. **Command-line argument handling** - Valid and invalid usage patterns
2. **Main workflow orchestration** - Sequential execution of plan → build → test
3. **ADW ID extraction logic** - Finding ADW ID from state files after planning step
4. **Error handling** - Handling failures at each workflow step
5. **Subprocess execution** - Mocking and verifying subprocess calls
6. **Exit code handling** - Success and failure scenarios

The tests must follow the existing project testing patterns and use pytest with appropriate mocking strategies.

## Relevant Files
Use these files to resolve the chore:

- **`adws/adw_plan_build_test_iso.py`** (Target file for testing - located in parent repository)
  - Main entry point that orchestrates plan → build → test workflow
  - Contains `main()` function with workflow orchestration logic
  - Handles command-line arguments parsing
  - Extracts ADW ID from state files if not provided
  - Executes subprocess calls to run individual workflow scripts

- **`tests/conftest.py`** (Test fixtures and configuration)
  - Contains shared pytest fixtures for unit tests
  - Provides mock objects and test environment setup
  - Pattern reference for creating test fixtures

- **`tests/test_factory.py`** (Testing pattern reference)
  - Demonstrates the project's testing style and conventions
  - Shows how to use unittest.mock for patching
  - Examples of test class organization and naming

- **`pyproject.toml`** (Project configuration)
  - Pytest configuration settings
  - Test path configuration (testpaths = ["tests"])
  - Coverage configuration for validation

- **`adws/README.md`** (ADW system documentation - located in parent repository)
  - Understanding ADW workflow dependencies and execution patterns
  - Context about state management and ADW ID generation
  - Information about workflow composition

- **`adws/adw_modules/state.py`** (State management module - located in parent repository)
  - Understanding ADWState class structure
  - How state files are structured (JSON format)
  - Location of state files: `agents/{adw_id}/adw_state.json`

### New Files

- **`tests/adws/test_adw_plan_build_test_iso.py`** (New test file)
  - Comprehensive unit tests for `adw_plan_build_test_iso.py`
  - Test all functions and code paths
  - Mock subprocess calls and file system operations
  - Achieve 100% code coverage

- **`tests/adws/__init__.py`** (Package initializer)
  - Empty init file to make `tests/adws/` a Python package
  - Required for pytest discovery

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create test directory structure
- Create `tests/adws/` directory if it doesn't exist
- Create `tests/adws/__init__.py` empty file to make it a package
- This follows the mirror structure pattern: `adws/` → `tests/adws/`

### 2. Analyze the target file thoroughly
- Read `/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py` completely to understand all code paths
- Identify all testable functions and code branches:
  - `main()` function with multiple execution paths
  - Command-line argument validation (missing args, valid args, optional ADW ID)
  - Step 1 execution (planning) with subprocess call
  - ADW ID extraction logic (searching state files, sorting by modification time)
  - Step 2 execution (building) with subprocess call
  - Step 3 execution (testing) with subprocess call and non-zero exit code handling
  - Error handling for each step (returncode != 0)
- Document edge cases and error scenarios that need testing
- Calculate the number of test cases needed to cover all branches

### 3. Design comprehensive test cases
- **Test command-line argument parsing:**
  - Missing required argument (issue number) → should exit with code 1
  - Valid issue number only → should proceed with ADW ID extraction
  - Valid issue number + ADW ID → should skip ADW ID extraction
  - Extra arguments → should be ignored (only first 2 used)

- **Test Step 1 (Planning) execution:**
  - Successful planning (returncode 0) → should continue to ADW ID extraction
  - Failed planning (returncode != 0) → should exit with code 1
  - Correct subprocess command construction with/without ADW ID
  - Verify print statements for step header

- **Test ADW ID extraction logic:**
  - ADW ID provided via CLI → should skip extraction
  - ADW ID not provided, found in state file → should extract successfully
  - ADW ID not provided, state file not found → should exit with code 1
  - Multiple state files exist → should use most recent one
  - State file with matching issue number → should extract ADW ID
  - State file with non-matching issue number → should skip and continue searching
  - Malformed JSON in state file → should handle gracefully and continue
  - Empty agents directory → should fail gracefully

- **Test Step 2 (Building) execution:**
  - Successful building (returncode 0) → should continue to Step 3
  - Failed building (returncode != 0) → should exit with code 1
  - Correct subprocess command construction with issue number and ADW ID
  - Verify print statements for step header

- **Test Step 3 (Testing) execution:**
  - Successful testing (returncode 0) → should print success message
  - Failed testing (returncode != 0) → should print warning (not error)
  - Correct subprocess command construction with issue number and ADW ID
  - Verify print statements for step header
  - Note: Testing step does NOT exit with error on failure (different from Steps 1 & 2)

- **Test environment and file system mocking:**
  - Mock `os.path.exists()` for agents directory
  - Mock `os.listdir()` for listing agent directories
  - Mock `os.path.getmtime()` for file modification times
  - Mock `open()` for reading state files
  - Mock `json.load()` for parsing state files
  - Mock `subprocess.run()` for all workflow script executions
  - Mock `sys.argv` for command-line argument testing
  - Mock `sys.exit()` to verify exit codes without actually exiting
  - Mock `print()` to verify output messages (optional but recommended)
  - Mock `load_dotenv()` to avoid loading environment variables during tests

### 4. Create the test file with comprehensive coverage
- Create `tests/adws/test_adw_plan_build_test_iso.py`
- Import required modules: pytest, unittest.mock, subprocess, sys, os, json
- Import the target script as a module using importlib or sys.path manipulation
- Structure tests using pytest test classes for organization:
  - `TestCommandLineArguments` - Test argument parsing and validation
  - `TestMainWorkflow` - Test complete workflow execution paths
  - `TestADWIDExtraction` - Test ADW ID extraction logic
  - `TestStepExecution` - Test individual step executions and error handling
- Each test should:
  - Have a clear, descriptive name explaining what it tests
  - Use appropriate mocking to isolate the code under test
  - Assert expected behavior (subprocess calls, exit codes, print statements)
  - Follow the pattern from `tests/test_factory.py` for consistency
- Use `@patch` decorators to mock external dependencies:
  - `@patch('sys.argv')` for CLI argument mocking
  - `@patch('sys.exit')` for exit code verification
  - `@patch('subprocess.run')` for subprocess execution
  - `@patch('os.path.exists')` for file system checks
  - `@patch('os.listdir')` for directory listing
  - `@patch('os.path.getmtime')` for file modification time
  - `@patch('builtins.open')` for file reading
  - `@patch('json.load')` for JSON parsing
  - `@patch('builtins.print')` for output verification
  - `@patch('dotenv.load_dotenv')` for environment loading
- Ensure all branches are covered:
  - All if/else conditions
  - All try/except blocks
  - All error handling paths
  - Early returns and exits
- **Important**: The target script is located in the parent repository at `/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py`, not in the worktree. You'll need to set up proper imports to test this file.

### 5. Implement mock fixtures and test helpers
- Create reusable mock fixtures for common test scenarios:
  - `mock_subprocess_success` - Mock successful subprocess.run() with returncode 0
  - `mock_subprocess_failure` - Mock failed subprocess.run() with returncode 1
  - `mock_state_file_exists` - Mock agents directory with valid state files
  - `mock_state_file_not_found` - Mock empty agents directory
  - `mock_state_json` - Mock state JSON data with issue_number and ADW ID
- Use pytest fixtures where appropriate to reduce code duplication
- Follow the pattern from `tests/conftest.py` for fixture structure

### 6. Run tests and verify 100% coverage
- Execute: `pytest tests/adws/test_adw_plan_build_test_iso.py -v`
- Verify all tests pass with no errors
- Generate coverage report: `pytest tests/adws/test_adw_plan_build_test_iso.py --cov=/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py --cov-report=term-missing`
- Review coverage report to identify any uncovered lines
- If coverage < 100%, add additional test cases for uncovered branches
- Iterate until 100% coverage is achieved

### 7. Run validation commands
- Execute all validation commands to ensure 100% confidence that the chore is complete
- Verify zero regressions in the existing test suite
- Confirm the new tests integrate properly with the project

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `pytest tests/adws/test_adw_plan_build_test_iso.py -v` - Run new tests to verify all pass
- `pytest tests/adws/test_adw_plan_build_test_iso.py --cov=/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py --cov-report=term-missing` - Verify 100% coverage for target file
- `pytest tests/ -v` - Run all tests to validate zero regressions

## Notes
- The target file `adw_plan_build_test_iso.py` is located in the parent repository (`/Users/Bek/Downloads/rococo-sample-backend/adws/`), not in the worktree
- The worktree only contains the application code (`common/`, `flask/`, `tests/`, etc.), not the ADW scripts
- The script is a single-file Python script with shebang and inline dependencies
- The script uses subprocess to execute other Python scripts, so mocking subprocess.run() is critical
- The ADW ID extraction logic involves file system operations (reading JSON files, checking directories), requiring careful mocking
- The script has different error handling for Step 3 (testing) - it prints a warning but doesn't exit with error code
- State files are located at `agents/{adw_id}/adw_state.json` and contain JSON with `issue_number` field
- The script sorts state files by modification time (newest first) when searching for ADW ID
- SCRIPT_DIR constant is set using `os.path.dirname(os.path.abspath(__file__))` and used to construct paths to other scripts
- The script calls `load_dotenv()` at the start of main() - this should be mocked in tests
- All subprocess commands use `sys.executable` to invoke Python, ensuring compatibility with different Python environments
- The script expects specific exit codes: 0 for success, non-zero for failure (except Step 3)
- When importing the target script in tests, you'll need to add the parent repository's adws directory to the Python path or use importlib
