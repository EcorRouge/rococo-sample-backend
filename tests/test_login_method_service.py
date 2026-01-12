"""
Unit tests for common/services/login_method.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.login_method import LoginMethodService
from common.models import LoginMethod


class TestLoginMethodServiceInitialization:
    """Tests for LoginMethodService initialization."""

    @patch('common.services.login_method.RepositoryFactory')
    def test_init_creates_repository(self, mock_factory_class, mock_config):
        """Test that __init__ creates login_method repository."""
        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = MagicMock()

        service = LoginMethodService(mock_config)

        assert service.config == mock_config
        assert service.login_method_repo is not None


class TestSaveLoginMethod:
    """Tests for save_login_method method."""

    @patch('common.services.login_method.RepositoryFactory')
    def test_save_login_method_success(self, mock_factory_class, mock_config):
        """Test successful login method save."""
        mock_repo = MagicMock()
        saved_login_method = MagicMock(entity_id="login-123")
        mock_repo.save.return_value = saved_login_method

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        login_method = MagicMock()
        result = service.save_login_method(login_method)

        assert result == saved_login_method
        mock_repo.save.assert_called_once_with(login_method)


class TestGetLoginMethodByEmailId:
    """Tests for get_login_method_by_email_id method."""

    @patch('common.services.login_method.RepositoryFactory')
    def test_get_login_method_found(self, mock_factory_class, mock_config):
        """Test getting login method by email ID when found."""
        mock_repo = MagicMock()
        found_login_method = MagicMock(entity_id="login-123", email_id="email-123")
        mock_repo.get_one.return_value = found_login_method

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        result = service.get_login_method_by_email_id("email-123")

        assert result == found_login_method
        mock_repo.get_one.assert_called_once_with({"email_id": "email-123"})

    @patch('common.services.login_method.RepositoryFactory')
    def test_get_login_method_not_found(self, mock_factory_class, mock_config):
        """Test getting login method when not found."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        result = service.get_login_method_by_email_id("nonexistent-email-id")

        assert result is None


class TestGetLoginMethodById:
    """Tests for get_login_method_by_id method."""

    @patch('common.services.login_method.RepositoryFactory')
    def test_get_login_method_by_id_found(self, mock_factory_class, mock_config):
        """Test getting login method by entity ID when found."""
        mock_repo = MagicMock()
        found_login_method = MagicMock(entity_id="login-123")
        mock_repo.get_one.return_value = found_login_method

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        result = service.get_login_method_by_id("login-123")

        assert result == found_login_method
        mock_repo.get_one.assert_called_once_with({"entity_id": "login-123"})

    @patch('common.services.login_method.RepositoryFactory')
    def test_get_login_method_by_id_not_found(self, mock_factory_class, mock_config):
        """Test getting login method by ID when not found."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        result = service.get_login_method_by_id("nonexistent-id")

        assert result is None


class TestUpdatePassword:
    """Tests for update_password method."""

    @patch('common.services.login_method.RepositoryFactory')
    def test_update_password_success(self, mock_factory_class, mock_config):
        """Test successful password update."""
        mock_repo = MagicMock()
        login_method = MagicMock(entity_id="login-123", password="old_password")
        updated_login_method = MagicMock(entity_id="login-123", password="new_password")
        mock_repo.save.return_value = updated_login_method

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        result = service.update_password(login_method, "new_password")

        assert login_method.password == "new_password"
        assert result == updated_login_method
        mock_repo.save.assert_called_once_with(login_method)

    @patch('common.services.login_method.RepositoryFactory')
    def test_update_password_sets_password_field(self, mock_factory_class, mock_config):
        """Test that update_password sets the password field."""
        mock_repo = MagicMock()
        login_method = MagicMock(password="old_password")
        mock_repo.save.return_value = login_method

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = LoginMethodService(mock_config)
        service.update_password(login_method, "updated_password")

        assert login_method.password == "updated_password"
