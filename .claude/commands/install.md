# Install & Prime

## Read
- `README.md` - Project overview
- `local.env` (never read `.env.secrets` directly, but understand it's needed)
- `.claude/commands/prime.md` - Execute this to understand the codebase

## Run
- Think through each of these steps to make sure you don't miss anything.
- Verify Docker and Docker Compose are installed: `docker --version` and `docker compose version`
- Install uv (if not already installed): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Verify Python 3.11 or 3.12 is installed (required for Flask app):
  - Check: `python3.11 --version` or `python3.12 --version`
  - If not installed, install via Homebrew: `brew install python@3.11` (or `python@3.12`)
- Install Poetry (if not already installed) for Flask dependencies:
  - `curl -sSL https://install.python-poetry.org | python3 -`
  - Ensure Poetry is in your PATH (usually `$HOME/.local/bin`)
- Configure Poetry to use Python 3.11 or 3.12:
  - `poetry env use python3.11` (preferred) or `poetry env use python3.12`
  - If neither is available, install Python 3.11 first: `brew install python@3.11`
- Install Flask application dependencies:
  - `cd flask && poetry install && cd ..`
- Install test and database dependencies using uv:
  - `uv pip install pytest pytest-cov`
  - `uv pip install "rococo[postgres,mysql]>=1.0.33"`
  - `uv pip install DBUtils psycopg2-binary pymysql bcrypt cryptography`
- Verify all dependencies are installed:
  - Run `uv pip list | grep -E "pytest|rococo|pymysql|dbutils|psycopg2|flask"` to verify dependencies are available
- Set up environment files:
  - Ensure `local.env` exists (it should already be present)
  - If `test.env` doesn't exist and you need it, copy from `local.env` and adjust values

## Report
- Output the work you've just done in a concise bullet point list.
- List all installed dependencies:
  - Flask application dependencies (installed via Poetry)
  - Test dependencies (pytest, pytest-cov)
  - Database dependencies (rococo with postgres/mysql extras, DBUtils, psycopg2-binary, pymysql)
  - Security dependencies (bcrypt, cryptography)
- If `.env.secrets` does not exist, instruct the user to create it with `APP_ENV=local` (or appropriate environment)
- Mention: 'To run tests locally: `PYTHONPATH=.:common:flask uv run pytest tests/ -v`'
- Mention: 'To start services, use the /start command'