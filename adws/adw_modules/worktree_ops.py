"""Worktree operations for ADW isolated workflows."""

import os
import subprocess
import sys
import logging
from typing import Tuple, Optional
import socket


def get_project_root() -> str:
    """Get the project root directory."""
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return script_dir


def create_worktree(adw_id: str, branch_name: str, logger: logging.Logger) -> Tuple[str, Optional[str]]:
    """Create an isolated git worktree for an ADW workflow.
    
    Args:
        adw_id: The ADW ID for this workflow
        branch_name: The branch name to create/checkout in the worktree
        logger: Logger instance
        
    Returns:
        Tuple of (worktree_path, error). On success, returns (path, None).
        On failure, returns (None, error_message).
    """
    project_root = get_project_root()
    worktree_path = os.path.join(project_root, "trees", adw_id)
    
    # Check if worktree already exists
    if os.path.exists(worktree_path):
        logger.info(f"Worktree directory already exists: {worktree_path}")
        # Validate the existing worktree
        is_valid, error = validate_worktree_path(worktree_path, logger)
        if is_valid:
            return worktree_path, None
        else:
            # If invalid, remove it and create a new one
            logger.warning(f"Existing worktree is invalid: {error}. Removing and recreating...")
            try:
                result = subprocess.run(
                    ["git", "worktree", "remove", worktree_path, "--force"],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                )
                if result.returncode != 0:
                    # Try manual removal
                    import shutil
                    shutil.rmtree(worktree_path)
            except Exception as e:
                logger.warning(f"Error removing invalid worktree: {e}")
                # Continue to try creating new one
    
    # Ensure trees directory exists
    trees_dir = os.path.join(project_root, "trees")
    os.makedirs(trees_dir, exist_ok=True)
    
    try:
        # Check if branch exists
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        branch_exists = bool(result.stdout.strip())
        
        if branch_exists:
            # Worktree from existing branch
            logger.info(f"Creating worktree from existing branch: {branch_name}")
            result = subprocess.run(
                ["git", "worktree", "add", worktree_path, branch_name],
                capture_output=True,
                text=True,
                cwd=project_root,
            )
        else:
            # Create new branch in worktree
            logger.info(f"Creating worktree with new branch: {branch_name}")
            result = subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, worktree_path],
                capture_output=True,
                text=True,
                cwd=project_root,
            )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"Failed to create worktree: {error_msg}")
            return None, error_msg
        
        logger.info(f"Created worktree at: {worktree_path}")
        return worktree_path, None
        
    except Exception as e:
        error_msg = f"Exception creating worktree: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def validate_worktree_path(worktree_path: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """Validate that a worktree path is a valid git worktree.
    
    Args:
        worktree_path: Path to the worktree directory
        logger: Logger instance
        
    Returns:
        Tuple of (is_valid, error_message). If valid, returns (True, None).
        If invalid, returns (False, error_message).
    """
    if not os.path.exists(worktree_path):
        return False, f"Worktree path does not exist: {worktree_path}"
    
    if not os.path.isdir(worktree_path):
        return False, f"Worktree path is not a directory: {worktree_path}"
    
    # Check if it's a git repository
    git_dir = os.path.join(worktree_path, ".git")
    if not os.path.exists(git_dir):
        return False, f"Worktree is not a git repository: {worktree_path}"
    
    # Verify it's registered as a worktree
    try:
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True,
            cwd=get_project_root(),
        )
        if result.returncode != 0:
            return False, "Failed to list worktrees"
        
        # Check if our path is in the list
        if worktree_path not in result.stdout:
            return False, f"Worktree not registered in git: {worktree_path}"
        
        return True, None
        
    except Exception as e:
        return False, f"Error validating worktree: {str(e)}"


def validate_worktree(adw_id: str, state) -> Tuple[bool, Optional[str]]:
    """Validate worktree from ADW state.
    
    Convenience wrapper that extracts worktree_path from state and validates it.
    
    Args:
        adw_id: The ADW ID
        state: ADWState instance
        
    Returns:
        Tuple of (is_valid, error_message). If valid, returns (True, None).
        If invalid, returns (False, error_message).
    """
    from adw_modules.utils import setup_logger
    
    worktree_path = state.get("worktree_path")
    if not worktree_path:
        return False, f"No worktree_path in state for ADW ID: {adw_id}"
    
    logger = setup_logger(adw_id, "worktree_ops")
    return validate_worktree_path(worktree_path, logger)


def setup_worktree_environment(worktree_path: str, backend_port: int, logger: logging.Logger) -> None:
    """Set up worktree environment.
    
    Note: Port configuration will be added in the future.
    Currently, ports are tracked in state but not written to .ports.env
    since docker-compose.yml uses hardcoded ports.
    """
    # Port allocation is tracked in state for future use
    # .ports.env file creation will be implemented when docker-compose.yml
    # is updated to use environment variables for ports
    logger.debug(f"Port allocated: Backend={backend_port}")


def get_ports_for_adw(adw_id: str) -> Tuple[int, Optional[int]]:
    """Deterministically assign ports based on ADW ID.
    
    For rococo-sample-backend.
    Returns (backend_port, None).
    """
    try:
        id_chars = ''.join(c for c in adw_id[:8] if c.isalnum())
        index = int(id_chars, 36) % 15
    except ValueError:
        index = hash(adw_id) % 15
    
    backend_port = 9100 + index
    return backend_port, None


def is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('localhost', port))
            return True
    except (socket.error, OSError):
        return False


def find_next_available_ports(adw_id: str, max_attempts: int = 15) -> Tuple[int, Optional[int]]:
    """Find available ports starting from deterministic assignment."""
    base_backend, _ = get_ports_for_adw(adw_id)
    base_index = base_backend - 9100
    
    for offset in range(max_attempts):
        index = (base_index + offset) % 15
        backend_port = 9100 + index
        
        if is_port_available(backend_port):
            return backend_port, None
    
    raise RuntimeError("No available ports in the allocated range")
