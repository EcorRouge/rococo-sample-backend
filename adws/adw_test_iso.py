#!/usr/bin/env python3
"""
ADW Test Iso - AI Developer Workflow for agentic testing in isolated worktrees

Usage:
  uv run adws/adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]
  # or: python3 adws/adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]  # with venv activated

Workflow:
1. Load state and validate worktree exists
2. Run pytest test suite in worktree
3. Generate tests for uncovered code (using SonarQube coverage if available)
4. Auto-resolve test failures
5. Report results to issue
6. Commit test results in worktree
7. Push and update PR

Dependencies:
This workflow REQUIRES:
- adw_plan_iso.py (or adw_patch_iso.py) to be run first to create the worktree and state
- The worktree must exist at trees/<adw-id>/
- State file must exist at agents/<adw-id>/adw_state.json

Alternative Usage:
For a complete workflow that handles dependencies automatically:
  uv run adws/adw_plan_build_test_iso.py <issue-number>
This will run planning, building, and testing in sequence.
"""

import json
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional, List
from dotenv import load_dotenv
from adw_modules.data_types import (
    AgentTemplateRequest,
    AgentPromptResponse,
    TestResult,
)
from adw_modules.agent import execute_template
from adw_modules.github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    get_repo_url,
)
from adw_modules.utils import setup_logger, parse_json
from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.workflow_ops import (
    format_issue_message,
    create_commit,
)
from adw_modules.worktree_ops import validate_worktree
from adw_modules.sonarqube import SonarQubeClient
from adw_modules.error_handling import (
    handle_error,
    safe_execute,
    validate_tuple_result,
    ADWError,
    ErrorSeverity,
)
from adw_modules.preflight import run_preflight_checks

AGENT_TESTER = "test_runner"
MAX_TEST_RETRY_ATTEMPTS = 4
MAX_TEST_GENERATION_ITERATIONS = 1  # Limit iterations to prevent infinite loops


def run_tests(
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    coverage_data: Optional[str] = None,
) -> AgentPromptResponse:
    """Run the test suite using the /test command.
    
    Args:
        adw_id: ADW ID
        logger: Logger instance
        working_dir: Working directory for execution
        coverage_data: Optional SonarQube coverage data to pass to the command
    """
    args = []
    if coverage_data:
        args = [coverage_data]
    
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"test_template_request: {json.dumps(test_template_request.as_dict(), indent=2)}"
    )

    test_response = execute_template(test_template_request)

    logger.debug(
        f"test_response: {json.dumps(test_response.as_dict(), indent=2)}"
    )

    return test_response


def run_pytest(working_dir: str, logger: logging.Logger) -> Tuple[bool, str, str]:
    """Run pytest and return (success, stdout, stderr).
    
    Uses sys.executable -m pytest to ensure pytest runs with the same Python
    interpreter that's running this script, avoiding PATH issues.
    """
    try:
        # Use sys.executable -m pytest for reliability
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error running pytest: {e}")
        return False, "", str(e)


def parse_test_results(
    output: str, logger: logging.Logger
) -> Tuple[List[TestResult], int, int]:
    """Parse test results JSON and return (results, passed_count, failed_count).
    
    Handles cases where the output may contain markdown text before/after the JSON.
    """
    try:
        import re
        json_str = None
        
        # Strategy 1: Try to find JSON array in markdown code blocks (with flexible whitespace)
        json_match = re.search(r'```(?:json)?\s*\n(\[.*?\])\n```', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Strategy 2: Find the first [ and its matching ] bracket
            # Look for the first [ and matching ]
            bracket_start = output.find('[')
            if bracket_start != -1:
                # Find the matching closing bracket
                bracket_count = 0
                bracket_end = bracket_start
                for i in range(bracket_start, len(output)):
                    if output[i] == '[':
                        bracket_count += 1
                    elif output[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            bracket_end = i
                            break
                if bracket_end > bracket_start:
                    json_str = output[bracket_start:bracket_end + 1]
        
        # Strategy 3: If still no JSON found, try parse_json which has its own extraction logic
        if not json_str:
            json_str = output
        
        # Parse JSON - may return list of dicts or list of TestResult objects
        parsed = parse_json(json_str, List[TestResult])
        
        # Convert dicts to TestResult objects if needed
        results = []
        for item in parsed:
            if isinstance(item, dict):
                # Convert dict to TestResult
                try:
                    result = TestResult.from_dict(item)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to convert dict to TestResult: {e}, dict: {item}")
                    # Try to create TestResult manually
                    try:
                        result = TestResult(
                            test_name=item.get("test_name", "unknown"),
                            passed=bool(item.get("passed", False)),
                            execution_command=item.get("execution_command", ""),
                            test_purpose=item.get("test_purpose", ""),
                            error=item.get("error"),
                        )
                        results.append(result)
                    except Exception as e2:
                        logger.error(f"Failed to create TestResult from dict: {e2}")
            elif isinstance(item, TestResult):
                results.append(item)
            else:
                logger.warning(f"Unexpected item type in results: {type(item)}")
        
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count
        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing test results: {e}")
        logger.debug(f"Output that failed to parse: {output[:500]}")
        return [], 0, 0


def format_test_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format test results for GitHub issue comment."""
    if not results:
        return "❌ No test results found"

    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    comment_parts = []

    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed Tests")
        comment_parts.append("")

        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.as_dict(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    if passed_tests:
        comment_parts.append("## ✅ Passed Tests")
        comment_parts.append("")
        comment_parts.append(f"Total: {len(passed_tests)} tests passed")

    comment_parts.append("")
    comment_parts.append("## Summary")
    comment_parts.append(f"- **Passed**: {passed_count}")
    comment_parts.append(f"- **Failed**: {failed_count}")
    comment_parts.append(f"- **Total**: {len(results)}")

    return "\n".join(comment_parts)


def resolve_failed_tests(
    failed_tests: List[TestResult],
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Attempt to resolve failed tests using /resolve_failed_test command."""
    if not failed_tests:
        return AgentPromptResponse(output="No failed tests to resolve", success=True)

    failed_test_info = json.dumps([test.as_dict() for test in failed_tests], indent=2)

    request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/resolve_failed_test",
        args=[failed_test_info],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.info(f"Attempting to resolve {len(failed_tests)} failed test(s)")

    response = execute_template(request)

    return response


def main():
    """Main entry point."""
    load_dotenv()

    skip_e2e = "--skip-e2e" in sys.argv
    args = [arg for arg in sys.argv if arg != "--skip-e2e"]

    if len(args) < 3:
        print("Usage: python adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]")
        sys.exit(1)

    issue_number = args[1]
    adw_id = args[2]

    temp_logger = setup_logger(adw_id, "adw_test_iso")
    state = ADWState.load(adw_id, temp_logger)
    if not state:
        logger = setup_logger(adw_id, "adw_test_iso")
        error_msg = (
            f"No state found for ADW ID: {adw_id}.\n\n"
            f"**This workflow requires a previous workflow to create the worktree:**\n"
            f"1. Run `adw_plan_iso.py` (or `adw_patch_iso.py`) first to create the worktree and state\n"
            f"   Example: uv run adws/adw_plan_iso.py {issue_number}\n\n"
            f"2. Then use the ADW ID returned from step 1 to run this workflow\n"
            f"   Example: uv run adws/adw_test_iso.py {issue_number} <adw-id>\n\n"
            f"**Alternative: Use the combined workflow that handles dependencies automatically:**\n"
            f"   uv run adws/adw_plan_build_test_iso.py {issue_number}\n"
            f"   This will run planning, building, and testing in sequence."
        )
        raise ADWError(
            message=error_msg,
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name="ops",
        )

    state.append_adw_id("adw_test_iso")

    logger = setup_logger(adw_id, "adw_test_iso")
    logger.info(f"ADW Test Iso starting - ID: {adw_id}, Issue: {issue_number}")

    # Run pre-flight validation checks
    try:
        run_preflight_checks(
            logger,
            issue_number=issue_number,
            adw_id=adw_id,
            checks=["env_vars", "git_repo", "git_remote"],
        )
    except ADWError as e:
        handle_error(e, logger, issue_number, adw_id, "ops", "Pre-flight validation")

    # Validate worktree
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        raise ADWError(
            message=f"Worktree validation failed: {error}",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name="ops",
        )

    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")

    # Get repository URL and path
    github_repo_url = safe_execute(
        lambda: get_repo_url(),
        logger,
        "Failed to get repository URL",
        issue_number,
        adw_id,
        "ops",
        "Getting repository URL",
    )
    
    repo_path = safe_execute(
        lambda: extract_repo_path(github_repo_url),
        logger,
        "Failed to extract repository path",
        issue_number,
        adw_id,
        "ops",
        "Extracting repository path",
    )

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "🧪 Starting test execution...")
    )

    # Fetch SonarQube coverage data FIRST - REQUIRED for test generation
    coverage_data = None
    try:
        sonar_client = SonarQubeClient()
        logger.info("Fetching SonarQube coverage data (REQUIRED for test generation)...")
        coverage_summary = sonar_client.get_uncovered_files_summary()
        if not coverage_summary:
            error_msg = "Could not fetch SonarQube coverage data. Test generation requires SonarQube coverage data."
            logger.error(error_msg)
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_TESTER, f"❌ {error_msg}")
            )
            raise ADWError(
                message=error_msg,
                issue_number=issue_number,
                adw_id=adw_id,
                agent_name=AGENT_TESTER,
            )
        
        # ONLY include flask/ and common/ directories, exclude everything else
        import json as json_lib
        coverage_dict = json_lib.loads(coverage_summary)
        filtered_files = [
            f for f in coverage_dict.get('files', [])
            if (f['path'].startswith('flask/') or f['path'].startswith('common/'))
            and not f['path'].startswith('adws/')
            and not f['path'].startswith('tests/')
        ]
        
        if not filtered_files:
            logger.warning("No uncovered files found in flask/ or common/ directories")
            # Create empty coverage data structure to prevent codebase scanning
            coverage_dict['files'] = []
            coverage_dict['total_uncovered_files'] = 0
            coverage_data = json_lib.dumps(coverage_dict, indent=2)
        else:
            coverage_dict['files'] = filtered_files
            coverage_dict['total_uncovered_files'] = len(filtered_files)
            coverage_data = json_lib.dumps(coverage_dict, indent=2)
            logger.info(f"Filtered to {len(filtered_files)} uncovered files in flask/ and common/ (excluded adws/ and tests/)")
        
        # Log summary
        metrics = sonar_client.get_project_metrics()
        if metrics:
            logger.info(
                f"Overall coverage: {metrics.coverage:.2f}%, "
                f"Uncovered lines: {metrics.uncovered_lines}"
            )
    except ADWError:
        raise  # Re-raise ADWError
    except Exception as e:
        error_msg = f"SonarQube integration not available: {e}. Test generation requires SonarQube coverage data."
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, f"❌ {error_msg}")
        )
        raise ADWError(
            message=error_msg,
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_TESTER,
        ) from e
    
    # Verify we have coverage_data before proceeding
    if not coverage_data:
        error_msg = "No coverage data available. Test generation requires SonarQube coverage data."
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, f"❌ {error_msg}")
        )
        raise ADWError(
            message=error_msg,
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_TESTER,
        )

    # Run pytest first to get baseline
    logger.info("Running pytest test suite...")
    pytest_success, pytest_stdout, pytest_stderr = run_pytest(worktree_path, logger)
    
    # Parse pytest output to get actual test count
    pytest_test_count = 0
    if pytest_stdout:
        # Extract test count from pytest output (e.g., "8 passed" or "8 passed, 2 failed")
        import re
        match = re.search(r'(\d+)\s+passed', pytest_stdout)
        if match:
            pytest_test_count = int(match.group(1))
        logger.info(f"Pytest found {pytest_test_count} passing tests")

    # Run ADW test command to generate tests for uncovered code
    # Limit iterations to prevent infinite loops when trying to reach 100% coverage
    all_results = []
    total_passed = 0
    total_failed = 0
    test_generation_success = False
    
    for iteration in range(MAX_TEST_GENERATION_ITERATIONS):
        logger.info(f"Running ADW test generation (iteration {iteration + 1}/{MAX_TEST_GENERATION_ITERATIONS})...")
        test_response = run_tests(adw_id, logger, working_dir=worktree_path, coverage_data=coverage_data)

        if not test_response.success:
            logger.error(f"Test generation failed: {test_response.output}")
            if iteration == 0:  # Only report failure on first iteration
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, AGENT_TESTER, f"❌ Test generation failed: {test_response.output[:500]}")
                )
            break

        test_generation_success = True
        results, passed_count, failed_count = parse_test_results(test_response.output, logger)
        all_results.extend(results)
        total_passed += passed_count
        total_failed += failed_count

        if failed_count > 0:
            failed_tests = [test for test in results if not test.passed]
            
            # Attempt to resolve failures
            for attempt in range(MAX_TEST_RETRY_ATTEMPTS):
                logger.info(f"Attempting to resolve test failures (attempt {attempt + 1}/{MAX_TEST_RETRY_ATTEMPTS})")
                resolve_response = resolve_failed_tests(failed_tests, adw_id, logger, working_dir=worktree_path)
                
                if resolve_response.success:
                    # Re-run tests to verify fixes
                    test_response = run_tests(adw_id, logger, working_dir=worktree_path, coverage_data=coverage_data)
                    if test_response.success:
                        results, passed_count, failed_count = parse_test_results(test_response.output, logger)
                        # Update accumulated counts
                        all_results.extend(results)
                        total_passed += passed_count
                        total_failed += failed_count
                        if failed_count == 0:
                            logger.info("All tests resolved successfully!")
                            break
                        failed_tests = [test for test in results if not test.passed]
        
        # If no failures and we have results, we can stop
        if failed_count == 0 and len(results) > 0:
            logger.info(f"Test generation completed successfully after {iteration + 1} iteration(s)")
            break
    
    # Re-run pytest to get final test count after all test generation
    logger.info("Running final pytest to get complete test results...")
    final_pytest_success, final_pytest_stdout, final_pytest_stderr = run_pytest(worktree_path, logger)
    
    # Parse final pytest output for accurate reporting
    final_test_count = 0
    final_passed = 0
    final_failed = 0
    if final_pytest_stdout:
        import re
        # Match patterns like "150 passed" or "145 passed, 5 failed"
        passed_match = re.search(r'(\d+)\s+passed', final_pytest_stdout)
        failed_match = re.search(r'(\d+)\s+failed', final_pytest_stdout)
        if passed_match:
            final_passed = int(passed_match.group(1))
        if failed_match:
            final_failed = int(failed_match.group(1))
        final_test_count = final_passed + final_failed
        logger.info(f"Final pytest results: {final_passed} passed, {final_failed} failed, {final_test_count} total")
    
    # Use pytest results if available, otherwise fall back to command results
    if final_test_count > 0:
        passed_count = final_passed
        failed_count = final_failed
        # Create a summary result instead of individual test results
        results = []  # Clear individual results, we'll use pytest summary
        comment = f"## ✅ Test Suite Results\n\n"
        comment += f"**Total Tests**: {final_test_count}\n"
        comment += f"**Passed**: {final_passed}\n"
        comment += f"**Failed**: {final_failed}\n\n"
        if final_pytest_stdout:
            # Extract summary from pytest output
            lines = final_pytest_stdout.split('\n')
            summary_lines = [line for line in lines if 'passed' in line.lower() or 'failed' in line.lower() or 'error' in line.lower() or 'warnings' in line.lower()]
            if summary_lines:
                comment += "**Test Summary:**\n```\n" + '\n'.join(summary_lines[-10:]) + "\n```"
        # Store final_test_count for commit message
        final_test_count_for_commit = final_test_count
    else:
        # Fall back to command results if pytest parsing failed
        results = all_results
        passed_count = total_passed
        failed_count = total_failed
        comment = format_test_results_comment(results, passed_count, failed_count)
        # Store count for commit message
        final_test_count_for_commit = len(results)
    
    if not test_generation_success:
        # Exit early if test generation failed
        finalize_git_operations(state, logger, cwd=worktree_path)
        logger.error("ADW Test Iso failed - test generation unsuccessful")
        sys.exit(1)

    # Format and post results
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, comment)
    )

    # Commit test results
    try:
        commit_message = f"test: Add/update tests (ADW {adw_id})\n\n- Passed: {passed_count}\n- Failed: {failed_count}\n- Total: {final_test_count_for_commit}"
        success, error = commit_changes(commit_message, cwd=worktree_path)
        if not success:
            logger.warning(f"Failed to commit test results: {error}")
    except Exception as e:
        logger.warning(f"Could not commit test results: {e}")

    finalize_git_operations(state, logger, cwd=worktree_path)

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "✅ Test execution complete!")
    )

    logger.info("ADW Test Iso completed successfully")


if __name__ == "__main__":
    try:
        main()
    except ADWError as e:
        # ADWError is already handled, just exit
        sys.exit(e.exit_code)
    except Exception as e:
        # Unexpected error - log and exit
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

