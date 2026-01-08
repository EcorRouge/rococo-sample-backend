"""
Unit tests for BaseRepository class.
"""
import pytest
from unittest.mock import MagicMock
from common.repositories.base import BaseRepository
from common.models.person import Person


class TestBaseRepository:
    """Test base repository MODEL validation."""

    def test_subclass_without_model_raises_error(self):
        """Test that subclasses without MODEL attribute raise TypeError."""
        with pytest.raises(TypeError) as exc_info:
            class InvalidRepository(BaseRepository):
                pass

        assert "must define the MODEL attribute" in str(exc_info.value)

    def test_subclass_with_model_initializes_correctly(self):
        """Test that subclasses with MODEL attribute initialize correctly."""
        class ValidRepository(BaseRepository):
            MODEL = Person

        # Should not raise an error
        assert ValidRepository.MODEL == Person

    def test_subclass_with_none_model_raises_error(self):
        """Test that subclasses with MODEL=None raise TypeError."""
        with pytest.raises(TypeError) as exc_info:
            class NoneModelRepository(BaseRepository):
                MODEL = None

        assert "must define the MODEL attribute" in str(exc_info.value)

    def test_repository_initialization_with_valid_model(self):
        """Test repository can be initialized with valid MODEL."""
        class ValidRepository(BaseRepository):
            MODEL = Person

        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"
        user_id = "test-user-id"

        repo = ValidRepository(db_adapter, message_adapter, queue_name, user_id)

        assert repo is not None
        assert repo.MODEL == Person

    def test_init_subclass_validation_logic(self):
        """Test __init_subclass__ validation catches missing MODEL."""
        with pytest.raises(TypeError) as exc_info:
            class TestRepo(BaseRepository):
                pass

        error_message = str(exc_info.value)
        assert "must define the MODEL attribute" in error_message
