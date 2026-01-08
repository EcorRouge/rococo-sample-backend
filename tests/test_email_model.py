"""
Unit tests for Email model validation logic.
"""
import pytest
from rococo.models.versioned_model import ModelValidationError
from common.models.email import Email


class TestEmailValidation:
    """Test email validation logic including formats, types, and lengths."""

    def test_valid_email_standard_format(self):
        """Test email validation with standard email format."""
        email = Email(email="user@example.com")
        email.validate_email()

    def test_valid_email_with_plus_sign(self):
        """Test email validation with plus sign in address."""
        email = Email(email="user+tag@example.com")
        email.validate_email()

    def test_valid_email_with_dots(self):
        """Test email validation with dots in username."""
        email = Email(email="first.last@example.com")
        email.validate_email()

    def test_valid_email_with_subdomain(self):
        """Test email validation with subdomain."""
        email = Email(email="user@mail.example.com")
        email.validate_email()

    def test_valid_email_with_numbers(self):
        """Test email validation with numbers."""
        email = Email(email="user123@example456.com")
        email.validate_email()

    def test_invalid_email_missing_at_symbol(self):
        """Test email validation fails when missing @ symbol."""
        email = Email(email="userexample.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format." in str(exc_info.value)

    def test_invalid_email_missing_domain(self):
        """Test email validation fails when missing domain."""
        email = Email(email="user@")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format." in str(exc_info.value)

    def test_invalid_email_missing_username(self):
        """Test email validation fails when missing username."""
        email = Email(email="@example.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format." in str(exc_info.value)

    def test_invalid_email_with_spaces(self):
        """Test email validation fails with spaces."""
        email = Email(email="user name@example.com")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format." in str(exc_info.value)

    def test_invalid_email_missing_tld(self):
        """Test email validation fails when missing top-level domain."""
        email = Email(email="user@example")
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Invalid email address format." in str(exc_info.value)

    def test_email_with_integer_type(self):
        """Test email validation fails when email is an integer."""
        email = Email(email=12345)
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Email address must be a string." in str(exc_info.value)

    def test_email_with_none_type(self):
        """Test email validation fails when email is None."""
        email = Email(email=None)
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Email address must be a string." in str(exc_info.value)

    def test_email_with_list_type(self):
        """Test email validation fails when email is a list."""
        email = Email(email=["user@example.com"])
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        assert "Email address must be a string." in str(exc_info.value)

    def test_email_exceeds_max_length(self):
        """Test email validation fails when exceeding 254 characters."""
        # Create an email with 255 characters
        long_email = "a" * 240 + "@example.com"  # Total 252 chars, within limit
        email = Email(email=long_email)
        email.validate_email()  # Should pass

        # Now test with 255 characters
        longer_email = "a" * 241 + "@example.com"  # Total 253 chars
        email2 = Email(email=longer_email)
        email2.validate_email()  # Should pass

        # Now test exceeding the limit
        too_long_email = "a" * 242 + "@example.com"  # Total 254 chars, boundary
        email3 = Email(email=too_long_email)
        email3.validate_email()  # Should pass at exactly 254

        # Exceed limit
        way_too_long = "a" * 243 + "@example.com"  # Total 255 chars
        email4 = Email(email=way_too_long)
        with pytest.raises(ModelValidationError) as exc_info:
            email4.validate_email()
        assert "Email address exceeds maximum length of 254 characters." in str(exc_info.value)

    def test_email_exactly_254_characters(self):
        """Test email validation passes at exactly 254 characters."""
        # Create email with exactly 254 characters
        exact_email = "a" * 242 + "@example.com"  # 242 + 1 (@) + 11 (example.com) = 254
        email = Email(email=exact_email)
        email.validate_email()

    def test_email_with_multiple_validation_errors(self):
        """Test email validation reports multiple errors."""
        # Create email that is both too long and not a string
        email = Email(email=12345)
        with pytest.raises(ModelValidationError) as exc_info:
            email.validate_email()
        # Should fail on type check first
        assert "Email address must be a string." in str(exc_info.value)
