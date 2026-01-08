"""
Unit tests for OrganizationRepository class.
"""
import pytest
from unittest.mock import MagicMock, patch
from common.repositories.organization import OrganizationRepository
from common.models.organization import Organization


class TestOrganizationRepository:
    """Test organization repository methods."""

    def test_model_attribute_is_organization_class(self):
        """Test MODEL attribute is set to Organization class."""
        assert OrganizationRepository.MODEL == Organization

    def test_repository_instantiation(self):
        """Test repository can be instantiated with required parameters."""
        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"
        user_id = "test-user-id"

        repo = OrganizationRepository(db_adapter, message_adapter, queue_name, user_id)

        assert repo is not None
        assert repo.MODEL == Organization

    def test_get_organizations_by_person_id_with_valid_id(self):
        """Test get_organizations_by_person_id method with valid person_id."""
        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"
        user_id = "test-user-id"
        person_id = "test-person-id"

        # Mock the execute_query to return test data
        expected_results = [
            {"entity_id": "org1", "name": "Org 1", "role": "admin"},
            {"entity_id": "org2", "name": "Org 2", "role": "member"}
        ]
        db_adapter.execute_query = MagicMock(return_value=expected_results)
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=None)

        repo = OrganizationRepository(db_adapter, message_adapter, queue_name, user_id)
        results = repo.get_organizations_by_person_id(person_id)

        assert results == expected_results
        db_adapter.execute_query.assert_called_once()

        # Verify the query parameters
        call_args = db_adapter.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "SELECT o.*, por.role" in query
        assert "FROM organization AS o" in query
        assert "JOIN person_organization_role AS por" in query
        assert "WHERE por.person_id = %s" in query
        assert params == (person_id,)

    def test_get_organizations_by_person_id_with_empty_results(self):
        """Test get_organizations_by_person_id returns empty list when no results."""
        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"
        user_id = "test-user-id"
        person_id = "nonexistent-person-id"

        # Mock empty results
        db_adapter.execute_query = MagicMock(return_value=[])
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=None)

        repo = OrganizationRepository(db_adapter, message_adapter, queue_name, user_id)
        results = repo.get_organizations_by_person_id(person_id)

        assert results == []
        db_adapter.execute_query.assert_called_once()

    def test_database_adapter_context_manager_usage(self):
        """Test that the method uses database adapter as context manager."""
        db_adapter = MagicMock()
        message_adapter = MagicMock()
        queue_name = "test-queue"
        user_id = "test-user-id"
        person_id = "test-person-id"

        db_adapter.execute_query = MagicMock(return_value=[])
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=None)

        repo = OrganizationRepository(db_adapter, message_adapter, queue_name, user_id)
        repo.get_organizations_by_person_id(person_id)

        # Verify context manager methods were called
        db_adapter.__enter__.assert_called_once()
        db_adapter.__exit__.assert_called_once()

    def test_repository_inherits_from_base_repository(self):
        """Test OrganizationRepository inherits from BaseRepository."""
        from common.repositories.base import BaseRepository
        assert issubclass(OrganizationRepository, BaseRepository)
