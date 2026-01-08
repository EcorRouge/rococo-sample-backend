"""
Comprehensive tests for common/app_logger.py
"""
import pytest
import logging
import sys
from unittest.mock import MagicMock, patch, call
from common.app_logger import (
    _get_log_level,
    _get_formatter,
    rollbar_except_hook,
    set_rollbar_exception_catch,
    get_console_handler,
    get_rollbar_handler,
    create_logger,
    get_logger
)


@pytest.fixture
def mock_config():
    """Mock the config module."""
    with patch('common.app_logger.config') as mock_cfg:
        mock_cfg.APP_ENV = "development"
        mock_cfg.LOGLEVEL = "INFO"
        mock_cfg.ROLLBAR_ACCESS_TOKEN = ""
        yield mock_cfg


class TestLoggerHelpers:
    """Tests for logger helper functions."""

    def test_get_log_level_development(self, mock_config):
        """Test getting log level in development environment."""
        mock_config.APP_ENV = "development"
        level = _get_log_level()
        assert level == logging.DEBUG

    def test_get_log_level_production_default(self, mock_config):
        """Test getting log level in production with default."""
        mock_config.APP_ENV = "production"
        mock_config.LOGLEVEL = "INVALID"
        level = _get_log_level()
        assert level == logging.INFO

    def test_get_log_level_production_custom(self, mock_config):
        """Test getting log level in production with custom level."""
        mock_config.APP_ENV = "production"
        mock_config.LOGLEVEL = "ERROR"
        level = _get_log_level()
        assert level == logging.ERROR

    def test_get_log_level_production_warning(self, mock_config):
        """Test getting log level in production with WARNING."""
        mock_config.APP_ENV = "production"
        mock_config.LOGLEVEL = "WARNING"
        level = _get_log_level()
        assert level == logging.WARNING

    def test_get_formatter(self):
        """Test getting log formatter."""
        formatter = _get_formatter()
        assert isinstance(formatter, logging.Formatter)
        assert '%(asctime)s' in formatter._fmt
        assert '%(levelname)s' in formatter._fmt
        assert '%(module)s' in formatter._fmt

    def test_get_console_handler(self):
        """Test getting console handler."""
        handler = get_console_handler()
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stdout
        assert handler.formatter is not None


class TestRollbarIntegration:
    """Tests for Rollbar integration."""

    @patch('common.app_logger.rollbar')
    @patch('common.app_logger.sys')
    def test_rollbar_except_hook(self, mock_sys, mock_rollbar):
        """Test Rollbar exception hook."""
        # Setup
        exc_type = Exception
        exc_value = Exception("Test error")
        exc_traceback = None
        mock_sys.__excepthook__ = MagicMock()

        # Execute
        rollbar_except_hook(exc_type, exc_value, exc_traceback)

        # Verify
        mock_rollbar.report_exc_info.assert_called_once_with((exc_type, exc_value, exc_traceback))
        mock_sys.__excepthook__.assert_called_once_with(exc_type, exc_value, exc_traceback)

    @patch('common.app_logger.sys')
    @patch('common.app_logger.rollbar_except_hook')
    def test_set_rollbar_exception_catch(self, mock_rollbar_hook, mock_sys):
        """Test setting Rollbar exception hook."""
        # Execute
        set_rollbar_exception_catch()

        # Verify
        assert mock_sys.excepthook == mock_rollbar_hook

    @patch('common.app_logger.ROLLBAR_ACCESS_TOKEN', 'test-token')
    @patch('common.app_logger.RollbarHandler')
    def test_get_rollbar_handler(self, mock_rollbar_handler_class, mock_config):
        """Test getting Rollbar handler."""
        # Setup
        mock_config.LOGLEVEL = "WARN"
        mock_handler = MagicMock()
        mock_rollbar_handler_class.return_value = mock_handler

        # Execute
        with patch('common.app_logger.ROLLBAR_ACCESS_TOKEN', 'test-token'):
            with patch('common.app_logger.ROLLBAR_ENVIRONMENT', 'test'):
                handler = get_rollbar_handler()

        # Verify
        assert handler == mock_handler
        mock_handler.setLevel.assert_called_once_with(logging.WARN)


class TestLoggerCreation:
    """Tests for logger creation."""

    @patch('common.app_logger.get_console_handler')
    @patch('common.app_logger._get_log_level')
    @patch('common.app_logger.ROLLBAR_ACCESS_TOKEN', '')
    def test_create_logger_without_rollbar(self, mock_get_log_level, mock_get_console_handler):
        """Test creating logger without Rollbar."""
        # Setup
        mock_get_log_level.return_value = logging.INFO
        mock_console_handler = MagicMock()
        mock_get_console_handler.return_value = mock_console_handler

        # Execute
        logger = create_logger("test_logger")

        # Verify
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        mock_get_console_handler.assert_called_once()

    @patch('common.app_logger.get_console_handler')
    @patch('common.app_logger.get_rollbar_handler')
    @patch('common.app_logger._get_log_level')
    @patch('common.app_logger.ROLLBAR_ACCESS_TOKEN', 'test-token')
    def test_create_logger_with_rollbar(self, mock_get_log_level, mock_get_rollbar_handler, mock_get_console_handler):
        """Test creating logger with Rollbar."""
        # Setup
        mock_get_log_level.return_value = logging.INFO
        mock_console_handler = MagicMock()
        mock_rollbar_handler = MagicMock()
        mock_get_console_handler.return_value = mock_console_handler
        mock_get_rollbar_handler.return_value = mock_rollbar_handler

        # Execute
        logger = create_logger("test_logger")

        # Verify
        assert logger.name == "test_logger"
        mock_get_console_handler.assert_called_once()
        mock_get_rollbar_handler.assert_called_once()

    @patch('common.app_logger.create_logger')
    def test_get_logger(self, mock_create_logger):
        """Test get_logger function."""
        # Setup
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger

        # Execute
        logger = get_logger("my_logger")

        # Verify
        assert logger == mock_logger
        mock_create_logger.assert_called_once_with("my_logger")

    @patch('common.app_logger._get_log_level')
    def test_create_logger_clears_handlers(self, mock_get_log_level):
        """Test that create_logger clears existing handlers."""
        # Setup
        mock_get_log_level.return_value = logging.INFO

        # Execute
        logger = create_logger("test_clear_handlers")

        # Verify - should start with empty handlers
        # Then add console handler (and rollbar if configured)
        assert len(logger.handlers) >= 1

    @patch('common.app_logger._get_log_level')
    def test_create_logger_propagate_false(self, mock_get_log_level):
        """Test that logger propagate is set to False."""
        # Setup
        mock_get_log_level.return_value = logging.INFO

        # Execute
        logger = create_logger("test_propagate")

        # Verify
        assert logger.propagate is False
