"""Shared AI Developer Workflow (ADW) operations."""

import glob
import json
import logging
import os
import subprocess
import re
from typing import Tuple, Optional
from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
    ADWExtractionResult,
)
from adw_modules.agent import execute_template
from adw_modules.github import get_repo_url, extract_repo_path, ADW_BOT_IDENTIFIER
from adw_modules.state import ADWState
from adw_modules.utils import parse_json


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"

# Available ADW workflows for runtime validation
AVAILABLE_ADW_WORKFLOWS = [
    "adw_plan_iso",
    "adw_patch_iso",
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
    "adw_sdlc_ZTE_iso",
    "adw_plan_build_iso",
    "adw_plan_build_test_iso",
    "adw_plan_build_test_review_iso",
    "adw_plan_build_document_iso",
    "adw_plan_build_review_iso",
    "adw_sdlc_iso",
]


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier."""
    if session_id:
        return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"


def extract_adw_info(text: str, temp_adw_id: str) -> ADWExtractionResult:
    """Extract ADW workflow, ID, and model_set from text using classify_adw agent."""
    request = AgentTemplateRequest(
        agent_name="adw_classifier",
        slash_command="/classify_adw",
        args=[text],
        adw_id=temp_adw_id,
    )

    try:
        response = execute_template(request)

        if not response.success:
            print(f"Failed to classify ADW: {response.output}")
            return ADWExtractionResult()

        try:
            data = parse_json(response.output, dict)
            adw_command = data.get("adw_slash_command", "").replace("/", "")
            adw_id = data.get("adw_id")
            model_set = data.get("model_set", "base")

            if adw_command and adw_command in AVAILABLE_ADW_WORKFLOWS:
                return ADWExtractionResult(
                    workflow_command=adw_command,
                    adw_id=adw_id,
                    model_set=model_set
                )

            return ADWExtractionResult()

        except ValueError as e:
            print(f"Failed to parse classify_adw response: {e}")
            return ADWExtractionResult()

    except Exception as e:
        print(f"Error calling classify_adw: {e}")
        return ADWExtractionResult()


def classify_issue(
    issue: GitHubIssue, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command."""
    # Extract minimal issue data using rococo
    issue_dict = issue.as_dict()
    minimal_issue = {
        "number": issue_dict.get("number"),
        "title": issue_dict.get("title"),
        "body": issue_dict.get("body"),
    }
    minimal_issue_json = json.dumps(minimal_issue, default=str)

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[minimal_issue_json],
        adw_id=adw_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")

    response = execute_template(request)

    logger.debug(
        f"Classification response: {json.dumps(response.as_dict(), indent=2)}"
    )

    if not response.success:
        return None, response.output

    output = response.output.strip()
    
    # Try multiple patterns to extract the classification
    # Pattern 1: Look for markdown format with backticks: **Classification:** `/chore`
    # Handles: **Classification:** `/chore` or Classification: `/chore`
    markdown_backtick_match = re.search(
        r"(?:\*\*)?Classification[:\s]+[`*]*(/chore|/bug|/feature|0)[`*]+", 
        output, 
        re.IGNORECASE
    )
    if markdown_backtick_match:
        issue_command = markdown_backtick_match.group(1)
    else:
        # Pattern 2: Look for markdown format: **Classification:** `/chore` or Classification: `/chore`
        markdown_match = re.search(
            r"(?:\*\*)?Classification[:\s]*[`*]*(/chore|/bug|/feature|0)[`*]*", 
            output, 
            re.IGNORECASE
        )
        if markdown_match:
            issue_command = markdown_match.group(1)
        else:
            # Pattern 3: Look for /chore, /bug, /feature, or 0 (with word boundaries or after whitespace)
            classification_match = re.search(r"(?:^|\s|`|\*)(/chore|/bug|/feature|0)(?:\s|`|\*|$)", output)
            if classification_match:
                issue_command = classification_match.group(1)
            else:
                # Pattern 4: Look for it at the start or end of a line
                line_match = re.search(r"^\s*(/chore|/bug|/feature|0)\s*$", output, re.MULTILINE)
                if line_match:
                    issue_command = line_match.group(1)
                else:
                    # Fallback: use entire output if it's a valid command
                    issue_command = output.strip()

    # Normalize the command (ensure it starts with /)
    if issue_command and not issue_command.startswith("/") and issue_command in ["chore", "bug", "feature"]:
        issue_command = f"/{issue_command}"

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        return None, f"Invalid command selected. Expected /chore, /bug, or /feature, got: {issue_command}. Full response: {response.output[:200]}"

    return issue_command, None  # type: ignore


def build_plan(
    issue: GitHubIssue,
    command: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command."""
    # Extract minimal issue data using rococo
    issue_dict = issue.as_dict()
    minimal_issue = {
        "number": issue_dict.get("number"),
        "title": issue_dict.get("title"),
        "body": issue_dict.get("body"),
    }
    minimal_issue_json = json.dumps(minimal_issue, default=str)

    issue_plan_template_request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=command,
        args=[str(issue.number), adw_id, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"issue_plan_template_request: {json.dumps(issue_plan_template_request.as_dict(), indent=2)}"
    )

    issue_plan_response = execute_template(issue_plan_template_request)

    logger.debug(
        f"issue_plan_response: {json.dumps(issue_plan_response.as_dict(), indent=2)}"
    )

    return issue_plan_response


def implement_plan(
    plan_file: str,
    adw_id: str,
    logger: logging.Logger,
    agent_name: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Implement the plan using the /implement command."""
    implementor_name = agent_name or AGENT_IMPLEMENTOR

    implement_template_request = AgentTemplateRequest(
        agent_name=implementor_name,
        slash_command="/implement",
        args=[plan_file],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"implement_template_request: {json.dumps(implement_template_request.as_dict(), indent=2)}"
    )

    implement_response = execute_template(implement_template_request)

    logger.debug(
        f"implement_response: {json.dumps(implement_response.as_dict(), indent=2)}"
    )

    return implement_response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate a git branch name for the issue."""
    issue_type = issue_class.replace("/", "")

    # Extract minimal issue data using rococo
    issue_dict = issue.as_dict()
    minimal_issue = {
        "number": issue_dict.get("number"),
        "title": issue_dict.get("title"),
        "body": issue_dict.get("body"),
    }
    minimal_issue_json = json.dumps(minimal_issue, default=str)

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, minimal_issue_json],
        adw_id=adw_id,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    # Parse the response to extract just the branch name
    output = response.output.strip()
    
    # Try to extract from code blocks first (most common format)
    code_block_match = re.search(r'```(?:[a-z]+)?\n([a-z0-9-]+)\n```', output, re.IGNORECASE)
    if code_block_match:
        branch_name = code_block_match.group(1).strip()
    else:
        # Try to find pattern: {type}-issue-{number}-adw-{id}-{slug}
        pattern = rf'{re.escape(issue_type)}-issue-\d+-adw-{re.escape(adw_id)}-[a-z0-9-]+'
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            branch_name = match.group(0)
        else:
            # Try to find any line that looks like a branch name
            lines = [line.strip() for line in output.split('\n')]
            branch_name = None
            for line in lines:
                # Check if line contains the pattern elements
                if (f'issue-{issue.number}' in line and 
                    adw_id in line and 
                    issue_type in line.lower() and
                    '-' in line and
                    not line.startswith('#') and
                    not line.startswith('*') and
                    not line.startswith('`')):
                    # Clean up the line
                    branch_name = re.sub(r'[`"\']', '', line).strip()
                    # Extract just the branch name part if there's extra text
                    pattern_match = re.search(pattern, branch_name, re.IGNORECASE)
                    if pattern_match:
                        branch_name = pattern_match.group(0)
                    break
            
            if not branch_name:
                # Last resort: use first non-empty line, clean it up
                for line in lines:
                    if line and not line.startswith('#') and not line.startswith('*'):
                        branch_name = re.sub(r'[`"\']', '', line).strip()
                        # Remove any markdown formatting
                        branch_name = re.sub(r'^\*\s*', '', branch_name)  # Remove bullet points
                        branch_name = re.sub(r'^-\s*', '', branch_name)    # Remove dashes
                        if branch_name and len(branch_name) < 100:  # Reasonable branch name length
                            break
    
    # Final cleanup: remove any remaining invalid characters for git branch names
    if branch_name:
        # Git branch names can't contain: spaces, ~, ^, :, ?, *, [, \, @, {, }
        branch_name = re.sub(r'[ ~^:?*\[\\@{}\n\r\t]', '-', branch_name)
        # Remove consecutive hyphens
        branch_name = re.sub(r'-+', '-', branch_name)
        # Remove leading/trailing hyphens
        branch_name = branch_name.strip('-')
        # Ensure it's not empty
        if not branch_name:
            return None, "Could not extract valid branch name from response"
    else:
        return None, "Could not extract branch name from response"
    
    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message."""
    issue_type = issue_class.replace("/", "")
    unique_agent_name = f"{agent_name}_committer"

    # Extract minimal issue data using rococo
    issue_dict = issue.as_dict()
    minimal_issue = {
        "number": issue_dict.get("number"),
        "title": issue_dict.get("title"),
        "body": issue_dict.get("body"),
    }
    minimal_issue_json = json.dumps(minimal_issue, default=str)

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        slash_command="/commit",
        args=[agent_name, issue_type, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit message: {commit_message}")
    return commit_message, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes."""
    plan_file = state.get("plan_file") or "No plan file (test run)"
    adw_id = state.get("adw_id")

    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        from adw_modules.data_types import GitHubIssue

        try:
            issue_model = GitHubIssue.from_dict(issue)
            # Extract only the fields we need
            issue_dict = issue_model.as_dict()
            filtered_issue = {
                "number": issue_dict.get("number"),
                "title": issue_dict.get("title"),
                "body": issue_dict.get("body"),
            }
            issue_json = json.dumps(filtered_issue, default=str)
        except Exception:
            issue_json = json.dumps(issue, default=str)
    else:
        # Issue is already a GitHubIssue model
        issue_dict = issue.as_dict()
        filtered_issue = {
            "number": issue_dict.get("number"),
            "title": issue_dict.get("title"),
            "body": issue_dict.get("body"),
        }
        issue_json = json.dumps(filtered_issue, default=str)

    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[branch_name, issue_json, plan_file, adw_id],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def ensure_plan_exists(state: ADWState, issue_number: str) -> str:
    """Find or error if no plan exists for issue."""
    if state.get("plan_file"):
        return state.get("plan_file")

    from adw_modules.git_ops import get_current_branch

    branch = get_current_branch()

    if f"-{issue_number}-" in branch:
        plans = glob.glob(f"specs/*{issue_number}*.md")
        if plans:
            return plans[0]

    raise ValueError(
        f"No plan found for issue {issue_number}. Run adw_plan_iso.py first."
    )


def ensure_adw_id(
    issue_number: str,
    adw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get ADW ID or create a new one and initialize state."""
    if adw_id:
        state = ADWState.load(adw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ADW state for ID: {adw_id}")
            else:
                print(f"Found existing ADW state for ID: {adw_id}")
            return adw_id
        state = ADWState(adw_id)
        state.update(adw_id=adw_id, issue_number=issue_number)
        state.save("ensure_adw_id")
        if logger:
            logger.info(f"Created new ADW state for provided ID: {adw_id}")
        else:
            print(f"Created new ADW state for provided ID: {adw_id}")
        return adw_id

    from adw_modules.utils import make_adw_id

    new_adw_id = make_adw_id()
    state = ADWState(new_adw_id)
    state.update(adw_id=new_adw_id, issue_number=issue_number)
    state.save("ensure_adw_id")
    if logger:
        logger.info(f"Created new ADW ID and state: {new_adw_id}")
    else:
        print(f"Created new ADW ID and state: {new_adw_id}")
    return new_adw_id


def find_existing_branch_for_issue(
    issue_number: str, adw_id: Optional[str] = None, cwd: Optional[str] = None
) -> Optional[str]:
    """Find an existing branch for the given issue number."""
    result = subprocess.run(
        ["git", "branch", "-a"], capture_output=True, text=True, cwd=cwd
    )

    if result.returncode != 0:
        return None

    branches = result.stdout.strip().split("\n")

    for branch in branches:
        branch = branch.strip().replace("* ", "").replace("remotes/origin/", "")
        if f"-issue-{issue_number}-" in branch:
            if adw_id and f"-adw-{adw_id}-" in branch:
                return branch
            elif not adw_id:
                return branch

    return None


def find_plan_for_issue(
    issue_number: str, adw_id: Optional[str] = None
) -> Optional[str]:
    """Find plan file for the given issue number and optional adw_id."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    agents_dir = os.path.join(project_root, "agents")

    if not os.path.exists(agents_dir):
        return None

    if adw_id:
        plan_path = os.path.join(agents_dir, adw_id, AGENT_PLANNER, "plan.md")
        if os.path.exists(plan_path):
            return plan_path

    for agent_id in os.listdir(agents_dir):
        agent_path = os.path.join(agents_dir, agent_id)
        if os.path.isdir(agent_path):
            plan_path = os.path.join(agent_path, AGENT_PLANNER, "plan.md")
            if os.path.exists(plan_path):
                return plan_path

    return None


def create_or_find_branch(
    issue_number: str,
    issue: GitHubIssue,
    state: ADWState,
    logger: logging.Logger,
    cwd: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Create or find a branch for the given issue."""
    branch_name = state.get("branch_name") or state.get("branch", {}).get("name")
    if branch_name:
        logger.info(f"Found branch in state: {branch_name}")
        from adw_modules.git_ops import get_current_branch

        current = get_current_branch(cwd=cwd)
        if current != branch_name:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                )
                if result.returncode != 0:
                    return "", f"Failed to checkout branch: {result.stderr}"
        return branch_name, None

    adw_id = state.get("adw_id")
    existing_branch = find_existing_branch_for_issue(issue_number, adw_id, cwd=cwd)
    if existing_branch:
        logger.info(f"Found existing branch: {existing_branch}")
        result = subprocess.run(
            ["git", "checkout", existing_branch],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode != 0:
            return "", f"Failed to checkout branch: {result.stderr}"
        state.update(branch_name=existing_branch)
        return existing_branch, None

    logger.info("No existing branch found, creating new one")

    issue_command, error = classify_issue(issue, adw_id, logger)
    if error:
        return "", f"Failed to classify issue: {error}"

    state.update(issue_class=issue_command)

    branch_name, error = generate_branch_name(issue, issue_command, adw_id, logger)
    if error:
        return "", f"Failed to generate branch name: {error}"

    from adw_modules.git_ops import create_branch

    success, error = create_branch(branch_name, cwd=cwd)
    if not success:
        return "", f"Failed to create branch: {error}"

    state.update(branch_name=branch_name)
    logger.info(f"Created and checked out new branch: {branch_name}")

    return branch_name, None


def find_spec_file(state: ADWState, logger: logging.Logger) -> Optional[str]:
    """Find the spec file from state or by examining git diff."""
    worktree_path = state.get("worktree_path")

    spec_file = state.get("plan_file")
    if spec_file:
        if worktree_path and not os.path.isabs(spec_file):
            spec_file = os.path.join(worktree_path, spec_file)

        if os.path.exists(spec_file):
            logger.info(f"Using spec file from state: {spec_file}")
            return spec_file

    logger.info("Looking for spec file in git diff")
    result = subprocess.run(
        ["git", "diff", "origin/main", "--name-only"],
        capture_output=True,
        text=True,
        cwd=worktree_path,
    )

    if result.returncode == 0:
        files = result.stdout.strip().split("\n")
        spec_files = [f for f in files if f.startswith("specs/") and f.endswith(".md")]

        if spec_files:
            spec_file = spec_files[0]
            if worktree_path:
                spec_file = os.path.join(worktree_path, spec_file)
            logger.info(f"Found spec file: {spec_file}")
            return spec_file

    branch_name = state.get("branch_name")
    if branch_name:
        import re

        match = re.search(r"issue-(\d+)", branch_name)
        if match:
            issue_num = match.group(1)
            adw_id = state.get("adw_id")

            search_dir = worktree_path if worktree_path else os.getcwd()
            pattern = os.path.join(
                search_dir, f"specs/issue-{issue_num}-adw-{adw_id}*.md"
            )
            spec_files = glob.glob(pattern)

            if spec_files:
                spec_file = spec_files[0]
                logger.info(f"Found spec file by pattern: {spec_file}")
                return spec_file

    logger.warning("No spec file found")
    return None


def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
    """Create a patch plan and implement it."""
    args = [adw_id, review_change_request]

    if spec_path:
        args.append(spec_path)
    else:
        args.append("")

    args.append(agent_name_planner)

    if issue_screenshots:
        args.append(issue_screenshots)

    request = AgentTemplateRequest(
        agent_name=agent_name_planner,
        slash_command="/patch",
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"Patch plan request: {json.dumps(request.as_dict(), indent=2)}"
    )

    response = execute_template(request)

    logger.debug(
        f"Patch plan response: {json.dumps(response.as_dict(), indent=2)}"
    )

    if not response.success:
        logger.error(f"Error creating patch plan: {response.output}")
        return None, AgentPromptResponse(
            output=f"Failed to create patch plan: {response.output}", success=False
        )

    patch_file_path = response.output.strip()

    if "specs/patch/" not in patch_file_path or not patch_file_path.endswith(".md"):
        logger.error(f"Invalid patch plan path returned: {patch_file_path}")
        return None, AgentPromptResponse(
            output=f"Invalid patch plan path: {patch_file_path}", success=False
        )

    logger.info(f"Created patch plan: {patch_file_path}")

    implement_response = implement_plan(
        patch_file_path, adw_id, logger, agent_name_implementor, working_dir=working_dir
    )

    return patch_file_path, implement_response

