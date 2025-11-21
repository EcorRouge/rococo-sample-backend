# TodoMVC Backend

A rococo-based backend for TodoMVC application.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for generating secrets)

## Quick Start

### 1. Setup Environment Variables

Copy `.env.secrets.example` to `.env.secrets`:

```bash
cp .env.secrets.example .env.secrets
```

### 2. Configure Secrets

Edit `.env.secrets` and fill in all required values:


- **Add Mailjet credentials** (provided in project requirements)

Example `.env.secrets`:
```bash

MAILJET_API_KEY=<your-mailjet-key>
MAILJET_API_SECRET=<your-mailjet-secret>
```

### 3. Run the Backend

```bash
./run.sh
```

This will start all required services:
- **API**: Flask application on port 5000
- **PostgreSQL**: Database on port 5432
- **RabbitMQ**: Message queue on port 5672
- **Email Transmitter**: Handles email sending via Mailjet

### 4. Verify Setup

Check that containers are running:
```bash
docker ps
```

Test the API:
```bash
curl http://localhost:5000/api/
```

## API Endpoints

- **Base URL**: `http://localhost:5000`
- **API Documentation**: `http://localhost:5000/api/`
- **Swagger UI**: Available at `/api/` endpoint

### Main Endpoints

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/tasks` - Get user's tasks
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/:id` - Update a task
- `PATCH /api/tasks/:id/complete` - Toggle task completion
- `DELETE /api/tasks/:id` - Delete a task

## Rebuilding Containers

To rebuild Docker images from scratch:

```bash
./run.sh --rebuild true
```

## Troubleshooting

### Containers won't start

- Ensure `.env.secrets` file exists and contains valid values
- Check that ports 5000, 5432, and 5672 are not already in use
- Verify Docker has sufficient resources allocated

### API not accessible

- Check container logs: `docker logs todomvc_api`
- Verify API container is healthy: `docker ps`
- Test API directly: `curl http://localhost:5000/api/`

### Database errors

- Check PostgreSQL logs: `docker logs todomvc_postgres`
- Verify database password matches in `.env.secrets`
- Ensure migrations ran successfully (check container startup logs)

### Email not sending

- Verify Mailjet credentials in `.env.secrets`
- Check email transmitter logs: `docker logs todomvc_email_transmitter`
- Ensure you're using a real email address (not test.com or mailinator)

## Development

The backend uses:
- **Flask** with Flask-RestX for API endpoints
- **Rococo Framework** for models and repositories
- **PostgreSQL** for data storage
- **RabbitMQ** for message queuing
- **Mailjet** for email delivery


