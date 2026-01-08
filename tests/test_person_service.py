"""
Comprehensive tests for common/services/person.py
"""
import pytest
from unittest.mock import MagicMock, patch
from common.services.person import PersonService
from common.models.person import Person


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MagicMock()


@pytest.fixture
def person_service(mock_config):
    """Create a PersonService instance with mocked dependencies."""
    with patch('common.services.person.RepositoryFactory'):
        service = PersonService(mock_config)
        service.person_repo = MagicMock()
        service.email_service = MagicMock()
        return service


class TestPersonService:
    """Tests for PersonService."""

    def test_save_person(self, person_service):
        """Test saving a person."""
        # Setup
        person = MagicMock(spec=Person)
        person.entity_id = "person-123"
        person_service.person_repo.save = MagicMock(return_value=person)

        # Execute
        result = person_service.save_person(person)

        # Verify
        assert result == person
        person_service.person_repo.save.assert_called_once_with(person)

    def test_get_person_by_email_address(self, person_service):
        """Test getting person by email address."""
        # Setup
        email_obj = MagicMock()
        email_obj.person_id = "person-123"

        person = MagicMock(spec=Person)
        person.entity_id = "person-123"

        person_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        person_service.person_repo.get_one = MagicMock(return_value=person)

        # Execute
        result = person_service.get_person_by_email_address("test@example.com")

        # Verify
        assert result == person
        person_service.email_service.get_email_by_email_address.assert_called_once_with("test@example.com")
        person_service.person_repo.get_one.assert_called_once_with({"entity_id": "person-123"})

    def test_get_person_by_email_address_email_not_found(self, person_service):
        """Test getting person when email doesn't exist."""
        # Setup
        person_service.email_service.get_email_by_email_address = MagicMock(return_value=None)

        # Execute
        result = person_service.get_person_by_email_address("notfound@example.com")

        # Verify
        assert result is None
        person_service.person_repo.get_one.assert_not_called()

    def test_get_person_by_email_address_person_not_found(self, person_service):
        """Test getting person when person doesn't exist for email."""
        # Setup
        email_obj = MagicMock()
        email_obj.person_id = "person-123"

        person_service.email_service.get_email_by_email_address = MagicMock(return_value=email_obj)
        person_service.person_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = person_service.get_person_by_email_address("test@example.com")

        # Verify
        assert result is None

    def test_get_person_by_id(self, person_service):
        """Test getting person by ID."""
        # Setup
        person = MagicMock(spec=Person)
        person.entity_id = "person-123"
        person_service.person_repo.get_one = MagicMock(return_value=person)

        # Execute
        result = person_service.get_person_by_id("person-123")

        # Verify
        assert result == person
        person_service.person_repo.get_one.assert_called_once_with({"entity_id": "person-123"})

    def test_get_person_by_id_not_found(self, person_service):
        """Test getting person by ID when not found."""
        # Setup
        person_service.person_repo.get_one = MagicMock(return_value=None)

        # Execute
        result = person_service.get_person_by_id("nonexistent")

        # Verify
        assert result is None
