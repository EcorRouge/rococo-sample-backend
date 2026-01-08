"""
Comprehensive tests for common/repositories/base.py
"""
import pytest
from unittest.mock import MagicMock
from common.repositories.base import BaseRepository
from common.models.person import Person


class TestBaseRepository:
    """Tests for BaseRepository."""

    def test_init_subclass_without_model(self):
        """Test that subclassing without MODEL raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            class InvalidRepository(BaseRepository):
                pass

        assert "must define the MODEL attribute" in str(exc_info.value)

    def test_init_subclass_with_model(self):
        """Test that subclassing with MODEL succeeds."""
        # This should not raise an exception
        class ValidRepository(BaseRepository):
            MODEL = Person

        assert ValidRepository.MODEL == Person

    def test_initialization(self):
        """Test repository initialization."""
        # Create a valid repository class
        class TestRepository(BaseRepository):
            MODEL = Person

        # Setup mocks
        mock_db_adapter = MagicMock()
        mock_message_adapter = MagicMock()

        # Create instance
        repo = TestRepository(
            db_adapter=mock_db_adapter,
            message_adapter=mock_message_adapter,
            queue_name="test-queue",
            user_id="test-user"
        )

        # Verify
        assert repo.MODEL == Person

    def test_initialization_without_message_adapter(self):
        """Test repository initialization without message adapter."""
        # Create a valid repository class
        class TestRepository(BaseRepository):
            MODEL = Person

        # Setup mocks
        mock_db_adapter = MagicMock()

        # Create instance
        repo = TestRepository(
            db_adapter=mock_db_adapter,
            message_adapter=None,
            queue_name="test-queue"
        )

        # Verify
        assert repo.MODEL == Person
