"""
Unit tests for PersonService class.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPersonService:
    """Test person service methods."""

    @patch('common.services.person.RepositoryFactory')
    def test_init(self, mock_repo_factory_class):
        """Test __init__ initializes config and repository factory."""
        from common.services.person import PersonService

        mock_config = MagicMock()
        mock_person_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_person_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        service = PersonService(mock_config)

        assert service.config == mock_config
        assert service.repository_factory == mock_repo_factory
        assert service.person_repo == mock_person_repo

    @patch('common.services.person.RepositoryFactory')
    def test_save_person(self, mock_repo_factory_class):
        """Test save_person method saves and returns person."""
        from common.services.person import PersonService
        from common.models.person import Person

        mock_config = MagicMock()
        mock_person_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_person_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        test_person = Person(first_name="John", last_name="Doe")
        saved_person = Person(entity_id="saved-id", first_name="John", last_name="Doe")
        mock_person_repo.save.return_value = saved_person

        service = PersonService(mock_config)
        result = service.save_person(test_person)

        assert result == saved_person
        mock_person_repo.save.assert_called_once_with(test_person)

    @patch('common.services.person.RepositoryFactory')
    def test_get_person_by_id(self, mock_repo_factory_class):
        """Test get_person_by_id retrieves person by entity_id."""
        from common.services.person import PersonService
        from common.models.person import Person

        mock_config = MagicMock()
        mock_person_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_person_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        entity_id = "test-person-id"
        expected_person = Person(entity_id=entity_id, first_name="Jane", last_name="Doe")
        mock_person_repo.get_one.return_value = expected_person

        service = PersonService(mock_config)
        result = service.get_person_by_id(entity_id)

        assert result == expected_person
        mock_person_repo.get_one.assert_called_once_with({"entity_id": entity_id})

    @patch('common.services.person.RepositoryFactory')
    def test_get_person_by_email_address(self, mock_repo_factory_class):
        """Test get_person_by_email_address retrieves person via email."""
        from common.services.person import PersonService
        from common.models.person import Person
        from common.models.email import Email

        mock_config = MagicMock()
        mock_person_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_person_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        email_obj = Email(entity_id="email-id", email="test@example.com", person_id="person-id")
        expected_person = Person(entity_id="person-id", first_name="Test", last_name="User")
        mock_person_repo.get_one.return_value = expected_person

        service = PersonService(mock_config)
        # Mock the email_service after initialization
        service.email_service = MagicMock()
        service.email_service.get_email_by_email_address.return_value = email_obj

        result = service.get_person_by_email_address("test@example.com")

        assert result == expected_person
        service.email_service.get_email_by_email_address.assert_called_once_with("test@example.com")
        mock_person_repo.get_one.assert_called_once_with({"entity_id": "person-id"})

    @patch('common.services.person.RepositoryFactory')
    def test_get_person_by_email_address_no_email(self, mock_repo_factory_class):
        """Test get_person_by_email_address returns None when email not found."""
        from common.services.person import PersonService

        mock_config = MagicMock()
        mock_person_repo = MagicMock()
        mock_repo_factory = MagicMock()
        mock_repo_factory.get_repository.return_value = mock_person_repo
        mock_repo_factory_class.return_value = mock_repo_factory

        service = PersonService(mock_config)
        # Mock the email_service after initialization
        service.email_service = MagicMock()
        service.email_service.get_email_by_email_address.return_value = None

        result = service.get_person_by_email_address("nonexistent@example.com")

        assert result is None
        mock_person_repo.get_one.assert_not_called()
