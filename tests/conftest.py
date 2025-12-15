"""
Shared pytest fixtures for unit tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional
from flask import Flask


@dataclass
class MockPerson:
    """Mock person object for testing."""
    entity_id: str = "test-person-id"
    first_name: str = "Test"
    last_name: str = "User"


@dataclass
class MockEmail:
    """Mock email object for testing."""
    entity_id: str = "test-email-id"
    email: str = "test@example.com"


@dataclass
class MockOrganization:
    """Mock organization object for testing."""
    entity_id: str = "test-org-id"
    name: str = "Test Organization"


@dataclass
class MockPersonOrganizationRole:
    """Mock person organization role object for testing."""
    entity_id: str = "test-role-id"
    person_id: str = "test-person-id"
    organization_id: str = "test-org-id"
    role: str = "member"


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    config = MagicMock()
    config.POSTGRES_HOST = "localhost"
    config.POSTGRES_PORT = "5432"
    config.POSTGRES_USER = "test"
    config.POSTGRES_PASSWORD = "test"  # NOSONAR - Test fixture data, not a real credential
    config.POSTGRES_DB = "testdb"
    config.RABBITMQ_HOST = "localhost"
    config.RABBITMQ_PORT = "5672"
    config.RABBITMQ_USER = "guest"
    config.RABBITMQ_PASSWORD = "guest"  # NOSONAR - Test fixture data, not a real credential
    config.RABBITMQ_VIRTUAL_HOST = "/"
    config.SUPER_ADMIN_ORGANIZATION_NAME = "SuperAdmin"
    return config


@pytest.fixture
def mock_person():
    """Create a mock person."""
    return MockPerson()


@pytest.fixture
def mock_email():
    """Create a mock email."""
    return MockEmail()


@pytest.fixture
def mock_organization():
    """Create a mock organization."""
    return MockOrganization()


@pytest.fixture
def mock_person_organization_role():
    """Create a mock person organization role."""
    return MockPersonOrganizationRole()


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = MagicMock()
    repo.save = MagicMock(return_value=MagicMock())
    repo.get_one = MagicMock(return_value=MagicMock())
    repo.get_many = MagicMock(return_value=[MagicMock()])
    return repo


@pytest.fixture(autouse=True)
def app_context():
    """Create an application context for tests."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    with app.app_context():
        yield app


@pytest.fixture(autouse=True)
def request_context(app_context):
    """Create a request context for tests."""
    with app_context.test_request_context():
        yield
