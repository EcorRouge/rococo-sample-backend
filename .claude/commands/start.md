# /start - Start Rococo Sample Backend Services

Start the Rococo Sample Backend application using Docker Compose.

## Usage

```
/start [--rebuild]
```

## Behavior

1. Make `run.sh` executable if it's not already: `chmod +x run.sh`
2. Execute `run.sh` to start the Docker Compose services
3. The script will:
   - Read `APP_ENV` from `.env.secrets` file
   - Start Docker Compose services (PostgreSQL, RabbitMQ, API)
   - Optionally rebuild images if `--rebuild` flag is provided

## Arguments

- Optional: `--rebuild` - Rebuild Docker images before starting (default: false)

## Examples

```bash
# Start services without rebuilding
/start

# Start services with rebuild
/start --rebuild
```

## Guidelines

- Ensure `.env.secrets` file exists in the project root
- Ensure the appropriate environment file (e.g., `local.env`, `test.env`) exists
- Verify Docker and Docker Compose are installed and running
- The script will start services in detached mode (`-d` flag)
- Services will be available on configured ports (PostgreSQL: 5432, RabbitMQ: 5672, API: 5000)

## Output

The command should execute `run.sh` and display its output, which includes:
- Confirmation of APP_ENV found in `.env.secrets`
- Status of Docker Compose service startup
- Any errors if services fail to start

