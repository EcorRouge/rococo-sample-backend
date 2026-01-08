# Chore: Generate tests for uncovered code to reach 100% coverage

## Metadata
issue_number: `5`
adw_id: `f754f9e8`
issue_json: `{"number": 5, "title": "Generate tests", "body": "adw_plan_build_test_iso.py\n\nGenerate test for uncovered code. The coverage must reach 100%."}`

## Chore Description
This chore focuses on generating comprehensive unit tests for all uncovered code in the rococo-sample-backend project to achieve 100% test coverage. The current test coverage is 77% (1644 statements, 376 missed). The primary focus areas are:

1. **Authentication & Security** (15% coverage) - `common/services/auth.py` with critical authentication flows
2. **Helper Utilities** (28-34% coverage) - `common/helpers/auth.py` and `common/helpers/string_utils.py`
3. **Service Layer** (22-44% coverage) - OAuth, Email, Person, Organization services
4. **Models** (31% coverage) - Email model
5. **Repositories** (50-83% coverage) - Organization and Base repository classes
6. **Tasks** (31% coverage) - Message sending functionality
7. **Flask Application** (30-76% coverage) - Application initialization and logging

All tests must follow the existing test patterns using pytest, unittest.mock, and the fixtures defined in `tests/conftest.py`. Tests should be comprehensive, covering success paths, error paths, edge cases, and exception handling.

## Relevant Files
Use these files to resolve the chore:

- **tests/conftest.py** - Contains shared test fixtures and setup. Will be used as reference for creating new test fixtures and mocks.

- **pyproject.toml** - Contains pytest and coverage configuration. Defines which files to include in coverage reports and test paths.

- **common/services/auth.py** (15% coverage, 137 lines uncovered) - The highest priority file containing critical authentication logic including:
  - User signup with email/password
  - OAuth login flows (Google, Microsoft)
  - Password reset functionality
  - JWT token generation and parsing
  - Email verification workflows

- **common/helpers/auth.py** (28% coverage, 21 lines uncovered) - Contains JWT token helpers:
  - `generate_access_token()` - Token generation with person/email data
  - `parse_access_token()` - Token validation and parsing
  - `create_person_from_token()` - Person object creation from token
  - `create_email_from_token()` - Email object creation from token

- **common/helpers/string_utils.py** (34% coverage, 25 lines uncovered) - String manipulation utilities including base64 encoding/decoding and URL-safe string operations

- **common/services/oauth.py** (22% coverage, 36 lines uncovered) - OAuth integration service for Google and Microsoft authentication

- **common/services/email.py** (42% coverage, 11 lines uncovered) - Email service for managing email records

- **common/services/login_method.py** (42% coverage, 11 lines uncovered) - Login method service for authentication methods

- **common/services/organization.py** (44% coverage, 9 lines uncovered) - Organization service for managing organizations

- **common/services/person.py** (33% coverage, 14 lines uncovered) - Person service for managing user profiles

- **common/models/email.py** (31% coverage, 11 lines uncovered) - Email model with validation and business logic

- **common/repositories/organization.py** (50% coverage, 5 lines uncovered) - Organization repository with database operations

- **common/repositories/base.py** (83% coverage, 2 lines uncovered) - Base repository class with common database operations

- **common/tasks/send_message.py** (31% coverage, 25 lines uncovered) - Message queue integration for sending emails via RabbitMQ

- **common/app_logger.py** (76% coverage, 10 lines uncovered) - Application logging configuration

- **flask/app/__init__.py** (30% coverage, 26 lines uncovered) - Flask application factory and initialization

- **flask/logger.py** (75% coverage, 11 lines uncovered) - Flask-specific logging setup

- **common/app_config.py** (90% coverage, 5 lines uncovered) - Application configuration management

### New Files
The following test files need to be created:

- **tests/test_auth_helper.py** - Tests for `common/helpers/auth.py` covering token generation, parsing, and object creation from tokens

- **tests/test_string_utils.py** - Tests for `common/helpers/string_utils.py` covering all string manipulation utilities

- **tests/test_auth_service.py** - Comprehensive tests for `common/services/auth.py` covering signup, login, OAuth flows, password reset, and email verification

- **tests/test_oauth_service.py** - Tests for `common/services/oauth.py` covering Google and Microsoft OAuth integration

- **tests/test_email_service.py** - Tests for `common/services/email.py` covering email CRUD operations

- **tests/test_login_method_service.py** - Tests for `common/services/login_method.py` covering login method management

- **tests/test_organization_service.py** - Tests for `common/services/organization.py` covering organization operations

- **tests/test_person_service.py** - Tests for `common/services/person.py` covering person/user management

- **tests/test_email_model.py** - Tests for `common/models/email.py` covering email model validation and properties

- **tests/test_organization_repository.py** - Tests for `common/repositories/organization.py` covering database operations

- **tests/test_base_repository.py** - Tests for `common/repositories/base.py` covering base repository functionality

- **tests/test_send_message.py** - Tests for `common/tasks/send_message.py` covering message queue operations

- **tests/test_app_logger.py** - Tests for `common/app_logger.py` covering logger initialization and configuration

- **tests/test_flask_factory.py** - Tests for `flask/app/__init__.py` covering Flask app creation and configuration

- **tests/test_flask_logger.py** - Tests for `flask/logger.py` covering Flask logging setup

- **tests/test_app_config.py** - Tests for `common/app_config.py` covering configuration loading and validation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create tests for helper utilities (Foundation)
Start with the foundational helper modules that other components depend on:

- Create `tests/test_string_utils.py` with comprehensive tests for:
  - `urlsafe_base64_encode()` with various byte inputs
  - `urlsafe_base64_decode()` with valid and invalid inputs
  - `force_bytes()` with strings and bytes
  - `force_str()` with bytes and strings
  - All utility functions with edge cases (empty strings, None values, special characters)

- Create `tests/test_auth_helper.py` with tests for:
  - `generate_access_token()` with LoginMethod, Person, and Email objects
  - `generate_access_token()` with only LoginMethod (missing Person/Email)
  - `parse_access_token()` with valid tokens
  - `parse_access_token()` with expired tokens
  - `parse_access_token()` with invalid tokens (malformed, wrong signature)
  - `create_person_from_token()` with complete and minimal token data
  - `create_email_from_token()` with complete and minimal token data

### Step 2: Create tests for configuration and logging
Test the application configuration and logging setup:

- Create `tests/test_app_config.py` with tests for:
  - Configuration loading from environment variables
  - Default values when environment variables are missing
  - Required field validation
  - Type conversion for integer and boolean fields

- Create `tests/test_app_logger.py` with tests for:
  - Logger initialization with different log levels
  - Logger configuration for different environments (test, dev, prod)
  - Log message formatting
  - Error handling in logger setup

- Create `tests/test_flask_logger.py` with tests for:
  - Flask-specific logging configuration
  - Integration with Flask application context
  - Log level configuration

### Step 3: Create tests for repository layer
Test the data access layer:

- Create `tests/test_base_repository.py` with tests for:
  - Base repository initialization
  - Common database operation patterns
  - Connection handling and error cases

- Create `tests/test_organization_repository.py` with tests for:
  - `get_organization_by_id()` with valid and invalid IDs
  - `get_organization_by_name()` with existing and non-existing names
  - Organization save operations
  - Organization query operations

### Step 4: Create tests for model layer
Test the business logic in models:

- Create `tests/test_email_model.py` with tests for:
  - Email model initialization with valid data
  - Email validation (valid email format)
  - Email validation failure cases (invalid format)
  - `is_verified` property behavior
  - Email entity_id generation

### Step 5: Create tests for service layer (Core business logic)
Test the service layer with comprehensive coverage:

- Create `tests/test_person_service.py` with tests for:
  - `save_person()` with valid Person object
  - `get_person_by_id()` with existing and non-existing IDs
  - Person update operations
  - Error handling for database failures

- Create `tests/test_email_service.py` with tests for:
  - `save_email()` with valid Email object
  - `get_email_by_email_address()` with existing and non-existing emails
  - `get_email_by_id()` with valid and invalid IDs
  - `verify_email()` setting is_verified to True
  - Error handling for database operations

- Create `tests/test_login_method_service.py` with tests for:
  - `save_login_method()` with valid LoginMethod
  - `get_login_method_by_email_id()` with existing and non-existing IDs
  - `get_login_method_by_id()` with valid and invalid IDs
  - `update_password()` updating hashed password
  - Error handling for database failures

- Create `tests/test_organization_service.py` with tests for:
  - `save_organization()` with valid Organization object
  - `get_organization_by_id()` with existing and non-existing IDs
  - `get_organization_by_name()` with valid organization names
  - Error handling for duplicate organizations

### Step 6: Create tests for OAuth service
Test OAuth integration:

- Create `tests/test_oauth_service.py` with tests for:
  - Google OAuth token exchange success
  - Google OAuth token exchange failure (invalid token)
  - Google OAuth user info retrieval
  - Microsoft OAuth token exchange success
  - Microsoft OAuth token exchange failure
  - Microsoft OAuth user info retrieval
  - Error handling for network failures
  - Error handling for invalid OAuth responses

### Step 7: Create tests for authentication service (Critical)
Test the critical authentication flows with comprehensive coverage:

- Create `tests/test_auth_service.py` with tests covering:

**Signup Flow:**
  - `signup()` with valid email, first_name, last_name
  - `signup()` with duplicate email (already registered)
  - `signup()` with email already registered via OAuth (should raise InputValidationError with provider name)
  - `signup()` creates Person, Email, LoginMethod, Organization, PersonOrganizationRole
  - `signup()` sends welcome email with confirmation link

**Login by Email/Password:**
  - `login_user_by_email_password()` with valid credentials
  - `login_user_by_email_password()` with non-existent email
  - `login_user_by_email_password()` with incorrect password
  - `login_user_by_email_password()` for OAuth account (should raise error)
  - `login_user_by_email_password()` with no password set (edge case)
  - Returns valid access token and expiry

**OAuth Login Flow:**
  - `login_user_by_oauth()` with new user (creates all entities)
  - `login_user_by_oauth()` with existing user (returns existing person)
  - `login_user_by_oauth()` with existing email but no login method (creates login method)
  - `login_user_by_oauth()` converts email/password account to OAuth
  - `login_user_by_oauth()` verifies email automatically for OAuth users
  - `login_user_by_oauth()` creates organization with default name
  - Returns valid access token, expiry, and person

**Password Reset Flow:**
  - `generate_reset_password_token()` creates valid JWT token
  - `prepare_password_reset_url()` generates correct URL format
  - `send_password_reset_email()` sends message to queue
  - `trigger_forgot_password_email()` with valid email
  - `trigger_forgot_password_email()` with non-existent email (raises APIException)
  - `parse_reset_password_token()` with valid token
  - `parse_reset_password_token()` with expired token
  - `parse_reset_password_token()` with invalid token
  - `reset_user_password()` with valid token and password
  - `reset_user_password()` with invalid token (raises APIException)
  - `reset_user_password()` with invalid uidb64 (raises APIException)
  - `reset_user_password()` updates password hash correctly
  - `reset_user_password()` verifies email after reset
  - `reset_user_password()` returns access token and expiry

**Welcome Email:**
  - `send_welcome_email()` sends message with confirmation link
  - `send_welcome_email()` includes recipient name in message

### Step 8: Create tests for messaging/tasks
Test the message queue integration:

- Create `tests/test_send_message.py` with tests for:
  - `MessageSender` initialization
  - `send_message()` successfully publishes to RabbitMQ queue
  - `send_message()` handles connection errors
  - `send_message()` handles invalid queue names
  - `send_message()` serializes message data correctly
  - Connection pooling and cleanup

### Step 9: Create tests for Flask application factory
Test Flask application initialization:

- Create `tests/test_flask_factory.py` with tests for:
  - `create_app()` with different configurations
  - Application context setup
  - Database connection pooling initialization
  - Blueprint registration
  - Error handler registration
  - CORS configuration
  - Environment-specific configuration loading

### Step 10: Run coverage analysis and fill gaps
After creating all test files, identify any remaining gaps:

- Run `pytest tests/ --cov=. --cov-report=term-missing` to generate coverage report
- Identify any remaining uncovered lines
- Add additional test cases to cover edge cases and error paths
- Ensure all branches (if/else, try/except) are covered
- Add tests for any missed error handling paths

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `pytest tests/ -v` - Run all tests to ensure they pass without errors
- `pytest tests/ --cov=. --cov-report=term-missing` - Generate coverage report and verify 100% coverage for targeted files
- `pytest tests/ --cov=. --cov-report=html` - Generate HTML coverage report for detailed analysis
- `pytest tests/test_auth_service.py -v` - Verify authentication service tests pass
- `pytest tests/test_auth_helper.py -v` - Verify authentication helper tests pass
- `pytest tests/test_oauth_service.py -v` - Verify OAuth service tests pass
- `pytest tests/ -k "test_auth" -v` - Run all authentication-related tests
- `pytest tests/ --cov=common/services/auth.py --cov-report=term-missing` - Verify 100% coverage for auth service
- `pytest tests/ --cov=common/helpers/auth.py --cov-report=term-missing` - Verify 100% coverage for auth helper
- `pytest tests/ --cov=common/services --cov-report=term-missing` - Verify comprehensive service layer coverage

## Notes

### Testing Strategy
1. **Use existing patterns**: Follow the test structure in `tests/test_decorators.py`, `tests/test_login_method.py`, and `tests/test_person_org_role_service.py` as references
2. **Mock external dependencies**: Use `unittest.mock` to mock database connections, external API calls, and message queues
3. **Leverage fixtures**: Utilize fixtures from `tests/conftest.py` (mock_config, mock_person, mock_email, mock_organization, etc.)
4. **Test class organization**: Organize tests into classes by functionality (e.g., `TestAuthServiceSignup`, `TestAuthServiceLogin`)
5. **Descriptive test names**: Use clear test names that describe what is being tested (e.g., `test_signup_with_valid_data_creates_all_entities`)

### Priority Order
The step-by-step tasks are ordered to build from foundation to complex:
1. Helpers (no dependencies)
2. Configuration (minimal dependencies)
3. Repositories (data layer)
4. Models (business logic)
5. Services (depends on repos and models)
6. Auth Service (depends on all services)
7. Tasks (messaging infrastructure)
8. Flask app (integration layer)

### Coverage Target
- Target: 100% line coverage for all files listed in `pyproject.toml` coverage configuration
- Current: 77% overall coverage (1644 statements, 376 missed)
- Gap: 376 lines need test coverage
- Focus: Prioritize files with <50% coverage first, then improve files with 50-80% coverage

### Mock Strategy for Testing
- **Database calls**: Mock repository methods to return predefined objects
- **External APIs**: Mock HTTP requests to OAuth providers (Google, Microsoft)
- **Message queues**: Mock RabbitMQ connections and message publishing
- **Time-dependent code**: Mock `time.time()` for consistent JWT expiry testing
- **JWT encoding/decoding**: Use actual JWT library but mock time for expiry tests
- **Password hashing**: Use actual werkzeug functions but with test passwords

### Edge Cases to Cover
- None/null values for optional parameters
- Empty strings and whitespace-only strings
- Expired JWT tokens
- Invalid JWT signatures
- Database connection failures
- Network timeouts for OAuth providers
- Duplicate records (email, organization name)
- Missing environment variables
- Invalid email formats
- OAuth provider returning unexpected data formats
