````md
# AI Developer Workflow (ADW) System

ADW automates software development using isolated git worktrees.


## Quick Start

### 1. Set Environment Variables

Create `.env` file in `adws/` directory:

```bash
ANTHROPIC_API_KEY=sk-ant-...
SONARQUBE_URL=https://sonarqube.ecortest.com
SONARQUBE_TOKEN=squ_...
SONARQUBE_PROJECT_KEY=rococo-sample-backend  
GITHUB_PAT=ghp_...
CLAUDE_CODE_PATH=claude
````

Or export in shell:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SONARQUBE_URL=https://sonarqube.ecortest.com
export SONARQUBE_TOKEN=squ_...
export SONARQUBE_PROJECT_KEY=rococo-sample-backend  
export GITHUB_PAT=ghp_...
export CLAUDE_CODE_PATH=claude
```

### 2. Install Prerequisites

```bash
# GitHub CLI 
brew install gh  # macOS
gh auth login

# Python dependencies
pip install -e ".[adw]"  # From project root with venv activated

# Or using uv
uv run --extra adw adws/adw_plan_iso.py 123 
```

### 3. Run Workflows

## Workflow Process

ADW workflows start with a GitHub issue. You have two options:

### Option 1: Automatic Webhook Dispatch

1. **Create a GitHub issue** with title and body on your repository
2. **In the issue body**, describe what you want the AI to accomplish
3. **In the same issue body**, specify the workflow to be triggered (example: `adw_plan_build_test_iso`)
4. The webhook enqueues the workflow for execution by the ADW worker (see below on how to configure the webhook)

**Example:**

* Create issue #123: "Add tests for uncovered code"
* In the issue body describe what you want and include:

  ```
  Workflow: adw_plan_build_test_iso
  ```
* The workflow runs automatically

### Option 2: Manual Execution

1. **Create a GitHub issue** on your repository (or use an existing one)
2. **Get the issue number** from the GitHub issue URL (e.g., `#123`)
3. **Run the workflow manually** from your terminal:

```bash
# Using python
python adws/adw_plan_build_test_iso.py 123

# Using uv (alternative)
uv run --extra adw adws/adw_plan_build_test_iso.py 123
```

**Complete workflow example:**

```bash
# Single command - handles everything automatically
python adws/adw_plan_build_test_iso.py 123
```

**Manual step-by-step:**

```bash
# Step 1: Create plan and worktree
python adws/adw_plan_iso.py 123  # Returns ADW ID (e.g., a1b2c3d4)

# Step 2: Build (requires ADW ID from step 1)
python adws/adw_build_iso.py 123 a1b2c3d4

# Step 3: Test (requires ADW ID from step 1)
python adws/adw_test_iso.py 123 a1b2c3d4
```

## Workflow Scripts

**Entry Point Workflows** (can run independently):

* `adw_plan_iso.py` - Create plan and isolated worktree
* `adw_patch_iso.py` - Create patch plan and worktree

**Dependent Workflows** (require ADW ID):

* `adw_build_iso.py <issue-number> <adw-id>` - Implement code
* `adw_test_iso.py <issue-number> <adw-id>` - Run tests
* `adw_document_iso.py <issue-number> <adw-id>` - Generate docs

**Compositional Workflows** (recommended - handle dependencies automatically):

* `adw_plan_build_test_iso.py <issue-number>` - Complete workflow
* `adw_plan_build_iso.py <issue-number>` - Plan + build
* `adw_plan_build_document_iso.py <issue-number>` - Full workflow with docs

**Usage:**

```bash
# Using python (with venv activated)
python adws/<script>.py <args>

# Using uv (alternative)
uv run --extra adw adws/<script>.py <args>
```

## Key Concepts

* **ADW ID**: Unique 8-character identifier tracks all workflow phases
* **Isolated Worktrees**: Each workflow runs in `trees/<adw_id>/` with complete isolation
* **Port Allocation**: Unique ports (9100-9114) per instance
* **State Management**: Persistent state in `agents/<adw_id>/adw_state.json`

## GitHub Webhook Setup

````md
**1. Start webhook listener:**
```bash
python adws/adw_triggers/trigger_webhook.py
````

**2. Create ngrok tunnel:**

```bash
ngrok http 8001
```

**3. Configure GitHub webhook:**

* Repository → Settings → Webhooks → Add webhook
* Payload URL: `https://your-ngrok-url.ngrok-free.app/gh-webhook`
* Content type: `application/json`
* Events: Select **Issues** and **Issue comments**

**4. Trigger workflows:**

* Create a GitHub issue with a title and body
* In the body, specify what the AI should do and include the workflow name (e.g. `adw_plan_build_test_iso`)

````

## Worktree Cleanup

```bash
# Remove worktrees older than 7 days (default)
python adws/cleanup_worktrees.py

# Dry run
python adws/cleanup_worktrees.py --dry-run

# Remove specific ADW ID
python adws/cleanup_worktrees.py --adw-id <adw-id>

# Remove all (use with caution!)
python adws/cleanup_worktrees.py --all
````

## Troubleshooting

**"No worktree found"**

* Run an entry point workflow first: `python adws/adw_plan_iso.py <issue-number>`

**"Port already in use"**

* ADW will automatically find alternative ports

**"trees/ or agents/ directory growing too large"**

* Run cleanup: `python adws/cleanup_worktrees.py --older-than 7`

**"Webhook not receiving events"**

* Check webhook server: `curl http://localhost:8001/health`
* Verify GitHub webhook deliveries in repository settings
