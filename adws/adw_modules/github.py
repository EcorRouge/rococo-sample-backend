#!/usr/bin/env python3
"""
GitHub Operations Module - AI Developer Workflow (ADW)

This module contains all GitHub-related operations including:
- Issue fetching and manipulation
- Comment posting
- Repository path extraction
- Issue status management
"""

import subprocess
import sys
import os
import json
import re
from typing import Dict, List, Optional
from adw_modules.data_types import GitHubIssue, GitHubIssueListItem, GitHubComment

# Bot identifier to prevent webhook loops and filter bot comments
ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"


def get_github_env() -> Optional[dict]:
    """Get environment with GitHub token set up. Returns None if no GITHUB_PAT."""
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        return None
    
    env = {
        "GH_TOKEN": github_pat,
        "PATH": os.environ.get("PATH", ""),
    }
    return env


def get_repo_url() -> str:
    """Get GitHub repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(
            "No git remote 'origin' found. Please ensure you're in a git repository with a remote."
        )
    except FileNotFoundError:
        raise ValueError("git command not found. Please ensure git is installed.")


def extract_repo_path(github_url: str) -> str:
    """Extract repository path (owner/repo) from GitHub URL.
    
    Supports multiple URL formats:
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - http://github.com/owner/repo
    
    Args:
        github_url: GitHub repository URL in any common format
        
    Returns:
        Repository path in format "owner/repo"
        
    Raises:
        ValueError: If URL format cannot be parsed
    """
    # Handle various URL formats: https://github.com/owner/repo.git, git@github.com:owner/repo.git
    patterns = [
        r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$",  # Matches both https:// and git@ formats
        r"([^/]+/[^/]+?)(?:\.git)?/?$",  # Fallback for bare owner/repo format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, github_url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract repo path from URL: {github_url}")


def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue:
    """Fetch GitHub issue using gh CLI and return typed model."""
    cmd = [
        "gh",
        "issue",
        "view",
        issue_number,
        "-R",
        repo_path,
        "--json",
        "number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url",
    ]

    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            issue_data = json.loads(result.stdout)
            # Filter and convert GitHub API data to match our model structure
            # Only include fields that exist in GitHubIssue, GitHubComment, GitHubUser models
            filtered_issue = {}
            
            # Basic issue fields
            if "number" in issue_data:
                filtered_issue["number"] = issue_data["number"]
            if "title" in issue_data:
                filtered_issue["title"] = issue_data["title"]
            if "body" in issue_data:
                filtered_issue["body"] = issue_data["body"]
            if "state" in issue_data:
                filtered_issue["state"] = issue_data["state"]
            if "url" in issue_data:
                filtered_issue["url"] = issue_data["url"]
            
            # Convert date fields (camelCase -> snake_case)
            if "createdAt" in issue_data:
                filtered_issue["created_at"] = issue_data["createdAt"]
            if "updatedAt" in issue_data:
                filtered_issue["updated_at"] = issue_data["updatedAt"]
            if "closedAt" in issue_data:
                filtered_issue["closed_at"] = issue_data["closedAt"]
            
            # Author field
            if "author" in issue_data:
                author = issue_data["author"]
                filtered_issue["author"] = {
                    "login": author.get("login"),
                    "id": author.get("id"),
                    "name": author.get("name"),
                    "is_bot": author.get("isBot", False),
                }
            
            # Assignees
            if "assignees" in issue_data:
                filtered_issue["assignees"] = [
                    {
                        "login": a.get("login"),
                        "id": a.get("id"),
                        "name": a.get("name"),
                        "is_bot": a.get("isBot", False),
                    }
                    for a in issue_data["assignees"]
                ]
            
            # Labels
            if "labels" in issue_data:
                filtered_issue["labels"] = [
                    {
                        "id": l.get("id"),
                        "name": l.get("name"),
                        "color": l.get("color"),
                        "description": l.get("description"),
                    }
                    for l in issue_data["labels"]
                ]
            
            # Comments - filter and convert
            if "comments" in issue_data:
                filtered_comments = []
                for comment in issue_data["comments"]:
                    filtered_comment = {
                        "id": comment.get("id"),
                        "body": comment.get("body"),
                    }
                    # Convert date fields
                    if "createdAt" in comment:
                        filtered_comment["created_at"] = comment["createdAt"]
                    if "updatedAt" in comment:
                        filtered_comment["updated_at"] = comment["updatedAt"]
                    # Author in comment
                    if "author" in comment:
                        author = comment["author"]
                        filtered_comment["author"] = {
                            "login": author.get("login"),
                            "id": author.get("id"),
                            "name": author.get("name"),
                            "is_bot": author.get("isBot", False),
                        }
                    filtered_comments.append(filtered_comment)
                filtered_issue["comments"] = filtered_comments
            
            # Milestone
            if "milestone" in issue_data and issue_data["milestone"]:
                milestone = issue_data["milestone"]
                filtered_issue["milestone"] = {
                    "id": milestone.get("id"),
                    "number": milestone.get("number"),
                    "title": milestone.get("title"),
                    "state": milestone.get("state"),
                    "description": milestone.get("description"),
                }
            
            issue = GitHubIssue.from_dict(filtered_issue)
            return issue
        else:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        print("\nTo install gh:", file=sys.stderr)
        print("  - macOS: brew install gh", file=sys.stderr)
        print("  - Linux: See https://github.com/cli/cli#installation", file=sys.stderr)
        print("  - Windows: See https://github.com/cli/cli#installation", file=sys.stderr)
        print("\nAfter installation, authenticate with: gh auth login", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing issue data: {e}", file=sys.stderr)
        sys.exit(1)


def make_issue_comment(issue_id: str, comment: str, repo_path: Optional[str] = None) -> None:
    """Post a comment to a GitHub issue using gh CLI.
    
    Args:
        issue_id: Issue number as string
        comment: Comment body to post
        repo_path: Optional repository path (owner/repo). If not provided, extracted from git remote.
        
    Note:
        If comment doesn't start with ADW_BOT_IDENTIFIER, it will be prepended automatically.
        However, most callers should use format_issue_message() which already includes it.
    """
    if not repo_path:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)

    # Only add bot identifier if not already present (to support both direct calls and formatted messages)
    if not comment.startswith(ADW_BOT_IDENTIFIER):
        comment = f"{ADW_BOT_IDENTIFIER} {comment}"

    cmd = [
        "gh",
        "issue",
        "comment",
        issue_id,
        "-R",
        repo_path,
        "--body",
        comment,
    ]

    env = get_github_env()
    if not env:
        raise ValueError("GITHUB_PAT not set. Cannot post comment without authentication.")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"Successfully posted comment to issue #{issue_id}")
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            raise RuntimeError(f"Failed to post comment: {result.stderr}")
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        raise RuntimeError("GitHub CLI (gh) not found. Please install it: https://cli.github.com/")
    except Exception as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        raise


def mark_issue_in_progress(issue_id: str) -> None:
    """Mark issue as in progress by adding label and comment."""
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-label",
        "in_progress",
    ]

    env = get_github_env()

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Note: Could not add 'in_progress' label: {result.stderr}")

    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-assignee",
        "@me",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"Assigned issue #{issue_id} to self")


def fetch_open_issues(repo_path: str) -> List[GitHubIssueListItem]:
    """Fetch all open issues from the GitHub repository."""
    try:
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo",
            repo_path,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,createdAt,updatedAt",
            "--limit",
            "1000",
        ]

        env = get_github_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )

        issues_data = json.loads(result.stdout)
        # Convert GitHub API field names (camelCase) to model field names (snake_case)
        for issue_data in issues_data:
            if "createdAt" in issue_data:
                issue_data["created_at"] = issue_data.pop("createdAt")
            if "updatedAt" in issue_data:
                issue_data["updated_at"] = issue_data.pop("updatedAt")
        issues = [GitHubIssueListItem.from_dict(issue_data) for issue_data in issues_data]
        print(f"Fetched {len(issues)} open issues")
        return issues

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to fetch issues: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse issues JSON: {e}", file=sys.stderr)
        return []


def fetch_issue_comments(repo_path: str, issue_number: int) -> List[Dict]:
    """Fetch all comments for a specific issue."""
    try:
        cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo_path,
            "--json",
            "comments",
        ]

        env = get_github_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )
        data = json.loads(result.stdout)
        comments = data.get("comments", [])

        comments.sort(key=lambda c: c.get("createdAt", ""))

        return comments

    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Failed to fetch comments for issue #{issue_number}: {e.stderr}",
            file=sys.stderr,
        )
        return []
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Failed to parse comments JSON for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []


def find_keyword_from_comment(keyword: str, issue: GitHubIssue) -> Optional[GitHubComment]:
    """Find the latest comment containing a specific keyword.
    
    Args:
        keyword: Keyword to search for in comments (case-insensitive)
        issue: GitHubIssue object with comments
        
    Returns:
        Latest GitHubComment containing the keyword (excluding bot comments), or None if not found
    """
    if not issue.comments:
        return None
    
    # Sort comments by creation time (newest first)
    sorted_comments = sorted(issue.comments, key=lambda c: c.created_at, reverse=True)
    
    # Case-insensitive search, excluding bot comments
    keyword_lower = keyword.lower()
    for comment in sorted_comments:
        # Skip bot comments to avoid loops
        if ADW_BOT_IDENTIFIER in comment.body:
            continue
            
        # Case-insensitive keyword search
        if keyword_lower in comment.body.lower():
            return comment
    
    return None

