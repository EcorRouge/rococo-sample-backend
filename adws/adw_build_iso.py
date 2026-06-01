#!/usr/bin/env python3
"""
ADW Build Iso - AI Developer Workflow for agentic building in isolated worktrees

Usage: 
  uv run adws/adw_build_iso.py <issue-number> <adw-id>
  # or: python3 adws/adw_build_iso.py <issue-number> <adw-id>  # with venv activated

Workflow:
1. Load state and validate worktree exists
2. Find existing plan (from state)
3. Implement the solution based on plan in worktree
4. Commit implementation in worktree
5. Push and update PR

Dependencies:
This workflow REQUIRES:
- adw_plan_iso.py to be run first to create the worktree, state, and plan
- The worktree must exist at trees/<adw-id>/
- State file must exist at agents/<adw-id>/adw_state.json
- Plan file must exist (specified in state.plan_file)

Alternative Usage:
For a complete workflow that handles dependencies automatically:
  uv run adws/adw_plan_build_iso.py <issue-number>
This will run planning and building in sequence.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations, get_current_branch
from adw_modules.github import fetch_issue, make_issue_comment, get_repo_url, extract_repo_path
from adw_modules.workflow_ops import (
    implement_plan,
    create_commit,
    format_issue_message,
    AGENT_IMPLEMENTOR,
)
from adw_modules.utils import setup_logger
from adw_modules.data_types import GitHubIssue
from adw_modules.worktree_ops import validate_worktree
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
    
    if len(sys.argv) < 3:
        print("Usage: python adw_build_iso.py <issue-number> <adw-id>")
        print("\nError: adw-id is required to locate the worktree and plan file")
        print("Run adw_plan_iso.py first to create the worktree")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    temp_logger = setup_logger(adw_id, "adw_build_iso")
    state = ADWState.load(adw_id, temp_logger)
    if state:
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🔍 Found existing state - resuming isolated build\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )
    else:
        logger = setup_logger(adw_id, "adw_build_iso")
        raise ADWError(
            message=f"No state found for ADW ID: {adw_id}. Run adw_plan_iso.py first to create the worktree and state",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name="ops",
        )
    
    state.append_adw_id("adw_build_iso")
    
    logger = setup_logger(adw_id, "adw_build_iso")
    logger.info(f"ADW Build Iso starting - ID: {adw_id}, Issue: {issue_number}")
    
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
            message=f"Worktree validation failed: {error}. Run adw_plan_iso.py first",
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
    
    # Validate required state fields
    if not state.get("branch_name"):
        raise ADWError(
            message="No branch name in state - run adw_plan_iso.py first",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name="ops",
        )
    
    if not state.get("plan_file"):
        raise ADWError(
            message="No plan file in state - run adw_plan_iso.py first",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name="ops",
        )
    
    # Checkout branch
    branch_name = state.get("branch_name")
    result = safe_execute(
        lambda: subprocess.run(
            ["git", "checkout", branch_name],
            capture_output=True,
            text=True,
            check=True,
            cwd=worktree_path,
        ),
        logger,
        f"Failed to checkout branch {branch_name} in worktree",
        issue_number,
        adw_id,
        "ops",
        "Checking out branch",
    )
    logger.info(f"Checked out branch in worktree: {branch_name}")
    
    plan_file = state.get("plan_file")
    logger.info(f"Using plan file: {plan_file}")
    
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "🔨 Starting implementation...")
    )
    
    # Implement plan
    implement_response = safe_execute(
        lambda: implement_plan(plan_file, adw_id, logger, working_dir=worktree_path),
        logger,
        "Failed to implement plan",
        issue_number,
        adw_id,
        AGENT_IMPLEMENTOR,
        "Implementing plan",
    )
    
    if not implement_response or not implement_response.success:
        error_msg = implement_response.output if implement_response else "Unknown error"
        raise ADWError(
            message=f"Implementation failed: {error_msg[:500]}",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_IMPLEMENTOR,
        )
    
    logger.info("Implementation completed successfully")
    
    try:
        issue = safe_execute(
            lambda: fetch_issue(issue_number, repo_path),
            logger,
            "Failed to fetch issue for commit",
            issue_number,
            adw_id,
            "ops",
            "Fetching issue for commit",
            reraise=True,
        )
        issue_class = state.get("issue_class")
        
        commit_message, error = create_commit(
            AGENT_IMPLEMENTOR, issue, issue_class, adw_id, logger, worktree_path
        )
        if error:
            logger.warning(f"Failed to create commit message: {error}")
        else:
            success, error = commit_changes(commit_message, cwd=worktree_path)
            if not success:
                logger.warning(f"Failed to commit: {error}")
    except Exception as e:
        logger.warning(f"Could not create commit: {e}")
    
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementation complete!")
    )
    
    logger.info("ADW Build Iso completed successfully")


if __name__ == "__main__":
    try:
        main()
    except ADWError as e:
        sys.exit(e.exit_code)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

