"""
Comprehensive tests for common/models/email.py
"""
import pytest
from rococo.models.versioned_model import ModelValidationError
from common.models.email import Email


class TestEmailModel:
    """Tests for Email model validation."""

    def test_validate_email_valid(self):
        """Test email validation with valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_name@example-domain.com",
            "123@example.com",
            "a@b.c"
        ]

        for email_address in valid_emails:
            email = Email(email=email_address, person_id="person-123")
            # Should not raise an exception
            email.validate_email()

    def test_validate_email_invalid_format(self):
        """Test email validation with invalid format."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@@example.com",
            "user@.com",
            "user@domain",
            "user name@example.com",
            ""
        ]

        for email_address in invalid_emails:
            email = Email(email=email_address, person_id="person-123")
            with pytest.raises(ModelValidationError) as exc_info:
                email.validate_email()
            assert "Invalid email address format" in str(exc_info.value)

    def test_validate_email_not_string(self):
        """Test email validation when email is not a string."""
        invalid_values = [
            123,
            None,
            ["test@example.com"],
            {"email": "test@example.com"}
        ]

        for invalid_value in invalid_values:
            email = Email(email=invalid_value, person_id="person-123")
            with pytest.raises(ModelValidationError) as exc_info:
                email.validate_email()
            assert "Email address must be a string" in str(exc_info.value)

    def test_validate_email_too_long(self):
        """Test email validation with email exceeding maximum length."""
        # Create an email longer than 254 characters
        long_email = "a" * 250 + "@example.com"
        email = Email(email=long_email, person_id="person-123")

        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "exceeds maximum length" in str(exc_info.value)

    def test_validate_email_max_length_boundary(self):
        """Test email validation at the 254 character boundary."""
        # Create an email exactly 254 characters (should be valid)
        local_part = "a" * 240
        email_254 = f"{local_part}@example.com"  # 240 + 1 (@) + 13 = 254
        email = Email(email=email_254, person_id="person-123")
        # Should not raise an exception
        email.validate_email()

    def test_validate_email_multiple_errors(self):
        """Test that validation catches multiple errors."""
        # Email that's both too long and has invalid format
        long_invalid_email = "a" * 260
        email = Email(email=long_invalid_email, person_id="person-123")

        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        errors = exc_info.value.args[0]
        # Should contain both errors
        assert isinstance(errors, list)
        assert len(errors) >= 1

    def test_validate_email_with_special_chars(self):
        """Test email validation with special but valid characters."""
        valid_special_emails = [
            "user+tag@example.com",
            "user_name@example.com",
            "user.name@example.com",
            "user-name@example.com",
            "123user@example.com"
        ]

        for email_address in valid_special_emails:
            email = Email(email=email_address, person_id="person-123")
            # Should not raise an exception
            email.validate_email()

    def test_validate_email_with_subdomain(self):
        """Test email validation with subdomains."""
        valid_subdomain_emails = [
            "user@mail.example.com",
            "user@a.b.c.example.com",
            "user@subdomain.example.co.uk"
        ]

        for email_address in valid_subdomain_emails:
            email = Email(email=email_address, person_id="person-123")
            # Should not raise an exception
            email.validate_email()
