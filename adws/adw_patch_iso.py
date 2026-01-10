#!/usr/bin/env python3
"""
ADW Patch Isolated - AI Developer Workflow for single-issue patches with worktree isolation

Usage:
  uv run adws/adw_patch_iso.py <issue-number> [adw-id]

Workflow:
1. Create/validate isolated worktree
2. Allocate dedicated ports (backend only)
3. Fetch GitHub issue details
4. Check for 'adw_patch' keyword in comments or issue body
5. Create patch plan based on content containing 'adw_patch'
6. Implement the patch plan
7. Commit changes
8. Push and create/update PR

This workflow requires 'adw_patch' keyword to be present either in:
- A comment on the issue (uses latest comment containing keyword)
- The issue body itself (uses issue title + body)

Key features:
- Runs in isolated git worktree under trees/<adw_id>/
- Uses dedicated ports to avoid conflicts
- Passes working_dir to all agent and git operations
- Enables parallel execution of multiple patches
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
    find_keyword_from_comment,
)
from adw_modules.workflow_ops import (
    create_commit,
    format_issue_message,
    ensure_adw_id,
    implement_plan,
    create_and_implement_patch,
    AGENT_IMPLEMENTOR,
)
from adw_modules.worktree_ops import (
    create_worktree,
    validate_worktree,
    get_ports_for_adw,
    is_port_available,
    find_next_available_ports,
    setup_worktree_environment,
)
from adw_modules.utils import setup_logger
from adw_modules.data_types import (
    GitHubIssue,
    AgentTemplateRequest,
    AgentPromptResponse,
)
from adw_modules.agent import execute_template
from adw_modules.error_handling import (
    handle_error,
    safe_execute,
    validate_tuple_result,
    ADWError,
    ErrorSeverity,
)
from adw_modules.preflight import run_preflight_checks

# Agent name constants
AGENT_PATCH_PLANNER = "patch_planner"
AGENT_PATCH_IMPLEMENTOR = "patch_implementor"


def get_patch_content(
    issue: GitHubIssue, issue_number: str, adw_id: str, logger: logging.Logger
) -> str:
    """Get patch content from either issue comments or body containing 'adw_patch'.

    Args:
        issue: The GitHub issue
        issue_number: Issue number for comments
        adw_id: ADW ID for formatting messages
        logger: Logger instance

    Returns:
        The patch content to use for creating the patch plan

    Raises:
        SystemExit: If 'adw_patch' keyword is not found
    """
    # First, check for the latest comment containing 'adw_patch'
    keyword_comment = find_keyword_from_comment("adw_patch", issue)

    if keyword_comment:
        # Use the comment body as the review change request
        logger.info(
            f"Found 'adw_patch' in comment, using comment body: {keyword_comment.body}"
        )
        review_change_request = keyword_comment.body
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_PATCH_PLANNER,
                f"✅ Creating patch plan from comment containing 'adw_patch':\n\n```\n{keyword_comment.body}\n```",
            ),
        )
        return review_change_request
    elif "adw_patch" in issue.body:
        # Use issue title and body as the review change request
        logger.info("Found 'adw_patch' in issue body, using issue title and body")
        review_change_request = f"Issue #{issue.number}: {issue.title}\n\n{issue.body}"
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_PATCH_PLANNER,
                "✅ Creating patch plan from issue containing 'adw_patch'",
            ),
        )
        return review_change_request
    else:
        # No 'adw_patch' keyword found, exit
        raise ADWError(
            message="No 'adw_patch' keyword found in issue body or comments. Add 'adw_patch' to trigger patch workflow.",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name="ops",
        )


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 2:
        print("Usage: uv run adws/adw_patch_iso.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(adw_id, "adw_patch_iso") if adw_id else None
    adw_id = ensure_adw_id(issue_number, adw_id, temp_logger)

    # Load the state that was created/found by ensure_adw_id
    state = ADWState.load(adw_id, temp_logger)

    # Ensure state has the adw_id field
    if not state.get("adw_id"):
        state.update(adw_id=adw_id)

    # Track that this ADW workflow has run
    state.append_adw_id("adw_patch_iso")

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_patch_iso")
    logger.info(f"ADW Patch Isolated starting - ID: {adw_id}, Issue: {issue_number}")

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

    # Get repo information
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

    # Fetch issue details
    issue = safe_execute(
        lambda: fetch_issue(issue_number, repo_path),
        logger,
        "Failed to fetch GitHub issue",
        issue_number,
        adw_id,
        "ops",
        "Fetching issue",
    )

    logger.debug(f"Fetched issue: {issue.model_dump_json(indent=2, by_alias=True)}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Starting isolated patch workflow"),
    )

    # Determine branch name without checking out in main repo
    # 1. Check if branch name is already in state
    branch_name = state.get("branch_name")

    if not branch_name:
        # 2. Look for existing branch without checking it out
        from adw_modules.workflow_ops import find_existing_branch_for_issue

        existing_branch = find_existing_branch_for_issue(issue_number, adw_id)

        if existing_branch:
            logger.info(f"Found existing branch: {existing_branch}")
            branch_name = existing_branch
        else:
            # 3. No existing branch, need to classify and generate name
            logger.info("No existing branch found, creating new one")

            # Classify the issue
            from adw_modules.workflow_ops import classify_issue

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

            # Generate branch name
            from adw_modules.workflow_ops import generate_branch_name

            branch_name = validate_tuple_result(
                generate_branch_name(issue, issue_command, adw_id, logger),
                "Error generating branch name",
                logger,
                issue_number,
                adw_id,
                "ops",
                "Generating branch name",
            )

    # Update state with branch name
    state.update(branch_name=branch_name)

    # Save state with branch name
    state.save("adw_patch_iso")
    logger.info(f"Working on branch: {branch_name}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Working on branch: {branch_name}"),
    )

    # Check if worktree already exists
    worktree_path = state.get("worktree_path")
    if worktree_path and os.path.exists(worktree_path):
        logger.info(f"Using existing worktree: {worktree_path}")
        backend_port = state.get("backend_port", 9100)
    else:
        # Create isolated worktree
        logger.info("Creating isolated worktree")
        worktree_path = validate_tuple_result(
            create_worktree(adw_id, branch_name, logger),
            "Error creating worktree",
            logger,
            issue_number,
            adw_id,
            "ops",
            "Creating worktree",
        )

        # Get deterministic ports for this ADW ID (backend only)
        backend_port, _ = get_ports_for_adw(adw_id)

        # Check if port is available, find alternative if not
        if not is_port_available(backend_port):
            logger.warning(
                f"Preferred port {backend_port} not available, finding alternative"
            )
            backend_port, _ = find_next_available_ports(adw_id)

        logger.info(f"Allocated backend port: {backend_port}")

        # Set up worktree environment (copy files, create .ports.env)
        setup_worktree_environment(worktree_path, backend_port, logger)

        # Update state with worktree info
        state.update(
            worktree_path=worktree_path,
            backend_port=backend_port,
        )
        state.save("adw_patch_iso")

    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            "ops",
            f"✅ Using isolated worktree\n"
            f"🏠 Path: {worktree_path}\n"
            f"🔌 Backend Port: {backend_port}",
        ),
    )

    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 🔍 Using state\n```json\n{json.dumps(state.data, indent=2)}\n```",
    )

    # Get patch content from issue or comments containing 'adw_patch'
    logger.info("Checking for 'adw_patch' keyword")
    review_change_request = get_patch_content(issue, issue_number, adw_id, logger)

    # Use the shared method to create and implement patch
    patch_file, implement_response = create_and_implement_patch(
        adw_id=adw_id,
        review_change_request=review_change_request,
        logger=logger,
        agent_name_planner=AGENT_PATCH_PLANNER,
        agent_name_implementor=AGENT_PATCH_IMPLEMENTOR,
        spec_path=None,  # No spec file for direct issue patches
        working_dir=worktree_path,  # Pass worktree path for isolated execution
    )

    if not patch_file:
        raise ADWError(
            message="Failed to create patch plan",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_PATCH_PLANNER,
        )

    state.update(patch_file=patch_file)
    state.save("adw_patch_iso")
    logger.info(f"Patch plan created: {patch_file}")
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, AGENT_PATCH_PLANNER, f"✅ Patch plan created: {patch_file}"
        ),
    )

    if not implement_response.success:
        raise ADWError(
            message=f"Error implementing patch: {implement_response.output}",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=AGENT_PATCH_IMPLEMENTOR,
        )

    logger.debug(f"Implementation response: {implement_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PATCH_IMPLEMENTOR, "✅ Patch implemented"),
    )

    # Create commit message
    logger.info("Creating patch commit")

    issue_command = "/patch"
    commit_msg, error = create_commit(
        AGENT_PATCH_IMPLEMENTOR, issue, issue_command, adw_id, logger, worktree_path
    )

    if error:
        logger.warning(f"Error creating commit message: {error}")
    else:
        # Commit the patch (in worktree)
        success, error = commit_changes(commit_msg, cwd=worktree_path)
        if not success:
            logger.warning(f"Error committing patch: {error}")

    logger.info(f"Committed patch: {commit_msg}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PATCH_IMPLEMENTOR, "✅ Patch committed"),
    )

    logger.info("Finalizing git operations")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "🔧 Finalizing git operations"),
    )

    # Finalize git operations (push and PR) - passing cwd for worktree
    finalize_git_operations(state, logger, cwd=worktree_path)

    logger.info("Isolated patch workflow completed successfully")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Isolated patch workflow completed"),
    )

    # Save final state
    state.save("adw_patch_iso")

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final isolated patch state:\n```json\n{json.dumps(state.data, indent=2)}\n```",
    )


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

