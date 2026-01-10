"""
Unit tests for common/services/oauth.py
"""
import pytest
import requests
from unittest.mock import MagicMock, patch, Mock
from common.services.oauth import OAuthClient


class TestOAuthClientInitialization:
    """Tests for OAuthClient initialization."""

    def test_init_with_config(self, mock_config):
        """Test initialization with config."""
        client = OAuthClient(mock_config)
        assert client.config == mock_config


class TestGetGoogleToken:
    """Tests for get_google_token method."""

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_success(self, mock_post, mock_config):
        """Test successful Google token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'google_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_google_token('auth_code', 'http://localhost/callback', 'code_verifier')

        assert result['access_token'] == 'google_access_token'
        mock_post.assert_called_once()

        # Verify the call was made with correct parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://oauth2.googleapis.com/token'
        assert call_args[1]['data']['code'] == 'auth_code'
        assert call_args[1]['data']['redirect_uri'] == 'http://localhost/callback'
        assert call_args[1]['data']['code_verifier'] == 'code_verifier'

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_error_response(self, mock_post, mock_config):
        """Test Google token retrieval with error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('Bad Request')
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_google_token('invalid_code', 'http://localhost/callback', 'code_verifier')

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_request_exception(self, mock_post, mock_config):
        """Test Google token retrieval with request exception."""
        mock_post.side_effect = requests.exceptions.RequestException('Connection error')

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.RequestException):
            client.get_google_token('auth_code', 'http://localhost/callback', 'code_verifier')

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_uses_config_credentials(self, mock_post, mock_config):
        """Test that get_google_token uses config credentials."""
        mock_config.GOOGLE_CLIENT_ID = 'test_client_id'
        mock_config.GOOGLE_CLIENT_SECRET = 'test_client_secret'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_google_token('code', 'redirect', 'verifier')

        call_args = mock_post.call_args
        assert call_args[1]['data']['client_id'] == 'test_client_id'
        assert call_args[1]['data']['client_secret'] == 'test_client_secret'


class TestGetGoogleUserInfo:
    """Tests for get_google_user_info method."""

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_success(self, mock_get, mock_config):
        """Test successful retrieval of Google user info."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'sub': '123456789',
            'email': 'user@gmail.com',
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'https://example.com/photo.jpg'
        }
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_google_user_info('access_token')

        assert result['email'] == 'user@gmail.com'
        assert result['name'] == 'Test User'
        mock_get.assert_called_once_with(
            'https://openidconnect.googleapis.com/v1/userinfo',
            headers={'Authorization': 'Bearer access_token'}
        )

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_error(self, mock_get, mock_config):
        """Test Google user info retrieval with error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('Unauthorized')
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_google_user_info('invalid_token')

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_uses_bearer_token(self, mock_get, mock_config):
        """Test that get_google_user_info uses Bearer token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'email': 'test@example.com'}
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_google_user_info('my_access_token')

        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer my_access_token'


class TestGetMicrosoftToken:
    """Tests for get_microsoft_token method."""

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_success(self, mock_post, mock_config):
        """Test successful Microsoft token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'microsoft_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'User.Read'
        }
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_token('auth_code', 'http://localhost/callback', 'code_verifier')

        assert result['access_token'] == 'microsoft_access_token'
        mock_post.assert_called_once()

        # Verify the call was made with correct URL
        call_args = mock_post.call_args
        assert 'login.microsoftonline.com' in call_args[0][0]
        assert call_args[1]['data']['code'] == 'auth_code'

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_error_response(self, mock_post, mock_config):
        """Test Microsoft token retrieval with error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'invalid_grant'}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('Bad Request')
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_microsoft_token('invalid_code', 'http://localhost/callback', 'code_verifier')

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_uses_config_credentials(self, mock_post, mock_config):
        """Test that get_microsoft_token uses config credentials."""
        mock_config.MICROSOFT_CLIENT_ID = 'ms_client_id'
        mock_config.MICROSOFT_CLIENT_SECRET = 'ms_client_secret'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_microsoft_token('code', 'redirect', 'verifier')

        call_args = mock_post.call_args
        assert call_args[1]['data']['client_id'] == 'ms_client_id'
        assert call_args[1]['data']['client_secret'] == 'ms_client_secret'

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_includes_scope(self, mock_post, mock_config):
        """Test that get_microsoft_token includes User.Read scope."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_microsoft_token('code', 'redirect', 'verifier')

        call_args = mock_post.call_args
        assert call_args[1]['data']['scope'] == 'User.Read'


class TestGetMicrosoftUserInfo:
    """Tests for get_microsoft_user_info method."""

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_success(self, mock_get, mock_config):
        """Test successful retrieval of Microsoft user info."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123456',
            'displayName': 'Test User',
            'userPrincipalName': 'user@example.com',
            'givenName': 'Test',
            'surname': 'User'
        }
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_user_info('access_token')

        assert result['email'] == 'user@example.com'
        assert result['name'] == 'Test User'
        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': 'Bearer access_token'}
        )

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_with_mail_field(self, mock_get, mock_config):
        """Test Microsoft user info when using 'mail' field instead of 'userPrincipalName'."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123456',
            'displayName': 'Test User',
            'mail': 'user@company.com',
            'givenName': 'Test',
            'surname': 'User'
        }
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_user_info('access_token')

        assert result['email'] == 'user@company.com'
        assert result['name'] == 'Test User'

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_missing_display_name(self, mock_get, mock_config):
        """Test Microsoft user info with missing displayName."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123456',
            'userPrincipalName': 'user@example.com',
        }
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_user_info('access_token')

        assert result['email'] == 'user@example.com'
        assert result['name'] == ''

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_error(self, mock_get, mock_config):
        """Test Microsoft user info retrieval with error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'invalid_token'}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('Unauthorized')
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_microsoft_user_info('invalid_token')

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_uses_bearer_token(self, mock_get, mock_config):
        """Test that get_microsoft_user_info uses Bearer token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'displayName': 'User',
            'userPrincipalName': 'user@example.com'
        }
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_microsoft_user_info('my_ms_token')

        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer my_ms_token'
