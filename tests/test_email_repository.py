"""
Unit tests for EmailRepository class.
"""
import pytest
from unittest.mock import MagicMock
from common.repositories.email import EmailRepository
from common.models.email import Email


class TestEmailRepository:
    """Test email repository instantiation and attributes."""

    def test_model_attribute_is_email_class(self):
        """Test MODEL attribute is set to Email class."""
        assert EmailRepository.MODEL == Email

    def test_repository_instantiation_with_required_parameters(self):
        """Test repository can be instantiated with required parameters."""
        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"
        user_id = "test-user-id"

        repo = EmailRepository(db_adapter, message_adapter, queue_name, user_id)

        assert repo is not None
        assert repo.MODEL == Email

    def test_repository_instantiation_without_user_id(self):
        """Test repository can be instantiated without user_id."""
        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"

        repo = EmailRepository(db_adapter, message_adapter, queue_name)

        assert repo is not None
        assert repo.MODEL == Email

    def test_repository_inherits_from_base_repository(self):
        """Test EmailRepository inherits from BaseRepository."""
        from common.repositories.base import BaseRepository
        assert issubclass(EmailRepository, BaseRepository)
