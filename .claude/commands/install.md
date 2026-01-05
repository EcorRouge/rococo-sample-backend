# Install & Prime

## Read
- `README.md` - Project overview
- `adws/README.md` - ADW system documentation
- `adws/ENVIRONMENT_VARIABLES.md` - Required environment variables
- `local.env` (never read `.env.secrets` directly, but understand it's needed)
- `.claude/commands/prime.md` - Execute this to understand the codebase

## Run
- Think through each of these steps to make sure you don't miss anything.
- Verify Docker and Docker Compose are installed: `docker --version` and `docker compose version`
- Install uv (if not already installed): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Install Python dependencies for the project using uv:
  - `uv sync` (installs all dependencies from root pyproject.toml, including test dependencies like pytest, rococo[postgres,mysql], DBUtils, psycopg2-binary, pymysql, etc.)
  - OR if you prefer to install ADW dependencies separately: `uv pip install -r adws/requirements.txt`
- Install Poetry (if not already installed) for Flask dependencies:
  - `curl -sSL https://install.python-poetry.org | python3 -`
  - Ensure Poetry is in your PATH (usually `$HOME/.local/bin`)
- Install Flask application dependencies:
  - `cd flask && poetry install && cd ..`
- Verify all test dependencies are installed:
  - Run `uv pip list | grep -E "pytest|rococo|pymysql|dbutils|psycopg2"` to verify test dependencies are available
- Set up environment files:
  - Ensure `local.env` exists (it should already be present)
  - If `test.env` doesn't exist and you need it, copy from `local.env` and adjust values
- Make `run.sh` executable: `chmod +x run.sh`
- Start Docker services using `run.sh`:
  - Run `./run.sh` to start services normally
  - Or run `./run.sh --rebuild true` to rebuild Docker images before starting
  - Services will start in detached mode (PostgreSQL on 5432, RabbitMQ on 5672, API on 5000)
- Verify services are running:
  - `docker compose ps` - should show all services as running
  - `curl http://localhost:5000/health` (if health endpoint exists) or check logs: `docker compose logs api`

## Report
- Output the work you've just done in a concise bullet point list.
- Mention the services that are now running:
  - PostgreSQL database on port 5432
  - RabbitMQ message broker on port 5672
  - Flask API on port 5000
  - Email transmitter service
- If `.env.secrets` does not exist, instruct the user to create it with `APP_ENV=local` (or appropriate environment)
- If ADW environment variables are not set, instruct the user to:
  - Review `adws/ENVIRONMENT_VARIABLES.md` for required variables
  - Set up `ANTHROPIC_API_KEY`, `SONARQUBE_URL`, `SONARQUBE_TOKEN`, etc.
  - Run health check: `python adws/adw_tests/health_check.py`
- Mention: 'To setup your ADW Agent, be sure to configure GitHub integration:
  - Fork the repository if you haven't already
  - Set git remote: `git remote set-url origin <your-forked-repo-url>`
  - Authenticate GitHub CLI: `gh auth login`
  - Set `GITHUB_REPO_URL` environment variable (or verify auto-detection works)
- Mention: 'To view code coverage on SonarQube, visit: https://sonarqube.ecortest.com/dashboard?id=rococo-sample-backend'
- Mention: 'To run tests locally: `PYTHONPATH=.:common:flask uv run pytest tests/ -v` or `uv run pytest tests/ -v`'
- Mention: 'To stop services: `docker compose down`'
- Mention: 'To view logs: `docker compose logs -f [service_name]` (e.g., `docker compose logs -f api`)'
