"""
Unit tests for flask/app/helpers/response.py
"""
import pytest
from unittest.mock import MagicMock, patch
import json


class TestParseRequestBody:
    """Tests for parse_request_body function."""

    def test_parse_request_body_success(self):
        """Test parsing valid JSON request body."""
        from app.helpers.response import parse_request_body

        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            'name': 'John',
            'email': 'john@example.com',
            'age': 30
        }

        result = parse_request_body(mock_request, ['name', 'email'])

        assert result == {'name': 'John', 'email': 'john@example.com'}

    def test_parse_request_body_with_missing_key(self):
        """Test parsing with missing key uses default value."""
        from app.helpers.response import parse_request_body

        mock_request = MagicMock()
        mock_request.get_json.return_value = {'name': 'John'}

        result = parse_request_body(mock_request, ['name', 'missing_key'], default_value='default')

        assert result == {'name': 'John', 'missing_key': 'default'}

    def test_parse_request_body_invalid_json(self):
        """Test parsing invalid JSON raises InputValidationError."""
        from app.helpers.response import parse_request_body
        from common.helpers.exceptions import InputValidationError

        mock_request = MagicMock()
        mock_request.get_json.side_effect = Exception("Invalid JSON")

        with pytest.raises(InputValidationError) as exc_info:
            parse_request_body(mock_request, ['name'])

        assert "Error parsing request body" in str(exc_info.value)


class TestValidateRequiredFields:
    """Tests for validate_required_fields function."""

    def test_validate_required_fields_success(self):
        """Test validation passes for all required fields present."""
        from app.helpers.response import validate_required_fields

        # Should not raise
        validate_required_fields({
            'name': 'John',
            'email': 'john@example.com'
        })

    def test_validate_required_fields_empty_string(self):
        """Test validation fails for empty string."""
        from app.helpers.response import validate_required_fields
        from common.helpers.exceptions import InputValidationError

        with pytest.raises(InputValidationError) as exc_info:
            validate_required_fields({'name': ''})

        assert "'name' is required" in str(exc_info.value)

    def test_validate_required_fields_whitespace_only(self):
        """Test validation fails for whitespace-only string."""
        from app.helpers.response import validate_required_fields
        from common.helpers.exceptions import InputValidationError

        with pytest.raises(InputValidationError) as exc_info:
            validate_required_fields({'name': '   '})

        assert "'name' is required" in str(exc_info.value)

    def test_validate_required_fields_none_value(self):
        """Test validation fails for None value."""
        from app.helpers.response import validate_required_fields
        from common.helpers.exceptions import InputValidationError

        with pytest.raises(InputValidationError) as exc_info:
            validate_required_fields({'name': None})

        assert "'name' is required" in str(exc_info.value)


class TestGetResponse:
    """Tests for _get_response function."""

    @patch('app.helpers.response.app', new_callable=MagicMock)
    def test_get_response(self, mock_app):
        """Test _get_response creates proper Flask response."""
        from app.helpers.response import _get_response

        mock_response = MagicMock()
        mock_app.response_class.return_value = mock_response
        mock_app.json.dumps.return_value = '{"key": "value"}'
        mock_app.config = {'MIME_TYPE': 'application/json'}

        result = _get_response({'key': 'value'}, 200)

        assert result == mock_response
        mock_app.response_class.assert_called_once()


class TestGetFailureResponse:
    """Tests for get_failure_response function."""

    @patch('app.helpers.response._get_response')
    def test_get_failure_response(self, mock_get_response):
        """Test get_failure_response creates failure response."""
        from app.helpers.response import get_failure_response

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = get_failure_response('Error occurred', 400)

        assert result == mock_response
        mock_get_response.assert_called_once_with(
            {'success': False, 'message': 'Error occurred'},
            400
        )

    @patch('app.helpers.response._get_response')
    def test_get_failure_response_default_status(self, mock_get_response):
        """Test get_failure_response uses default status code."""
        from app.helpers.response import get_failure_response

        get_failure_response('Error')

        mock_get_response.assert_called_once_with(
            {'success': False, 'message': 'Error'},
            200
        )


class TestGetSuccessResponse:
    """Tests for get_success_response function."""

    @patch('app.helpers.response._get_response')
    def test_get_success_response(self, mock_get_response):
        """Test get_success_response creates success response."""
        from app.helpers.response import get_success_response

        mock_response = MagicMock()
        mock_get_response.return_value = mock_response

        result = get_success_response(201, user='John', id=123)

        assert result == mock_response
        mock_get_response.assert_called_once_with(
            {'success': True, 'user': 'John', 'id': 123},
            201
        )

    @patch('app.helpers.response._get_response')
    def test_get_success_response_default_status(self, mock_get_response):
        """Test get_success_response uses default status code."""
        from app.helpers.response import get_success_response

        get_success_response(data='test')

        mock_get_response.assert_called_once_with(
            {'success': True, 'data': 'test'},
            200
        )
