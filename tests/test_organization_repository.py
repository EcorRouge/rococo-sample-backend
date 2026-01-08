"""
Comprehensive tests for common/repositories/organization.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.repositories.organization import OrganizationRepository
from common.models.organization import Organization


@pytest.fixture
def mock_db_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.__enter__ = MagicMock(return_value=adapter)
    adapter.__exit__ = MagicMock(return_value=False)
    return adapter


@pytest.fixture
def organization_repository(mock_db_adapter):
    """Create an OrganizationRepository instance with mocked dependencies."""
    repo = OrganizationRepository(
        db_adapter=mock_db_adapter,
        message_adapter=None,
        queue_name="test-queue",
        user_id="test-user"
    )
    return repo


class TestOrganizationRepository:
    """Tests for OrganizationRepository."""

    def test_model_attribute(self):
        """Test that MODEL attribute is set correctly."""
        assert OrganizationRepository.MODEL == Organization

    def test_get_organizations_by_person_id(self, organization_repository, mock_db_adapter):
        """Test getting organizations by person ID."""
        # Setup
        expected_results = [
            {"entity_id": "org-1", "name": "Organization 1", "role": "admin"},
            {"entity_id": "org-2", "name": "Organization 2", "role": "member"}
        ]
        mock_db_adapter.execute_query = MagicMock(return_value=expected_results)

        # Execute
        results = organization_repository.get_organizations_by_person_id("person-123")

        # Verify
        assert results == expected_results
        mock_db_adapter.execute_query.assert_called_once()

        # Verify the SQL query
        call_args = mock_db_adapter.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "SELECT o.*, por.role" in query
        assert "FROM organization AS o" in query
        assert "JOIN person_organization_role AS por" in query
        assert "WHERE por.person_id = %s" in query
        assert params == ("person-123",)

    def test_get_organizations_by_person_id_empty(self, organization_repository, mock_db_adapter):
        """Test getting organizations when person has none."""
        # Setup
        mock_db_adapter.execute_query = MagicMock(return_value=[])

        # Execute
        results = organization_repository.get_organizations_by_person_id("person-456")

        # Verify
        assert results == []
        mock_db_adapter.execute_query.assert_called_once()

    def test_get_organizations_by_person_id_single_org(self, organization_repository, mock_db_adapter):
        """Test getting a single organization for a person."""
        # Setup
        expected_results = [
            {"entity_id": "org-1", "name": "Solo Organization", "role": "owner"}
        ]
        mock_db_adapter.execute_query = MagicMock(return_value=expected_results)

        # Execute
        results = organization_repository.get_organizations_by_person_id("person-789")

        # Verify
        assert len(results) == 1
        assert results[0]["entity_id"] == "org-1"
        assert results[0]["role"] == "owner"
