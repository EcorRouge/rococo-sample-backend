"""
Tests to ensure conftest fixtures are properly covered.
"""


def test_mock_person_fixture(mock_person):
    """Test that mock_person fixture works."""
    assert mock_person is not None
    assert hasattr(mock_person, 'entity_id')


def test_mock_email_fixture(mock_email):
    """Test that mock_email fixture works."""
    assert mock_email is not None
    assert hasattr(mock_email, 'entity_id')


def test_mock_organization_fixture(mock_organization):
    """Test that mock_organization fixture works."""
    assert mock_organization is not None
    assert hasattr(mock_organization, 'entity_id')


def test_mock_person_organization_role_fixture(mock_person_organization_role):
    """Test that mock_person_organization_role fixture works."""
    assert mock_person_organization_role is not None
    assert hasattr(mock_person_organization_role, 'entity_id')


def test_mock_repository_fixture(mock_repository):
    """Test that mock_repository fixture works."""
    assert mock_repository is not None
    assert hasattr(mock_repository, 'save')
    assert hasattr(mock_repository, 'get_one')
    assert hasattr(mock_repository, 'get_many')
