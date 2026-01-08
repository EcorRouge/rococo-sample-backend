"""
Comprehensive tests for common/services/oauth.py
"""
import pytest
from unittest.mock import MagicMock, patch
import requests
from common.services.oauth import OAuthClient


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    config = MagicMock()
    config.GOOGLE_CLIENT_ID = "test-google-client-id"
    config.GOOGLE_CLIENT_SECRET = "test-google-secret"
    config.MICROSOFT_CLIENT_ID = "test-microsoft-client-id"
    config.MICROSOFT_CLIENT_SECRET = "test-microsoft-secret"
    return config


@pytest.fixture
def oauth_client(mock_config):
    """Create an OAuthClient instance."""
    return OAuthClient(mock_config)


class TestOAuthClientGoogle:
    """Tests for Google OAuth functionality."""

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_success(self, mock_post, oauth_client):
        """Test successful Google token exchange."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_post.return_value = mock_response

        # Execute
        result = oauth_client.get_google_token(
            code="auth-code",
            redirect_uri="http://localhost:3000/callback",
            code_verifier="test-verifier"
        )

        # Verify
        assert result["access_token"] == "test-access-token"
        assert result["expires_in"] == 3600
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://oauth2.googleapis.com/token'
        assert call_args[1]['data']['client_id'] == "test-google-client-id"
        assert call_args[1]['data']['code'] == "auth-code"

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_failure(self, mock_post, oauth_client):
        """Test Google token exchange failure."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid grant"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
        mock_post.return_value = mock_response

        # Execute & Verify
        with pytest.raises(requests.exceptions.HTTPError):
            oauth_client.get_google_token(
                code="invalid-code",
                redirect_uri="http://localhost:3000/callback",
                code_verifier="test-verifier"
            )

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_request_exception(self, mock_post, oauth_client):
        """Test Google token exchange with network error."""
        # Setup
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        # Execute & Verify
        with pytest.raises(requests.exceptions.RequestException):
            oauth_client.get_google_token(
                code="auth-code",
                redirect_uri="http://localhost:3000/callback",
                code_verifier="test-verifier"
            )

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_success(self, mock_get, oauth_client):
        """Test successful Google user info retrieval."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/photo.jpg"
        }
        mock_get.return_value = mock_response

        # Execute
        result = oauth_client.get_google_user_info("test-access-token")

        # Verify
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == 'https://openidconnect.googleapis.com/v1/userinfo'
        assert call_args[1]['headers']['Authorization'] == 'Bearer test-access-token'

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_failure(self, mock_get, oauth_client):
        """Test Google user info retrieval failure."""
        # Setup
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        # Execute & Verify
        with pytest.raises(requests.exceptions.HTTPError):
            oauth_client.get_google_user_info("invalid-token")


class TestOAuthClientMicrosoft:
    """Tests for Microsoft OAuth functionality."""

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_success(self, mock_post, oauth_client):
        """Test successful Microsoft token exchange."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test-ms-access-token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_post.return_value = mock_response

        # Execute
        result = oauth_client.get_microsoft_token(
            code="ms-auth-code",
            redirect_uri="http://localhost:3000/callback",
            code_verifier="test-verifier"
        )

        # Verify
        assert result["access_token"] == "test-ms-access-token"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        assert call_args[1]['data']['client_id'] == "test-microsoft-client-id"
        assert call_args[1]['data']['code'] == "ms-auth-code"
        assert call_args[1]['data']['scope'] == 'User.Read'

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_failure(self, mock_post, oauth_client):
        """Test Microsoft token exchange failure."""
        # Setup
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
        mock_post.return_value = mock_response

        # Execute & Verify
        with pytest.raises(requests.exceptions.HTTPError):
            oauth_client.get_microsoft_token(
                code="invalid-code",
                redirect_uri="http://localhost:3000/callback",
                code_verifier="test-verifier"
            )

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_success(self, mock_get, oauth_client):
        """Test successful Microsoft user info retrieval."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "userPrincipalName": "testuser@example.com",
            "displayName": "Test User",
            "givenName": "Test",
            "surname": "User"
        }
        mock_get.return_value = mock_response

        # Execute
        result = oauth_client.get_microsoft_user_info("test-ms-access-token")

        # Verify
        assert result["email"] == "testuser@example.com"
        assert result["name"] == "Test User"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == 'https://graph.microsoft.com/v1.0/me'
        assert call_args[1]['headers']['Authorization'] == 'Bearer test-ms-access-token'

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_with_mail_field(self, mock_get, oauth_client):
        """Test Microsoft user info retrieval using mail field instead of userPrincipalName."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "mail": "testuser@example.com",
            "displayName": "Test User"
        }
        mock_get.return_value = mock_response

        # Execute
        result = oauth_client.get_microsoft_user_info("test-ms-access-token")

        # Verify
        assert result["email"] == "testuser@example.com"
        assert result["name"] == "Test User"

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_no_display_name(self, mock_get, oauth_client):
        """Test Microsoft user info retrieval with missing displayName."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "userPrincipalName": "testuser@example.com"
        }
        mock_get.return_value = mock_response

        # Execute
        result = oauth_client.get_microsoft_user_info("test-ms-access-token")

        # Verify
        assert result["email"] == "testuser@example.com"
        assert result["name"] == ""

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_failure(self, mock_get, oauth_client):
        """Test Microsoft user info retrieval failure."""
        # Setup
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        # Execute & Verify
        with pytest.raises(requests.exceptions.HTTPError):
            oauth_client.get_microsoft_user_info("invalid-token")


class TestOAuthClientIntegration:
    """Integration tests for OAuthClient."""

    def test_oauth_client_initialization(self, mock_config):
        """Test OAuthClient initialization with config."""
        # Execute
        client = OAuthClient(mock_config)

        # Verify
        assert client.config == mock_config
        assert client.config.GOOGLE_CLIENT_ID == "test-google-client-id"
        assert client.config.MICROSOFT_CLIENT_ID == "test-microsoft-client-id"
