"""
Unit tests for Organization model.
"""
import pytest
from common.models.organization import Organization
from rococo.models import Organization as BaseOrganization


class TestOrganizationModel:
    """Test organization model instantiation and inheritance."""

    def test_organization_instantiation(self):
        """Test organization model can be instantiated with valid data."""
        org = Organization(name="Test Organization")
        assert org.name == "Test Organization"

    def test_organization_inherits_from_base(self):
        """Test organization model inherits from base Organization class."""
        org = Organization(name="Test Org")
        assert isinstance(org, BaseOrganization)

    def test_organization_with_entity_id(self):
        """Test organization model can be instantiated with entity_id."""
        org = Organization(entity_id="test-org-id", name="Test Organization")
        assert org.entity_id == "test-org-id"
        assert org.name == "Test Organization"

    def test_organization_attributes(self):
        """Test organization model has expected attributes from base class."""
        org = Organization(name="Test Org")
        # Check that common BaseModel attributes are accessible
        assert hasattr(org, 'entity_id')
        assert hasattr(org, 'name')
