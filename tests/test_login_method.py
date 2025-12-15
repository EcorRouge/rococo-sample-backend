"""
Unit tests for common/models/login_method.py
"""
import pytest
from unittest.mock import MagicMock, patch


class TestLoginMethodHashPassword:
    """Tests for password hashing functionality."""

    @patch('common.models.login_method.generate_password_hash')
    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_hash_password_with_valid_password(self, mock_post_init, mock_hash):
        """Test that password is hashed when raw_password is provided."""
        from common.models.login_method import LoginMethod

        mock_hash.return_value = 'hashed_password'

        login_method = LoginMethod(
            method_type='password',
            raw_password='ValidPass1!'  # NOSONAR - Test data for password validation
        )

        mock_hash.assert_called_once()
        assert login_method.password == 'hashed_password'

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_hash_password_without_raw_password(self, mock_post_init):
        """Test that no hashing occurs when raw_password is None."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='oauth-google')

        # raw_password should be None or deleted after __post_init__
        # Note: del on dataclass fields may not always remove the attr
        assert getattr(login_method, 'raw_password', None) is None


class TestLoginMethodValidateRawPassword:
    """Tests for password validation."""

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_too_short(self, mock_post_init):
        """Test validation fails for password less than 8 characters."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password='Short1!')  # NOSONAR - Test data

        assert "at least 8 character" in str(exc_info.value)

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_too_long(self, mock_post_init):
        """Test validation fails for password more than 100 characters."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        long_password = 'A' * 90 + 'a1!' + 'x' * 10  # More than 100 chars
        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password=long_password)

        assert "at max 100 character" in str(exc_info.value)

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_missing_uppercase(self, mock_post_init):
        """Test validation fails when missing uppercase letter."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password='lowercase1!')  # NOSONAR - Test data

        assert "uppercase letter" in str(exc_info.value)

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_missing_lowercase(self, mock_post_init):
        """Test validation fails when missing lowercase letter."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password='UPPERCASE1!')  # NOSONAR - Test data

        assert "lowercase letter" in str(exc_info.value)

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_missing_digit(self, mock_post_init):
        """Test validation fails when missing digit."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password='NoDigitHere!')  # NOSONAR - Test data

        assert "contain a digit" in str(exc_info.value)

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_missing_special_char(self, mock_post_init):
        """Test validation fails when missing special character."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password='NoSpecial1A')  # NOSONAR - Test data

        assert "special character" in str(exc_info.value)

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_password_invalid_character(self, mock_post_init):
        """Test validation fails when containing invalid character."""
        from common.models.login_method import LoginMethod
        from rococo.models.versioned_model import ModelValidationError

        with pytest.raises(ModelValidationError) as exc_info:
            LoginMethod(method_type='password', raw_password='ValidPass1!€')  # NOSONAR - Test data with invalid char

        assert "invalid character" in str(exc_info.value)

    @patch('common.models.login_method.generate_password_hash')
    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_valid_password_passes(self, mock_post_init, mock_hash):
        """Test that a valid password passes all validations."""
        from common.models.login_method import LoginMethod

        mock_hash.return_value = 'hashed'

        # Should not raise
        login_method = LoginMethod(
            method_type='password',
            raw_password='ValidPass1!'  # NOSONAR - Test data for password validation
        )

        assert login_method.password == 'hashed'

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_validate_raw_password_with_none(self, mock_post_init):
        """Test validate_raw_password returns early when raw_password is None."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='oauth-google')
        # Should not raise, as validate_raw_password returns early for None
        login_method.validate_raw_password()


class TestLoginMethodOAuthProperties:
    """Tests for OAuth-related properties."""

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_is_oauth_method_true(self, mock_post_init):
        """Test is_oauth_method returns True for OAuth methods."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='oauth-google')

        assert login_method.is_oauth_method is True

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_is_oauth_method_false(self, mock_post_init):
        """Test is_oauth_method returns False for non-OAuth methods."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='password')

        assert login_method.is_oauth_method is False

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_is_oauth_method_none_method_type(self, mock_post_init):
        """Test is_oauth_method returns False when method_type is None."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type=None)

        assert login_method.is_oauth_method is False

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_oauth_provider_name_google(self, mock_post_init):
        """Test oauth_provider_name extracts provider correctly."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='oauth-google')

        assert login_method.oauth_provider_name == 'google'

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_oauth_provider_name_facebook(self, mock_post_init):
        """Test oauth_provider_name for Facebook OAuth."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='oauth-facebook')

        assert login_method.oauth_provider_name == 'facebook'

    @patch('common.models.login_method.BaseLoginMethod.__post_init__')
    def test_oauth_provider_name_non_oauth(self, mock_post_init):
        """Test oauth_provider_name returns None for non-OAuth methods."""
        from common.models.login_method import LoginMethod

        login_method = LoginMethod(method_type='password')

        assert login_method.oauth_provider_name is None
