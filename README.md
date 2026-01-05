# rococo-sample-backend
A rococo-based backend for web apps

---

## Claude Code Setup

This project includes Claude Code configuration for AI-assisted development.

---

## Prerequisites

* Claude Code must be installed. Refer to the [Claude Code setup guide](https://code.claude.com/docs/en/setup) for installation instructions.
* Replace the placeholder Anthropic API key in `.claude/anthropic_key.sh` with your real key
* Make the file executable:

  ```bash
  chmod +x .claude/anthropic_key.sh
  ```

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
