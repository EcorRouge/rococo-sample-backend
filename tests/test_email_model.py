"""
Unit tests for common/models/email.py
"""
import pytest
from common.models.email import Email
from rococo.models.versioned_model import ModelValidationError


class TestEmailValidation:
    """Tests for email validation functionality."""

    def test_valid_email_address(self):
        """Test that a valid email passes validation."""
        email = Email(person_id="test-person", email="test@example.com")
        # Should not raise
        email.validate_email()

    def test_valid_email_with_subdomain(self):
        """Test that an email with subdomain passes validation."""
        email = Email(person_id="test-person", email="test@mail.example.com")
        email.validate_email()

    def test_valid_email_with_plus(self):
        """Test that an email with plus sign passes validation."""
        email = Email(person_id="test-person", email="test+tag@example.com")
        email.validate_email()

    def test_valid_email_with_dots(self):
        """Test that an email with dots passes validation."""
        email = Email(person_id="test-person", email="first.last@example.com")
        email.validate_email()

    def test_valid_email_with_numbers(self):
        """Test that an email with numbers passes validation."""
        email = Email(person_id="test-person", email="user123@example456.com")
        email.validate_email()

    def test_valid_email_with_underscore(self):
        """Test that an email with underscore passes validation."""
        email = Email(person_id="test-person", email="test_user@example.com")
        email.validate_email()

    def test_valid_email_with_hyphen(self):
        """Test that an email with hyphen passes validation."""
        email = Email(person_id="test-person", email="test-user@my-domain.com")
        email.validate_email()

    def test_invalid_email_not_string(self):
        """Test that non-string email raises error."""
        email = Email(person_id="test-person", email=123)
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "must be a string" in str(exc_info.value)

    def test_invalid_email_missing_at_sign(self):
        """Test that email without @ sign fails validation."""
        email = Email(person_id="test-person", email="testexample.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_invalid_email_missing_domain(self):
        """Test that email without domain fails validation."""
        email = Email(person_id="test-person", email="test@")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_invalid_email_missing_username(self):
        """Test that email without username fails validation."""
        email = Email(person_id="test-person", email="@example.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_invalid_email_missing_tld(self):
        """Test that email without TLD fails validation."""
        email = Email(person_id="test-person", email="test@example")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_invalid_email_multiple_at_signs(self):
        """Test that email with multiple @ signs fails validation."""
        email = Email(person_id="test-person", email="test@@example.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_invalid_email_spaces(self):
        """Test that email with spaces fails validation."""
        email = Email(person_id="test-person", email="test user@example.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_invalid_email_special_chars(self):
        """Test that email with invalid special characters fails validation."""
        email = Email(person_id="test-person", email="test#user@example.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format" in str(exc_info.value)

    def test_email_too_long(self):
        """Test that email exceeding 254 characters fails validation."""
        # Create an email that's too long
        long_username = "a" * 250
        long_email = f"{long_username}@test.com"
        email = Email(person_id="test-person", email=long_email)
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "exceeds maximum length" in str(exc_info.value)

    def test_email_exactly_254_chars(self):
        """Test that email with exactly 254 characters passes validation."""
        # Create an email that's exactly 254 characters
        # Format: username@domain.com (need to account for @ and .com)
        username = "a" * 242
        long_email = f"{username}@example.com"  # Total 254 chars
        assert len(long_email) == 254
        email = Email(person_id="test-person", email=long_email)
        # Should not raise
        email.validate_email()

    def test_email_creation_with_all_fields(self):
        """Test creating email with all fields."""
        email = Email(
            person_id="test-person",
            email="test@example.com",
            is_verified=True,
            is_default=True,
            entity_id="test-email-id"
        )
        assert email.person_id == "test-person"
        assert email.email == "test@example.com"
        assert email.is_verified is True
        assert email.is_default is True
        assert email.entity_id == "test-email-id"

    def test_email_creation_with_minimal_fields(self):
        """Test creating email with minimal required fields."""
        email = Email(person_id="test-person", email="test@example.com")
        assert email.person_id == "test-person"
        assert email.email == "test@example.com"
        assert email.is_verified is False  # Default value
        assert email.is_default is False  # Default value

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors can be raised together."""
        # Create email that's too long and has invalid format
        long_invalid = "a" * 260  # Too long and no @ sign
        email = Email(person_id="test-person", email=long_invalid)
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        # Should have multiple errors
        error_str = str(exc_info.value)
        assert "Invalid email address format" in error_str
        assert "exceeds maximum length" in error_str
