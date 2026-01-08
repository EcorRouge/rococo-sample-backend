# Chore: Generate Tests

## Metadata
issue_number: `3`
adw_id: `beaea8d4`
issue_json: `{"number": 3, "title": "Generate Tests", "body": "adw_test_iso.py\n\nGenerate test for uncovered code. The coverage must reach 100%. "}`

## Chore Description
Generate comprehensive unit tests for all uncovered code modules in the `common/` and `flask/app/helpers/` directories to achieve 100% code coverage. The current test suite lacks complete coverage for many critical modules including models, repositories, services, and helper utilities. This chore involves systematically identifying uncovered code paths and writing thorough unit tests that cover all branches, edge cases, and error conditions.

The coverage configuration in `pyproject.toml` specifies the following modules to be covered:
- `common/models/*`
- `common/repositories/*`
- `common/services/*`
- `common/utils/*`
- `flask/app/helpers/*`

## Relevant Files
Use these files to resolve the chore:

### Existing Test Infrastructure
- `tests/conftest.py` - Contains shared pytest fixtures including mock objects, test environment setup, and Flask application context. This provides the foundation for all test files.
- `tests/test_person_org_role_service.py` - Example of existing service test patterns using mocks and patches. Use this as a reference for testing service classes.
- `tests/test_decorators.py` - Existing decorator tests for Flask helpers.
- `tests/test_response.py` - Existing response helper tests.
- `tests/test_factory.py` - Existing factory pattern tests.
- `tests/test_login_method.py` - Existing login method tests.
- `tests/test_version.py` - Existing version utility tests.

### Modules Requiring Test Coverage

#### Models (common/models/)
- `common/models/email.py` - Email model with validation logic including regex pattern matching, string type checking, and length validation.
- `common/models/organization.py` - Simple organization model that extends base class.
- `common/models/person.py` - Person model with type checking enabled.
- `common/models/login_method.py` - Login method model (needs verification if existing tests are sufficient).
- `common/models/person_organization_role.py` - Person-organization-role model (needs verification if existing tests are sufficient).

#### Services (common/services/)
- `common/services/auth.py` - Complex authentication service with signup, login, password reset, OAuth integration, JWT token handling, and email sending functionality.
- `common/services/email.py` - Email service for saving, retrieving, and verifying emails.
- `common/services/oauth.py` - OAuth client for Google and Microsoft authentication with token exchange and user info retrieval.
- `common/services/login_method.py` - Login method service (needs verification if existing tests are sufficient).
- `common/services/organization.py` - Organization service (needs verification if existing tests are sufficient).
- `common/services/person.py` - Person service (needs verification if existing tests are sufficient).

#### Repositories (common/repositories/)
- `common/repositories/base.py` - Base repository class with MODEL validation in __init_subclass__.
- `common/repositories/email.py` - Email repository extending base repository.
- `common/repositories/organization.py` - Organization repository with custom query method for getting organizations by person ID.
- `common/repositories/person.py` - Person repository (needs verification if existing tests are sufficient).
- `common/repositories/person_organization_role.py` - Person-organization-role repository (needs verification if existing tests are sufficient).
- `common/repositories/login_method.py` - Login method repository (needs verification if existing tests are sufficient).

#### Utilities (common/utils/)
- `common/utils/version.py` - Version utility functions.

#### Flask Helpers (flask/app/helpers/)
- `flask/app/helpers/decorators.py` - Already has tests, but needs verification for 100% coverage.
- `flask/app/helpers/response.py` - Already has tests, but needs verification for 100% coverage.

### Configuration
- `pyproject.toml` - pytest and coverage configuration defining which modules to include in coverage reports.
- `local.env` - Environment variables for test configuration.

### New Files

#### Model Tests
- `tests/test_email_model.py` - Tests for email model validation including valid/invalid email formats, type checking, and length limits.
- `tests/test_organization_model.py` - Tests for organization model instantiation and inheritance.
- `tests/test_person_model.py` - Tests for person model with type checking.

#### Service Tests
- `tests/test_auth_service.py` - Comprehensive tests for all authentication flows including signup, login (email/password and OAuth), password reset, token generation/parsing, and email triggers.
- `tests/test_email_service.py` - Tests for email service methods including save, get by address, get by ID, and verify email.
- `tests/test_oauth_service.py` - Tests for OAuth client methods including Google/Microsoft token exchange and user info retrieval with proper error handling.
- `tests/test_login_method_service.py` - Tests for login method service operations (if not already covered).
- `tests/test_organization_service.py` - Tests for organization service operations (if not already covered).
- `tests/test_person_service.py` - Tests for person service operations (if not already covered).

#### Repository Tests
- `tests/test_base_repository.py` - Tests for base repository including MODEL validation in subclass initialization.
- `tests/test_email_repository.py` - Tests for email repository instantiation and MODEL attribute.
- `tests/test_organization_repository.py` - Tests for organization repository including custom get_organizations_by_person_id query method.
- `tests/test_person_repository.py` - Tests for person repository (if not already covered).
- `tests/test_person_org_role_repository.py` - Tests for person-organization-role repository (if not already covered).
- `tests/test_login_method_repository.py` - Tests for login method repository (if not already covered).

#### Utility Tests
- `tests/test_version_utils.py` - Tests for version utility functions (if test_version.py doesn't cover common/utils/version.py).

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Run Initial Coverage Analysis
- Execute pytest with coverage reporting to identify all uncovered code paths
- Generate coverage report to understand current baseline
- Document which modules have 0% coverage vs partial coverage
- Identify specific functions, methods, and branches that lack test coverage

### Step 2: Generate Model Tests
- Create `tests/test_email_model.py` to test email validation logic:
  - Test valid email formats (standard, with plus signs, with dots, various TLDs)
  - Test invalid email formats (missing @, missing domain, invalid characters)
  - Test non-string email addresses (integers, None, objects)
  - Test email length validation (exactly 254 chars, over 254 chars)
  - Test multiple validation errors at once
- Create `tests/test_organization_model.py` to test organization model:
  - Test model instantiation with valid data
  - Test model inherits from base class correctly
- Create `tests/test_person_model.py` to test person model:
  - Test model instantiation with type checking enabled
  - Test ClassVar use_type_checking attribute

### Step 3: Generate Repository Tests
- Create `tests/test_base_repository.py` to test base repository:
  - Test that subclasses without MODEL attribute raise TypeError
  - Test that subclasses with MODEL attribute initialize correctly
  - Test __init_subclass__ validation logic
- Create `tests/test_email_repository.py` to test email repository:
  - Test MODEL attribute is set to Email class
  - Test repository instantiation with required parameters
- Create `tests/test_organization_repository.py` to test organization repository:
  - Test MODEL attribute is set to Organization class
  - Test get_organizations_by_person_id method with valid person_id
  - Test database adapter query execution and parameter binding
  - Test empty results handling

### Step 4: Generate Service Tests - Email Service
- Create `tests/test_email_service.py` to test email service:
  - Test __init__ initializes config and repository factory
  - Test save_email method saves and returns email
  - Test get_email_by_email_address retrieves correct email
  - Test get_email_by_email_address returns None when not found
  - Test get_email_by_id retrieves email by entity_id
  - Test get_email_by_id returns None when not found
  - Test verify_email sets is_verified=True and saves

### Step 5: Generate Service Tests - OAuth Service
- Create `tests/test_oauth_service.py` to test OAuth client:
  - Test __init__ initializes config correctly
  - Test get_google_token with valid code, redirect_uri, and code_verifier
  - Test get_google_token handles 200 response correctly
  - Test get_google_token handles non-200 responses with logging
  - Test get_google_token handles request exceptions
  - Test get_user_info with valid access token
  - Test get_google_user_info makes correct API call with Authorization header
  - Test get_google_user_info handles response correctly
  - Test get_microsoft_token with valid parameters
  - Test get_microsoft_token handles response correctly
  - Test get_microsoft_user_info with valid access token
  - Test get_microsoft_user_info transforms response correctly (userPrincipalName vs mail)
  - Mock all external requests.post and requests.get calls

### Step 6: Generate Service Tests - Auth Service
- Create `tests/test_auth_service.py` to test authentication service:
  - Test __init__ initializes all dependent services and config
  - Test signup with new email creates person, email, login_method, organization, and person_org_role
  - Test signup with existing email raises InputValidationError
  - Test signup with OAuth-registered email raises specific InputValidationError with provider name
  - Test signup sends welcome email via message sender
  - Test generate_reset_password_token creates valid JWT with correct claims
  - Test prepare_password_reset_url generates correct URL format with token and uid
  - Test send_welcome_email constructs correct message structure
  - Test send_welcome_email includes confirmation_link in message data
  - Test login_user_by_email_password with valid credentials returns token and expiry
  - Test login_user_by_email_password with unregistered email raises InputValidationError
  - Test login_user_by_email_password with no login_method raises InputValidationError
  - Test login_user_by_email_password with OAuth account raises InputValidationError with provider name
  - Test login_user_by_email_password with None password raises InputValidationError
  - Test login_user_by_email_password with incorrect password raises InputValidationError
  - Test login_user_by_oauth with existing email returns token and person
  - Test login_user_by_oauth with existing email creates login_method if missing
  - Test login_user_by_oauth with existing email updates login_method to OAuth type
  - Test login_user_by_oauth with existing email verifies email if not verified
  - Test login_user_by_oauth with new email creates all entities (person, email, login_method, org, role)
  - Test login_user_by_oauth with new email uses provided person_id if given
  - Test login_user_by_oauth sets is_verified=True for OAuth users
  - Test login_user_by_oauth clears password field for OAuth login methods
  - Test parse_reset_password_token with valid token returns decoded data
  - Test parse_reset_password_token with expired token returns None
  - Test parse_reset_password_token with invalid token returns None
  - Test trigger_forgot_password_email with registered email sends reset email
  - Test trigger_forgot_password_email with unregistered email raises APIException
  - Test trigger_forgot_password_email with no person raises APIException
  - Test trigger_forgot_password_email with no login_method raises APIException
  - Test send_password_reset_email constructs correct message structure
  - Test reset_user_password with valid token and uidb64 updates password
  - Test reset_user_password with valid token verifies email
  - Test reset_user_password with valid token returns access token
  - Test reset_user_password with invalid uidb64 raises APIException
  - Test reset_user_password with invalid token raises APIException
  - Test reset_user_password with missing email raises APIException
  - Test reset_user_password with missing person raises APIException
  - Mock all service dependencies (PersonService, EmailService, LoginMethodService, etc.)

### Step 7: Verify and Enhance Existing Test Coverage
- Review `tests/test_decorators.py` and ensure all decorator code paths are covered
- Review `tests/test_response.py` and ensure all response helper methods are covered
- Review `tests/test_factory.py` and ensure all factory methods are covered
- Review `tests/test_login_method.py` and ensure login method service is fully covered
- Add any missing test cases to achieve 100% coverage in these files

### Step 8: Run Full Coverage Analysis
- Execute pytest with coverage to validate all new tests pass
- Generate detailed coverage report (HTML and terminal)
- Verify that all modules in pyproject.toml coverage config reach 100%
- Identify any remaining uncovered lines or branches

### Step 9: Address Remaining Coverage Gaps
- For any modules still below 100%, analyze uncovered lines
- Write additional test cases targeting specific uncovered branches
- Test edge cases, error conditions, and exception handling paths
- Ensure all defensive code paths are tested

### Step 10: Run Validation Commands
- Execute all validation commands to ensure 100% coverage with zero regressions
- Verify all tests pass without errors
- Confirm coverage report shows 100% for all configured modules

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `pytest tests/ -v` - Run all tests with verbose output to ensure zero test failures
- `pytest tests/ -v --cov=common/models --cov=common/repositories --cov=common/services --cov=common/utils --cov=flask/app/helpers --cov-report=term-missing` - Run tests with detailed coverage report showing line numbers of any missing coverage
- `pytest tests/ -v --cov=common/models --cov=common/repositories --cov=common/services --cov=common/utils --cov=flask/app/helpers --cov-report=html` - Generate HTML coverage report for detailed analysis
- Manually verify that coverage report shows 100% coverage for all modules listed in `pyproject.toml`

## Notes
- Use pytest mocking extensively with `unittest.mock.MagicMock` and `@patch` decorators following patterns from `tests/test_person_org_role_service.py`
- Leverage existing fixtures in `tests/conftest.py` for mock objects, config, and Flask application context
- Follow the existing test structure and naming conventions (test_<module_name>.py)
- For services, mock all repository dependencies and external services (MessageSender, requests)
- For repositories, mock database adapters and message adapters
- For models, test validation logic directly without mocking
- Pay special attention to error handling paths and edge cases (None values, empty strings, invalid inputs)
- The auth service is particularly complex with OAuth flows - ensure comprehensive coverage of all branches
- Test both success paths and failure paths for all methods
- Use descriptive test names that clearly indicate what is being tested
- Group related tests into test classes following the pattern `class Test<ServiceName>`
- For OAuth tests, mock all external HTTP requests to Google and Microsoft APIs
- Ensure tests are isolated and do not depend on external services or database state
- Add NOSONAR comments to any test fixture passwords or secrets to avoid security scanning false positives
