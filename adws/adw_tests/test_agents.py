#!/usr/bin/env python3
"""
Test Agent Models - Verify opus and sonnet models work with Claude Code

This script tests that both models can execute a simple prompt through agent.py.
"""

import sys
import os
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.data_types import AgentPromptRequest
from adw_modules.agent import prompt_claude_code
from adw_modules.utils import make_adw_id

load_dotenv()

MODELS = ["sonnet", "opus"]
TEST_PROMPT = """You are a helpful assistant. Please respond to this test with:
1. Confirm you received this message
2. State which model you are (opus or sonnet)
3. Say "Test successful!"

Keep your response brief."""


def test_model(model: str, adw_id: str) -> tuple[bool, str]:
    """Test a specific model and return success status and message."""
    print(f"\n{'='*50}")
    print(f"Testing model: {model}")
    print(f"{'='*50}")

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_file = os.path.join(project_root, "agents", adw_id, f"test_{model}", "raw_output.jsonl")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    request = AgentPromptRequest(
        prompt=TEST_PROMPT,
        adw_id=adw_id,
        agent_name=f"test_{model}",
        model=model,
        dangerously_skip_permissions=True,
        output_file=output_file
    )

    try:
        print(f"Executing prompt for {model}...")
        response = prompt_claude_code(request)

        if response.success:
            print(f"✅ {model} - Success!")
            print(f"Session ID: {response.session_id}")
            print(f"Response preview: {response.output[:200]}...")
            return True, f"{model}: Success"
        else:
            print(f"❌ {model} - Failed!")
            print(f"Error: {response.output}")
            return False, f"{model}: {response.output}"

    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"❌ {model} - Exception!")
        print(error_msg)
        return False, f"{model}: {error_msg}"


def main():
    """Main entry point."""
    print("🧪 Testing ADW Agent Models\n")
    
    adw_id = make_adw_id()
    print(f"Using ADW ID: {adw_id}\n")

    results = {}
    all_passed = True

    for model in MODELS:
        success, message = test_model(model, adw_id)
        results[model] = {"success": success, "message": message}
        if not success:
            all_passed = False

    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)

    for model, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {model}: {result['message']}")

    if all_passed:
        print("\n✅ All model tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some model tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

