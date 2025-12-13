"""
Unit tests for common/services/person_organization_role.py
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPersonOrganizationRoleService:
    """Tests for PersonOrganizationRoleService."""

    @patch('common.services.person_organization_role.RepositoryFactory')
    def test_init(self, mock_factory_class, mock_config):
        """Test service initialization."""
        from common.services.person_organization_role import PersonOrganizationRoleService

        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory

        service = PersonOrganizationRoleService(mock_config)

        assert service.config == mock_config
        mock_factory_class.assert_called_once_with(mock_config)

    @patch('common.services.person_organization_role.RepositoryFactory')
    def test_save_person_organization_role(self, mock_factory_class, mock_config):
        """Test saving a person organization role."""
        from common.services.person_organization_role import PersonOrganizationRoleService

        mock_repo = MagicMock()
        mock_saved_role = MagicMock()
        mock_repo.save.return_value = mock_saved_role

        mock_factory = MagicMock()
        mock_factory.get_repository.return_value = mock_repo
        mock_factory_class.return_value = mock_factory

        service = PersonOrganizationRoleService(mock_config)

        input_role = MagicMock()
        result = service.save_person_organization_role(input_role)

        assert result == mock_saved_role
        mock_repo.save.assert_called_once_with(input_role)

    @patch('common.services.person_organization_role.RepositoryFactory')
    def test_get_roles_by_person_id(self, mock_factory_class, mock_config):
        """Test getting roles by person ID."""
        from common.services.person_organization_role import PersonOrganizationRoleService

        mock_repo = MagicMock()
        mock_roles = [MagicMock(), MagicMock()]
        mock_repo.get_many.return_value = mock_roles

        mock_factory = MagicMock()
        mock_factory.get_repository.return_value = mock_repo
        mock_factory_class.return_value = mock_factory

        service = PersonOrganizationRoleService(mock_config)

        result = service.get_roles_by_person_id('person-123')

        assert result == mock_roles
        mock_repo.get_many.assert_called_once_with({'person_id': 'person-123'})

    @patch('common.services.person_organization_role.RepositoryFactory')
    def test_get_role_of_person_in_organization(self, mock_factory_class, mock_config):
        """Test getting a specific role of a person in an organization."""
        from common.services.person_organization_role import PersonOrganizationRoleService

        mock_repo = MagicMock()
        mock_role = MagicMock()
        mock_repo.get_one.return_value = mock_role

        mock_factory = MagicMock()
        mock_factory.get_repository.return_value = mock_repo
        mock_factory_class.return_value = mock_factory

        service = PersonOrganizationRoleService(mock_config)

        result = service.get_role_of_person_in_organization(
            person_id='person-123',
            organization_id='org-456'
        )

        assert result == mock_role
        mock_repo.get_one.assert_called_once_with({
            'person_id': 'person-123',
            'organization_id': 'org-456'
        })

    @patch('common.services.person_organization_role.RepositoryFactory')
    def test_get_role_of_person_in_organization_not_found(self, mock_factory_class, mock_config):
        """Test getting role when person is not in organization."""
        from common.services.person_organization_role import PersonOrganizationRoleService

        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = MagicMock()
        mock_factory.get_repository.return_value = mock_repo
        mock_factory_class.return_value = mock_factory

        service = PersonOrganizationRoleService(mock_config)

        result = service.get_role_of_person_in_organization(
            person_id='person-123',
            organization_id='org-456'
        )

        assert result is None
