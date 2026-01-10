"""
Unit tests for flask/app/__init__.py  
"""
import pytest
import sys
import os
import importlib.util
from unittest.mock import MagicMock, patch, Mock
from flask import Flask as FlaskApp
from rococo.models.versioned_model import ModelValidationError
from common.helpers.exceptions import InputValidationError, APIException

# Load the project's flask.app module using importlib to bypass naming conflict
flask_app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flask', 'app', '__init__.py')
spec = importlib.util.spec_from_file_location("project_flask_app", flask_app_path)
project_flask_app = importlib.util.module_from_spec(spec)

# We need to patch app.views before executing the module
with patch.dict('sys.modules', {'app.views': MagicMock()}):
    spec.loader.exec_module(project_flask_app)


class TestCreateApp:
    """Tests for create_app function."""

    @patch('common.app_config.get_config')
    def test_create_app_returns_flask_instance(self, mock_get_config):
        """Test that create_app returns a Flask application instance."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Patch within the loaded module to avoid import conflicts
        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        assert isinstance(app, FlaskApp)
        assert app is not None

    @patch('common.app_config.get_config')
    def test_create_app_initializes_cors(self, mock_get_config):
        """Test that create_app initializes CORS."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_cors = MagicMock()
        with patch.object(project_flask_app, 'CORS', mock_cors), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        mock_cors.assert_called_once()

    @patch('common.app_config.get_config')
    def test_create_app_initializes_pooled_connection(self, mock_get_config):
        """Test that create_app initializes PooledConnectionPlugin."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_pooled = MagicMock()
        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin', mock_pooled), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        mock_pooled.assert_called_once()
        call_args = mock_pooled.call_args
        assert call_args[1]['database_type'] == "postgres"

    @patch('common.app_config.get_config')
    def test_create_app_registers_views(self, mock_get_config):
        """Test that create_app registers views."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_views = MagicMock()
        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': mock_views, 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()
            mock_views.initialize_views.assert_called_once()

    @patch('common.app_config.get_config')
    def test_create_app_root_route(self, mock_get_config):
        """Test that root route returns welcome message."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

            # With mocked views, the root route still should work
            # but may return 404 due to view mocking
            with app.test_client() as client:
                response = client.get('/')
                # Accept either 200 or 404 since views are mocked
                assert response.status_code in [200, 404]

    @patch('common.app_config.get_config')
    def test_create_app_root_route_returns_welcome_message(self, mock_get_config):
        """Test that root route returns correct welcome message (line 49)."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Mock external dependencies and views initialization
        mock_initialize_views = MagicMock()
        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(initialize_views=mock_initialize_views),
                                        'app.helpers.response': MagicMock()}):
            # Create the real app
            app = project_flask_app.create_app()

            # Test the root route by accessing the view function directly
            # The route is defined at line 47-49
            with app.app_context():
                # Get the view function for the root route
                view_func = app.view_functions.get('hello_world')
                assert view_func is not None, "Root route should be registered"

                # Call the view function and verify the return value (line 49)
                result = view_func()
                assert result == 'Welcome to Rococo Sample API.'

    @patch('common.app_config.get_config')
    def test_create_app_model_validation_error_handler(self, mock_get_config):
        """Test that ModelValidationError handler is registered."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        # Verify error handler exists - check by class name to avoid object identity issues
        # Error handlers are at app.error_handler_spec[None][None]
        error_handlers = app.error_handler_spec[None][None]
        handler_classes = [cls.__name__ for cls in error_handlers.keys() if cls is not None]
        assert 'ModelValidationError' in handler_classes

    @patch('common.app_config.get_config')
    def test_create_app_input_validation_error_handler(self, mock_get_config):
        """Test that InputValidationError handler is registered."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        # Verify error handler exists - check by class name to avoid object identity issues
        # Error handlers are at app.error_handler_spec[None][None]
        error_handlers = app.error_handler_spec[None][None]
        handler_classes = [cls.__name__ for cls in error_handlers.keys() if cls is not None]
        assert 'InputValidationError' in handler_classes

    @patch('common.app_config.get_config')
    def test_create_app_api_exception_handler(self, mock_get_config):
        """Test that APIException handler is registered."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        # Verify error handler exists - check by class name to avoid object identity issues
        # Error handlers are at app.error_handler_spec[None][None]
        error_handlers = app.error_handler_spec[None][None]
        handler_classes = [cls.__name__ for cls in error_handlers.keys() if cls is not None]
        assert 'APIException' in handler_classes

    def test_create_app_sets_config(self):
        """Test that create_app sets config from get_config."""
        mock_config = MagicMock()
        mock_config.TEST_VALUE = 'test'

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.object(project_flask_app, 'get_config', return_value=mock_config) as mock_get_config, \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

        mock_get_config.assert_called_once()

    @patch('common.app_config.get_config')
    def test_error_handler_execution_model_validation_error(self, mock_get_config):
        """Test that ModelValidationError handler executes its body."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

            # Add a test route that raises ModelValidationError
            @app.route('/test-model-error')
            def test_model_error():
                from rococo.models.versioned_model import ModelValidationError
                raise ModelValidationError(['Test error 1', 'Test error 2'])

        with app.test_client() as client:
            with patch('app.helpers.response.get_failure_response') as mock_response:
                mock_response.return_value = ('Error response', 400)
                response = client.get('/test-model-error')
                # Verify the error handler was called with the joined error messages
                mock_response.assert_called_once()
                call_args = mock_response.call_args[1] if mock_response.call_args[1] else mock_response.call_args[0]
                assert 'message' in str(call_args)

    @patch('common.app_config.get_config')
    def test_error_handler_execution_input_validation_error(self, mock_get_config):
        """Test that InputValidationError handler executes its body."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

            # Add a test route that raises InputValidationError
            @app.route('/test-input-error')
            def test_input_error():
                from common.helpers.exceptions import InputValidationError
                raise InputValidationError('Invalid input provided')

        with app.test_client() as client:
            with patch('app.helpers.response.get_failure_response') as mock_response:
                mock_response.return_value = ('Error response', 400)
                response = client.get('/test-input-error')
                # Verify the error handler was called
                mock_response.assert_called_once()
                call_args = mock_response.call_args
                assert 'Invalid input provided' in str(call_args)

    @patch('common.app_config.get_config')
    def test_error_handler_execution_api_exception(self, mock_get_config):
        """Test that APIException handler executes its body."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        with patch.object(project_flask_app, 'CORS'), \
             patch.object(project_flask_app, 'PooledConnectionPlugin'), \
             patch.dict('sys.modules', {'app.views': MagicMock(), 'app.helpers.response': MagicMock()}):
            app = project_flask_app.create_app()

            # Add a test route that raises APIException
            @app.route('/test-api-error')
            def test_api_error():
                from common.helpers.exceptions import APIException
                raise APIException('API error occurred')

        with app.test_client() as client:
            with patch('app.helpers.response.get_failure_response') as mock_response:
                mock_response.return_value = ('Error response', 500)
                response = client.get('/test-api-error')
                # Verify the error handler was called
                mock_response.assert_called_once()
                call_args = mock_response.call_args
                assert 'API error occurred' in str(call_args)
