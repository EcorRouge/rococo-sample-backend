#!/usr/bin/env python3
"""
ADW Plan Iso - AI Developer Workflow for agentic planning in isolated worktrees

Usage:
  uv run adws/adw_plan_iso.py <issue-number> [adw-id]
  # or: python3 adws/adw_plan_iso.py <issue-number> [adw-id]  # with venv activated

Workflow:
1. Fetch GitHub issue details
2. Check/create worktree for isolated execution
3. Allocate unique ports for services
4. Setup worktree environment
5. Classify issue type (/chore, /bug, /feature)
6. Create feature branch in worktree
7. Generate implementation plan in worktree
8. Commit plan in worktree
9. Push and create/update PR
"""

import sys
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from adw_modules.workflow_ops import (
    classify_issue,
    build_plan,
    generate_branch_name,
    create_commit,
    format_issue_message,
    ensure_adw_id,
    AGENT_PLANNER,
)
from adw_modules.utils import setup_logger
from adw_modules.data_types import GitHubIssue
from adw_modules.worktree_ops import (
    create_worktree,
    validate_worktree,
    get_ports_for_adw,
    is_port_available,
    find_next_available_ports,
    setup_worktree_environment,
)
from adw_modules.error_handling import (
    handle_error,
    safe_execute,
    validate_tuple_result,
    ADWError,
    ErrorSeverity,
)
from adw_modules.preflight import run_preflight_checks


def main():
    """Main entry point."""
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: uv run adws/adw_plan_iso.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    temp_logger = setup_logger(adw_id or "temp", "adw_plan_iso") if adw_id else None
    adw_id = ensure_adw_id(issue_number, adw_id, temp_logger)

    state = ADWState.load(adw_id, temp_logger)

    if not state.get("adw_id"):
        state.update(adw_id=adw_id)
    
    state.append_adw_id("adw_plan_iso")

    logger = setup_logger(adw_id, "adw_plan_iso")
    logger.info(f"ADW Plan Iso starting - ID: {adw_id}, Issue: {issue_number}")

    # Run pre-flight validation checks
    try:
        run_preflight_checks(
            logger,
            issue_number=issue_number,
            adw_id=adw_id,
            checks=["env_vars", "git_repo", "git_remote", "disk_space", "worktree_directory"],
        )
    except ADWError as e:
        handle_error(e, logger, issue_number, adw_id, "ops", "Pre-flight validation")

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

    # Fetch issue
    issue = safe_execute(
        lambda: fetch_issue(issue_number, repo_path),
        logger,
        "Failed to fetch GitHub issue",
        issue_number,
        adw_id,
        "ops",
        "Fetching issue",
    )

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "🚀 Starting ADW planning workflow...")
    )

    state.update(issue_number=issue_number)
    state.save("adw_plan_iso")

    # Classify issue
    issue_command = validate_tuple_result(
        classify_issue(issue, adw_id, logger),
        "Failed to classify issue",
        logger,
            issue_number,
        adw_id,
        "ops",
        "Classifying issue",
        )

    state.update(issue_class=issue_command)
    logger.info(f"Issue classified as: {issue_command}")

    # Generate branch name
    branch_name = validate_tuple_result(
        generate_branch_name(issue, issue_command, adw_id, logger),
        "Failed to generate branch name",
        logger,
        issue_number,
        adw_id,
        "ops",
        "Generating branch name",
    )

    state.update(branch_name=branch_name)

    backend_port, _ = find_next_available_ports(adw_id)
    state.update(backend_port=backend_port)

    # Create worktree
    worktree_path = validate_tuple_result(
        create_worktree(adw_id, branch_name, logger),
        "Failed to create worktree",
        logger,
        issue_number,
        adw_id,
        "ops",
        "Creating worktree",
    )

    state.update(worktree_path=worktree_path)
    setup_worktree_environment(worktree_path, backend_port, logger)

    # Build plan
    plan_response = safe_execute(
        lambda: build_plan(issue, issue_command, adw_id, logger, worktree_path),
        logger,
        "Failed to build plan",
        issue_number,
        adw_id,
        AGENT_PLANNER,
        "Building plan",
    )

    if not plan_response or not plan_response.success:
        error_msg = plan_response.output if plan_response else "Unknown error"
        raise ADWError(
            message=f"Failed to build plan: {error_msg}",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_PLANNER,
        )

    plan_file = plan_response.output.strip()
    if not os.path.isabs(plan_file) and worktree_path:
        plan_file = os.path.join(worktree_path, plan_file)

    state.update(plan_file=plan_file)
    state.save("adw_plan_iso")

    # Create commit (non-critical, log but don't fail)
    commit_message, error = create_commit(
        AGENT_PLANNER, issue, issue_command, adw_id, logger, worktree_path
    )
    if error:
        logger.warning(f"Failed to create commit message: {error}")
    else:
        success, error = commit_changes(commit_message, cwd=worktree_path)
        if not success:
            logger.warning(f"Failed to commit: {error}")

    finalize_git_operations(state, logger, cwd=worktree_path)

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, f"✅ Planning complete! Plan file: {plan_file}")
    )

    logger.info("ADW Plan Iso completed successfully")


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

