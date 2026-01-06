# rococo-sample-backend
A rococo-based backend for web apps

---

## Prerequisites

* Claude Code must be installed. Refer to the [Claude Code setup guide](https://code.claude.com/docs/en/setup) for installation instructions.

---

## Claude IDE Configuration

### Setting Up Anthropic API Key

To use Claude IDE features, configure your Anthropic API key in your **user profile directory** (not in the project). This avoids committing keys to the repository and works across all projects.

**Step 1: Create or edit `~/.claude/settings.json`** in your home directory:

- **macOS/Linux**: `~/.claude/settings.json` (e.g., `/Users/YourUsername/.claude/settings.json`)
- **Windows**: `%USERPROFILE%\.claude\settings.json` (e.g., `C:\Users\YourUsername\.claude\settings.json`)

**Step 2: Add this configuration** (replace with your actual API key):

```json
{
  "apiKeyHelper": "echo sk-ant-your-actual-anthropic-api-key-here"
}
```

**Example:**
```json
{
  "apiKeyHelper": "echo sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Quick Setup Commands:**

```bash
# macOS/Linux
mkdir -p ~/.claude
nano ~/.claude/settings.json  # or use your preferred editor

# Windows (PowerShell)
New-Item -ItemType Directory -Path "$env:USERPROFILE\.claude" -Force
notepad "$env:USERPROFILE\.claude\settings.json"
```

**Benefits:**
- ✅ Works on Windows, Mac, and Linux
- ✅ Configure once, works for all projects
- ✅ No risk of committing keys to version control
- ✅ Claude IDE automatically uses this configuration

**Note:** After configuring, restart Claude IDE if it's already running. This configuration applies globally and will be used for all your Claude IDE projects.

---

## Getting Started

### 1. Start Claude Code

Type the following in your project terminal:

```bash
claude
```

---

### 2. Install dependencies

Inside Claude Code, run:

```
/install
```

---

### 3. Start services

```
/start
```

---

### 4. Run tests

```
/run_tests
```

---

## Available Commands

```
/install     - Install all dependencies
/start       - Start Docker services
/run_tests   - Execute test suite
/test        - Generate tests for uncovered code
/feature     - Development workflow
/bug         - Development workflow
/chore       - Development workflow
/review      - Code review
/implement   - Code implementation
```

Type the command in Claude Code chat to use it.

---
