"""
Unit tests for common/repositories/base.py
"""
import pytest
from unittest.mock import MagicMock, Mock, patch
from common.repositories.base import BaseRepository
from common.models.person import Person
from rococo.data.postgresql import PostgreSQLAdapter
from rococo.messaging.base import MessageAdapter


class TestBaseRepositorySubclassing:
    """Tests for BaseRepository subclassing requirements."""

    def test_subclass_without_model_raises_error(self):
        """Test that creating a subclass without MODEL attribute raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            class InvalidRepository(BaseRepository):
                pass  # Missing MODEL attribute

        assert "must define the MODEL attribute" in str(exc_info.value)

    def test_subclass_with_model_succeeds(self):
        """Test that creating a subclass with MODEL attribute succeeds."""
        # Should not raise
        class ValidRepository(BaseRepository):
            MODEL = Person

        assert ValidRepository.MODEL == Person


class TestBaseRepositoryInitialization:
    """Tests for BaseRepository initialization."""

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        class TestRepository(BaseRepository):
            MODEL = Person

        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)
        queue_name = "test-queue"
        user_id = "user-123"

        repo = TestRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name=queue_name,
            user_id=user_id
        )

        assert repo is not None
        assert repo.MODEL == Person

    def test_init_without_user_id(self):
        """Test initialization without user_id (optional parameter)."""
        class TestRepository(BaseRepository):
            MODEL = Person

        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)
        queue_name = "test-queue"

        repo = TestRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name=queue_name
        )

        assert repo is not None

    def test_init_with_none_message_adapter(self):
        """Test initialization with None message_adapter."""
        class TestRepository(BaseRepository):
            MODEL = Person

        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        queue_name = "test-queue"

        repo = TestRepository(
            db_adapter=db_adapter,
            message_adapter=None,
            queue_name=queue_name
        )

        assert repo is not None

    def test_model_passed_to_parent(self):
        """Test that MODEL is correctly passed to parent class."""
        class TestRepository(BaseRepository):
            MODEL = Person

        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)
        queue_name = "test-queue"

        # Mock the parent __init__ to verify it's called with correct params
        with patch('rococo.repositories.postgresql.PostgreSQLRepository.__init__', return_value=None) as mock_parent_init:
            repo = TestRepository(
                db_adapter=db_adapter,
                message_adapter=message_adapter,
                queue_name=queue_name,
                user_id="test-user"
            )

            # Verify parent __init__ was called with MODEL
            mock_parent_init.assert_called_once_with(
                db_adapter, Person, message_adapter, queue_name, user_id="test-user"
            )
