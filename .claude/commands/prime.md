# Prime
> Execute the following sections to understand the codebase then summarize your understanding.

## Run
git ls-files

## Read
- README.md - Project overview
- docker-compose.yml - Service architecture (PostgreSQL, RabbitMQ, Flask API, Email Transmitter)
- ADW_IMPLEMENTATION_SUMMARY.md - Overview of ADW system implementation
- adws/README.md - ADW system documentation and usage
- adws/ENVIRONMENT_VARIABLES.md - Required environment variables for ADW
- .claude/commands/conditional_docs.md - Guide to determine which documentation to read based on the upcoming task

## Understand Project Structure
- `flask/` - Flask application code (main API)
- `common/` - Shared code (models, repositories, services, helpers)
- `services/` - Docker service definitions (postgres, rabbitmq, email_transmitter)
- `tests/` - Pytest test suite
- `adws/` - AI Developer Workflow system
- `specs/` - Specification files
- `agents/` - ADW agent state files (created during workflow execution)