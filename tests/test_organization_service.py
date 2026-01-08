"""
Unit tests for OrganizationService class.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestOrganizationService:
    """Test organization service methods."""

    @patch('common.services.organization.RepositoryFactory')
    def test_init(self, mock_repo_factory_class):
        """Test __init__ initializes config and repository factory."""
        from common.services.organization import OrganizationService

        mock_config = MagicMock()
        mock_org_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_org_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        service = OrganizationService(mock_config)

        assert service.config == mock_config
        assert service.repository_factory == mock_repo_factory
        assert service.organization_repo == mock_org_repo

    @patch('common.services.organization.RepositoryFactory')
    def test_save_organization(self, mock_repo_factory_class):
        """Test save_organization method saves and returns organization."""
        from common.services.organization import OrganizationService
        from common.models.organization import Organization

        mock_config = MagicMock()
        mock_org_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_org_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        test_org = Organization(name="Test Org")
        saved_org = Organization(entity_id="saved-id", name="Test Org")
        mock_org_repo.save.return_value = saved_org

        service = OrganizationService(mock_config)
        result = service.save_organization(test_org)

        assert result == saved_org
        mock_org_repo.save.assert_called_once_with(test_org)

    @patch('common.services.organization.RepositoryFactory')
    def test_get_organization_by_id(self, mock_repo_factory_class):
        """Test get_organization_by_id retrieves organization by entity_id."""
        from common.services.organization import OrganizationService
        from common.models.organization import Organization

        mock_config = MagicMock()
        mock_org_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_org_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        entity_id = "test-org-id"
        expected_org = Organization(entity_id=entity_id, name="Test Organization")
        mock_org_repo.get_one.return_value = expected_org

        service = OrganizationService(mock_config)
        result = service.get_organization_by_id(entity_id)

        assert result == expected_org
        mock_org_repo.get_one.assert_called_once_with({"entity_id": entity_id})

    @patch('common.services.organization.RepositoryFactory')
    def test_get_organizations_with_roles_by_person(self, mock_repo_factory_class):
        """Test get_organizations_with_roles_by_person retrieves organizations for a person."""
        from common.services.organization import OrganizationService

        mock_config = MagicMock()
        mock_org_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_org_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        person_id = "test-person-id"
        expected_results = [{"name": "Org1", "role": "admin"}, {"name": "Org2", "role": "member"}]
        mock_org_repo.get_organizations_by_person_id.return_value = expected_results

        service = OrganizationService(mock_config)
        result = service.get_organizations_with_roles_by_person(person_id)

        assert result == expected_results
        mock_org_repo.get_organizations_by_person_id.assert_called_once_with(person_id)
