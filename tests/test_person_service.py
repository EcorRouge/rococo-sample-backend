"""
Unit tests for common/services/person.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.person import PersonService
from common.models.person import Person


class TestPersonServiceInitialization:
    """Tests for PersonService initialization."""

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_init_creates_repository_and_email_service(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test that __init__ creates person repository and email service."""
        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = MagicMock()

        service = PersonService(mock_config)

        assert service.config == mock_config
        assert service.email_service is not None
        assert service.person_repo is not None


class TestSavePerson:
    """Tests for save_person method."""

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_save_person_success(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test successful person save."""
        mock_repo = MagicMock()
        saved_person = MagicMock(entity_id="person-123", first_name="John", last_name="Doe")
        mock_repo.save.return_value = saved_person

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = PersonService(mock_config)
        person = MagicMock(first_name="John", last_name="Doe")
        result = service.save_person(person)

        assert result == saved_person
        mock_repo.save.assert_called_once_with(person)


class TestGetPersonByEmailAddress:
    """Tests for get_person_by_email_address method."""

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_get_person_by_email_address_found(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test getting person by email address when found."""
        mock_repo = MagicMock()
        found_person = MagicMock(entity_id="person-123", first_name="John")
        mock_repo.get_one.return_value = found_person

        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(person_id="person-123")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = PersonService(mock_config)
        result = service.get_person_by_email_address("test@example.com")

        assert result == found_person
        mock_email_service.get_email_by_email_address.assert_called_once_with("test@example.com")
        mock_repo.get_one.assert_called_once_with({"entity_id": "person-123"})

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_get_person_by_email_address_email_not_found(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test getting person when email doesn't exist."""
        mock_email_service = mock_email_service_class.return_value
        mock_email_service.get_email_by_email_address.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = MagicMock()

        service = PersonService(mock_config)
        result = service.get_person_by_email_address("nonexistent@example.com")

        assert result is None

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_get_person_by_email_address_person_not_found(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test getting person when email exists but person doesn't."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_email_service = mock_email_service_class.return_value
        email_obj = MagicMock(person_id="nonexistent-person-id")
        mock_email_service.get_email_by_email_address.return_value = email_obj

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = PersonService(mock_config)
        result = service.get_person_by_email_address("test@example.com")

        assert result is None


class TestGetPersonById:
    """Tests for get_person_by_id method."""

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_get_person_by_id_found(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test getting person by ID when found."""
        mock_repo = MagicMock()
        found_person = MagicMock(entity_id="person-123", first_name="Jane", last_name="Doe")
        mock_repo.get_one.return_value = found_person

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = PersonService(mock_config)
        result = service.get_person_by_id("person-123")

        assert result == found_person
        mock_repo.get_one.assert_called_once_with({"entity_id": "person-123"})

    @patch('common.services.person.RepositoryFactory')
    @patch('common.services.EmailService')
    def test_get_person_by_id_not_found(self, mock_email_service_class, mock_factory_class, mock_config):
        """Test getting person by ID when not found."""
        mock_repo = MagicMock()
        mock_repo.get_one.return_value = None

        mock_factory = mock_factory_class.return_value
        mock_factory.get_repository.return_value = mock_repo

        service = PersonService(mock_config)
        result = service.get_person_by_id("nonexistent-id")

        assert result is None
