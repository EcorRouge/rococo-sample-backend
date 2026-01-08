"""
Comprehensive tests for common/services/organization.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.organization import OrganizationService
from common.models import Organization


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MagicMock()


@pytest.fixture
def organization_service(mock_config):
    """Create an OrganizationService instance with mocked dependencies."""
    with patch('common.services.organization.RepositoryFactory'):
        service = OrganizationService(mock_config)
        service.organization_repo = MagicMock()
        return service


class TestOrganizationService:
    """Tests for OrganizationService."""

    def test_save_organization(self, organization_service):
        """Test saving an organization."""
        # Setup
        organization = MagicMock(spec=Organization)
        organization.entity_id = "org-123"
        organization_service.organization_repo.save = MagicMock(return_value=organization)

        # Execute
        result = organization_service.save_organization(organization)

        # Verify
        assert result == organization
        organization_service.organization_repo.save.assert_called_once_with(organization)

    def test_get_organization_by_id(self, organization_service):
        """Test getting organization by ID."""
        # Setup
        organization = MagicMock(spec=Organization)
        organization.entity_id = "org-123"
        organization_service.organization_repo.get_one = MagicMock(return_value=organization)

        # Execute
        result = organization_service.get_organization_by_id("org-123")

        # Verify
        assert result == organization
        organization_service.organization_repo.get_one.assert_called_once_with({"entity_id": "org-123"})

    def test_get_organization_by_id_not_found(self, organization_service):
        """Test getting organization by ID when not found."""
        # Setup
        organization_service.organization_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = organization_service.get_organization_by_id("nonexistent")

        # Verify
        assert result is None

    def test_get_organizations_with_roles_by_person(self, organization_service):
        """Test getting organizations with roles for a person."""
        # Setup
        results = [
            {"entity_id": "org-1", "name": "Org 1", "role": "admin"},
            {"entity_id": "org-2", "name": "Org 2", "role": "member"}
        ]
        organization_service.organization_repo.get_organizations_by_person_id = MagicMock(return_value=results)

        # Execute
        result = organization_service.get_organizations_with_roles_by_person("person-123")

        # Verify
        assert result == results
        organization_service.organization_repo.get_organizations_by_person_id.assert_called_once_with("person-123")

    def test_get_organizations_with_roles_by_person_empty(self, organization_service):
        """Test getting organizations when person has none."""
        # Setup
        organization_service.organization_repo.get_organizations_by_person_id = MagicMock(return_value=[])

        # Execute
        result = organization_service.get_organizations_with_roles_by_person("person-123")

        # Verify
        assert result == []
