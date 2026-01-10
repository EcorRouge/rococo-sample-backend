#!/usr/bin/env python3
"""
Health Check Script for ADW System

Usage:
python adws/adw_tests/health_check.py [issue_number]

This script performs comprehensive health checks:
1. Validates all required environment variables
2. Checks git repository configuration
3. Tests Claude Code CLI functionality
4. Returns structured results
"""

import os
import sys
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import field
from datetime import datetime
from pathlib import Path
import argparse

from dotenv import load_dotenv
from dataclasses import dataclass
from rococo.models import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.github import get_repo_url, extract_repo_path, make_issue_comment
from adw_modules.utils import get_safe_subprocess_env

load_dotenv()


@dataclass(kw_only=True)
class CheckResult(BaseModel):
    """Individual check result."""

    success: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class HealthCheckResult(BaseModel):
    """Structure for health check results."""

    success: bool
    timestamp: str
    checks: Dict[str, CheckResult]
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def check_env_vars() -> CheckResult:
    """Check required environment variables."""
    required_vars = {
        "ANTHROPIC_API_KEY": "Anthropic API Key for Claude Code",
    }

    optional_vars = {
        "CLAUDE_CODE_PATH": "Path to Claude Code CLI (defaults to 'claude')",
        "GITHUB_PAT": "(Optional) GitHub Personal Access Token",
        "GITHUB_REPO_URL": "(Optional) GitHub repository URL",
        "SONARQUBE_URL": "(Optional) SonarQube server URL for coverage integration",
        "SONARQUBE_TOKEN": "(Optional) SonarQube authentication token",
        "SONARQUBE_PROJECT_KEY": "(Optional) SonarQube project key (defaults to 'rococo-sample-backend')",
    }

    missing_required = []
    missing_optional = []

    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"{var} ({desc})")

    for var, desc in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var} ({desc})")

    success = len(missing_required) == 0

    return CheckResult(
        success=success,
        error="Missing required environment variables" if not success else None,
        details={
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "claude_code_path": os.getenv("CLAUDE_CODE_PATH", "claude"),
        },
    )


def check_git_repo() -> CheckResult:
    """Check git repository configuration."""
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)

        return CheckResult(
            success=True,
            details={
                "repo_url": repo_url,
                "repo_path": repo_path,
            },
        )
    except ValueError as e:
        return CheckResult(success=False, error=str(e))


def check_claude_code() -> CheckResult:
    """Test Claude Code CLI functionality."""
    claude_path = os.getenv("CLAUDE_CODE_PATH", "claude")

    try:
        result = subprocess.run(
            [claude_path, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return CheckResult(
                success=False,
                error=f"Claude Code CLI not functional at '{claude_path}'",
            )
    except FileNotFoundError:
        return CheckResult(
            success=False,
            error=f"Claude Code CLI not found at '{claude_path}'. Please install or set CLAUDE_CODE_PATH correctly.",
        )

    test_prompt = "What is 2+2? Just respond with the number, nothing else."
    env = get_safe_subprocess_env()

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as tmp:
            output_file = tmp.name

        cmd = [
            claude_path,
            "-p",
            test_prompt,
            "--model",
            "sonnet",
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        with open(output_file, "w") as f:
            result = subprocess.run(
                cmd, stdout=f, stderr=subprocess.PIPE, text=True, env=env, timeout=30
            )

        if result.returncode != 0:
            return CheckResult(
                success=False, error=f"Claude Code test failed: {result.stderr}"
            )

        claude_responded = False
        response_text = ""

        try:
            with open(output_file, "r") as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        if msg.get("type") == "result":
                            claude_responded = True
                            response_text = msg.get("result", "")
                            break
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

        return CheckResult(
            success=claude_responded,
            details={
                "test_passed": "4" in response_text,
                "response": response_text[:100] if response_text else "No response",
            },
        )

    except subprocess.TimeoutExpired:
        return CheckResult(
            success=False, error="Claude Code test timed out after 30 seconds"
        )
    except Exception as e:
        return CheckResult(success=False, error=f"Claude Code test error: {str(e)}")


def check_github_cli() -> CheckResult:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            return CheckResult(success=False, error="GitHub CLI (gh) is not installed")

        env = get_safe_subprocess_env()
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, env=env
        )

        authenticated = result.returncode == 0

        return CheckResult(
            success=authenticated,
            error="GitHub CLI not authenticated" if not authenticated else None,
            details={"installed": True, "authenticated": authenticated},
        )

    except FileNotFoundError:
        return CheckResult(
            success=False,
            error="GitHub CLI (gh) is not installed. Install with: brew install gh",
            details={"installed": False},
        )


def run_health_check() -> HealthCheckResult:
    """Run all health checks and return results."""
    result = HealthCheckResult(
        success=True, timestamp=datetime.now().isoformat(), checks={}
    )

    env_check = check_env_vars()
    result.checks["environment"] = env_check
    if not env_check.success:
        result.success = False
        if env_check.error:
            result.errors.append(env_check.error)
        missing_required = env_check.details.get("missing_required", [])
        result.errors.extend(
            [f"Missing required env var: {var}" for var in missing_required]
        )

    git_check = check_git_repo()
    result.checks["git_repository"] = git_check
    if not git_check.success:
        result.success = False
        if git_check.error:
            result.errors.append(git_check.error)

    gh_check = check_github_cli()
    result.checks["github_cli"] = gh_check
    if not gh_check.success:
        result.success = False
        if gh_check.error:
            result.errors.append(gh_check.error)

    if os.getenv("ANTHROPIC_API_KEY"):
        claude_check = check_claude_code()
        result.checks["claude_code"] = claude_check
        if not claude_check.success:
            result.success = False
            if claude_check.error:
                result.errors.append(claude_check.error)
    else:
        result.checks["claude_code"] = CheckResult(
            success=False,
            details={"skipped": True, "reason": "ANTHROPIC_API_KEY not set"},
        )

    # Check SonarQube integration - optional
    sonarqube_url = os.getenv("SONARQUBE_URL")
    sonarqube_token = os.getenv("SONARQUBE_TOKEN")
    if sonarqube_url and sonarqube_token:
        try:
            from adw_modules.sonarqube import SonarQubeClient
            sonar_client = SonarQubeClient()
            metrics = sonar_client.get_project_metrics()
            if metrics:
                result.checks["sonarqube"] = CheckResult(
                    success=True,
                    details={
                        "url": sonarqube_url,
                        "project_key": sonar_client.project_key,
                        "coverage": f"{metrics.coverage:.2f}%",
                        "uncovered_lines": metrics.uncovered_lines,
                    },
                )
            else:
                result.checks["sonarqube"] = CheckResult(
                    success=False,
                    error="Could not fetch SonarQube metrics",
                    details={"url": sonarqube_url},
                )
        except Exception as e:
            result.checks["sonarqube"] = CheckResult(
                success=False,
                error=f"SonarQube integration error: {e}",
                details={"url": sonarqube_url},
            )
    else:
        result.checks["sonarqube"] = CheckResult(
            success=False,
            details={
                "skipped": True,
                "reason": "SONARQUBE_URL or SONARQUBE_TOKEN not set",
            },
        )

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ADW System Health Check")
    parser.add_argument(
        "issue_number",
        nargs="?",
        help="Optional GitHub issue number to post results to",
    )
    args = parser.parse_args()

    print("🏥 Running ADW System Health Check...\n")

    result = run_health_check()

    print(
        f"{'✅' if result.success else '❌'} Overall Status: {'HEALTHY' if result.success else 'UNHEALTHY'}"
    )
    print(f"📅 Timestamp: {result.timestamp}\n")

    print("📋 Check Results:")
    print("-" * 50)

    for check_name, check_result in result.checks.items():
        status = "✅" if check_result.success else "❌"
        print(f"\n{status} {check_name.replace('_', ' ').title()}:")

        for key, value in check_result.details.items():
            if value is not None and key not in ["missing_required", "missing_optional"]:
                print(f"   {key}: {value}")

        if check_result.error:
            print(f"   ❌ Error: {check_result.error}")
        if check_result.warning:
            print(f"   ⚠️  Warning: {check_result.warning}")

    if result.warnings:
        print("\n⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")

    if result.errors:
        print("\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")

    if not result.success:
        print("\n📝 Next Steps:")
        if any("ANTHROPIC_API_KEY" in e for e in result.errors):
            print("   1. Set ANTHROPIC_API_KEY in your .env file")
        if any("GitHub CLI" in e for e in result.errors):
            print("   2. Install GitHub CLI: brew install gh")
            print("   3. Authenticate: gh auth login")

    if args.issue_number:
        print(f"\n📤 Posting health check results to issue #{args.issue_number}...")
        status_emoji = "✅" if result.success else "❌"
        comment = f"{status_emoji} Health check completed: {'HEALTHY' if result.success else 'UNHEALTHY'}"
        try:
            make_issue_comment(args.issue_number, comment)
            print(f"✅ Posted health check comment to issue #{args.issue_number}")
        except Exception as e:
            print(f"❌ Failed to post comment: {e}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()

