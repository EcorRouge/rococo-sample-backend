#!/usr/bin/env python3
"""
GitHub Webhook Trigger - AI Developer Workflow (ADW)

FastAPI webhook endpoint that receives GitHub issue events and triggers ADW workflows.
Responds immediately to meet GitHub's 10-second timeout by launching workflows
in the background. Supports both standard and isolated workflows.

Usage: python adws/adw_triggers/trigger_webhook.py

Environment Requirements:
- PORT: Server port (default: 8001)
- All workflow requirements (GITHUB_PAT, ANTHROPIC_API_KEY, etc.)
"""

import os
import subprocess
import sys
from typing import Optional
from dotenv import load_dotenv

try:
    from fastapi import FastAPI, Request
    import uvicorn
except ImportError:
    print("ERROR: 'fastapi' and 'uvicorn' packages not installed.")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.utils import make_adw_id, setup_logger, get_safe_subprocess_env
from adw_modules.github import make_issue_comment, ADW_BOT_IDENTIFIER
from adw_modules.workflow_ops import extract_adw_info, AVAILABLE_ADW_WORKFLOWS
from adw_modules.state import ADWState

load_dotenv()

PORT = int(os.getenv("PORT", "8001"))

DEPENDENT_WORKFLOWS = [
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
]

app = FastAPI(
    title="ADW Webhook Trigger", description="GitHub webhook endpoint for ADW"
)

print(f"Starting ADW Webhook Trigger on port {PORT}")


def infer_workflow_from_content(content: str) -> Optional[str]:
    """
    Intelligently infer which ADW workflow to run based on natural language content.
    Returns workflow command name or None if cannot be determined.
    """
    if not content:
        return None
    
    content_lower = content.lower()
    
    # Test-related keywords
    test_keywords = ["test", "coverage", "generate test", "write test", "testing", "uncovered code", "100%", "test coverage", "coverage must reach"]
    if any(keyword in content_lower for keyword in test_keywords):
        return "adw_plan_build_test_iso"
    
    # Documentation keywords
    doc_keywords = ["document", "documentation", "readme", "doc", "write docs"]
    if any(keyword in content_lower for keyword in doc_keywords):
        return "adw_plan_build_document_iso"
    
    # Review keywords
    review_keywords = ["review", "code review", "audit", "inspect"]
    if any(keyword in content_lower for keyword in review_keywords):
        return "adw_plan_build_test_review_iso"
    
    # Bug fix keywords
    bug_keywords = ["fix", "bug", "error", "issue", "broken", "not working"]
    if any(keyword in content_lower for keyword in bug_keywords):
        return "adw_plan_build_test_iso"
    
    # Feature keywords
    feature_keywords = ["feature", "add", "implement", "create", "new", "enhancement"]
    if any(keyword in content_lower for keyword in feature_keywords):
        return "adw_plan_build_test_iso"
    
    # Default: full SDLC for any actionable content
    actionable_keywords = ["do", "make", "build", "generate", "write", "create", "implement"]
    if any(keyword in content_lower for keyword in actionable_keywords):
        return "adw_plan_build_test_iso"
    
    return None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "adw_webhook"}


@app.post("/gh-webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    try:
        event_type = request.headers.get("X-GitHub-Event", "")
        payload = await request.json()

        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")

        print(
            f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}"
        )

        workflow = None
        provided_adw_id = None
        model_set = None
        trigger_reason = ""
        content_to_check = ""

        if event_type == "issues" and action == "opened" and issue_number:
            issue_body = issue.get("body") or ""  # Handle None case
            issue_title = issue.get("title") or ""
            content_to_check = f"{issue_title}\n\n{issue_body}".strip()

            if ADW_BOT_IDENTIFIER in issue_body:
                print(f"Ignoring ADW bot issue to prevent loop")
                workflow = None
            elif content_to_check:
                # Always attempt classification, even without explicit "adw_" commands
                temp_id = make_adw_id()
                extraction_result = extract_adw_info(content_to_check, temp_id)
                if extraction_result.has_workflow:
                    workflow = extraction_result.workflow_command
                    provided_adw_id = extraction_result.adw_id
                    model_set = extraction_result.model_set
                    trigger_reason = f"New issue classified as {workflow}"
                else:
                    # No explicit workflow found, use intelligent inference
                    inferred_workflow = infer_workflow_from_content(content_to_check)
                    if inferred_workflow:
                        workflow = inferred_workflow
                        trigger_reason = f"New issue inferred workflow: {workflow}"
                    elif issue_body or issue_title:
                        # Default to full SDLC workflow for issues with content
                        workflow = "adw_plan_build_test_iso"
                        trigger_reason = f"New issue with content, defaulting to {workflow}"

        elif event_type == "issue_comment" and action == "created" and issue_number:
            comment = payload.get("comment", {})
            comment_body = comment.get("body") or ""  # Handle None case
            content_to_check = comment_body

            print(f"Comment body: '{comment_body}'")

            if ADW_BOT_IDENTIFIER in comment_body:
                print(f"Ignoring ADW bot comment to prevent loop")
                workflow = None
            elif comment_body:
                # Always attempt classification, even without explicit "adw_" commands
                temp_id = make_adw_id()
                extraction_result = extract_adw_info(comment_body, temp_id)
                if extraction_result.has_workflow:
                    workflow = extraction_result.workflow_command
                    provided_adw_id = extraction_result.adw_id
                    model_set = extraction_result.model_set
                    trigger_reason = f"Comment classified as {workflow}"
                else:
                    # No explicit workflow found, use intelligent inference
                    inferred_workflow = infer_workflow_from_content(comment_body)
                    if inferred_workflow:
                        workflow = inferred_workflow
                        trigger_reason = f"Comment inferred workflow: {workflow}"

        if workflow in DEPENDENT_WORKFLOWS:
            if not provided_adw_id:
                print(
                    f"{workflow} is a dependent workflow that requires an existing ADW ID"
                )
                workflow = None
                try:
                    make_issue_comment(
                        str(issue_number),
                        f"❌ Error: `{workflow}` is a dependent workflow that requires an existing ADW ID.\n\n"
                        f"To run this workflow, you must provide the ADW ID in your comment, for example:\n"
                        f"`{workflow} adw-12345678`\n\n"
                        f"The ADW ID should come from a previous workflow run (like `adw_plan_iso` or `adw_patch_iso`).",
                    )
                except Exception as e:
                    print(f"Failed to post error comment: {e}")

        if workflow:
            adw_id = provided_adw_id or make_adw_id()

            if model_set:
                state = ADWState(adw_id)
                state.update(model_set=model_set)
                state.save("webhook_trigger")

            script_name = f"adw_{workflow.replace('adw_', '')}.py"
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), script_name
            )

            if not os.path.exists(script_path):
                print(f"ERROR: Workflow script not found: {script_path}")
                return {"status": "error", "message": f"Workflow script not found: {script_name}"}

            cmd = [sys.executable, script_path, str(issue_number)]
            if provided_adw_id:
                cmd.append(provided_adw_id)

            print(f"INFO: Triggering {workflow} for issue #{issue_number} (ADW ID: {adw_id})")

            subprocess.Popen(
                cmd,
                cwd=os.path.dirname(script_path),
                env=get_safe_subprocess_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            try:
                make_issue_comment(
                    str(issue_number),
                    f"🚀 ADW workflow triggered: `{workflow}` (ADW ID: {adw_id})\n\n"
                    f"Reason: {trigger_reason}",
                )
            except Exception as e:
                print(f"Failed to post trigger comment: {e}")

            return {
                "status": "triggered",
                "workflow": workflow,
                "adw_id": adw_id,
                "issue_number": issue_number,
            }

        return {"status": "ignored", "reason": "No workflow triggered"}

    except Exception as e:
        print(f"ERROR: Exception in webhook handler: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def main():
    """Main entry point."""
    print(f"Starting ADW Webhook Trigger on port {PORT}")
    print(f"Webhook endpoint: http://localhost:{PORT}/gh-webhook")
    print(f"Health check: http://localhost:{PORT}/health")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()

