"""
Unit tests for OAuthClient class.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests


class TestOAuthClient:
    """Test OAuth client methods for Google and Microsoft."""

    def test_init_initializes_config_correctly(self):
        """Test __init__ initializes config correctly."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.GOOGLE_CLIENT_ID = "test-google-client-id"
        mock_config.GOOGLE_CLIENT_SECRET = "test-google-secret"  # NOSONAR
        mock_config.MICROSOFT_CLIENT_ID = "test-microsoft-client-id"
        mock_config.MICROSOFT_CLIENT_SECRET = "test-microsoft-secret"  # NOSONAR

        client = OAuthClient(mock_config)

        assert client.config == mock_config

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_with_valid_code(self, mock_post):
        """Test get_google_token with valid code, redirect_uri, and code_verifier."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.GOOGLE_CLIENT_ID = "test-client-id"
        mock_config.GOOGLE_CLIENT_SECRET = "test-secret"  # NOSONAR

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_google_token(
            code="test-auth-code",
            redirect_uri="http://localhost:3000/callback",
            code_verifier="test-code-verifier"
        )

        assert result["access_token"] == "test-access-token"
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://oauth2.googleapis.com/token'
        assert call_args[1]['data']['client_id'] == "test-client-id"
        assert call_args[1]['data']['code'] == "test-auth-code"
        assert call_args[1]['data']['grant_type'] == 'authorization_code'
        assert call_args[1]['data']['redirect_uri'] == "http://localhost:3000/callback"
        assert call_args[1]['data']['code_verifier'] == "test-code-verifier"

    @patch('common.services.oauth.requests.post')
    def test_get_google_token_handles_200_response_correctly(self, mock_post):
        """Test get_google_token handles 200 response correctly."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.GOOGLE_CLIENT_ID = "test-client-id"
        mock_config.GOOGLE_CLIENT_SECRET = "test-secret"  # NOSONAR

        expected_response = {"access_token": "token123", "refresh_token": "refresh123"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_google_token("code", "uri", "verifier")

        assert result == expected_response

    @patch('common.services.oauth.logger')
    @patch('common.services.oauth.requests.post')
    def test_get_google_token_handles_non_200_responses_with_logging(self, mock_post, mock_logger):
        """Test get_google_token handles non-200 responses with logging."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.GOOGLE_CLIENT_ID = "test-client-id"
        mock_config.GOOGLE_CLIENT_SECRET = "test-secret"  # NOSONAR

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid grant"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_google_token("invalid-code", "uri", "verifier")

        # Verify error logging was called
        mock_logger.error.assert_called()

    @patch('common.services.oauth.logger')
    @patch('common.services.oauth.requests.post')
    def test_get_google_token_handles_request_exceptions(self, mock_post, mock_logger):
        """Test get_google_token handles request exceptions."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.GOOGLE_CLIENT_ID = "test-client-id"
        mock_config.GOOGLE_CLIENT_SECRET = "test-secret"  # NOSONAR

        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        client = OAuthClient(mock_config)

        with pytest.raises(requests.exceptions.RequestException):
            client.get_google_token("code", "uri", "verifier")

        # Verify error logging was called
        mock_logger.error.assert_called()

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_with_valid_access_token(self, mock_get):
        """Test get_user_info with valid access token."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        expected_user_info = {
            "email": "test@example.com",
            "name": "Test User",
            "sub": "123456789"
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_user_info
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_google_user_info("test-access-token")

        assert result == expected_user_info
        mock_get.assert_called_once()

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_makes_correct_api_call_with_authorization_header(self, mock_get):
        """Test get_google_user_info makes correct API call with Authorization header."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "test@example.com"}
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_google_user_info("my-access-token")

        call_args = mock_get.call_args
        assert call_args[0][0] == 'https://openidconnect.googleapis.com/v1/userinfo'
        assert call_args[1]['headers']['Authorization'] == 'Bearer my-access-token'

    @patch('common.services.oauth.requests.get')
    def test_get_google_user_info_handles_response_correctly(self, mock_get):
        """Test get_google_user_info handles response correctly."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        user_data = {"email": "user@test.com", "verified_email": True}
        mock_response = MagicMock()
        mock_response.json.return_value = user_data
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_google_user_info("token")

        assert result == user_data
        mock_response.raise_for_status.assert_called_once()

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_with_valid_parameters(self, mock_post):
        """Test get_microsoft_token with valid parameters."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.MICROSOFT_CLIENT_ID = "test-microsoft-client-id"
        mock_config.MICROSOFT_CLIENT_SECRET = "test-microsoft-secret"  # NOSONAR

        expected_response = {
            "access_token": "ms-access-token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_token(
            code="ms-auth-code",
            redirect_uri="http://localhost:3000/callback",
            code_verifier="ms-code-verifier"
        )

        assert result == expected_response
        mock_post.assert_called_once()

    @patch('common.services.oauth.requests.post')
    def test_get_microsoft_token_handles_response_correctly(self, mock_post):
        """Test get_microsoft_token handles response correctly."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()
        mock_config.MICROSOFT_CLIENT_ID = "client-id"
        mock_config.MICROSOFT_CLIENT_SECRET = "secret"  # NOSONAR

        token_response = {"access_token": "token", "refresh_token": "refresh"}
        mock_response = MagicMock()
        mock_response.json.return_value = token_response
        mock_post.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_token("code", "uri", "verifier")

        assert result == token_response
        mock_response.raise_for_status.assert_called_once()

        # Verify the call parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        assert call_args[1]['data']['scope'] == 'User.Read'
        assert call_args[1]['data']['grant_type'] == 'authorization_code'

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_with_valid_access_token(self, mock_get):
        """Test get_microsoft_user_info with valid access token."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        graph_response = {
            "userPrincipalName": "user@example.com",
            "displayName": "Test User",
            "mail": "user.mail@example.com"
        }
        mock_response = MagicMock()
        mock_response.json.return_value = graph_response
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        result = client.get_microsoft_user_info("ms-access-token")

        assert result["email"] == "user@example.com"
        assert result["name"] == "Test User"
        mock_get.assert_called_once()

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_transforms_response_correctly(self, mock_get):
        """Test get_microsoft_user_info transforms response correctly (userPrincipalName vs mail)."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        # Test with userPrincipalName
        graph_response_1 = {
            "userPrincipalName": "principal@example.com",
            "displayName": "User One"
        }
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = graph_response_1
        mock_get.return_value = mock_response_1

        client = OAuthClient(mock_config)
        result_1 = client.get_microsoft_user_info("token")

        assert result_1["email"] == "principal@example.com"
        assert result_1["name"] == "User One"

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_uses_mail_when_no_principal_name(self, mock_get):
        """Test get_microsoft_user_info uses mail field when userPrincipalName is missing."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        # Test with mail field when userPrincipalName is None
        graph_response_2 = {
            "userPrincipalName": None,
            "mail": "mailfield@example.com",
            "displayName": "User Two"
        }
        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = graph_response_2
        mock_get.return_value = mock_response_2

        client = OAuthClient(mock_config)
        result_2 = client.get_microsoft_user_info("token")

        assert result_2["email"] == "mailfield@example.com"
        assert result_2["name"] == "User Two"

    @patch('common.services.oauth.requests.get')
    def test_get_microsoft_user_info_makes_correct_api_call(self, mock_get):
        """Test get_microsoft_user_info makes correct API call."""
        from common.services.oauth import OAuthClient

        mock_config = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"userPrincipalName": "test@example.com", "displayName": "Test"}
        mock_get.return_value = mock_response

        client = OAuthClient(mock_config)
        client.get_microsoft_user_info("my-token")

        call_args = mock_get.call_args
        assert call_args[0][0] == 'https://graph.microsoft.com/v1.0/me'
        assert call_args[1]['headers']['Authorization'] == 'Bearer my-token'
