"""
Comprehensive tests for common/services/login_method.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.login_method import LoginMethodService
from common.models import LoginMethod


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MagicMock()


@pytest.fixture
def login_method_service(mock_config):
    """Create a LoginMethodService instance with mocked dependencies."""
    with patch('common.services.login_method.RepositoryFactory'):
        service = LoginMethodService(mock_config)
        service.login_method_repo = MagicMock()
        return service


class TestLoginMethodService:
    """Tests for LoginMethodService."""

    def test_save_login_method(self, login_method_service):
        """Test saving a login method."""
        # Setup
        login_method = MagicMock(spec=LoginMethod)
        login_method.entity_id = "login-123"
        login_method_service.login_method_repo.save = MagicMock(return_value=login_method)

        # Execute
        result = login_method_service.save_login_method(login_method)

        # Verify
        assert result == login_method
        login_method_service.login_method_repo.save.assert_called_once_with(login_method)

    def test_get_login_method_by_email_id(self, login_method_service):
        """Test getting login method by email ID."""
        # Setup
        login_method = MagicMock(spec=LoginMethod)
        login_method.email_id = "email-123"
        login_method_service.login_method_repo.get_one = MagicMock(return_value=login_method)

        # Execute
        result = login_method_service.get_login_method_by_email_id("email-123")

        # Verify
        assert result == login_method
        login_method_service.login_method_repo.get_one.assert_called_once_with({"email_id": "email-123"})

    def test_get_login_method_by_email_id_not_found(self, login_method_service):
        """Test getting login method by email ID when not found."""
        # Setup
        login_method_service.login_method_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = login_method_service.get_login_method_by_email_id("nonexistent")

        # Verify
        assert result is None

    def test_get_login_method_by_id(self, login_method_service):
        """Test getting login method by ID."""
        # Setup
        login_method = MagicMock(spec=LoginMethod)
        login_method.entity_id = "login-123"
        login_method_service.login_method_repo.get_one = MagicMock(return_value=login_method)

        # Execute
        result = login_method_service.get_login_method_by_id("login-123")

        # Verify
        assert result == login_method
        login_method_service.login_method_repo.get_one.assert_called_once_with({"entity_id": "login-123"})

    def test_get_login_method_by_id_not_found(self, login_method_service):
        """Test getting login method by ID when not found."""
        # Setup
        login_method_service.login_method_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = login_method_service.get_login_method_by_id("nonexistent")

        # Verify
        assert result is None

    def test_update_password(self, login_method_service):
        """Test updating login method password."""
        # Setup
        login_method = MagicMock(spec=LoginMethod)
        login_method.password = "old-password"
        new_password = "new-hashed-password"
        login_method_service.login_method_repo.save = MagicMock(return_value=login_method)

        # Execute
        result = login_method_service.update_password(login_method, new_password)

        # Verify
        assert login_method.password == new_password
        login_method_service.login_method_repo.save.assert_called_once_with(login_method)
        assert result == login_method
