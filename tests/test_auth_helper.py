"""
Comprehensive tests for common/helpers/auth.py
"""
import pytest
import time
import jwt
from unittest.mock import MagicMock, patch
from common.helpers.auth import (
    generate_access_token,
    parse_access_token,
    create_person_from_token,
    create_email_from_token
)
from common.models import LoginMethod, Person, Email


@pytest.fixture
def mock_login_method():
    """Create a mock login method."""
    login_method = MagicMock(spec=LoginMethod)
    login_method.email_id = "email-123"
    login_method.person_id = "person-123"
    return login_method


@pytest.fixture
def mock_person():
    """Create a mock person."""
    person = MagicMock(spec=Person)
    person.entity_id = "person-123"
    person.first_name = "John"
    person.last_name = "Doe"
    return person


@pytest.fixture
def mock_email():
    """Create a mock email."""
    email = MagicMock(spec=Email)
    email.entity_id = "email-123"
    email.email = "test@example.com"
    email.is_verified = True
    return email


class TestGenerateAccessToken:
    """Tests for generate_access_token function."""

    @patch('common.helpers.auth.config')
    def test_generate_access_token_with_person_and_email(self, mock_config, mock_login_method, mock_person, mock_email):
        """Test generating access token with person and email data."""
        # Setup
        mock_config.ACCESS_TOKEN_EXPIRE = 3600
        mock_config.AUTH_JWT_SECRET = "test-secret"

        # Execute
        token, expiry = generate_access_token(mock_login_method, person=mock_person, email=mock_email)

        # Verify
        assert token is not None
        assert isinstance(token, str)
        assert expiry > time.time()

        # Decode and verify payload
        decoded = jwt.decode(token, mock_config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['email_id'] == "email-123"
        assert decoded['person_id'] == "person-123"
        assert decoded['person_first_name'] == "John"
        assert decoded['person_last_name'] == "Doe"
        assert decoded['person_entity_id'] == "person-123"
        assert decoded['email_address'] == "test@example.com"
        assert decoded['email_is_verified'] is True
        assert decoded['email_entity_id'] == "email-123"

    @patch('common.helpers.auth.config')
    def test_generate_access_token_without_person_and_email(self, mock_config, mock_login_method):
        """Test generating access token without person and email data."""
        # Setup
        mock_config.ACCESS_TOKEN_EXPIRE = 3600
        mock_config.AUTH_JWT_SECRET = "test-secret"

        # Execute
        token, expiry = generate_access_token(mock_login_method)

        # Verify
        assert token is not None
        assert isinstance(token, str)
        assert expiry > time.time()

        # Decode and verify payload
        decoded = jwt.decode(token, mock_config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['email_id'] == "email-123"
        assert decoded['person_id'] == "person-123"
        assert 'person_first_name' not in decoded
        assert 'email_address' not in decoded

    @patch('common.helpers.auth.config')
    def test_generate_access_token_with_only_person(self, mock_config, mock_login_method, mock_person):
        """Test generating access token with only person data."""
        # Setup
        mock_config.ACCESS_TOKEN_EXPIRE = 3600
        mock_config.AUTH_JWT_SECRET = "test-secret"

        # Execute
        token, expiry = generate_access_token(mock_login_method, person=mock_person)

        # Verify
        decoded = jwt.decode(token, mock_config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['person_first_name'] == "John"
        assert decoded['person_last_name'] == "Doe"
        assert 'email_address' not in decoded

    @patch('common.helpers.auth.config')
    def test_generate_access_token_with_only_email(self, mock_config, mock_login_method, mock_email):
        """Test generating access token with only email data."""
        # Setup
        mock_config.ACCESS_TOKEN_EXPIRE = 3600
        mock_config.AUTH_JWT_SECRET = "test-secret"

        # Execute
        token, expiry = generate_access_token(mock_login_method, email=mock_email)

        # Verify
        decoded = jwt.decode(token, mock_config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['email_address'] == "test@example.com"
        assert decoded['email_is_verified'] is True
        assert 'person_first_name' not in decoded

    @patch('common.helpers.auth.config')
    def test_generate_access_token_with_empty_names(self, mock_config, mock_login_method, mock_email):
        """Test generating access token with None values for names."""
        # Setup
        mock_config.ACCESS_TOKEN_EXPIRE = 3600
        mock_config.AUTH_JWT_SECRET = "test-secret"

        person = MagicMock(spec=Person)
        person.entity_id = "person-123"
        person.first_name = None
        person.last_name = None

        # Execute
        token, expiry = generate_access_token(mock_login_method, person=person, email=mock_email)

        # Verify
        decoded = jwt.decode(token, mock_config.AUTH_JWT_SECRET, algorithms=['HS256'])
        assert decoded['person_first_name'] == ''
        assert decoded['person_last_name'] == ''


class TestParseAccessToken:
    """Tests for parse_access_token function."""

    @patch('common.helpers.auth.config')
    def test_parse_access_token_valid(self, mock_config):
        """Test parsing a valid access token."""
        # Setup
        mock_config.AUTH_JWT_SECRET = "test-secret"

        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, mock_config.AUTH_JWT_SECRET, algorithm='HS256')

        # Execute
        decoded = parse_access_token(token)

        # Verify
        assert decoded is not None
        assert decoded['email_id'] == 'email-123'
        assert decoded['person_id'] == 'person-123'

    @patch('common.helpers.auth.config')
    def test_parse_access_token_expired(self, mock_config):
        """Test parsing an expired access token."""
        # Setup
        mock_config.AUTH_JWT_SECRET = "test-secret"

        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() - 100  # Expired
        }
        token = jwt.encode(payload, mock_config.AUTH_JWT_SECRET, algorithm='HS256')

        # Execute
        decoded = parse_access_token(token)

        # Verify
        assert decoded is None

    @patch('common.helpers.auth.config')
    def test_parse_access_token_invalid_signature(self, mock_config):
        """Test parsing token with invalid signature."""
        # Setup
        mock_config.AUTH_JWT_SECRET = "test-secret"

        payload = {
            'email_id': 'email-123',
            'person_id': 'person-123',
            'exp': time.time() + 3600
        }
        token = jwt.encode(payload, "wrong-secret", algorithm='HS256')

        # Execute
        decoded = parse_access_token(token)

        # Verify
        assert decoded is None

    @patch('common.helpers.auth.config')
    def test_parse_access_token_malformed(self, mock_config):
        """Test parsing a malformed token."""
        # Setup
        mock_config.AUTH_JWT_SECRET = "test-secret"

        # Execute
        decoded = parse_access_token("not-a-valid-jwt-token")

        # Verify
        assert decoded is None


class TestCreatePersonFromToken:
    """Tests for create_person_from_token function."""

    def test_create_person_from_token_with_all_data(self):
        """Test creating person from token with all fields."""
        # Setup
        token_data = {
            'person_entity_id': 'person-123',
            'person_first_name': 'John',
            'person_last_name': 'Doe'
        }

        # Execute
        person = create_person_from_token(token_data)

        # Verify
        assert isinstance(person, Person)
        assert person.entity_id == 'person-123'
        assert person.first_name == 'John'
        assert person.last_name == 'Doe'

    def test_create_person_from_token_with_person_id_fallback(self):
        """Test creating person when using person_id instead of person_entity_id."""
        # Setup
        token_data = {
            'person_id': 'person-456',
            'person_first_name': 'Jane',
            'person_last_name': 'Smith'
        }

        # Execute
        person = create_person_from_token(token_data)

        # Verify
        assert person.entity_id == 'person-456'
        assert person.first_name == 'Jane'
        assert person.last_name == 'Smith'

    def test_create_person_from_token_with_missing_data(self):
        """Test creating person from token with missing optional fields."""
        # Setup
        token_data = {
            'person_id': 'person-789'
        }

        # Execute
        person = create_person_from_token(token_data)

        # Verify
        assert person.entity_id == 'person-789'
        assert person.first_name == ''
        assert person.last_name == ''


class TestCreateEmailFromToken:
    """Tests for create_email_from_token function."""

    def test_create_email_from_token_with_all_data(self):
        """Test creating email from token with all fields."""
        # Setup
        token_data = {
            'email_entity_id': 'email-123',
            'person_id': 'person-123',
            'email_address': 'test@example.com',
            'email_is_verified': True
        }

        # Execute
        email = create_email_from_token(token_data)

        # Verify
        assert isinstance(email, Email)
        assert email.entity_id == 'email-123'
        assert email.person_id == 'person-123'
        assert email.email == 'test@example.com'
        assert email.is_verified is True

    def test_create_email_from_token_with_email_id_fallback(self):
        """Test creating email when using email_id instead of email_entity_id."""
        # Setup
        token_data = {
            'email_id': 'email-456',
            'person_id': 'person-456',
            'email_address': 'jane@example.com',
            'email_is_verified': False
        }

        # Execute
        email = create_email_from_token(token_data)

        # Verify
        assert email.entity_id == 'email-456'
        assert email.person_id == 'person-456'
        assert email.email == 'jane@example.com'
        assert email.is_verified is False

    def test_create_email_from_token_with_missing_data(self):
        """Test creating email from token with missing optional fields."""
        # Setup
        token_data = {
            'email_id': 'email-789',
            'person_id': 'person-789'
        }

        # Execute
        email = create_email_from_token(token_data)

        # Verify
        assert email.entity_id == 'email-789'
        assert email.person_id == 'person-789'
        assert email.email == ''
        assert email.is_verified is False

    def test_create_email_from_token_verified_status(self):
        """Test creating email with different verification statuses."""
        # Setup - Verified
        token_data_verified = {
            'email_entity_id': 'email-verified',
            'person_id': 'person-123',
            'email_address': 'verified@example.com',
            'email_is_verified': True
        }

        # Execute
        email_verified = create_email_from_token(token_data_verified)

        # Verify
        assert email_verified.is_verified is True

        # Setup - Unverified
        token_data_unverified = {
            'email_entity_id': 'email-unverified',
            'person_id': 'person-123',
            'email_address': 'unverified@example.com',
            'email_is_verified': False
        }

        # Execute
        email_unverified = create_email_from_token(token_data_unverified)

        # Verify
        assert email_unverified.is_verified is False
