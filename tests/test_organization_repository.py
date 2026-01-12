"""
Unit tests for common/repositories/organization.py
"""
import pytest
from unittest.mock import MagicMock, patch, call
from common.repositories.organization import OrganizationRepository
from common.models.organization import Organization
from rococo.data.postgresql import PostgreSQLAdapter
from rococo.messaging.base import MessageAdapter


class TestOrganizationRepository:
    """Tests for OrganizationRepository class."""

    def test_model_attribute(self):
        """Test that MODEL is set to Organization."""
        assert OrganizationRepository.MODEL == Organization

    def test_initialization(self):
        """Test that OrganizationRepository can be initialized."""
        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)
        queue_name = "test-queue"

        repo = OrganizationRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name=queue_name
        )

        assert repo is not None
        assert repo.MODEL == Organization


class TestGetOrganizationsByPersonId:
    """Tests for get_organizations_by_person_id method."""

    def test_get_organizations_with_results(self):
        """Test getting organizations for a person with results."""
        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)

        # Mock the execute_query to return some results
        mock_results = [
            {'entity_id': 'org-1', 'name': 'Org 1', 'role': 'admin'},
            {'entity_id': 'org-2', 'name': 'Org 2', 'role': 'member'}
        ]
        db_adapter.execute_query.return_value = mock_results

        # Mock the context manager
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=False)

        repo = OrganizationRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name="test-queue"
        )

        person_id = "person-123"
        results = repo.get_organizations_by_person_id(person_id)

        # Verify the query was executed with correct parameters
        db_adapter.execute_query.assert_called_once()
        call_args = db_adapter.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        # Check that the query contains expected elements
        assert "SELECT o.*" in query
        assert "FROM organization AS o" in query
        assert "JOIN person_organization_role AS por" in query
        assert "WHERE por.person_id = %s" in query
        assert params == ("person-123",)

        assert results == mock_results
        assert len(results) == 2

    def test_get_organizations_with_no_results(self):
        """Test getting organizations for a person with no results."""
        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)

        # Mock the execute_query to return empty results
        db_adapter.execute_query.return_value = []

        # Mock the context manager
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=False)

        repo = OrganizationRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name="test-queue"
        )

        person_id = "person-456"
        results = repo.get_organizations_by_person_id(person_id)

        assert results == []
        db_adapter.execute_query.assert_called_once()

    def test_get_organizations_with_different_person_ids(self):
        """Test getting organizations for different person IDs."""
        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)

        db_adapter.execute_query.return_value = []
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=False)

        repo = OrganizationRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name="test-queue"
        )

        # Test with different person IDs
        person_ids = ["person-1", "person-2", "person-3"]

        for person_id in person_ids:
            repo.get_organizations_by_person_id(person_id)

        # Verify execute_query was called for each person_id
        assert db_adapter.execute_query.call_count == 3

    def test_get_organizations_uses_adapter_context_manager(self):
        """Test that the method uses the adapter as a context manager."""
        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)

        db_adapter.execute_query.return_value = []
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=False)

        repo = OrganizationRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name="test-queue"
        )

        repo.get_organizations_by_person_id("person-123")

        # Verify context manager methods were called
        db_adapter.__enter__.assert_called_once()
        db_adapter.__exit__.assert_called_once()

    def test_get_organizations_query_includes_role(self):
        """Test that the query includes the role from person_organization_role."""
        db_adapter = MagicMock(spec=PostgreSQLAdapter)
        message_adapter = MagicMock(spec=MessageAdapter)

        db_adapter.execute_query.return_value = []
        db_adapter.__enter__ = MagicMock(return_value=db_adapter)
        db_adapter.__exit__ = MagicMock(return_value=False)

        repo = OrganizationRepository(
            db_adapter=db_adapter,
            message_adapter=message_adapter,
            queue_name="test-queue"
        )

        repo.get_organizations_by_person_id("person-123")

        # Get the query that was executed
        call_args = db_adapter.execute_query.call_args
        query = call_args[0][0]

        # Verify the query selects the role
        assert "por.role" in query
