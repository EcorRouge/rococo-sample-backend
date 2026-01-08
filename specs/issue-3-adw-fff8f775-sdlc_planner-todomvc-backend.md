# Feature: TodoMVC-Backend

## Metadata
issue_number: `3`
adw_id: `fff8f775`
issue_json: `{"number": 3, "title": "TodoMVC-Backend", "body": "- email transmitter configuration\r\n- Task API - CRUD Operations\r\n- User edit/set name logic"}`

## Feature Description
This feature implements a complete TodoMVC backend system with three core capabilities: email transmitter configuration for sending task-related notifications, a comprehensive Task API with full CRUD operations for managing todo items, and user profile management allowing users to edit and set their names. The TodoMVC backend serves as a task management system where authenticated users can create, read, update, and delete tasks while receiving email notifications for important task events. This feature extends the existing authentication and user management system to provide task tracking functionality.

## User Story
As a registered user of the Rococo Sample Backend
I want to create, manage, and track my tasks with email notifications
So that I can organize my work and receive timely updates about task changes

## Problem Statement
The current backend system provides authentication and user management but lacks task management capabilities. Users cannot create or track tasks, there is no mechanism for sending task-related email notifications, and users cannot update their profile names after registration. This limits the application's usefulness as a productivity tool and prevents users from personalizing their experience.

## Solution Statement
Implement a complete TodoMVC backend by creating a Task model and repository in the common layer, adding Task CRUD API endpoints in the Flask application with proper authentication, configuring the email transmitter service to send task-related notifications (creation, completion, deletion), and extending the Person API to support name editing. The solution follows the existing architectural patterns using the rococo framework's repository pattern, versioned models with audit trails, and RabbitMQ-based email messaging.

## Relevant Files
Use these files to implement the feature:

### Existing Files

- `common/models/__init__.py` - Import module for models, needs Task model import
- `common/models/person.py` - Person model, reference for creating Task model structure
- `common/models/email.py` - Email model, reference for model validation patterns
- `common/repositories/__init__.py` - Import module for repositories, needs TaskRepository import
- `common/repositories/base.py` - Base repository with PostgreSQLRepository pattern
- `common/repositories/person.py` - Person repository, reference for Task repository structure
- `common/repositories/factory.py` - Repository factory with RepoType enum, needs Task repository registration
- `common/services/__init__.py` - Import module for services, needs TaskService import
- `common/services/person.py` - Person service, reference for Task service structure
- `common/services/email.py` - Email service for sending messages
- `common/tasks/send_message.py` - RabbitMQ message sender for email notifications
- `flask/app/__init__.py` - Flask app initialization, registers API namespaces
- `flask/app/views/__init__.py` - View initialization module, needs task_api registration
- `flask/app/views/person.py` - Person API endpoints, needs name edit endpoint
- `flask/app/views/auth.py` - Authentication API, reference for endpoint structure and patterns
- `flask/app/helpers/response.py` - Response helpers for API responses
- `flask/app/helpers/decorators.py` - Contains @login_required decorator for authentication
- `flask/pyproject.toml` - Python dependencies configuration
- `docker-compose.yml` - Service configuration including email transmitter
- `services/email_transmitter/config.json` - Email templates configuration, needs task event templates
- `local.env` - Environment variables for local development
- `tests/conftest.py` - Test configuration and fixtures
- `tests/test_decorators.py` - Decorator tests, reference for testing patterns
- `tests/test_factory.py` - Repository factory tests, needs Task repository tests

### New Files

- `common/models/task.py` - Task model with title, description, completed status, person_id
- `common/repositories/task.py` - Task repository for database operations
- `common/services/task.py` - Task service with business logic
- `flask/app/views/task.py` - Task API endpoints for CRUD operations
- `flask/app/migrations/0000000006_0000000005_migration.py` - Database migration for task table
- `tests/test_task_model.py` - Unit tests for Task model
- `tests/test_task_repository.py` - Unit tests for Task repository
- `tests/test_task_service.py` - Unit tests for Task service
- `tests/test_task_api.py` - Integration tests for Task API endpoints
- `tests/test_person_name_edit.py` - Tests for person name editing functionality

## Implementation Plan
### Phase 1: Foundation
Create the foundational database schema and models for tasks. This includes designing the task table structure with proper audit trails following the rococo framework patterns (entity_id, version, previous_version, active, changed_by_id, changed_on). Create the Task model class inheriting from rococo base models, and implement the database migration script to create both the task and task_audit tables. This phase establishes the data layer foundation for all subsequent work.

### Phase 2: Core Implementation
Build the repository, service, and API layers for task management. Create the TaskRepository with CRUD methods, register it in the repository factory, implement the TaskService with business logic for task operations, and build the Flask REST API endpoints for creating, reading, updating, and deleting tasks. All endpoints must be protected with the @login_required decorator and follow the existing response format patterns. Implement proper error handling and input validation throughout.

### Phase 3: Integration
Integrate email notifications for task events and add user name editing functionality. Configure email templates in the email transmitter config for task creation, completion, and deletion events. Implement the email sending logic in the TaskService using RabbitMQ messaging. Add PUT endpoint to the Person API for updating user names (first_name and last_name). Ensure all components work together seamlessly with comprehensive integration tests.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Task Model and Migration
- Create `common/models/task.py` with Task model inheriting from rococo base model
- Define fields: title (varchar 255), description (text, nullable), completed (boolean default false), due_date (timestamp, nullable), person_id (varchar 32, foreign key)
- Add model validation for required fields and field lengths
- Create migration file `flask/app/migrations/0000000006_0000000005_migration.py`
- Define upgrade() to create task and task_audit tables with proper indexes
- Define downgrade() to drop both tables
- Add Task model import to `common/models/__init__.py`
- Write unit tests in `tests/test_task_model.py` for model validation and field requirements

### 2. Create Task Repository
- Create `common/repositories/task.py` with TaskRepository class
- Inherit from BaseRepository and set MODEL = Task
- Implement custom query method `get_tasks_by_person_id(person_id)` for filtering user's tasks
- Implement `get_completed_tasks(person_id)` and `get_pending_tasks(person_id)` helper methods
- Add TaskRepository import to `common/repositories/__init__.py`
- Register TaskRepository in `common/repositories/factory.py` RepoType enum as TASK
- Add TASK to the _repositories dictionary in RepositoryFactory
- Write unit tests in `tests/test_task_repository.py` for all repository methods

### 3. Create Task Service
- Create `common/services/task.py` with TaskService class
- Initialize with config and get TaskRepository from factory
- Implement `create_task(person_id, title, description, due_date)` method
- Implement `get_task_by_id(task_id, person_id)` with ownership verification
- Implement `get_all_tasks_for_user(person_id)` method
- Implement `update_task(task_id, person_id, title, description, completed, due_date)` with ownership check
- Implement `delete_task(task_id, person_id)` with ownership verification
- Implement `mark_task_completed(task_id, person_id)` convenience method
- Add TaskService import to `common/services/__init__.py`
- Write unit tests in `tests/test_task_service.py` for all service methods including authorization checks

### 4. Configure Email Transmitter for Task Events
- Update `services/email_transmitter/config.json` to add task event templates
- Add TASK_CREATED event with subject "New Task: {{var:task_title}}" and template configuration
- Add TASK_COMPLETED event with subject "Task Completed: {{var:task_title}}" and template configuration
- Add TASK_DELETED event with subject "Task Deleted: {{var:task_title}}" and template configuration
- Document required template variables in comments: recipient_name, task_title, task_description, task_due_date

### 5. Integrate Email Notifications in Task Service
- Import EmailService and MessageSender in `common/services/task.py`
- In `create_task()`, send TASK_CREATED email notification via RabbitMQ after successful creation
- In `mark_task_completed()`, send TASK_COMPLETED email notification after marking complete
- In `delete_task()`, send TASK_DELETED email notification before deletion
- Handle email sending failures gracefully with proper logging (don't fail the task operation)
- Ensure email messages include all required template variables

### 6. Create Task API Endpoints
- Create `flask/app/views/task.py` with task_api namespace
- Implement POST /task endpoint to create new task (requires @login_required)
- Implement GET /task/<task_id> endpoint to retrieve single task with ownership verification
- Implement GET /task endpoint to list all tasks for authenticated user with optional ?completed filter
- Implement PUT /task/<task_id> endpoint to update task (title, description, completed, due_date)
- Implement DELETE /task/<task_id> endpoint to delete task with ownership verification
- Use parse_request_body and validate_required_fields helpers from app.helpers.response
- Return proper success/failure responses using get_success_response and get_failure_response
- Add Flask-RESTX @api.expect decorators for request body documentation
- Add task_api import and registration in `flask/app/views/__init__.py`
- Write integration tests in `tests/test_task_api.py` for all endpoints including auth checks

### 7. Implement User Name Edit Functionality
- Update `common/services/person.py` to add `update_person_name(person_id, first_name, last_name)` method
- Validate that first_name and last_name are non-empty strings
- Use PersonRepository.save() to persist name changes
- Add PUT /person/me endpoint in `flask/app/views/person.py` for name updates
- Protect endpoint with @login_required decorator
- Parse and validate first_name and last_name from request body
- Return updated person object in success response
- Write tests in `tests/test_person_name_edit.py` for validation and authorization

### 8. Run Database Migrations
- Start PostgreSQL service via Docker Compose if not already running
- Run migration script to create task tables: execute migration 0000000006
- Verify task and task_audit tables exist in database with correct schema
- Verify indexes are created correctly
- Test rollback functionality with downgrade() method

### 9. Run Validation Commands
- Execute `pytest tests/ -v` to run all tests and validate zero regressions
- Start all services with Docker Compose: `docker-compose up -d`
- Verify email transmitter service is running and connected to RabbitMQ
- Test task creation via API: POST /task with valid auth token
- Test task retrieval: GET /task to list user's tasks
- Test task update: PUT /task/<id> to modify task fields
- Test task completion: PUT /task/<id> with completed=true
- Test task deletion: DELETE /task/<id>
- Test person name update: PUT /person/me with new first_name and last_name
- Verify email notifications are sent to RabbitMQ queue for task events
- Check logs for any errors or warnings
- Validate all API endpoints return proper success/error responses

## Testing Strategy
### Unit Tests
- **Task Model Tests**: Validate required fields (title, person_id), field length constraints (title max 255 chars), default values (completed=false), and proper inheritance from rococo base model
- **Task Repository Tests**: Mock database adapter, test CRUD operations, verify get_tasks_by_person_id filters correctly, test get_completed_tasks and get_pending_tasks, verify audit trail creation
- **Task Service Tests**: Mock repository and email service, test create_task with valid/invalid data, verify ownership checks in get/update/delete operations, test email notification integration, validate mark_task_completed logic
- **Person Service Tests**: Test update_person_name with valid names, verify validation for empty strings, test persistence through repository
- **Task API Tests**: Mock authentication, test all endpoints with valid/invalid auth tokens, verify request parsing and validation, test ownership verification on protected resources, validate response formats

### Edge Cases
- Creating task with title exceeding 255 characters (should fail validation)
- Updating task owned by different user (should return 403 Forbidden)
- Accessing task with invalid task_id (should return 404 Not Found)
- Creating task without authentication (should return 401 Unauthorized)
- Deleting already deleted task (should handle gracefully)
- Updating person name with empty strings (should fail validation)
- Email transmitter service down during task creation (task should still be created, email failure logged)
- Concurrent task updates by same user (verify audit trail handles versioning)
- Filtering tasks with invalid completed parameter (should handle gracefully)
- Setting due_date in the past (should allow for historical task tracking)

## Acceptance Criteria
- Task model created with proper fields and validation following rococo patterns
- Database migration successfully creates task and task_audit tables with indexes
- TaskRepository provides CRUD operations and person-specific queries
- TaskService implements all business logic with proper authorization checks
- Task API endpoints (POST, GET, PUT, DELETE) are functional and secured with @login_required
- Email transmitter configuration includes task event templates (TASK_CREATED, TASK_COMPLETED, TASK_DELETED)
- Task creation, completion, and deletion trigger email notifications via RabbitMQ
- Users can update their first_name and last_name through PUT /person/me endpoint
- All endpoints return consistent response formats using get_success_response/get_failure_response
- Comprehensive unit tests achieve high code coverage for all new components
- Integration tests verify end-to-end task workflow with authentication
- Zero regressions in existing test suite (all tests pass)
- Email notifications contain correct task information and recipient details
- Ownership verification prevents users from accessing other users' tasks
- API documentation generated via Flask-RESTX for all new endpoints

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `docker-compose up -d postgres rabbitmq` - Start required services for testing
- `docker-compose exec api python -c "from flask.app.migrations import run_migrations; run_migrations()"` - Run database migrations
- `pytest tests/test_task_model.py -v` - Validate Task model tests pass
- `pytest tests/test_task_repository.py -v` - Validate Task repository tests pass
- `pytest tests/test_task_service.py -v` - Validate Task service tests pass
- `pytest tests/test_task_api.py -v` - Validate Task API endpoint tests pass
- `pytest tests/test_person_name_edit.py -v` - Validate person name edit tests pass
- `pytest tests/ -v` - Run full test suite to validate zero regressions
- `docker-compose up -d` - Start all services including email transmitter
- `docker-compose logs email_transmitter | grep -i "connected"` - Verify email transmitter connected to RabbitMQ
- `curl -X POST http://localhost:5000/auth/login -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"test123"}'` - Get auth token for manual testing
- `curl -X POST http://localhost:5000/task -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"title":"Test Task","description":"Testing task creation"}'` - Test task creation
- `curl -X GET http://localhost:5000/task -H "Authorization: Bearer <token>"` - Test task listing
- `curl -X PUT http://localhost:5000/task/<task_id> -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"completed":true}'` - Test task completion
- `curl -X PUT http://localhost:5000/person/me -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"first_name":"John","last_name":"Doe"}'` - Test name update
- `docker-compose exec postgres psql -U rococo_sample_user -d rococo-sample-db -c "SELECT * FROM task;"` - Verify task records in database
- `docker-compose exec postgres psql -U rococo_sample_user -d rococo-sample-db -c "SELECT * FROM task_audit;"` - Verify audit trail creation

## Notes
- The Task model follows rococo framework conventions with entity_id, version, and audit trail
- All task operations require authentication via JWT tokens in Authorization header
- Email notifications are asynchronous via RabbitMQ and should not block task operations
- The email transmitter service requires mailjet credentials in .env.secrets file
- Task ownership is enforced through person_id field and verified in all service methods
- The completed field allows filtering tasks by completion status via query parameters
- Due dates are optional and stored as timestamps for potential future sorting/filtering
- Person name updates only modify first_name and last_name, not email or other fields
- All database operations use the repository pattern with connection pooling from Flask context
- The @login_required decorator automatically injects person object into endpoint methods
- Follow existing code patterns from auth.py and person.py for consistency
- No decorators should be used in service layer (business logic should be decorator-free)
- Test fixtures in conftest.py provide database and authentication mocks for testing
- Email template IDs in config.json must be created in Mailjet dashboard before use
- Consider using `uv add` in flask directory if any new Python packages are needed
