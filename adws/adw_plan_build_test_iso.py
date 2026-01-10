#!/usr/bin/env python3
"""
ADW Plan Build Test Iso - Combined workflow for planning, building, and testing

Usage:
  uv run adws/adw_plan_build_test_iso.py <issue-number> [adw-id]
  # or: python3 adws/adw_plan_build_test_iso.py <issue-number> [adw-id]  # with venv activated

This script orchestrates:
1. Planning (adw_plan_iso.py)
2. Building (adw_build_iso.py)
3. Testing (adw_test_iso.py)
"""

import sys
import subprocess
import os
from dotenv import load_dotenv

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    """Main entry point."""
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: uv run adws/adw_plan_build_test_iso.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Step 1: Plan
    print("\n" + "="*60)
    print("STEP 1: Planning")
    print("="*60 + "\n")
    plan_cmd = [sys.executable, os.path.join(SCRIPT_DIR, "adw_plan_iso.py"), issue_number]
    if adw_id:
        plan_cmd.append(adw_id)
    
    result = subprocess.run(plan_cmd)
    if result.returncode != 0:
        print(f"\n❌ Planning failed with exit code {result.returncode}")
        sys.exit(1)

    # Extract ADW ID from state if not provided
    if not adw_id:
        # Find the ADW ID created by Step 1 by searching for state files with this issue number
        import json
        import glob
        from adw_modules.state import ADWState
        
        agents_dir = os.path.join(os.path.dirname(SCRIPT_DIR), "agents")
        adw_id = None
        
        if os.path.exists(agents_dir):
            # Get all state files, sorted by modification time (newest first)
            state_files = []
            for agent_id in os.listdir(agents_dir):
                state_path = os.path.join(agents_dir, agent_id, "adw_state.json")
                if os.path.exists(state_path):
                    state_files.append((state_path, os.path.getmtime(state_path)))
            
            # Sort by modification time (newest first)
            state_files.sort(key=lambda x: x[1], reverse=True)
            
            # Find the most recent state file for this issue number
            for state_path, _ in state_files:
                try:
                    with open(state_path, 'r') as f:
                        state_data = json.load(f)
                        if state_data.get("issue_number") == issue_number:
                            adw_id = os.path.basename(os.path.dirname(state_path))
                            print(f"Found ADW ID from Step 1: {adw_id}")
                            break
                except (json.JSONDecodeError, KeyError, OSError):
                    continue
        
        if not adw_id:
            print(f"❌ Error: Could not find ADW ID for issue #{issue_number} after planning step")
            sys.exit(1)

    # Step 2: Build
    print("\n" + "="*60)
    print("STEP 2: Building")
    print("="*60 + "\n")
    build_cmd = [sys.executable, os.path.join(SCRIPT_DIR, "adw_build_iso.py"), issue_number, adw_id]
    
    result = subprocess.run(build_cmd)
    if result.returncode != 0:
        print(f"\n❌ Building failed with exit code {result.returncode}")
        sys.exit(1)

    # Step 3: Test
    print("\n" + "="*60)
    print("STEP 3: Testing")
    print("="*60 + "\n")
    test_cmd = [sys.executable, os.path.join(SCRIPT_DIR, "adw_test_iso.py"), issue_number, adw_id]
    
    result = subprocess.run(test_cmd)
    if result.returncode != 0:
        print(f"\n⚠️  Testing completed with some failures (exit code {result.returncode})")
        print("Review the test results in the GitHub issue comments")
    else:
        print("\n✅ All steps completed successfully!")


if __name__ == "__main__":
    main()

