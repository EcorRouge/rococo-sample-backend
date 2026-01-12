"""
Tests for common/helpers/auth.py
"""
import time
import jwt
import pytest
from unittest.mock import MagicMock, patch
from common.helpers.auth import (
    generate_access_token,
    parse_access_token,
    create_person_from_token,
    create_email_from_token,
)
from common.models import LoginMethod
from common.app_config import config


class TestGenerateAccessToken:
    """Test cases for generate_access_token function."""

    def test_generate_token_with_login_method_only(self):
        """Test token generation with only login_method."""
        login_method = MagicMock()
        login_method.email_id = "email-123"
        login_method.person_id = "person-123"

        token, expiry = generate_access_token(login_method)

        assert token is not None
        assert isinstance(token, str)
        assert expiry > time.time()

        # Decode and verify payload
        decoded = jwt.decode(token, config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['email_id'] == "email-123"
        assert decoded['person_id'] == "person-123"
        assert decoded['exp'] == expiry

    def test_generate_token_with_person(self):
        """Test token generation with login_method and person."""
        login_method = MagicMock()
        login_method.email_id = "email-123"
        login_method.person_id = "person-123"

        person = MagicMock()
        person.first_name = "John"
        person.last_name = "Doe"
        person.entity_id = "person-entity-123"

        token, expiry = generate_access_token(login_method, person=person)

        decoded = jwt.decode(token, config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['person_first_name'] == "John"
        assert decoded['person_last_name'] == "Doe"
        assert decoded['person_entity_id'] == "person-entity-123"

    def test_generate_token_with_email(self):
        """Test token generation with login_method and email."""
        login_method = MagicMock()
        login_method.email_id = "email-123"
        login_method.person_id = "person-123"

        email = MagicMock()
        email.email = "test@example.com"
        email.is_verified = True
        email.entity_id = "email-entity-123"

        token, expiry = generate_access_token(login_method, email=email)

        decoded = jwt.decode(token, config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['email_address'] == "test@example.com"
        assert decoded['email_is_verified'] is True
        assert decoded['email_entity_id'] == "email-entity-123"

    def test_generate_token_with_all_params(self):
        """Test token generation with all parameters."""
        login_method = MagicMock()
        login_method.email_id = "email-123"
        login_method.person_id = "person-123"

        person = MagicMock()
        person.first_name = "Jane"
        person.last_name = "Smith"
        person.entity_id = "person-entity-456"

        email = MagicMock()
        email.email = "jane@example.com"
        email.is_verified = False
        email.entity_id = "email-entity-456"

        token, expiry = generate_access_token(login_method, person=person, email=email)

        decoded = jwt.decode(token, config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['email_id'] == "email-123"
        assert decoded['person_id'] == "person-123"
        assert decoded['person_first_name'] == "Jane"
        assert decoded['person_last_name'] == "Smith"
        assert decoded['person_entity_id'] == "person-entity-456"
        assert decoded['email_address'] == "jane@example.com"
        assert decoded['email_is_verified'] is False
        assert decoded['email_entity_id'] == "email-entity-456"

    def test_generate_token_with_none_first_name(self):
        """Test token generation when person has None first_name."""
        login_method = MagicMock()
        login_method.email_id = "email-123"
        login_method.person_id = "person-123"

        person = MagicMock()
        person.first_name = None
        person.last_name = "Doe"
        person.entity_id = "person-entity-123"

        token, expiry = generate_access_token(login_method, person=person)

        decoded = jwt.decode(token, config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['person_first_name'] == ""
        assert decoded['person_last_name'] == "Doe"

    def test_generate_token_with_none_last_name(self):
        """Test token generation when person has None last_name."""
        login_method = MagicMock()
        login_method.email_id = "email-123"
        login_method.person_id = "person-123"

        person = MagicMock()
        person.first_name = "John"
        person.last_name = None
        person.entity_id = "person-entity-123"

        token, expiry = generate_access_token(login_method, person=person)

        decoded = jwt.decode(token, config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['person_first_name'] == "John"
        assert decoded['person_last_name'] == ""


class TestParseAccessToken:
    """Test cases for parse_access_token function."""

    def test_parse_valid_token(self):
        """Test parsing a valid token."""
        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600,  # Expires in 1 hour
        }
        token = jwt.encode(payload, config.AUTH_JWT_SECRET, algorithm='HS256')

        result = parse_access_token(token)

        assert result is not None
        assert result['email_id'] == 'email-123'
        assert result['person_id'] == 'person-123'

    def test_parse_expired_token(self):
        """Test parsing an expired token."""
        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() - 3600,  # Expired 1 hour ago
        }
        token = jwt.encode(payload, config.AUTH_JWT_SECRET, algorithm='HS256')

        result = parse_access_token(token)

        assert result is None

    @patch('common.helpers.auth.jwt.decode')
    @patch('common.helpers.auth.time')
    def test_parse_token_time_check_fails(self, mock_time, mock_jwt_decode):
        """Test the time check branch when token decodes but time check fails."""
        # Mock jwt.decode to return a valid decoded token (bypassing ExpiredSignatureError)
        mock_jwt_decode.return_value = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': 1000.0
        }
        # Mock time to be greater than exp
        mock_time.time.return_value = 2000.0

        result = parse_access_token('any-token')

        # Should return None because time.time() > exp_time
        assert result is None

    def test_parse_invalid_token(self):
        """Test parsing an invalid token."""
        invalid_token = "invalid.token.here"

        result = parse_access_token(invalid_token)

        assert result is None

    def test_parse_token_with_wrong_secret(self):
        """Test parsing a token signed with wrong secret."""
        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600,
        }
        token = jwt.encode(payload, 'wrong-secret', algorithm='HS256')

        result = parse_access_token(token)

        assert result is None

    def test_parse_malformed_token(self):
        """Test parsing a malformed token."""
        result = parse_access_token("noteven.atoken")

        assert result is None

    def test_parse_token_missing_exp(self):
        """Test parsing a token without exp field."""
        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
        }
        token = jwt.encode(payload, config.AUTH_JWT_SECRET, algorithm='HS256')

        # The application code will raise KeyError when 'exp' is missing
        with pytest.raises(KeyError):
            parse_access_token(token)


class TestCreatePersonFromToken:
    """Test cases for create_person_from_token function."""

    def test_create_person_with_complete_data(self):
        """Test creating person with complete token data."""
        token_data = {
            'person_entity_id': 'person-entity-123',
            'person_first_name': 'Alice',
            'person_last_name': 'Wonder',
        }

        person = create_person_from_token(token_data)

        assert person.entity_id == 'person-entity-123'
        assert person.first_name == 'Alice'
        assert person.last_name == 'Wonder'

    def test_create_person_with_fallback_entity_id(self):
        """Test creating person using person_id as fallback."""
        token_data = {
            'person_id': 'person-123',
            'person_first_name': 'Bob',
            'person_last_name': 'Builder',
        }

        person = create_person_from_token(token_data)

        assert person.entity_id == 'person-123'
        assert person.first_name == 'Bob'
        assert person.last_name == 'Builder'

    def test_create_person_with_missing_names(self):
        """Test creating person with missing name fields."""
        token_data = {
            'person_entity_id': 'person-entity-456',
        }

        person = create_person_from_token(token_data)

        assert person.entity_id == 'person-entity-456'
        assert person.first_name == ''
        assert person.last_name == ''

    def test_create_person_with_empty_names(self):
        """Test creating person with empty name strings."""
        token_data = {
            'person_entity_id': 'person-entity-789',
            'person_first_name': '',
            'person_last_name': '',
        }

        person = create_person_from_token(token_data)

        assert person.entity_id == 'person-entity-789'
        assert person.first_name == ''
        assert person.last_name == ''


class TestCreateEmailFromToken:
    """Test cases for create_email_from_token function."""

    def test_create_email_with_complete_data(self):
        """Test creating email with complete token data."""
        token_data = {
            'email_entity_id': 'email-entity-123',
            'person_id': 'person-123',
            'email_address': 'test@example.com',
            'email_is_verified': True,
        }

        email = create_email_from_token(token_data)

        assert email.entity_id == 'email-entity-123'
        assert email.person_id == 'person-123'
        assert email.email == 'test@example.com'
        assert email.is_verified is True

    def test_create_email_with_fallback_entity_id(self):
        """Test creating email using email_id as fallback."""
        token_data = {
            'email_id': 'email-123',
            'person_id': 'person-456',
            'email_address': 'fallback@example.com',
            'email_is_verified': False,
        }

        email = create_email_from_token(token_data)

        assert email.entity_id == 'email-123'
        assert email.person_id == 'person-456'
        assert email.email == 'fallback@example.com'
        assert email.is_verified is False

    def test_create_email_with_missing_fields(self):
        """Test creating email with missing optional fields."""
        token_data = {
            'email_entity_id': 'email-entity-789',
            'person_id': 'person-789',
        }

        email = create_email_from_token(token_data)

        assert email.entity_id == 'email-entity-789'
        assert email.person_id == 'person-789'
        assert email.email == ''
        assert email.is_verified is False

    def test_create_email_with_empty_address(self):
        """Test creating email with empty email address."""
        token_data = {
            'email_entity_id': 'email-entity-999',
            'person_id': 'person-999',
            'email_address': '',
            'email_is_verified': True,
        }

        email = create_email_from_token(token_data)

        assert email.entity_id == 'email-entity-999'
        assert email.person_id == 'person-999'
        assert email.email == ''
        assert email.is_verified is True
