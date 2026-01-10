#!/usr/bin/env python3
"""
ADW Plan Build Iso - Compositional workflow for isolated planning and building

Usage: uv run adws/adw_plan_build_iso.py <issue-number> [adw-id]

This script runs:
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_build_iso.py - Implementation phase (isolated)

The scripts are chained together via persistent state (adw_state.json).
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id
from adw_modules.error_handling import ADWError


def main():
    """Main entry point."""
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: uv run adws/adw_plan_build_iso.py <issue-number> [adw-id]")
        print("\nThis runs the isolated plan and build workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    temp_logger = None
    adw_id = ensure_adw_id(issue_number, adw_id, temp_logger)
    print(f"Using ADW ID: {adw_id}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run isolated plan with the ADW ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_plan_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print(f"❌ Isolated plan phase failed with exit code {plan.returncode}")
        sys.exit(plan.returncode)

    # Run isolated build with the ADW ID
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_build_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print(f"❌ Isolated build phase failed with exit code {build.returncode}")
        sys.exit(build.returncode)

    print(f"\n=== ISOLATED WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")


if __name__ == "__main__":
    main()

