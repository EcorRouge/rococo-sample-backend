# Prepare Application

Setup the application for review or testing.

## Variables

PORT: If `.ports.env` exists, read BACKEND_PORT from it, otherwise default to 5000

## Setup

1. Check if `.ports.env` exists:
   - If it exists, source it and use `BACKEND_PORT` for the PORT variable
   - If not, use default PORT: 5000

2. Start Docker services (if needed):
   - Run `docker-compose up -d` to start PostgreSQL, RabbitMQ, and other services
   - Wait for services to be healthy

3. Start the Flask application:
   - IMPORTANT: Make sure the application is running on a background process
   - Navigate to the flask directory: `cd flask`
   - Start the application: `python main.py` or use the run script
   - The application should use PORT from `.ports.env` if it exists
   - Use appropriate stop scripts to stop the application

4. Verify the application is running:
   - The API should be accessible at http://localhost:PORT (where PORT is from `.ports.env` or default 5000)
   - Check health endpoint if available

Note: Read `README.md` and `run.sh` for more information on how to start, stop and reset services.

