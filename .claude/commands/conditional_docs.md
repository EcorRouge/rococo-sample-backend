# Conditional Documentation Guide

This prompt helps you determine what documentation you should read based on the specific changes you need to make in the codebase. Review the conditions below and read the relevant documentation before proceeding with your task.

## Instructions
- Review the task you've been asked to perform
- Check each documentation path in the Conditional Documentation section
- For each path, evaluate if any of the listed conditions apply to your task
  - IMPORTANT: Only read the documentation if any one of the conditions match your task
- IMPORTANT: You don't want to excessively read documentation. Only read the documentation if it's relevant to your task.

## Conditional Documentation

- README.md
  - Conditions:
    - When first understanding the project structure
    - When you want to learn the commands to start or stop services
    - When understanding the overall project architecture

- docker-compose.yml
  - Conditions:
    - When working with Docker services (PostgreSQL, RabbitMQ, API, Email Transmitter)
    - When configuring service dependencies or networking
    - When troubleshooting service startup or connectivity issues
    - When modifying service ports or environment variables

- ADW_IMPLEMENTATION_SUMMARY.md
  - Conditions:
    - When understanding the ADW system architecture
    - When working with ADW workflows or modules
    - When troubleshooting ADW-related issues

- adws/README.md
  - Conditions:
    - When operating in the `adws/` directory
    - When working with ADW workflows (`adw_plan_iso.py`, `adw_build_iso.py`, `adw_test_iso.py`)
    - When setting up or configuring ADW system
    - When understanding ADW workflow execution

- adws/ENVIRONMENT_VARIABLES.md
  - Conditions:
    - When setting up ADW environment
    - When configuring SonarQube, GitHub, or Anthropic API integration
    - When troubleshooting ADW authentication or API connection issues

- adws/SONARQUBE_INTEGRATION.md
  - Conditions:
    - When working with SonarQube API integration
    - When fetching code coverage data
    - When troubleshooting SonarQube connection or coverage reporting

- adws/AGENTS_FOLDER_EXPLANATION.md
  - Conditions:
    - When understanding ADW state persistence
    - When debugging ADW workflow execution
    - When working with agent state files

- flask/pyproject.toml
  - Conditions:
    - When adding or modifying Flask application dependencies
    - When understanding Python package requirements
    - When troubleshooting dependency conflicts

- local.env (or test.env, etc.)
  - Conditions:
    - When configuring application environment variables
    - When setting up database, RabbitMQ, or email service connections
    - When troubleshooting service configuration issues
