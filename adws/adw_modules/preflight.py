"""Pre-flight validation checks for ADW workflows.

Validates system state, dependencies, and environment before workflow execution.
"""

import os
import sys
import subprocess
import shutil
import logging
import socket
from typing import List, Tuple, Optional
from pathlib import Path

from adw_modules.error_handling import ADWError, ErrorSeverity, handle_error
from adw_modules.utils import check_env_vars


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, success: bool, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        """Initialize validation result.
        
        Args:
            success: Whether validation passed
            message: Validation message
            severity: Severity if validation failed
        """
        self.success = success
        self.message = message
        self.severity = severity
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.success


def check_git_repo(logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check that we're in a git repository.
    
    Returns:
        ValidationResult indicating if git repo is valid
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=True,
        )
        return ValidationResult(True, "Git repository is valid")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return ValidationResult(
            False,
            f"Not in a valid git repository: {e}",
            ErrorSeverity.CRITICAL
        )


def check_git_clean(logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check that git working directory is clean (optional check).
    
    Returns:
        ValidationResult indicating if working directory is clean
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            return ValidationResult(
                False,
                "Git working directory has uncommitted changes (this is a warning, not an error)",
                ErrorSeverity.WARNING
            )
        return ValidationResult(True, "Git working directory is clean")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ValidationResult(
            False,
            "Could not check git status",
            ErrorSeverity.WARNING
        )


def check_git_remote(logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check that git remote is configured.
    
    Returns:
        ValidationResult indicating if remote is configured
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            return ValidationResult(True, "Git remote 'origin' is configured")
        return ValidationResult(
            False,
            "Git remote 'origin' is not configured",
            ErrorSeverity.ERROR
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ValidationResult(
            False,
            "Could not check git remote configuration",
            ErrorSeverity.ERROR
        )


def check_disk_space(
    required_gb: float = 1.0,
    path: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> ValidationResult:
    """Check that sufficient disk space is available.
    
    Args:
        required_gb: Required disk space in GB
        path: Path to check (defaults to current directory)
        logger: Optional logger
        
    Returns:
        ValidationResult indicating if sufficient disk space is available
    """
    try:
        import shutil
        
        check_path = path or os.getcwd()
        stat = shutil.disk_usage(check_path)
        available_gb = stat.free / (1024 ** 3)
        
        if available_gb >= required_gb:
            return ValidationResult(
                True,
                f"Sufficient disk space available: {available_gb:.2f} GB"
            )
        return ValidationResult(
            False,
            f"Insufficient disk space: {available_gb:.2f} GB available, {required_gb} GB required",
            ErrorSeverity.ERROR
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Could not check disk space: {e}",
            ErrorSeverity.WARNING
        )


def check_port_available(port: int, logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check if a port is available.
    
    Args:
        port: Port number to check
        logger: Optional logger
        
    Returns:
        ValidationResult indicating if port is available
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            if result == 0:
                return ValidationResult(
                    False,
                    f"Port {port} is already in use",
                    ErrorSeverity.ERROR
                )
            return ValidationResult(True, f"Port {port} is available")
    except Exception as e:
        return ValidationResult(
            False,
            f"Could not check port {port}: {e}",
            ErrorSeverity.WARNING
        )


def check_claude_code_cli(logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check that Claude Code CLI is available.
    
    Returns:
        ValidationResult indicating if Claude Code CLI is available
    """
    claude_path = os.getenv("CLAUDE_CODE_PATH", "claude")
    
    try:
        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip() if result.stdout.strip() else "unknown"
            return ValidationResult(True, f"Claude Code CLI is available: {version}")
        return ValidationResult(
            False,
            f"Claude Code CLI '{claude_path}' is not working (exit code: {result.returncode})",
            ErrorSeverity.ERROR
        )
    except FileNotFoundError:
        return ValidationResult(
            False,
            f"Claude Code CLI '{claude_path}' not found in PATH",
            ErrorSeverity.ERROR
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(
            False,
            f"Claude Code CLI '{claude_path}' timed out",
            ErrorSeverity.ERROR
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Could not check Claude Code CLI: {e}",
            ErrorSeverity.ERROR
        )


def check_github_cli(logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check that GitHub CLI (gh) is available.
    
    Returns:
        ValidationResult indicating if GitHub CLI is available
    """
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return ValidationResult(True, "GitHub CLI (gh) is available")
        return ValidationResult(
            False,
            "GitHub CLI (gh) is not working",
            ErrorSeverity.ERROR
        )
    except FileNotFoundError:
        return ValidationResult(
            False,
            "GitHub CLI (gh) not found in PATH",
            ErrorSeverity.ERROR
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(
            False,
            "GitHub CLI (gh) timed out",
            ErrorSeverity.ERROR
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Could not check GitHub CLI: {e}",
            ErrorSeverity.ERROR
        )


def check_github_auth(logger: Optional[logging.Logger] = None) -> ValidationResult:
    """Check that GitHub CLI is authenticated.
    
    Returns:
        ValidationResult indicating if GitHub is authenticated
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return ValidationResult(True, "GitHub CLI is authenticated")
        return ValidationResult(
            False,
            "GitHub CLI is not authenticated. Run 'gh auth login'",
            ErrorSeverity.ERROR
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ValidationResult(
            False,
            "Could not check GitHub authentication",
            ErrorSeverity.WARNING
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Could not check GitHub authentication: {e}",
            ErrorSeverity.WARNING
        )


def check_worktree_directory(
    trees_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> ValidationResult:
    """Check that worktree directory exists and is writable.
    
    Args:
        trees_dir: Path to trees directory (defaults to project_root/trees)
        logger: Optional logger
        
    Returns:
        ValidationResult indicating if worktree directory is valid
    """
    try:
        if trees_dir is None:
            # Get project root (parent of adws directory)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            trees_dir = os.path.join(project_root, "trees")
        
        # Check if directory exists or can be created
        os.makedirs(trees_dir, exist_ok=True)
        
        # Check if writable
        test_file = os.path.join(trees_dir, ".test_write")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return ValidationResult(True, f"Worktree directory is writable: {trees_dir}")
        except Exception as e:
            return ValidationResult(
                False,
                f"Worktree directory is not writable: {e}",
                ErrorSeverity.ERROR
            )
    except Exception as e:
        return ValidationResult(
            False,
            f"Could not check worktree directory: {e}",
            ErrorSeverity.ERROR
        )


def run_preflight_checks(
    logger: logging.Logger,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None,
    checks: Optional[List[str]] = None,
    fail_on_warning: bool = False,
) -> bool:
    """Run all pre-flight validation checks.
    
    Args:
        logger: Logger instance
        issue_number: GitHub issue number (for error reporting)
        adw_id: ADW ID (for context)
        checks: List of check names to run (None = all checks)
        fail_on_warning: If True, warnings will cause failure
        
    Returns:
        True if all checks passed, False otherwise
    """
    # Default checks to run
    default_checks = [
        "env_vars",
        "git_repo",
        "git_remote",
        "disk_space",
        "worktree_directory",
    ]
    
    checks_to_run = checks or default_checks
    
    logger.info("Running pre-flight validation checks...")
    
    all_passed = True
    results = []
    
    # Environment variables
    if "env_vars" in checks_to_run:
        try:
            check_env_vars(logger)
            results.append(("Environment Variables", ValidationResult(True, "All required env vars are set")))
        except SystemExit:
            results.append(("Environment Variables", ValidationResult(False, "Missing required environment variables", ErrorSeverity.CRITICAL)))
            all_passed = False
    
    # Git repository
    if "git_repo" in checks_to_run:
        result = check_git_repo(logger)
        results.append(("Git Repository", result))
        if not result.success:
            all_passed = False
    
    # Git remote
    if "git_remote" in checks_to_run:
        result = check_git_remote(logger)
        results.append(("Git Remote", result))
        if not result.success:
            all_passed = False
    
    # Git clean
    if "git_clean" in checks_to_run:
        result = check_git_clean(logger)
        results.append(("Git Working Directory", result))
        if not result.success and (fail_on_warning or result.severity != ErrorSeverity.WARNING):
            all_passed = False
    
    # Disk space
    if "disk_space" in checks_to_run:
        result = check_disk_space(required_gb=1.0, logger=logger)
        results.append(("Disk Space", result))
        if not result.success:
            all_passed = False
    
    # Worktree directory
    if "worktree_directory" in checks_to_run:
        result = check_worktree_directory(logger=logger)
        results.append(("Worktree Directory", result))
        if not result.success:
            all_passed = False
    
    # Claude Code CLI
    if "claude_code" in checks_to_run:
        result = check_claude_code_cli(logger)
        results.append(("Claude Code CLI", result))
        if not result.success:
            all_passed = False
    
    # GitHub CLI
    if "github_cli" in checks_to_run:
        result = check_github_cli(logger)
        results.append(("GitHub CLI", result))
        if not result.success:
            all_passed = False
    
    # GitHub auth
    if "github_auth" in checks_to_run:
        result = check_github_auth(logger)
        results.append(("GitHub Authentication", result))
        if not result.success:
            all_passed = False
    
    # Report results
    logger.info("\nPre-flight check results:")
    for check_name, result in results:
        status = "✅ PASS" if result.success else f"❌ FAIL ({result.severity.value})"
        logger.info(f"  {check_name}: {status} - {result.message}")
    
    if not all_passed:
        error_msg = "Pre-flight validation checks failed. Please fix the issues above and try again."
        if issue_number:
            from adw_modules.github import make_issue_comment
            from adw_modules.workflow_ops import format_issue_message
            try:
                comment = format_issue_message(
                    adw_id or "unknown",
                    "ops",
                    f"❌ {error_msg}"
                )
                make_issue_comment(issue_number, comment)
            except Exception:
                pass  # Don't fail if comment fails
        
        raise ADWError(
            message=error_msg,
            severity=ErrorSeverity.CRITICAL,
            issue_number=issue_number,
            adw_id=adw_id,
            should_exit=True,
        )
    
    logger.info("✅ All pre-flight checks passed!")
    return True

