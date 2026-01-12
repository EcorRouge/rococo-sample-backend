"""
Unit tests for common/services/auth.py
"""
import time
import jwt
import pytest
from unittest.mock import MagicMock, patch, call
from common.services.auth import AuthService
from common.models import Person, Email, LoginMethod, Organization, PersonOrganizationRole
from common.models.login_method import LoginMethodType
from common.helpers.exceptions import InputValidationError, APIException


class TestAuthServiceInitialization:
    """Tests for AuthService initialization."""

    def test_init_creates_all_services(self, mock_config):
        """Test that __init__ creates all required service instances."""
        with patch('common.services.auth.PersonService'), \
             patch('common.services.auth.EmailService'), \
             patch('common.services.auth.LoginMethodService'), \
             patch('common.services.auth.OrganizationService'), \
             patch('common.services.auth.PersonOrganizationRoleService'), \
             patch('common.services.auth.MessageSender'):

            auth_service = AuthService(mock_config)

            assert auth_service.config == mock_config
            assert auth_service.person_service is not None
            assert auth_service.email_service is not None
            assert auth_service.login_method_service is not None
            assert auth_service.organization_service is not None
            assert auth_service.person_organization_role_service is not None
            assert auth_service.message_sender is not None


class TestSignup:
    """Tests for signup method."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_signup_success(self, mock_person_service_class, mock_email_service_class,
                           mock_login_method_service_class, mock_org_service_class,
                           mock_por_service_class, mock_message_sender_class, mock_config):
        """Test successful user signup."""
        # Setup mocks
        mock_config.DEFAULT_USER_PASSWORD = "TestPass123!"  # Valid password for tests
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = 3600
        mock_config.QUEUE_NAME_PREFIX = "test_"
        mock_config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email_queue"

        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_email_address.return_value = None
        mock_email_service.save_email.return_value = MagicMock(email="test@example.com", entity_id="email-123")

        mock_person_service = mock_person_service_class.return_value
        mock_person_service.save_person.return_value = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")

        mock_login_method_service = mock_login_method_service_class.return_value
        # Create a proper mock with entity_id and password attributes
        mock_saved_login = MagicMock()
        mock_saved_login.entity_id = "login-123"
        mock_saved_login.password = "hashed_password_string"
        mock_login_method_service.save_login_method.return_value = mock_saved_login

        # Completely mock the message sender to avoid any JSON serialization
        mock_message_sender_instance = MagicMock()
        mock_message_sender_class.return_value = mock_message_sender_instance

        auth_service = AuthService(mock_config)

        # Patch send_welcome_email to avoid JSON serialization issues
        with patch.object(auth_service, 'send_welcome_email'):
            # Execute
            auth_service.signup("test@example.com", "John", "Doe")

        # Verify
        mock_email_service.get_email_by_email_address.assert_called_once_with("test@example.com")
        mock_email_service.save_email.assert_called_once()
        mock_person_service.save_person.assert_called_once()
        mock_login_method_service.save_login_method.assert_called_once()

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_signup_with_existing_email(self, mock_person_service_class, mock_email_service_class,
                                       mock_login_method_service_class, mock_org_service_class,
                                       mock_por_service_class, mock_message_sender_class, mock_config):
        """Test signup with already registered email."""
        # Setup mocks
        mock_config.DEFAULT_USER_PASSWORD = "TestPass123!"  # Valid password for tests

        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(entity_id="email-123", email="test@example.com")
        mock_email_service.get_email_by_email_address.return_value = existing_email

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method = MagicMock()
        mock_login_method.is_oauth_method = False
        mock_login_method_service.get_login_method_by_email_id.return_value = mock_login_method

        auth_service = AuthService(mock_config)

        # Execute and verify exception
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.signup("test@example.com", "John", "Doe")

        assert "already registered" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_signup_with_oauth_existing_email(self, mock_person_service_class, mock_email_service_class,
                                             mock_login_method_service_class, mock_org_service_class,
                                             mock_por_service_class, mock_message_sender_class, mock_config):
        """Test signup when email is already registered with OAuth."""
        # Setup mocks
        mock_config.DEFAULT_USER_PASSWORD = "TestPass123!"  # Valid password for tests

        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(entity_id="email-123", email="test@example.com")
        mock_email_service.get_email_by_email_address.return_value = existing_email

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method = MagicMock()
        mock_login_method.is_oauth_method = True
        mock_login_method.oauth_provider_name = "google"
        mock_login_method_service.get_login_method_by_email_id.return_value = mock_login_method

        auth_service = AuthService(mock_config)

        # Execute and verify exception
        with pytest.raises(InputValidationError) as exc_info:
            auth_service.signup("test@example.com", "John", "Doe")

        assert "google" in str(exc_info.value).lower()


class TestLoginUserByEmailPassword:
    """Tests for login_user_by_email_password method."""

    @patch('common.services.auth.check_password_hash')
    @patch('common.services.auth.generate_access_token')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_success(self, mock_person_service_class, mock_email_service_class,
                          mock_login_method_service_class, mock_org_service_class,
                          mock_por_service_class, mock_message_sender_class,
                          mock_generate_token, mock_check_password, mock_config):
        """Test successful login."""
        # Setup mocks
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123", email="test@example.com")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = False
        login_method.password = "hashed_password"
        login_method.person_id = "person-123"
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        mock_person_service = mock_person_service_class.return_value
        person = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")
        mock_person_service.get_person_by_id.return_value = person

        mock_check_password.return_value = True
        mock_generate_token.return_value = ("access_token", 1234567890)

        auth_service = AuthService(mock_config)

        # Execute
        token, expiry = auth_service.login_user_by_email_password("test@example.com", "password")  # NOSONAR - Test data

        # Verify
        assert token == "access_token"
        assert expiry == 1234567890
        mock_check_password.assert_called_once_with("hashed_password", "password")  # NOSONAR - Test data

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_email_not_registered(self, mock_person_service_class, mock_email_service_class,
                                       mock_login_method_service_class, mock_org_service_class,
                                       mock_por_service_class, mock_message_sender_class, mock_config):
        """Test login with unregistered email."""
        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_email_address.return_value = None

        auth_service = AuthService(mock_config)

        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password")  # NOSONAR - Test data

        assert "not registered" in str(exc_info.value)

    @patch('common.services.auth.check_password_hash')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_incorrect_password(self, mock_person_service_class, mock_email_service_class,
                                     mock_login_method_service_class, mock_org_service_class,
                                     mock_por_service_class, mock_message_sender_class,
                                     mock_check_password, mock_config):
        """Test login with incorrect password."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = False
        login_method.password = "hashed_password"
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        mock_check_password.return_value = False

        auth_service = AuthService(mock_config)

        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "wrong_password")  # NOSONAR - Test data

        assert "Incorrect" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_with_oauth_account(self, mock_person_service_class, mock_email_service_class,
                                      mock_login_method_service_class, mock_org_service_class,
                                      mock_por_service_class, mock_message_sender_class, mock_config):
        """Test login attempt on OAuth account."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = True
        login_method.oauth_provider_name = "google"
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        auth_service = AuthService(mock_config)

        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password")  # NOSONAR - Test data

        assert "google" in str(exc_info.value).lower()


class TestGenerateResetPasswordToken:
    """Tests for generate_reset_password_token method."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_generate_reset_token(self, mock_person_service_class, mock_email_service_class,
                                  mock_login_method_service_class, mock_org_service_class,
                                  mock_por_service_class, mock_message_sender_class, mock_config):
        """Test generating password reset token."""
        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed_password"

        token = auth_service.generate_reset_password_token(login_method, "test@example.com")

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify token
        decoded = jwt.decode(token, "hashed_password", algorithms=['HS256'])
        assert decoded['email'] == "test@example.com"
        assert decoded['email_id'] == "email-123"
        assert decoded['person_id'] == "person-123"
        assert 'exp' in decoded


class TestParseResetPasswordToken:
    """Tests for parse_reset_password_token method."""

    def test_parse_valid_token(self):
        """Test parsing a valid reset token."""
        login_method = MagicMock()
        login_method.password = "secret_key"

        # Create a valid token
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, "secret_key", algorithm='HS256')

        result = AuthService.parse_reset_password_token(token, login_method)

        assert result is not None
        assert result['email'] == 'test@example.com'

    def test_parse_expired_token(self):
        """Test parsing an expired token."""
        login_method = MagicMock()
        login_method.password = "secret_key"

        # Create an expired token
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() - 3600  # Expired
        }
        token = jwt.encode(payload, "secret_key", algorithm='HS256')

        result = AuthService.parse_reset_password_token(token, login_method)

        assert result is None


class TestLoginUserByOAuth:
    """Tests for login_user_by_oauth method."""

    @patch('common.services.auth.generate_access_token')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_existing_user(self, mock_person_service_class, mock_email_service_class,
                                      mock_login_method_service_class, mock_org_service_class,
                                      mock_por_service_class, mock_message_sender_class,
                                      mock_generate_token, mock_config):
        """Test OAuth login for existing user."""
        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(entity_id="email-123", person_id="person-123", is_verified=True)
        mock_email_service.get_email_by_email_address.return_value = existing_email

        mock_person_service = mock_person_service_class.return_value
        person = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")
        mock_person_service.get_person_by_id.return_value = person

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = True
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        mock_generate_token.return_value = ("access_token", 1234567890)

        auth_service = AuthService(mock_config)

        token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        assert token == "access_token"
        assert expiry == 1234567890
        assert returned_person == person

    @patch('common.services.auth.generate_access_token')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_new_user(self, mock_person_service_class, mock_email_service_class,
                                 mock_login_method_service_class, mock_org_service_class,
                                 mock_por_service_class, mock_message_sender_class,
                                 mock_generate_token, mock_config):
        """Test OAuth login for new user creation."""
        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_email_address.return_value = None
        mock_email_service.save_email.return_value = MagicMock(entity_id="email-123", email="test@example.com")

        mock_person_service = mock_person_service_class.return_value
        mock_person_service.save_person.return_value = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method_service.save_login_method.return_value = MagicMock(entity_id="login-123")

        mock_generate_token.return_value = ("access_token", 1234567890)

        auth_service = AuthService(mock_config)

        token, expiry, person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        assert token == "access_token"
        mock_email_service.save_email.assert_called_once()
        mock_person_service.save_person.assert_called_once()


class TestResetUserPassword:
    """Tests for reset_user_password method."""

    @patch('common.services.auth.generate_access_token')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_reset_password_success(self, mock_person_service_class, mock_email_service_class,
                                    mock_login_method_service_class, mock_org_service_class,
                                    mock_por_service_class, mock_message_sender_class,
                                    mock_generate_token, mock_config):
        """Test successful password reset."""
        from common.helpers.string_utils import urlsafe_base64_encode, force_bytes

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "old_hashed_password"
        mock_login_method_service.get_login_method_by_id.return_value = login_method
        mock_login_method_service.update_password.return_value = login_method

        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_id.return_value = email_obj
        mock_email_service.verify_email.return_value = email_obj

        mock_person_service = mock_person_service_class.return_value
        person_obj = MagicMock(entity_id="person-123")
        mock_person_service.get_person_by_id.return_value = person_obj

        mock_generate_token.return_value = ("new_token", 1234567890)

        auth_service = AuthService(mock_config)

        # Create a valid token
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, "old_hashed_password", algorithm='HS256')
        uidb64 = urlsafe_base64_encode(force_bytes("login-123"))

        access_token, expiry, person = auth_service.reset_user_password(token, uidb64, "NewPassword1!")  # NOSONAR - Test data

        assert access_token == "new_token"
        assert expiry == 1234567890
        mock_login_method_service.update_password.assert_called_once()
        mock_email_service.verify_email.assert_called_once()

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_reset_password_invalid_login_method(self, mock_person_service_class, mock_email_service_class,
                                                 mock_login_method_service_class, mock_org_service_class,
                                                 mock_por_service_class, mock_message_sender_class, mock_config):
        """Test password reset with invalid login method."""
        from common.helpers.string_utils import urlsafe_base64_encode, force_bytes

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method_service.get_login_method_by_id.return_value = None

        auth_service = AuthService(mock_config)

        uidb64 = urlsafe_base64_encode(force_bytes("invalid-login-id"))

        with pytest.raises(APIException) as exc_info:
            auth_service.reset_user_password("token", uidb64, "NewPassword1!")  # NOSONAR - Test data

        assert "Invalid password reset URL" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_reset_password_invalid_token(self, mock_person_service_class, mock_email_service_class,
                                          mock_login_method_service_class, mock_org_service_class,
                                          mock_por_service_class, mock_message_sender_class, mock_config):
        """Test password reset with invalid token."""
        from common.helpers.string_utils import urlsafe_base64_encode, force_bytes

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.password = "old_hashed_password"
        mock_login_method_service.get_login_method_by_id.return_value = login_method

        auth_service = AuthService(mock_config)

        uidb64 = urlsafe_base64_encode(force_bytes("login-123"))

        # Create a token that will fail validation - signed with wrong secret
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        invalid_token = jwt.encode(payload, "wrong_secret", algorithm='HS256')

        # The application code doesn't catch InvalidSignatureError, so it propagates
        # We test that it raises a JWT exception (InvalidSignatureError specifically)
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            auth_service.reset_user_password(invalid_token, uidb64, "NewPassword1!")  # NOSONAR - Test data

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_reset_password_expired_token(self, mock_person_service_class, mock_email_service_class,
                                          mock_login_method_service_class, mock_org_service_class,
                                          mock_por_service_class, mock_message_sender_class, mock_config):
        """Test password reset when token is expired."""
        from common.helpers.string_utils import urlsafe_base64_encode, force_bytes

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.password = "old_hashed_password"
        mock_login_method_service.get_login_method_by_id.return_value = login_method

        auth_service = AuthService(mock_config)
        uidb64 = urlsafe_base64_encode(force_bytes("login-123"))

        # Create an expired token
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() - 3600  # Expired 1 hour ago
        }
        expired_token = jwt.encode(payload, "old_hashed_password", algorithm='HS256')

        with pytest.raises(APIException) as exc_info:
            auth_service.reset_user_password(expired_token, uidb64, "NewPassword1!")  # NOSONAR - Test data

        assert "Invalid reset password token" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_reset_password_email_not_found(self, mock_person_service_class, mock_email_service_class,
                                            mock_login_method_service_class, mock_org_service_class,
                                            mock_por_service_class, mock_message_sender_class, mock_config):
        """Test password reset when email is not found."""
        from common.helpers.string_utils import urlsafe_base64_encode, force_bytes

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.password = "old_hashed_password"
        mock_login_method_service.get_login_method_by_id.return_value = login_method

        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_id.return_value = None

        auth_service = AuthService(mock_config)
        uidb64 = urlsafe_base64_encode(force_bytes("login-123"))

        # Create a valid token
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, "old_hashed_password", algorithm='HS256')

        with pytest.raises(APIException) as exc_info:
            auth_service.reset_user_password(token, uidb64, "NewPassword1!")  # NOSONAR - Test data

        assert "Email not found" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_reset_password_person_not_found(self, mock_person_service_class, mock_email_service_class,
                                             mock_login_method_service_class, mock_org_service_class,
                                             mock_por_service_class, mock_message_sender_class, mock_config):
        """Test password reset when person is not found."""
        from common.helpers.string_utils import urlsafe_base64_encode, force_bytes

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.password = "old_hashed_password"
        mock_login_method_service.get_login_method_by_id.return_value = login_method

        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_id.return_value = email_obj

        mock_person_service = mock_person_service_class.return_value
        mock_person_service.get_person_by_id.return_value = None

        auth_service = AuthService(mock_config)
        uidb64 = urlsafe_base64_encode(force_bytes("login-123"))

        # Create a valid token
        payload = {
            'email': 'test@example.com',
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, "old_hashed_password", algorithm='HS256')

        with pytest.raises(APIException) as exc_info:
            auth_service.reset_user_password(token, uidb64, "NewPassword1!")  # NOSONAR - Test data

        assert "Person with email not found" in str(exc_info.value)


class TestTriggerForgotPasswordEmail:
    """Tests for trigger_forgot_password_email method."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_trigger_forgot_password_email_not_registered(self, mock_person_service_class,
                                                          mock_email_service_class,
                                                          mock_login_method_service_class,
                                                          mock_org_service_class,
                                                          mock_por_service_class,
                                                          mock_message_sender_class, mock_config):
        """Test triggering forgot password for unregistered email."""
        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_email_address.return_value = None

        auth_service = AuthService(mock_config)

        with pytest.raises(APIException) as exc_info:
            auth_service.trigger_forgot_password_email("test@example.com")

        assert "not registered" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_trigger_forgot_password_person_not_exist(self, mock_person_service_class,
                                                       mock_email_service_class,
                                                       mock_login_method_service_class,
                                                       mock_org_service_class,
                                                       mock_por_service_class,
                                                       mock_message_sender_class, mock_config):
        """Test triggering forgot password when person doesn't exist."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123", person_id="person-123", email="test@example.com")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_person_service = mock_person_service_class.return_value
        mock_person_service.get_person_by_id.return_value = None

        auth_service = AuthService(mock_config)

        with pytest.raises(APIException) as exc_info:
            auth_service.trigger_forgot_password_email("test@example.com")

        assert "Person does not exist" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_trigger_forgot_password_login_method_not_exist(self, mock_person_service_class,
                                                             mock_email_service_class,
                                                             mock_login_method_service_class,
                                                             mock_org_service_class,
                                                             mock_por_service_class,
                                                             mock_message_sender_class, mock_config):
        """Test triggering forgot password when login method doesn't exist."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123", person_id="person-123", email="test@example.com")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_person_service = mock_person_service_class.return_value
        person = MagicMock(entity_id="person-123")
        mock_person_service.get_person_by_id.return_value = person

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method_service.get_login_method_by_email_id.return_value = None

        auth_service = AuthService(mock_config)

        with pytest.raises(APIException) as exc_info:
            auth_service.trigger_forgot_password_email("test@example.com")

        assert "Login method does not exist" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_trigger_forgot_password_success(self, mock_person_service_class,
                                             mock_email_service_class,
                                             mock_login_method_service_class,
                                             mock_org_service_class,
                                             mock_por_service_class,
                                             mock_message_sender_class, mock_config):
        """Test successful forgot password email trigger."""
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = 3600
        mock_config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email-queue"

        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123", person_id="person-123", email="test@example.com")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_person_service = mock_person_service_class.return_value
        person = MagicMock(entity_id="person-123")
        mock_person_service.get_person_by_id.return_value = person

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock(entity_id="login-123", person_id="person-123", email_id="email-123", password="hashed_password")
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        # Mock the message sender instance
        mock_message_sender = MagicMock()
        mock_message_sender_class.return_value = mock_message_sender

        auth_service = AuthService(mock_config)

        # This should complete successfully and send password reset email
        auth_service.trigger_forgot_password_email("test@example.com")

        # Verify get_login_method_by_email_id was called with correct email entity_id
        mock_login_method_service.get_login_method_by_email_id.assert_called_once_with("email-123")

        # Verify send_message was called (password reset email was sent)
        assert mock_message_sender.send_message.called


class TestPreparePasswordResetUrl:
    """Tests for prepare_password_reset_url method."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_prepare_password_reset_url(self, mock_person_service_class, mock_email_service_class,
                                       mock_login_method_service_class, mock_org_service_class,
                                       mock_por_service_class, mock_message_sender_class, mock_config):
        """Test preparing password reset URL."""
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = "3600"

        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed_password"

        url = auth_service.prepare_password_reset_url(login_method, "test@example.com")

        assert url is not None
        assert url.startswith("http://localhost:3000/set-password/")
        assert "login-123" in url or "bG9naW4tMTIz" in url  # base64 encoded


class TestSendPasswordResetEmail:
    """Tests for send_password_reset_email method."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_send_password_reset_email(self, mock_person_service_class, mock_email_service_class,
                                       mock_login_method_service_class, mock_org_service_class,
                                       mock_por_service_class, mock_message_sender_class, mock_config):
        """Test sending password reset email."""
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = "3600"
        mock_config.QUEUE_NAME_PREFIX = "test_"
        mock_config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email_queue"

        mock_message_sender = mock_message_sender_class.return_value

        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed_password"

        auth_service.send_password_reset_email("test@example.com", login_method)

        mock_message_sender.send_message.assert_called_once()
        call_args = mock_message_sender.send_message.call_args[0]
        assert call_args[0] == "test_email_queue"
        assert call_args[1]["event"] == "RESET_PASSWORD"
        assert "test@example.com" in call_args[1]["to_emails"]


class TestSendWelcomeEmail:
    """Tests for send_welcome_email method."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_send_welcome_email(self, mock_person_service_class, mock_email_service_class,
                                mock_login_method_service_class, mock_org_service_class,
                                mock_por_service_class, mock_message_sender_class, mock_config):
        """Test sending welcome email."""
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = "3600"
        mock_config.QUEUE_NAME_PREFIX = "test_"
        mock_config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email_queue"

        mock_message_sender = mock_message_sender_class.return_value

        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed_password"

        person = MagicMock()
        person.first_name = "John"
        person.last_name = "Doe"

        auth_service.send_welcome_email(login_method, person, "test@example.com")

        mock_message_sender.send_message.assert_called_once()
        call_args = mock_message_sender.send_message.call_args[0]
        assert call_args[0] == "test_email_queue"
        assert call_args[1]["event"] == "WELCOME_EMAIL"
        assert "test@example.com" in call_args[1]["to_emails"]
        assert call_args[1]["data"]["recipient_name"] == "John Doe"

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_send_welcome_email_no_reset_url(self, mock_person_service_class, mock_email_service_class,
                                             mock_login_method_service_class, mock_org_service_class,
                                             mock_por_service_class, mock_message_sender_class, mock_config):
        """Test send_welcome_email when prepare_password_reset_url returns None (line 98 branch)."""
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = "3600"
        mock_config.QUEUE_NAME_PREFIX = "test_"
        mock_config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email_queue"

        mock_message_sender = mock_message_sender_class.return_value

        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed_password"

        person = MagicMock()
        person.first_name = "John"
        person.last_name = "Doe"

        # Mock prepare_password_reset_url to return None to test the branch
        with patch.object(auth_service, 'prepare_password_reset_url', return_value=None):
            auth_service.send_welcome_email(login_method, person, "test@example.com")

        # No message should be sent when confirmation_link is None
        mock_message_sender.send_message.assert_not_called()

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_send_password_reset_email_no_reset_url(self, mock_person_service_class, mock_email_service_class,
                                                    mock_login_method_service_class, mock_org_service_class,
                                                    mock_por_service_class, mock_message_sender_class, mock_config):
        """Test send_password_reset_email when prepare_password_reset_url returns None (line 273 branch)."""
        mock_config.VUE_APP_URI = "http://localhost:3000"
        mock_config.RESET_TOKEN_EXPIRE = "3600"
        mock_config.QUEUE_NAME_PREFIX = "test_"
        mock_config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME = "email_queue"

        mock_message_sender = mock_message_sender_class.return_value

        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.entity_id = "login-123"
        login_method.person_id = "person-123"
        login_method.email_id = "email-123"
        login_method.password = "hashed_password"

        # Mock prepare_password_reset_url to return None to test the branch
        with patch.object(auth_service, 'prepare_password_reset_url', return_value=None):
            auth_service.send_password_reset_email("test@example.com", login_method)

        # No message should be sent when password_reset_url is None
        mock_message_sender.send_message.assert_not_called()

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_parse_reset_password_token_expired_time_check(self, mock_person_service_class, mock_email_service_class,
                                                           mock_login_method_service_class, mock_org_service_class,
                                                           mock_por_service_class, mock_message_sender_class, mock_config):
        """Test parse_reset_password_token when token passes JWT validation but fails time check (line 252 branch to exit)."""
        import jwt
        import time

        auth_service = AuthService(mock_config)

        login_method = MagicMock()
        login_method.password = "secret_key"

        # Create a token with an exp time in the past (but JWT decoding won't raise ExpiredSignatureError
        # because we'll mock jwt.decode to not check expiration)
        exp_time = time.time() - 100  # 100 seconds ago

        # Manually create the decoded token data (bypassing JWT's expiration check)
        decoded_data = {"exp": exp_time, "data": "test"}

        # Mock jwt.decode to return our decoded data without raising ExpiredSignatureError
        with patch('common.services.auth.jwt.decode', return_value=decoded_data):
            # Mock time.time() to return a time AFTER exp_time
            with patch('common.services.auth.time.time', return_value=exp_time + 10):
                result = auth_service.parse_reset_password_token("dummy_token", login_method)

        # Should return None because time.time() > exp_time (line 252 branch to exit)
        assert result is None


class TestOAuthLoginEdgeCases:
    """Tests for OAuth login edge cases."""

    @patch('common.services.auth.generate_access_token')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_existing_user_no_login_method(self, mock_person_service_class,
                                                       mock_email_service_class,
                                                       mock_login_method_service_class,
                                                       mock_org_service_class,
                                                       mock_por_service_class,
                                                       mock_message_sender_class,
                                                       mock_generate_token, mock_config):
        """Test OAuth login for existing user without login method."""
        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(entity_id="email-123", person_id="person-123", is_verified=False)
        mock_email_service.get_email_by_email_address.return_value = existing_email
        mock_email_service.verify_email.return_value = existing_email

        mock_person_service = mock_person_service_class.return_value
        person = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")
        mock_person_service.get_person_by_id.return_value = person

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method_service.get_login_method_by_email_id.return_value = None
        mock_login_method_service.save_login_method.return_value = MagicMock(entity_id="login-123")

        mock_generate_token.return_value = ("access_token", 1234567890)

        auth_service = AuthService(mock_config)

        token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        assert token == "access_token"
        assert expiry == 1234567890
        mock_login_method_service.save_login_method.assert_called_once()

    @patch('common.services.auth.generate_access_token')
    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_existing_user_unverified_email(self, mock_person_service_class,
                                                        mock_email_service_class,
                                                        mock_login_method_service_class,
                                                        mock_org_service_class,
                                                        mock_por_service_class,
                                                        mock_message_sender_class,
                                                        mock_generate_token, mock_config):
        """Test OAuth login verifies unverified email."""
        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(entity_id="email-123", person_id="person-123", is_verified=False)
        mock_email_service.get_email_by_email_address.return_value = existing_email
        verified_email = MagicMock(entity_id="email-123", person_id="person-123", is_verified=True)
        mock_email_service.verify_email.return_value = verified_email

        mock_person_service = mock_person_service_class.return_value
        person = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")
        mock_person_service.get_person_by_id.return_value = person

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = True
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        mock_generate_token.return_value = ("access_token", 1234567890)

        auth_service = AuthService(mock_config)

        token, expiry, returned_person = auth_service.login_user_by_oauth(
            "test@example.com", "John", "Doe", "google", {"sub": "123"}
        )

        assert token == "access_token"
        mock_email_service.verify_email.assert_called_once_with(existing_email)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_existing_user_no_person(self, mock_person_service_class,
                                                 mock_email_service_class,
                                                 mock_login_method_service_class,
                                                 mock_org_service_class,
                                                 mock_por_service_class,
                                                 mock_message_sender_class, mock_config):
        """Test OAuth login when person doesn't exist."""
        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(entity_id="email-123", person_id="person-123")
        mock_email_service.get_email_by_email_address.return_value = existing_email

        mock_person_service = mock_person_service_class.return_value
        mock_person_service.get_person_by_id.return_value = None

        auth_service = AuthService(mock_config)

        with pytest.raises(APIException) as exc_info:
            auth_service.login_user_by_oauth(
                "test@example.com", "John", "Doe", "google", {"sub": "123"}
            )

        assert "Person not found" in str(exc_info.value)


class TestLoginUserByEmailPasswordEdgeCases:
    """Tests for login_user_by_email_password edge cases."""

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_no_login_method(self, mock_person_service_class, mock_email_service_class,
                                   mock_login_method_service_class, mock_org_service_class,
                                   mock_por_service_class, mock_message_sender_class, mock_config):
        """Test login when no login method exists."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_login_method_service = mock_login_method_service_class.return_value
        mock_login_method_service.get_login_method_by_email_id.return_value = None

        auth_service = AuthService(mock_config)

        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password")  # NOSONAR - Test data

        assert "Login method not found" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_no_password_set(self, mock_person_service_class, mock_email_service_class,
                                   mock_login_method_service_class, mock_org_service_class,
                                   mock_por_service_class, mock_message_sender_class, mock_config):
        """Test login when password is not set."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = False
        login_method.password = None
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        auth_service = AuthService(mock_config)

        with pytest.raises(InputValidationError) as exc_info:
            auth_service.login_user_by_email_password("test@example.com", "password")  # NOSONAR - Test data

        assert "does not have a password set" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_login_person_not_found(self, mock_person_service_class, mock_email_service_class,
                                    mock_login_method_service_class, mock_org_service_class,
                                    mock_por_service_class, mock_message_sender_class, mock_config):
        """Test login when person is not found (line 137)."""
        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(entity_id="email-123")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_login_method_service = mock_login_method_service_class.return_value
        login_method = MagicMock()
        login_method.is_oauth_method = False
        login_method.password = "hashed_password"
        login_method.person_id = "person-123"
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method

        mock_person_service = mock_person_service_class.return_value
        mock_person_service.get_person_by_id.return_value = None  # Person not found

        with patch('common.services.auth.check_password_hash', return_value=True):
            auth_service = AuthService(mock_config)

            with pytest.raises(InputValidationError) as exc_info:
                auth_service.login_user_by_email_password("test@example.com", "password")  # NOSONAR - Test data

            assert "Could not find complete user profile" in str(exc_info.value)

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_convert_non_oauth_to_oauth(self, mock_person_service_class, mock_email_service_class,
                                                    mock_login_method_service_class, mock_org_service_class,
                                                    mock_por_service_class, mock_message_sender_class, mock_config):
        """Test OAuth login converts non-OAuth account to OAuth (lines 189-193)."""
        mock_email_service = mock_email_service_class.return_value
        existing_email = MagicMock(person_id="person-123", is_verified=True)
        mock_email_service.get_email_by_email_address.return_value = existing_email

        mock_person_service = mock_person_service_class.return_value
        existing_person = Person(first_name="John", last_name="Doe")
        mock_person_service.get_person_by_id.return_value = existing_person

        mock_login_method_service = mock_login_method_service_class.return_value
        # Create a login method that is NOT an OAuth method
        login_method = LoginMethod(person_id="person-123", email_id="email-123", method_type="email", password="hashed")
        login_method.is_oauth_method = False
        mock_login_method_service.get_login_method_by_email_id.return_value = login_method
        mock_login_method_service.save_login_method = MagicMock()

        with patch('common.services.auth.generate_access_token', return_value=("token", 1234567890)):
            auth_service = AuthService(mock_config)
            token, expiry, person = auth_service.login_user_by_oauth(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                provider="google",
                provider_data={"sub": "google-id"}
            )

            # Verify save_login_method was called to convert to OAuth
            mock_login_method_service.save_login_method.assert_called_once()
            assert token == "token"
            assert expiry == 1234567890
            assert person == existing_person

    @patch('common.services.auth.MessageSender')
    @patch('common.services.auth.PersonOrganizationRoleService')
    @patch('common.services.auth.OrganizationService')
    @patch('common.services.auth.LoginMethodService')
    @patch('common.services.auth.EmailService')
    @patch('common.services.auth.PersonService')
    def test_oauth_login_new_user_with_person_id(self, mock_person_service_class, mock_email_service_class,
                                                 mock_login_method_service_class, mock_org_service_class,
                                                 mock_por_service_class, mock_message_sender_class, mock_config):
        """Test OAuth login for new user with person_id parameter (line 206)."""
        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_email_address.return_value = None  # New user

        mock_person_service = mock_person_service_class.return_value
        new_person = Person(first_name="Jane", last_name="Smith")
        new_person.entity_id = "person-456"
        mock_person_service.save_person.return_value = new_person

        new_email = Email(email="jane@example.com", person_id="person-456", is_verified=True)
        new_email.entity_id = "email-456"
        mock_email_service.save_email.return_value = new_email

        mock_login_method_service = mock_login_method_service_class.return_value
        new_login_method = LoginMethod(person_id="person-456", email_id="email-456", method_type="oauth-google")
        mock_login_method_service.save_login_method.return_value = new_login_method

        with patch('common.services.auth.generate_access_token', return_value=("token", 1234567890)):
            auth_service = AuthService(mock_config)
            token, expiry, person = auth_service.login_user_by_oauth(
                email="jane@example.com",
                first_name="Jane",
                last_name="Smith",
                provider="google",
                provider_data={"sub": "google-id"},
                person_id="custom-person-id"  # This triggers line 206
            )

            assert token == "token"
            assert expiry == 1234567890
            assert person == new_person

