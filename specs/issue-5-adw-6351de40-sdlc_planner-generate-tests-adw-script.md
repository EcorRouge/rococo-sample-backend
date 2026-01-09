# Chore: Generate tests for adw_plan_build_test_iso.py

## Metadata
issue_number: `5`
adw_id: `6351de40`
issue_json: `{"number": 5, "title": "Generate tests", "body": "adw_plan_build_test_iso.py\n\nGenerate test for uncovered code. The coverage must reach 100%."}`

## Chore Description
Generate comprehensive unit tests for the `adw_plan_build_test_iso.py` script to achieve 100% code coverage. This script orchestrates the ADW (AI Developer Workflow) by sequentially executing three main steps:
1. Planning (via `adw_plan_iso.py`)
2. Building (via `adw_build_iso.py`)
3. Testing (via `adw_test_iso.py`)

The script handles subprocess execution, ADW ID detection from state files, error handling, and provides user-friendly console output. Tests must cover all execution paths including success scenarios, failure scenarios, and edge cases such as missing ADW IDs and invalid arguments.

## Relevant Files
Use these files to resolve the chore:

- **adws/adw_plan_build_test_iso.py** (lines 1-113) - The main script file that needs test coverage. Contains the `main()` function and subprocess orchestration logic that must be fully tested.
- **adws/adw_tests/test_agents.py** (lines 1-105) - Existing test file demonstrating the ADW testing patterns, fixture usage, and test structure. Use this as a reference for writing similar tests.
- **adws/adw_tests/__init__.py** - Test package initialization file to ensure proper test discovery.
- **adws/pyproject.toml** (lines 1-21) - Project configuration with dependencies including pytest. Defines the project structure and test requirements.
- **adws/adw_modules/state.py** - Contains `ADWState` class referenced in the script for state file operations and ADW ID management.
- **adws/adw_modules/utils.py** - Contains utility functions like `make_adw_id()` that may be needed for test fixtures.
- **adws/adw_modules/data_types.py** - Contains data type definitions used throughout the ADW system that may be needed in tests.

### New Files
- **adws/adw_tests/test_adw_plan_build_test_iso.py** - New comprehensive test file for `adw_plan_build_test_iso.py` with 100% coverage including all edge cases and error paths.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Read and analyze the target script
- Read `/Users/Bek/Downloads/rococo-sample-backend/adws/adw_plan_build_test_iso.py` to understand all functions, branches, and edge cases
- Identify all code paths that need test coverage:
  - Main entry point with valid arguments
  - Missing issue number argument (sys.exit(1) path)
  - ADW ID provided vs. auto-detected scenarios
  - Planning step success and failure paths
  - Building step success and failure paths
  - Testing step success and failure paths
  - ADW ID detection from state files (success and failure)
  - File I/O operations and JSON parsing edge cases

### 2. Read supporting modules for test context
- Read `adws/adw_modules/state.py` to understand `ADWState` class structure
- Read `adws/adw_modules/utils.py` to understand `make_adw_id()` and other utilities
- Review `adws/adw_tests/test_agents.py` to understand existing test patterns and conventions

### 3. Create comprehensive test file
- Create `adws/adw_tests/test_adw_plan_build_test_iso.py` with the following test cases:
  - `test_main_missing_issue_number()` - Test sys.exit(1) when no issue number provided
  - `test_main_with_adw_id_provided()` - Test successful execution when ADW ID is provided as argument
  - `test_main_without_adw_id_auto_detect_success()` - Test auto-detection of ADW ID from state files after planning step
  - `test_main_without_adw_id_auto_detect_failure()` - Test failure when ADW ID cannot be found in state files
  - `test_planning_step_failure()` - Test early exit when planning step fails (returncode != 0)
  - `test_building_step_failure()` - Test early exit when building step fails after successful planning
  - `test_testing_step_failure()` - Test handling of test failures (returncode != 0) with warning message
  - `test_all_steps_successful()` - Test complete successful workflow through all three steps
  - `test_state_file_json_decode_error()` - Test handling of corrupted JSON in state files
  - `test_state_file_missing_issue_number()` - Test handling of state files without issue_number field
  - `test_state_file_io_error()` - Test handling of file read errors during state file processing
  - `test_agents_directory_not_exists()` - Test handling when agents directory doesn't exist
  - `test_multiple_state_files_newest_first()` - Test that the most recently modified state file is checked first
- Use `unittest.mock` for mocking:
  - `sys.argv` for command-line arguments
  - `subprocess.run` for subprocess execution
  - `os.path.exists`, `os.listdir`, `os.path.getmtime` for file system operations
  - `open` and `json.load` for state file reading
- Use `pytest.MonkeyPatch` or `unittest.mock.patch` for environment isolation
- Include proper docstrings for each test explaining what is being tested
- Follow existing test patterns from `test_agents.py`

### 4. Run tests and verify 100% coverage
- Execute `pytest adws/adw_tests/test_adw_plan_build_test_iso.py -v` to verify all tests pass
- Execute `pytest adws/adw_tests/test_adw_plan_build_test_iso.py --cov=adws/adw_plan_build_test_iso --cov-report=term-missing` to verify 100% coverage
- Review coverage report to ensure no lines are missed
- If coverage is less than 100%, identify uncovered lines and add additional test cases

### 5. Validate with comprehensive test suite
- Run `pytest adws/adw_tests/ -v` to ensure new tests don't break existing tests
- Verify all tests pass with zero failures
- Check that test output is clear and descriptive

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd /Users/Bek/Downloads/rococo-sample-backend/adws && uv run pytest adw_tests/test_adw_plan_build_test_iso.py -v` - Run new tests to ensure they all pass
- `cd /Users/Bek/Downloads/rococo-sample-backend/adws && uv run pytest adw_tests/test_adw_plan_build_test_iso.py --cov=adw_plan_build_test_iso --cov-report=term-missing --cov-report=html` - Verify 100% coverage for the target script
- `cd /Users/Bek/Downloads/rococo-sample-backend/adws && uv run pytest adw_tests/ -v` - Run all ADW tests to ensure no regressions

## Notes
- The script uses `sys.executable` to ensure subprocess calls use the same Python interpreter as the parent process
- The ADW ID auto-detection logic searches for the most recent state file matching the issue number, so tests must verify sorting by modification time
- The testing step (Step 3) allows non-zero exit codes with a warning message, unlike Steps 1 and 2 which cause immediate exit on failure
- State files are located in `agents/<adw_id>/adw_state.json` relative to the project root (parent of SCRIPT_DIR)
- Use `SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))` pattern consistently in tests to match the script's approach
- Mock `subprocess.run` to avoid actually executing the ADW workflow scripts during tests
- Ensure tests are isolated and don't depend on actual file system state
