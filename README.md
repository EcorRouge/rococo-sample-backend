# rococo-sample-backend
A rococo-based backend for web apps with integrated AI development capabilities.

## Quick Start

### 1. Configure Claude API Key

Create `~/.claude/settings.json` in your home directory:

```json
{
  "apiKeyHelper": "echo your-actual-anthropic-api-key-here"
}
```

### 2. Getting Started

**1. Start Claude Code**

Type the following in your project terminal:

```bash
claude
```

**2. Install dependencies**

Inside Claude Code, run:

```
/install
```

**3. Start services**

```
/start
```

**4. Run tests**

```
/run_tests
```

## Claude Commands

Use these commands **in your IDE terminal with Claude** (works with any IDE):

| Command | Description |
|---------|-------------|
| `/install` | Install all project dependencies |
| `/start` | Start Docker services |
| `/run_tests` | Run test suite with coverage |
| `/feature <description>` | Plan and implement new features |
| `/bug <description>` | Fix bugs with AI assistance |
| `/chore <description>` | Handle chores and maintenance tasks |
| `/test` | Generate tests for uncovered code |
| `/review` | Review code changes |
| `/resolve_failed_test` | Fix failing tests |
| `/document <adw_id>` | Generate feature documentation |

## ADW (AI Developer Workflow) System

ADW automates complete development workflows using isolated git worktrees.

### Quick Setup

**1. Set Environment Variables**

Create `.env` file in `adws/` directory:

```bash
ANTHROPIC_API_KEY=sk-ant-...
SONARQUBE_URL=https://sonarqube.ecortest.com
SONARQUBE_TOKEN=squ_...
SONARQUBE_PROJECT_KEY=rococo-sample-backend  
GITHUB_PAT=ghp_...
CLAUDE_CODE_PATH=claude
```

**2. Install Dependencies**

```bash
# Using python (recommended)
pip install -e ".[adw]"

# Using uv (alternative)
uv pip install -e ".[adw]"
```

**3. Run Workflow**

```bash
# Using python
python adws/adw_plan_build_test_iso.py <issue-number>

# Using uv (alternative)
uv run --extra adw adws/adw_plan_build_test_iso.py <issue-number>
```

**For detailed ADW documentation, see [adws/README.md](adws/README.md)**

### Key Features

- Isolated git worktrees (`trees/<adw_id>/`)
- Support for concurrent instances
- Automated PR creation
- GitHub webhook integration

## Testing

**Run tests:**
```bash
# With Claude in your IDE
/run_tests

# From terminal
PYTHONPATH=.:common:flask pytest tests/ --cov --cov-report=term-missing --cov-branch -v
```

Test environment variables are automatically configured in `tests/conftest.py`. No manual setup required.
