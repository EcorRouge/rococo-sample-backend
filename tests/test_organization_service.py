"""
Unit tests for common/services/organization.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.organization import OrganizationService
from common.models import Organization


class TestOrganizationServiceInitialization:
    """Tests for OrganizationService initialization."""

    @patch('common.services.organization.RepositoryFactory')
    def test_init_creates_repository(self, mock_factory_class, mock_config):
        """Test that __init__ creates organization repository."""
        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = MagicMock()

        service = OrganizationService(mock_config)

        assert service.config == mock_config
        assert service.organization_repo is not None


class TestSaveOrganization:
    """Tests for save_organization method."""

    @patch('common.services.organization.RepositoryFactory')
    def test_save_organization_success(self, mock_factory_class, mock_config):
        """Test successful organization save."""
        mock_repo = MagicMock()
        saved_org = MagicMock(entity_id="org-123", name="Test Org")
        mock_repo.save.return_value = saved_org

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = OrganizationService(mock_config)
        org = MagicMock(name="Test Org")
        result = service.save_organization(org)

        assert result == saved_org
        mock_repo.save.assert_called_once_with(org)


class TestGetOrganizationById:
    """Tests for get_organization_by_id method."""

    @patch('common.services.organization.RepositoryFactory')
    def test_get_organization_by_id_found(self, mock_factory_class, mock_config):
        """Test getting organization by ID when found."""
        mock_repo = MagicMock()
        found_org = MagicMock(entity_id="org-123", name="Test Org")
        mock_repo.get_one.return_value = found_org

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = OrganizationService(mock_config)
        result = service.get_organization_by_id("org-123")

        assert result == found_org
        mock_repo.get_one.assert_called_once_with({"entity_id": "org-123"})

    @patch('common.services.organization.RepositoryFactory')
    def test_get_organization_by_id_not_found(self, mock_factory_class, mock_config):
        """Test getting organization by ID when not found."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = OrganizationService(mock_config)
        result = service.get_organization_by_id("nonexistent-id")

        assert result is None


class TestGetOrganizationsWithRolesByPerson:
    """Tests for get_organizations_with_roles_by_person method."""

    @patch('common.services.organization.RepositoryFactory')
    def test_get_organizations_with_roles_found(self, mock_factory_class, mock_config):
        """Test getting organizations with roles for a person."""
        mock_repo = MagicMock()
        results = [
            {'entity_id': 'org-1', 'name': 'Org 1', 'role': 'admin'},
            {'entity_id': 'org-2', 'name': 'Org 2', 'role': 'member'}
        ]
        mock_repo.get_organizations_by_person_id.return_value = results

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = OrganizationService(mock_config)
        result = service.get_organizations_with_roles_by_person("person-123")

        assert result == results
        assert len(result) == 2
        mock_repo.get_organizations_by_person_id.assert_called_once_with("person-123")

    @patch('common.services.organization.RepositoryFactory')
    def test_get_organizations_with_roles_empty(self, mock_factory_class, mock_config):
        """Test getting organizations when person has none."""
        mock_repo = MagicMock()
        mock_repo.get_organizations_by_person_id.return_value = []

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = OrganizationService(mock_config)
        result = service.get_organizations_with_roles_by_person("person-456")

        assert result == []
        mock_repo.get_organizations_by_person_id.assert_called_once_with("person-456")
