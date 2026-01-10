"""
Unit tests for common/services/email.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.email import EmailService
from common.models import Email


class TestEmailServiceInitialization:
    """Tests for EmailService initialization."""

    @patch('common.services.email.RepositoryFactory')
    def test_init_creates_repository(self, mock_factory_class, mock_config):
        """Test that __init__ creates email repository."""
        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = MagicMock()

        service = EmailService(mock_config)

        assert service.config == mock_config
        assert service.repository_factory is not None
        assert service.email_repo is not None


class TestSaveEmail:
    """Tests for save_email method."""

    @patch('common.services.email.RepositoryFactory')
    def test_save_email_success(self, mock_factory_class, mock_config):
        """Test successful email save."""
        mock_repo = MagicMock()
        saved_email = MagicMock(entity_id="email-123", email="test@example.com")
        mock_repo.save.return_value = saved_email

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        email = Email(person_id="person-123", email="test@example.com")
        result = service.save_email(email)

        assert result == saved_email
        mock_repo.save.assert_called_once_with(email)

    @patch('common.services.email.RepositoryFactory')
    def test_save_email_returns_saved_instance(self, mock_factory_class, mock_config):
        """Test that save_email returns the saved email instance."""
        mock_repo = MagicMock()
        email_input = MagicMock(email="test@example.com")
        email_saved = MagicMock(email="test@example.com", entity_id="new-id")
        mock_repo.save.return_value = email_saved

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.save_email(email_input)

        assert result == email_saved
        assert result.entity_id == "new-id"


class TestGetEmailByEmailAddress:
    """Tests for get_email_by_email_address method."""

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_address_found(self, mock_factory_class, mock_config):
        """Test getting email by address when found."""
        mock_repo = MagicMock()
        found_email = MagicMock(email="test@example.com", entity_id="email-123")
        mock_repo.get_one.return_value = found_email

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.get_email_by_email_address("test@example.com")

        assert result == found_email
        mock_repo.get_one.assert_called_once_with({'email': 'test@example.com'})

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_address_not_found(self, mock_factory_class, mock_config):
        """Test getting email by address when not found."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.get_email_by_email_address("nonexistent@example.com")

        assert result is None
        mock_repo.get_one.assert_called_once_with({'email': 'nonexistent@example.com'})


class TestGetEmailById:
    """Tests for get_email_by_id method."""

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_id_found(self, mock_factory_class, mock_config):
        """Test getting email by ID when found."""
        mock_repo = MagicMock()
        found_email = MagicMock(entity_id="email-123", email="test@example.com")
        mock_repo.get_one.return_value = found_email

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.get_email_by_id("email-123")

        assert result == found_email
        mock_repo.get_one.assert_called_once_with({'entity_id': 'email-123'})

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_id_not_found(self, mock_factory_class, mock_config):
        """Test getting email by ID when not found."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.get_email_by_id("nonexistent-id")

        assert result is None


class TestVerifyEmail:
    """Tests for verify_email method."""

    @patch('common.services.email.RepositoryFactory')
    def test_verify_email_sets_verified_flag(self, mock_factory_class, mock_config):
        """Test that verify_email sets is_verified to True."""
        mock_repo = MagicMock()
        email = MagicMock(entity_id="email-123", is_verified=False)
        verified_email = MagicMock(entity_id="email-123", is_verified=True)
        mock_repo.save.return_value = verified_email

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.verify_email(email)

        assert email.is_verified is True
        assert result == verified_email
        mock_repo.save.assert_called_once_with(email)

    @patch('common.services.email.RepositoryFactory')
    def test_verify_email_already_verified(self, mock_factory_class, mock_config):
        """Test verifying an already verified email."""
        mock_repo = MagicMock()
        email = MagicMock(entity_id="email-123", is_verified=True)
        mock_repo.save.return_value = email

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = EmailService(mock_config)
        result = service.verify_email(email)

        assert result.is_verified is True
        mock_repo.save.assert_called_once()
