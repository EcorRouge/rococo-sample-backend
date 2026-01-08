"""
Unit tests for EmailService class.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestEmailService:
    """Test email service methods."""

    @patch('common.services.email.RepositoryFactory')
    def test_init_initializes_config_and_repository_factory(self, mock_repo_factory_class):
        """Test __init__ initializes config and repository factory."""
        from common.services.email import EmailService

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        service = EmailService(mock_config)

        assert service.config == mock_config
        assert service.repository_factory == mock_repo_factory
        assert service.email_repo == mock_email_repo
        mock_repo_factory_class.assert_called_once_with(mock_config)

    @patch('common.services.email.RepositoryFactory')
    def test_save_email_saves_and_returns_email(self, mock_repo_factory_class):
        """Test save_email method saves and returns email."""
        from common.services.email import EmailService
        from common.models.email import Email

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        test_email = Email(email="test@example.com")
        saved_email = Email(entity_id="saved-id", email="test@example.com")
        mock_email_repo.save.return_value = saved_email

        service = EmailService(mock_config)
        result = service.save_email(test_email)

        assert result == saved_email
        mock_email_repo.save.assert_called_once_with(test_email)

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_email_address_retrieves_correct_email(self, mock_repo_factory_class):
        """Test get_email_by_email_address retrieves correct email."""
        from common.services.email import EmailService
        from common.models.email import Email

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        email_address = "test@example.com"
        expected_email = Email(entity_id="test-id", email=email_address)
        mock_email_repo.get_one.return_value = expected_email

        service = EmailService(mock_config)
        result = service.get_email_by_email_address(email_address)

        assert result == expected_email
        mock_email_repo.get_one.assert_called_once_with({'email': email_address})

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_email_address_returns_none_when_not_found(self, mock_repo_factory_class):
        """Test get_email_by_email_address returns None when not found."""
        from common.services.email import EmailService

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        email_address = "nonexistent@example.com"
        mock_email_repo.get_one.return_value = None

        service = EmailService(mock_config)
        result = service.get_email_by_email_address(email_address)

        assert result is None
        mock_email_repo.get_one.assert_called_once_with({'email': email_address})

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_id_retrieves_email_by_entity_id(self, mock_repo_factory_class):
        """Test get_email_by_id retrieves email by entity_id."""
        from common.services.email import EmailService
        from common.models.email import Email

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        entity_id = "test-email-id"
        expected_email = Email(entity_id=entity_id, email="test@example.com")
        mock_email_repo.get_one.return_value = expected_email

        service = EmailService(mock_config)
        result = service.get_email_by_id(entity_id)

        assert result == expected_email
        mock_email_repo.get_one.assert_called_once_with({'entity_id': entity_id})

    @patch('common.services.email.RepositoryFactory')
    def test_get_email_by_id_returns_none_when_not_found(self, mock_repo_factory_class):
        """Test get_email_by_id returns None when not found."""
        from common.services.email import EmailService

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        entity_id = "nonexistent-id"
        mock_email_repo.get_one.return_value = None

        service = EmailService(mock_config)
        result = service.get_email_by_id(entity_id)

        assert result is None
        mock_email_repo.get_one.assert_called_once_with({'entity_id': entity_id})

    @patch('common.services.email.RepositoryFactory')
    def test_verify_email_sets_is_verified_true_and_saves(self, mock_repo_factory_class):
        """Test verify_email sets is_verified=True and saves."""
        from common.services.email import EmailService
        from common.models.email import Email

        mock_config = MagicMock()
        mock_email_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_email_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        test_email = Email(entity_id="test-id", email="test@example.com", is_verified=False)
        verified_email = Email(entity_id="test-id", email="test@example.com", is_verified=True)
        mock_email_repo.save.return_value = verified_email

        service = EmailService(mock_config)
        result = service.verify_email(test_email)

        assert test_email.is_verified is True
        assert result == verified_email
        mock_email_repo.save.assert_called_once_with(test_email)
