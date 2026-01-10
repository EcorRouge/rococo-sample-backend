#!/usr/bin/env python3
"""
ADW Cleanup Utility

Clean up isolated ADW worktrees, state files, and agent artifacts to prevent
the trees/ and agents/ directories from growing indefinitely.

Usage:
  python adws/cleanup_worktrees.py [OPTIONS]
  
Options:
  --all              Remove all worktrees and states
  --adw-id <id>      Remove specific ADW ID (worktree + state + artifacts)
  --older-than <N>   Remove items older than N days (default: 7)
  --dry-run          Show what would be removed without actually removing
  --worktrees-only   Only clean worktrees (skip state files and artifacts)
  --states-only      Only clean state files and artifacts (skip worktrees)
  --keep-active      Skip ADW IDs that appear to be actively running
"""

import sys
import os
import subprocess
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Set

def get_project_root() -> str:
    """Get the project root directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def get_worktrees() -> List[Tuple[str, str]]:
    """Get list of all worktrees under trees/ directory.
    
    Returns:
        List of (adw_id, worktree_path) tuples
    """
    try:
    result = subprocess.run(
        ["git", "worktree", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    
    worktrees = []
    for line in result.stdout.strip().split('\n'):
        if 'trees/' in line:
            parts = line.split()
            worktree_path = parts[0]
            # Extract ADW ID from path like trees/bd40afd4
            adw_id = Path(worktree_path).name
            worktrees.append((adw_id, worktree_path))
    
    return worktrees


def get_state_files() -> List[Tuple[str, str]]:
    """Get list of all state files under agents/ directory.
    
    Returns:
        List of (adw_id, state_file_path) tuples
    """
    project_root = get_project_root()
    agents_dir = os.path.join(project_root, "agents")
    
    if not os.path.exists(agents_dir):
        return []
    
    state_files = []
    for adw_id_dir in os.listdir(agents_dir):
        adw_id_path = os.path.join(agents_dir, adw_id_dir)
        if not os.path.isdir(adw_id_path):
            continue
        
        state_file = os.path.join(adw_id_path, "adw_state.json")
        if os.path.exists(state_file):
            state_files.append((adw_id_dir, state_file))
    
    return state_files


def get_agent_artifacts(adw_id: str) -> List[str]:
    """Get list of agent artifact directories for an ADW ID.
    
    Returns:
        List of artifact directory paths
    """
    project_root = get_project_root()
    agents_dir = os.path.join(project_root, "agents", adw_id)
    
    if not os.path.exists(agents_dir):
        return []
    
    artifacts = []
    for item in os.listdir(agents_dir):
        item_path = os.path.join(agents_dir, item)
        # Skip state file and non-directories
        if item == "adw_state.json" or not os.path.isdir(item_path):
            continue
        artifacts.append(item_path)
    
    return artifacts


def get_file_age(file_path: str) -> int:
    """Get age of file/directory in days."""
    if not os.path.exists(file_path):
        return 0
    
    mtime = os.path.getmtime(file_path)
    age_days = (datetime.now().timestamp() - mtime) / (24 * 60 * 60)
    return int(age_days)


def is_active_workflow(adw_id: str, max_age_hours: int = 24) -> bool:
    """Check if an ADW ID appears to be actively running.
    
    A workflow is considered active if:
    - State file was modified in the last N hours (default: 24)
    - Worktree exists and was modified recently
    
    Args:
        adw_id: The ADW ID to check
        max_age_hours: Maximum age in hours to consider "active"
    
    Returns:
        True if workflow appears active
    """
    project_root = get_project_root()
    
    # Check state file
    state_file = os.path.join(project_root, "agents", adw_id, "adw_state.json")
    if os.path.exists(state_file):
        age_hours = get_file_age(state_file) * 24
        if age_hours < max_age_hours:
            return True
    
    # Check worktree
    worktree_path = os.path.join(project_root, "trees", adw_id)
    if os.path.exists(worktree_path):
        age_hours = get_file_age(worktree_path) * 24
        if age_hours < max_age_hours:
            return True
    
    return False


def remove_worktree(worktree_path: str, dry_run: bool = False) -> Tuple[bool, str]:
    """Remove a worktree.
    
    Returns:
        (success, message)
    """
    if dry_run:
        return True, f"[DRY RUN] Would remove worktree: {worktree_path}"
    
    try:
        result = subprocess.run(
            ["git", "worktree", "remove", worktree_path, "--force"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, f"Removed worktree: {worktree_path}"
    except subprocess.CalledProcessError as e:
        # Try manual removal if git worktree remove fails
        if os.path.exists(worktree_path):
            try:
                shutil.rmtree(worktree_path)
                return True, f"Manually removed worktree: {worktree_path}"
            except Exception as manual_error:
                return False, f"Failed to remove {worktree_path}: {e.stderr}, manual cleanup failed: {manual_error}"
        return False, f"Failed to remove {worktree_path}: {e.stderr}"


def remove_state_and_artifacts(adw_id: str, dry_run: bool = False) -> Tuple[bool, str, int]:
    """Remove state file and all agent artifacts for an ADW ID.
    
    Returns:
        (success, message, items_removed_count)
    """
    project_root = get_project_root()
    agents_dir = os.path.join(project_root, "agents", adw_id)
    
    if not os.path.exists(agents_dir):
        return True, f"No agents directory found for {adw_id}", 0
    
    if dry_run:
        artifacts = get_agent_artifacts(adw_id)
        state_file = os.path.join(agents_dir, "adw_state.json")
        count = len(artifacts) + (1 if os.path.exists(state_file) else 0)
        return True, f"[DRY RUN] Would remove {count} item(s) from agents/{adw_id}/", count
    
    removed_count = 0
    errors = []
    
    # Remove agent artifacts
    artifacts = get_agent_artifacts(adw_id)
    for artifact_path in artifacts:
        try:
            shutil.rmtree(artifact_path)
            removed_count += 1
        except Exception as e:
            errors.append(f"Failed to remove {artifact_path}: {e}")
    
    # Remove state file
    state_file = os.path.join(agents_dir, "adw_state.json")
    if os.path.exists(state_file):
        try:
            os.remove(state_file)
            removed_count += 1
        except Exception as e:
            errors.append(f"Failed to remove {state_file}: {e}")
    
    # Remove agents directory if empty
    try:
        if os.path.exists(agents_dir) and not os.listdir(agents_dir):
            os.rmdir(agents_dir)
    except Exception:
        pass  # Ignore errors removing empty directory
    
    if errors:
        return False, f"Partial cleanup: {removed_count} removed, errors: {'; '.join(errors)}", removed_count
    
    return True, f"Removed {removed_count} item(s) from agents/{adw_id}/", removed_count


def main():
    parser = argparse.ArgumentParser(
        description="Clean up ADW worktrees, state files, and agent artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run: see what would be cleaned (older than 7 days)
  python adws/cleanup_worktrees.py --dry-run

  # Clean items older than 14 days
  python adws/cleanup_worktrees.py --older-than 14

  # Clean specific ADW ID
  python adws/cleanup_worktrees.py --adw-id bd40afd4

  # Clean only worktrees (keep state files)
  python adws/cleanup_worktrees.py --worktrees-only --older-than 7

  # Clean only state files (keep worktrees)
  python adws/cleanup_worktrees.py --states-only --older-than 7
        """
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Remove all worktrees and states (use with caution!)"
    )
    parser.add_argument(
        "--adw-id",
        type=str,
        help="Remove specific ADW ID (worktree + state + artifacts)"
    )
    parser.add_argument(
        "--older-than",
        type=int,
        default=7,
        help="Remove items older than N days (default: 7)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing"
    )
    parser.add_argument(
        "--worktrees-only",
        action="store_true",
        help="Only clean worktrees (skip state files and artifacts)"
    )
    parser.add_argument(
        "--states-only",
        action="store_true",
        help="Only clean state files and artifacts (skip worktrees)"
    )
    parser.add_argument(
        "--keep-active",
        action="store_true",
        help="Skip ADW IDs that appear to be actively running (modified in last 24h)"
    )
    
    args = parser.parse_args()
    
    if args.worktrees_only and args.states_only:
        print("Error: --worktrees-only and --states-only cannot be used together")
        return 1
    
    # Get all ADW IDs from worktrees and state files
    worktrees = get_worktrees()
    state_files = get_state_files()
    
    # Combine all ADW IDs
    all_adw_ids: Set[str] = set()
    for adw_id, _ in worktrees:
        all_adw_ids.add(adw_id)
    for adw_id, _ in state_files:
        all_adw_ids.add(adw_id)
    
    if not all_adw_ids:
        print("No ADW worktrees or state files found")
        return 0
    
    # Filter out active workflows if requested
    if args.keep_active:
        active_ids = {adw_id for adw_id in all_adw_ids if is_active_workflow(adw_id)}
        if active_ids:
            print(f"Skipping {len(active_ids)} active workflow(s): {', '.join(sorted(active_ids))}")
            all_adw_ids = all_adw_ids - active_ids
    
    if not all_adw_ids:
        print("No ADW IDs to clean (all are active or none found)")
        return 0
    
    # Determine which ADW IDs to clean
    to_clean: Set[str] = set()
    
    if args.all:
        to_clean = all_adw_ids
        print(f"\n{'[DRY RUN] Would clean' if args.dry_run else 'Cleaning'} all {len(to_clean)} ADW ID(s)...")
    elif args.adw_id:
        if args.adw_id not in all_adw_ids:
            print(f"Error: ADW ID '{args.adw_id}' not found")
            return 1
        to_clean = {args.adw_id}
        print(f"\n{'[DRY RUN] Would clean' if args.dry_run else 'Cleaning'} ADW ID: {args.adw_id}...")
    else:
        # Default: clean items older than specified days
        cutoff_age = args.older_than
        
        for adw_id in all_adw_ids:
            # Check worktree age
            worktree_path = os.path.join(get_project_root(), "trees", adw_id)
            if os.path.exists(worktree_path):
                if get_file_age(worktree_path) >= cutoff_age:
                    to_clean.add(adw_id)
                    continue
            
            # Check state file age
            state_file = os.path.join(get_project_root(), "agents", adw_id, "adw_state.json")
            if os.path.exists(state_file):
                if get_file_age(state_file) >= cutoff_age:
                    to_clean.add(adw_id)
        
        if not to_clean:
            print(f"\nNo ADW IDs older than {args.older_than} days found")
            return 0
        
        print(f"\n{'[DRY RUN] Would clean' if args.dry_run else 'Cleaning'} {len(to_clean)} ADW ID(s) older than {args.older_than} days...")
    
    # Display what will be cleaned
    print("\nADW IDs to clean:")
    for adw_id in sorted(to_clean):
        worktree_path = os.path.join(get_project_root(), "trees", adw_id)
        state_file = os.path.join(get_project_root(), "agents", adw_id, "adw_state.json")
        
        worktree_age = get_file_age(worktree_path) if os.path.exists(worktree_path) else None
        state_age = get_file_age(state_file) if os.path.exists(state_file) else None
        
        info_parts = []
        if worktree_age is not None:
            info_parts.append(f"worktree: {worktree_age}d")
        if state_age is not None:
            info_parts.append(f"state: {state_age}d")
        
        print(f"  - {adw_id}: {', '.join(info_parts) if info_parts else 'no files found'}")
    
    # Perform cleanup
    worktrees_removed = 0
    worktrees_failed = 0
    states_removed = 0
    states_failed = 0
    total_items_removed = 0
    
    for adw_id in sorted(to_clean):
        print(f"\nCleaning {adw_id}...")
        
        # Clean worktrees
        if not args.states_only:
            worktree_path = os.path.join(get_project_root(), "trees", adw_id)
            matching_worktrees = [wt for wt in worktrees if wt[0] == adw_id]
            
            for _, wt_path in matching_worktrees:
                success, message = remove_worktree(wt_path, dry_run=args.dry_run)
                print(f"  {message}")
                if success:
                    worktrees_removed += 1
                else:
                    worktrees_failed += 1
        
        # Clean state files and artifacts
        if not args.worktrees_only:
            success, message, items_count = remove_state_and_artifacts(adw_id, dry_run=args.dry_run)
        print(f"  {message}")
        if success:
                states_removed += 1
                total_items_removed += items_count
        else:
                states_failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    if not args.states_only:
        print(f"  Worktrees: {worktrees_removed} removed, {worktrees_failed} failed")
    if not args.worktrees_only:
        print(f"  States/Artifacts: {states_removed} ADW ID(s) cleaned, {total_items_removed} item(s) removed, {states_failed} failed")
    print(f"{'='*60}")
    
    # Prune stale worktree entries
    if not args.dry_run and worktrees_removed > 0:
        try:
            subprocess.run(["git", "worktree", "prune"], check=False, capture_output=True)
        print("Ran 'git worktree prune' to clean up stale entries")
        except Exception:
            pass
    
    return 0 if (worktrees_failed == 0 and states_failed == 0) else 1


if __name__ == "__main__":
    sys.exit(main())

