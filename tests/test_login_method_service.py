"""
Unit tests for LoginMethodService class.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestLoginMethodService:
    """Test login method service methods."""

    @patch('common.services.login_method.RepositoryFactory')
    def test_init(self, mock_repo_factory_class):
        """Test __init__ initializes config and repository factory."""
        from common.services.login_method import LoginMethodService

        mock_config = MagicMock()
        mock_login_method_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_login_method_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        service = LoginMethodService(mock_config)

        assert service.config == mock_config
        assert service.repository_factory == mock_repo_factory
        assert service.login_method_repo == mock_login_method_repo

    @patch('common.services.login_method.RepositoryFactory')
    def test_save_login_method(self, mock_repo_factory_class):
        """Test save_login_method method saves and returns login_method."""
        from common.services.login_method import LoginMethodService
        from common.models.login_method import LoginMethod

        mock_config = MagicMock()
        mock_login_method_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_login_method_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        test_login_method = LoginMethod(method_type="email-password")
        saved_login_method = LoginMethod(entity_id="saved-id", method_type="email-password")
        mock_login_method_repo.save.return_value = saved_login_method

        service = LoginMethodService(mock_config)
        result = service.save_login_method(test_login_method)

        assert result == saved_login_method
        mock_login_method_repo.save.assert_called_once_with(test_login_method)

    @patch('common.services.login_method.RepositoryFactory')
    def test_get_login_method_by_email_id(self, mock_repo_factory_class):
        """Test get_login_method_by_email_id retrieves login_method by email_id."""
        from common.services.login_method import LoginMethodService
        from common.models.login_method import LoginMethod

        mock_config = MagicMock()
        mock_login_method_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_login_method_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        email_id = "test-email-id"
        expected_login_method = LoginMethod(entity_id="login-id", email_id=email_id)
        mock_login_method_repo.get_one.return_value = expected_login_method

        service = LoginMethodService(mock_config)
        result = service.get_login_method_by_email_id(email_id)

        assert result == expected_login_method
        mock_login_method_repo.get_one.assert_called_once_with({"email_id": email_id})

    @patch('common.services.login_method.RepositoryFactory')
    def test_get_login_method_by_id(self, mock_repo_factory_class):
        """Test get_login_method_by_id retrieves login_method by entity_id."""
        from common.services.login_method import LoginMethodService
        from common.models.login_method import LoginMethod

        mock_config = MagicMock()
        mock_login_method_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_login_method_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        entity_id = "test-login-id"
        expected_login_method = LoginMethod(entity_id=entity_id, method_type="email-password")
        mock_login_method_repo.get_one.return_value = expected_login_method

        service = LoginMethodService(mock_config)
        result = service.get_login_method_by_id(entity_id)

        assert result == expected_login_method
        mock_login_method_repo.get_one.assert_called_once_with({"entity_id": entity_id})

    @patch('common.services.login_method.RepositoryFactory')
    def test_update_password(self, mock_repo_factory_class):
        """Test update_password updates password and saves login_method."""
        from common.services.login_method import LoginMethodService
        from common.models.login_method import LoginMethod

        mock_config = MagicMock()
        mock_login_method_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_login_method_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        test_login_method = LoginMethod(entity_id="login-id", method_type="email-password", password="old-hash")
        updated_login_method = LoginMethod(entity_id="login-id", method_type="email-password", password="new-hash")
        mock_login_method_repo.save.return_value = updated_login_method

        service = LoginMethodService(mock_config)
        result = service.update_password(test_login_method, "new-hash")

        assert test_login_method.password == "new-hash"
        assert result == updated_login_method
        mock_login_method_repo.save.assert_called_once_with(test_login_method)
