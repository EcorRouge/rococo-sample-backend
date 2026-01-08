"""
Unit tests for Person model.
"""
import pytest
from typing import ClassVar
from common.models.person import Person
from rococo.models import Person as BasePerson


class TestPersonModel:
    """Test person model with type checking enabled."""

    def test_person_instantiation(self):
        """Test person model can be instantiated with valid data."""
        person = Person(first_name="John", last_name="Doe")
        assert person.first_name == "John"
        assert person.last_name == "Doe"

    def test_person_inherits_from_base(self):
        """Test person model inherits from base Person class."""
        person = Person(first_name="Jane", last_name="Smith")
        assert isinstance(person, BasePerson)

    def test_person_use_type_checking_attribute(self):
        """Test person model has use_type_checking ClassVar set to True."""
        assert hasattr(Person, 'use_type_checking')
        assert Person.use_type_checking is True

    def test_person_use_type_checking_is_class_var(self):
        """Test use_type_checking is a ClassVar and not an instance attribute."""
        person = Person(first_name="Test", last_name="User")
        # ClassVar should be accessible on the class
        assert Person.use_type_checking is True
        # But accessing on instance should reference the class attribute
        assert person.use_type_checking is True

    def test_person_with_entity_id(self):
        """Test person model can be instantiated with entity_id."""
        person = Person(entity_id="test-person-id", first_name="John", last_name="Doe")
        assert person.entity_id == "test-person-id"
        assert person.first_name == "John"
        assert person.last_name == "Doe"

    def test_person_attributes(self):
        """Test person model has expected attributes from base class."""
        person = Person(first_name="Jane", last_name="Doe")
        # Check that common BaseModel attributes are accessible
        assert hasattr(person, 'entity_id')
        assert hasattr(person, 'first_name')
        assert hasattr(person, 'last_name')
