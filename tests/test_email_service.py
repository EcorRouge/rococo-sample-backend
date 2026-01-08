"""
Comprehensive tests for common/services/email.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.email import EmailService
from common.models import Email


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MagicMock()


@pytest.fixture
def email_service(mock_config):
    """Create an EmailService instance with mocked dependencies."""
    with patch('common.services.email.RepositoryFactory'):
        service = EmailService(mock_config)
        service.email_repo = MagicMock()
        return service


class TestEmailService:
    """Tests for EmailService."""

    def test_save_email(self, email_service):
        """Test saving an email."""
        # Setup
        email = MagicMock(spec=Email)
        email.entity_id = "email-123"
        email_service.email_repo.save = MagicMock(return_value=email)

        # Execute
        result = email_service.save_email(email)

        # Verify
        assert result == email
        email_service.email_repo.save.assert_called_once_with(email)

    def test_get_email_by_email_address(self, email_service):
        """Test getting email by email address."""
        # Setup
        email = MagicMock(spec=Email)
        email.email = "test@example.com"
        email_service.email_repo.get_one = MagicMock(return_value=email)

        # Execute
        result = email_service.get_email_by_email_address("test@example.com")

        # Verify
        assert result == email
        email_service.email_repo.get_one.assert_called_once_with({'email': 'test@example.com'})

    def test_get_email_by_email_address_not_found(self, email_service):
        """Test getting email by email address when not found."""
        # Setup
        email_service.email_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = email_service.get_email_by_email_address("notfound@example.com")

        # Verify
        assert result is None

    def test_get_email_by_id(self, email_service):
        """Test getting email by ID."""
        # Setup
        email = MagicMock(spec=Email)
        email.entity_id = "email-123"
        email_service.email_repo.get_one = MagicMock(return_value=email)

        # Execute
        result = email_service.get_email_by_id("email-123")

        # Verify
        assert result == email
        email_service.email_repo.get_one.assert_called_once_with({'entity_id': 'email-123'})

    def test_get_email_by_id_not_found(self, email_service):
        """Test getting email by ID when not found."""
        # Setup
        email_service.email_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = email_service.get_email_by_id("nonexistent")

        # Verify
        assert result is None

    def test_verify_email(self, email_service):
        """Test verifying an email."""
        # Setup
        email = MagicMock(spec=Email)
        email.is_verified = False
        email_service.email_repo.save = MagicMock(return_value=email)

        # Execute
        result = email_service.verify_email(email)

        # Verify
        assert email.is_verified is True
        email_service.email_repo.save.assert_called_once_with(email)
        assert result == email

    def test_verify_email_already_verified(self, email_service):
        """Test verifying an already verified email."""
        # Setup
        email = MagicMock(spec=Email)
        email.is_verified = True
        email_service.email_repo.save = MagicMock(return_value=email)

        # Execute
        result = email_service.verify_email(email)

        # Verify
        assert email.is_verified is True
        email_service.email_repo.save.assert_called_once_with(email)
