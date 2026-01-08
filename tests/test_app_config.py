"""
Comprehensive tests for common/app_config.py
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from common.app_config import BaseConfig, Config, get_config


class TestBaseConfig:
    """Tests for BaseConfig class."""

    def test_base_config_env_property(self):
        """Test that ENV property returns APP_ENV."""
        # Setup
        with patch.dict(os.environ, {'APP_ENV': 'test'}):
            config = BaseConfig()

            # Verify
            assert config.ENV == 'test'

    def test_base_config_different_environments(self):
        """Test BaseConfig with different environment values."""
        environments = ['development', 'staging', 'production', 'test']

        for env in environments:
            with patch.dict(os.environ, {'APP_ENV': env}):
                config = BaseConfig()
                assert config.ENV == env
                assert config.APP_ENV == env


class TestConfig:
    """Tests for Config class."""

    def test_config_default_values(self):
        """Test Config with default values."""
        # Setup minimal required env vars
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_DB': 'testdb',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'test-secret'
        }, clear=True):
            config = Config()

            # Verify defaults
            assert config.DEBUG is False
            assert config.TESTING is False
            assert config.LOGLEVEL == 'INFO'
            assert config.ACCESS_TOKEN_EXPIRE == 3600
            assert config.MIME_TYPE == 'application/json'

    def test_config_custom_values(self):
        """Test Config with custom values."""
        with patch.dict(os.environ, {
            'APP_ENV': 'production',
            'DEBUG': 'true',
            'TESTING': 'true',
            'LOGLEVEL': 'ERROR',
            'ACCESS_TOKEN_EXPIRE': '7200',
            'POSTGRES_HOST': 'db.example.com',
            'POSTGRES_PORT': '5433',
            'POSTGRES_USER': 'produser',
            'POSTGRES_PASSWORD': 'prodpass',
            'POSTGRES_DB': 'proddb',
            'RABBITMQ_HOST': 'mq.example.com',
            'RABBITMQ_PORT': '5673',
            'RABBITMQ_USER': 'admin',
            'RABBITMQ_PASSWORD': 'adminpass',
            'AUTH_JWT_SECRET': 'prod-secret'
        }, clear=True):
            config = Config()

            # Verify custom values
            assert config.DEBUG is True
            assert config.TESTING is True
            assert config.LOGLEVEL == 'ERROR'
            assert config.ACCESS_TOKEN_EXPIRE == 7200

    def test_config_database_settings(self):
        """Test database configuration settings."""
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'POSTGRES_HOST': 'dbhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'dbuser',
            'POSTGRES_PASSWORD': 'dbpass',
            'POSTGRES_DB': 'mydb',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = Config()

            assert config.POSTGRES_HOST == 'dbhost'
            assert config.POSTGRES_PORT == 5432
            assert config.POSTGRES_USER == 'dbuser'
            assert config.POSTGRES_PASSWORD == 'dbpass'
            assert config.POSTGRES_DB == 'mydb'

    def test_config_rabbitmq_settings(self):
        """Test RabbitMQ configuration settings."""
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'RABBITMQ_HOST': 'mqhost',
            'RABBITMQ_PORT': '5673',
            'RABBITMQ_VIRTUAL_HOST': '/custom',
            'RABBITMQ_USER': 'mquser',
            'RABBITMQ_PASSWORD': 'mqpass',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = Config()

            assert config.RABBITMQ_HOST == 'mqhost'
            assert config.RABBITMQ_PORT == 5673
            assert config.RABBITMQ_VIRTUAL_HOST == '/custom'
            assert config.RABBITMQ_USER == 'mquser'
            assert config.RABBITMQ_PASSWORD == 'mqpass'

    def test_config_oauth_settings(self):
        """Test OAuth configuration settings."""
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'GOOGLE_CLIENT_ID': 'google-id',
            'GOOGLE_CLIENT_SECRET': 'google-secret',
            'MICROSOFT_CLIENT_ID': 'ms-id',
            'MICROSOFT_CLIENT_SECRET': 'ms-secret',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = Config()

            assert config.GOOGLE_CLIENT_ID == 'google-id'
            assert config.GOOGLE_CLIENT_SECRET == 'google-secret'
            assert config.MICROSOFT_CLIENT_ID == 'ms-id'
            assert config.MICROSOFT_CLIENT_SECRET == 'ms-secret'

    def test_config_default_user_password_production(self):
        """Test DEFAULT_USER_PASSWORD in production generates random password."""
        with patch.dict(os.environ, {
            'APP_ENV': 'production',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = Config()

            # Verify it's random (12 characters)
            password = config.DEFAULT_USER_PASSWORD
            assert len(password) == 12
            assert password.isalnum()

    def test_config_default_user_password_development(self):
        """Test DEFAULT_USER_PASSWORD in development uses default."""
        with patch.dict(os.environ, {
            'APP_ENV': 'development',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = Config()

            assert config.DEFAULT_USER_PASSWORD == 'Default@Password123'

    def test_config_queue_settings(self):
        """Test queue configuration settings."""
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'QUEUE_NAME_PREFIX': 'prod_',
            'EmailServiceProcessor_QUEUE_NAME': 'email-processor',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = Config()

            assert config.QUEUE_NAME_PREFIX == 'prod_'
            assert config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME == 'email-processor'


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_returns_config_instance(self):
        """Test that get_config returns a Config instance."""
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config = get_config()

            assert isinstance(config, Config)
            assert config.APP_ENV == 'test'

    def test_get_config_multiple_calls(self):
        """Test that get_config can be called multiple times."""
        with patch.dict(os.environ, {
            'APP_ENV': 'test',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'pass',
            'POSTGRES_DB': 'db',
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'guest',
            'RABBITMQ_PASSWORD': 'guest',
            'AUTH_JWT_SECRET': 'secret'
        }, clear=True):
            config1 = get_config()
            config2 = get_config()

            # Both should be Config instances
            assert isinstance(config1, Config)
            assert isinstance(config2, Config)
