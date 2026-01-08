"""
Comprehensive tests for common/services/auth.py
"""
import pytest
import time
import jwt
from unittest.mock import MagicMock, patch, call
from common.services.auth import AuthService
from common.models import Person, Email, LoginMethod, Organization, PersonOrganizationRole
from common.models.login_method import LoginMethodType
from common.helpers.exceptions import InputValidationError, APIException


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    config = MagicMock()
    config.QUEUE_NAME_PREFIX = "test_"
    config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email-queue"
    config.DEFAULT_USER_PASSWORD = "Default@Password123"
    config.VUE_APP_URI = "http://localhost:3000"
    config.RESET_TOKEN_EXPIRE = 3600
    config.AUTH_JWT_SECRET = "test-secret"
    config.ACCESS_TOKEN_EXPIRE = 3600
    return config


@pytest.fixture
def auth_service(mock_config):
    """Create an AuthService instance with mocked dependencies."""
    with patch('common.services.auth.PersonService'), \
         patch('common.services.auth.EmailService'), \
         patch('common.services.auth.LoginMethodService'), \
         patch('common.services.auth.OrganizationService'), \
         patch('common.services.auth.PersonOrganizationRoleService'), \
         patch('common.services.auth.MessageSender'):
        service = AuthService(mock_config)
        return service


class TestAuthServiceSignup:
    """Tests for AuthService.signup method."""

    def test_signup_success(self, auth_service):
        """Test successful user signup."""
        # Setup
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=None)
        auth_service.email_service.save_email = MagicMock(side_effect=lambda x: x)
        auth_service.person_service.save_person = MagicMock(side_effect=lambda x: x)
        auth_service.login_method_service.save_login_method = MagicMock(side_effect=lambda x: x)
        auth_service.organization_service.save_organization = MagicMock(side_effect=lambda x: x)
        auth_service.person_organization_role_service.save_person_organization_role = MagicMock(side_effect=lambda x: x)
        auth_service.message_sender.send_message = MagicMock()

        # Execute
        auth_service.signup("test@example.com", "John", "Doe")

        # Verify
        auth_service.email_service.save_email.assert_called_once()
        auth_service.person_service.save_person.assert_called_once()
        auth_service.login_method_service.save_login_method.assert_called_once()
        auth_service.organization_service.save_organization.assert_called_once()
        auth_service.person_organization_role_service.save_person_organization_role.assert_called_once()
        auth_service.message_sender.send_message.assert_called_once()

    def test_signup_email_already_exists(self, auth_service):
        """Test signup with already registered email."""
        # Setup
        existing_email = MagicMock()
        existing_email.entity_id = "email-123"
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=existing_email)

        existing_login_method = MagicMock()
        existing_login_method.is_oauth_method = False
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=existing_login_method)

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.signup("test@example.com", "John", "Doe")
        assert "already registered" in str(exc_info.value)

    def test_signup_email_already_exists_with_oauth(self, auth_service):
        """Test signup with email already registered via OAuth."""
        # Setup
        existing_email = MagicMock()
        existing_email.entity_id = "email-123"
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=existing_email)

        existing_login_method = MagicMock()
        existing_login_method.is_oauth_method = True
        existing_login_method.oauth_provider_name = "Google"
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=existing_login_method)

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.signup("test@example.com", "John", "Doe")
        assert "Google" in str(exc_info.value)
        assert "OAuth provider" in str(exc_info.value)


class TestAuthServicePasswordReset:
    """Tests for password reset functionality."""

    def test_generate_reset_password_token(self, auth_service):
        """Test reset password token generation."""
        # Setup
        login_method = MagicMock()
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed-password"

        # Execute
        token = auth_service.generate_reset_password_token(login_method, "test@example.com")

        # Verify
        assert token is not None
        assert isinstance(token, str)

    def test_prepare_password_reset_url(self, auth_service):
        """Test password reset URL preparation."""
        # Setup
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed-password"

        # Execute
        url = auth_service.prepare_password_reset_url(login_method, "test@example.com")

        # Verify
        assert url is not None
        assert auth_service.config.VUE_APP_URI in url
        assert "/set-password/" in url

    def test_send_welcome_email(self, auth_service):
        """Test welcome email sending."""
        # Setup
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed-password"

        person = MagicMock()
        person.first_name = "John"
        person.last_name = "Doe"

        auth_service.message_sender.send_message = MagicMock()

        # Execute
        auth_service.send_welcome_email(login_method, person, "test@example.com")

        # Verify
        auth_service.message_sender.send_message.assert_called_once()
        call_args = auth_service.message_sender.send_message.call_args
        assert call_args[0][1]["event"] == "WELCOME_EMAIL"
        assert "test@example.com" in call_args[0][1]["to_emails"]

    def test_parse_reset_password_token_valid(self, auth_service):
        """Test parsing valid reset password token."""
        # Setup
        login_method = MagicMock()
        login_method.password = "test-secret"

        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, login_method.password, algorithm='HS256')

        # Execute
        decoded = AuthService.parse_reset_password_token(token, login_method)

        # Verify
        assert decoded is not None
        assert decoded['email'] == 'test@example.com'
        assert decoded['person_id'] == 'person-123'

    def test_parse_reset_password_token_expired(self, auth_service):
        """Test parsing expired reset password token."""
        # Setup
        login_method = MagicMock()
        login_method.password = "test-secret"

        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() - 100  # Expired
        }
        token = jwt.encode(payload, login_method.password, algorithm='HS256')

        # Execute
        decoded = AuthService.parse_reset_password_token(token, login_method)

        # Verify
        assert decoded is None

    def test_trigger_forgot_password_email_success(self, auth_service):
        """Test triggering forgot password email successfully."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.person_id = "person-123"
        email_obj.email = "test@example.com"

        person = MagicMock()
        person.entity_id = "person-123"

        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.password = "hashed-password"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)
        auth_service.message_sender.send_message = MagicMock()

        # Execute
        auth_service.trigger_forgot_password_email("test@example.com")

        # Verify
        auth_service.message_sender.send_message.assert_called_once()

    def test_trigger_forgot_password_email_no_email(self, auth_service):
        """Test triggering forgot password with non-existent email."""
        # Setup
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=None)

        # Execute & Verify
        with pytest.raises(APIException) as exc_info:
            auth_service.trigger_forgot_password_email("test@example.com")
        assert "not registered" in str(exc_info.value)

    def test_trigger_forgot_password_email_no_person(self, auth_service):
        """Test triggering forgot password when person doesn't exist."""
        # Setup
        email_obj = MagicMock()
        email_obj.person_id = "person-123"
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=None)

        # Execute & Verify
        with pytest.raises(APIException) as exc_info:
            auth_service.trigger_forgot_password_email("test@example.com")
        assert "Person does not exist" in str(exc_info.value)

    def test_send_password_reset_email(self, auth_service):
        """Test sending password reset email."""
        # Setup
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed-password"

        auth_service.message_sender.send_message = MagicMock()

        # Execute
        auth_service.send_password_reset_email("test@example.com", login_method)

        # Verify
        auth_service.message_sender.send_message.assert_called_once()
        call_args = auth_service.message_sender.send_message.call_args
        assert call_args[0][1]["event"] == "RESET_PASSWORD"

    @patch('common.services.auth.urlsafe_base64_decode')
    @patch('common.services.auth.force_str')
    def test_reset_user_password_success(self, mock_force_str, mock_decode, auth_service):
        """Test successful password reset."""
        # Setup
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "old-hashed-password"

        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.email = "test@example.com"

        person_obj = MagicMock()
        person_obj.entity_id = "person-123"

        # Mock token generation and decoding
        token_payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(token_payload, login_method.password, algorithm='HS256')

        mock_force_str.return_value = "login-123"
        mock_decode.return_value = b"login-123"

        auth_service.login_method_service.get_login_method_by_id = MagicMock(return_value=login_method)
        auth_service.email_service.get_email_by_id = MagicMock(return_value=email_obj)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person_obj)
        auth_service.login_method_service.update_password = MagicMock(return_value=login_method)
        auth_service.email_service.verify_email = MagicMock(return_value=email_obj)

        with patch('common.services.auth.generate_access_token') as mock_gen_token:
            mock_gen_token.return_value = ("access-token", time.time() + 3600)

            # Execute
            access_token, expiry, person = auth_service.reset_user_password(token, "uidb64", "NewPassword123!")

            # Verify
            assert access_token == "access-token"
            assert person == person_obj
            auth_service.login_method_service.update_password.assert_called_once()
            auth_service.email_service.verify_email.assert_called_once()

    @patch('common.services.auth.urlsafe_base64_decode')
    @patch('common.services.auth.force_str')
    def test_reset_user_password_invalid_login_method(self, mock_force_str, mock_decode, auth_service):
        """Test password reset with invalid login method."""
        # Setup
        mock_force_str.return_value = "invalid-login-id"
        mock_decode.return_value = b"invalid-login-id"
        auth_service.login_method_service.get_login_method_by_id = MagicMock(return_value=None)

        # Execute & Verify
        with pytest.raises(APIException) as exc_info:
            auth_service.reset_user_password("token", "uidb64", "NewPassword123!")
        assert "Invalid password reset URL" in str(exc_info.value)

    @patch('common.services.auth.urlsafe_base64_decode')
    @patch('common.services.auth.force_str')
    def test_reset_user_password_invalid_token(self, mock_force_str, mock_decode, auth_service):
        """Test password reset with invalid token."""
        # Setup
        login_method = MagicMock()
        login_method.password = "hashed-password"

        mock_force_str.return_value = "login-123"
        mock_decode.return_value = b"login-123"
        auth_service.login_method_service.get_login_method_by_id = MagicMock(return_value=login_method)

        # Execute & Verify
        with pytest.raises(APIException) as exc_info:
            auth_service.reset_user_password("invalid-token", "uidb64", "NewPassword123!")
        assert "Invalid reset password token" in str(exc_info.value)


class TestAuthServiceLogin:
    """Tests for login functionality."""

    @patch('common.services.auth.check_password_hash')
    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_email_password_success(self, mock_gen_token, mock_check_password, auth_service):
        """Test successful login with email and password."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.email = "test@example.com"

        login_method = MagicMock()
        login_method.person_id = "person-123"
        login_method.password = "hashed-password"
        login_method.is_oauth_method = False

        person = MagicMock()
        person.entity_id = "person-123"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person)

        mock_check_password.return_value = True
        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry = auth_service.login_user_by_email_password("test@example.com", "password123")

        # Verify
        assert access_token == "access-token"
        mock_check_password.assert_called_once_with("hashed-password", "password123")

    def test_login_user_by_email_password_email_not_found(self, auth_service):
        """Test login with non-existent email."""
        # Setup
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=None)

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password123")
        assert "Email is not registered" in str(exc_info.value)

    def test_login_user_by_email_password_no_login_method(self, auth_service):
        """Test login when login method doesn't exist."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=None)

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password123")
        assert "Login method not found" in str(exc_info.value)

    def test_login_user_by_email_password_oauth_account(self, auth_service):
        """Test login with OAuth account using email/password."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"

        login_method = MagicMock()
        login_method.is_oauth_method = True
        login_method.oauth_provider_name = "Google"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password123")
        assert "Google" in str(exc_info.value)

    def test_login_user_by_email_password_no_password_set(self, auth_service):
        """Test login when account has no password set."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"

        login_method = MagicMock()
        login_method.is_oauth_method = False
        login_method.password = None

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password123")
        assert "does not have a password set" in str(exc_info.value)

    @patch('common.services.auth.check_password_hash')
    def test_login_user_by_email_password_incorrect_password(self, mock_check_password, auth_service):
        """Test login with incorrect password."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"

        login_method = MagicMock()
        login_method.password = "hashed-password"
        login_method.is_oauth_method = False

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)

        mock_check_password.return_value = False

        # Execute & Verify
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "wrong-password")
        assert "Incorrect email or password" in str(exc_info.value)


class TestAuthServiceOAuthLogin:
    """Tests for OAuth login functionality."""

    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_oauth_existing_user(self, mock_gen_token, auth_service):
        """Test OAuth login for existing user."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.person_id = "person-123"
        email_obj.is_verified = True

        login_method = MagicMock()
        login_method.is_oauth_method = True

        person = MagicMock()
        person.entity_id = "person-123"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person)

        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        # Verify
        assert access_token == "access-token"
        assert returned_person == person

    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_oauth_existing_user_unverified_email(self, mock_gen_token, auth_service):
        """Test OAuth login verifies unverified email."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.person_id = "person-123"
        email_obj.is_verified = False

        login_method = MagicMock()
        login_method.is_oauth_method = True

        person = MagicMock()
        person.entity_id = "person-123"

        verified_email = MagicMock()
        verified_email.is_verified = True

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person)
        auth_service.email_service.verify_email = MagicMock(return_value=verified_email)

        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        # Verify
        auth_service.email_service.verify_email.assert_called_once()

    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_oauth_existing_user_no_login_method(self, mock_gen_token, auth_service):
        """Test OAuth login creates login method for existing user without one."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.person_id = "person-123"
        email_obj.is_verified = True

        person = MagicMock()
        person.entity_id = "person-123"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=None)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person)
        auth_service.login_method_service.save_login_method = MagicMock(side_effect=lambda x: x)

        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        # Verify
        auth_service.login_method_service.save_login_method.assert_called_once()
        assert returned_person == person

    def test_login_user_by_oauth_existing_user_no_person(self, auth_service):
        """Test OAuth login fails when person doesn't exist."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.person_id = "person-123"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=None)

        # Execute & Verify
        with pytest.raises(APIException) as exc_info:
            auth_service.login_user_by_oauth(
                "test@example.com", "John", "Doe", "google", {"sub": "123"}
            )
        assert "Person not found" in str(exc_info.value)

    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_oauth_existing_non_oauth_method(self, mock_gen_token, auth_service):
        """Test OAuth login updates non-OAuth login method to OAuth."""
        # Setup
        email_obj = MagicMock()
        email_obj.entity_id = "email-123"
        email_obj.person_id = "person-123"
        email_obj.is_verified = True

        login_method = MagicMock()
        login_method.is_oauth_method = False

        person = MagicMock()
        person.entity_id = "person-123"

        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        auth_service.login_method_service.get_login_method_by_email_id = MagicMock(return_value=login_method)
        auth_service.person_service.get_person_by_id = MagicMock(return_value=person)
        auth_service.login_method_service.save_login_method = MagicMock()

        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        # Verify
        auth_service.login_method_service.save_login_method.assert_called_once()
        assert login_method.method_type == "oauth-google"
        assert login_method.password is None

    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_oauth_new_user(self, mock_gen_token, auth_service):
        """Test OAuth login creates new user."""
        # Setup
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=None)
        auth_service.email_service.save_email = MagicMock(side_effect=lambda x: x)
        auth_service.person_service.save_person = MagicMock(side_effect=lambda x: x)
        auth_service.login_method_service.save_login_method = MagicMock(side_effect=lambda x: x)
        auth_service.organization_service.save_organization = MagicMock()
        auth_service.person_organization_role_service.save_person_organization_role = MagicMock()

        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry, person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        # Verify
        assert access_token == "access-token"
        auth_service.email_service.save_email.assert_called_once()
        auth_service.person_service.save_person.assert_called_once()
        auth_service.login_method_service.save_login_method.assert_called_once()
        auth_service.organization_service.save_organization.assert_called_once()
        auth_service.person_organization_role_service.save_person_organization_role.assert_called_once()

    @patch('common.services.auth.generate_access_token')
    def test_login_user_by_oauth_new_user_with_person_id(self, mock_gen_token, auth_service):
        """Test OAuth login creates new user with provided person_id."""
        # Setup
        auth_service.email_service.get_email_by_email_address = MagicMock(return_value=None)
        auth_service.email_service.save_email = MagicMock(side_effect=lambda x: x)
        auth_service.person_service.save_person = MagicMock(side_effect=lambda x: x)
        auth_service.login_method_service.save_login_method = MagicMock(side_effect=lambda x: x)
        auth_service.organization_service.save_organization = MagicMock()
        auth_service.person_organization_role_service.save_person_organization_role = MagicMock()

        mock_gen_token.return_value = ("access-token", time.time() + 3600)

        # Execute
        access_token, expiry, person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "microsoft", {"sub": "456"}, person_id="custom-person-id"
        )

        # Verify
        assert person.entity_id == "custom-person-id"
