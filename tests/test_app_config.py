"""
Unit tests for common/app_config.py
"""
import pytest
import os
from unittest.mock import MagicMock, patch
from common.app_config import BaseConfig, Config, get_config


class TestBaseConfig:
    """Tests for BaseConfig class."""

    def test_base_config_env_property(self):
        """Test that ENV property returns APP_ENV value."""
        config = BaseConfig(APP_ENV='test')
        assert config.ENV == 'test'

    def test_base_config_different_env_values(self):
        """Test ENV property with different values."""
        for env in ['development', 'production', 'staging']:
            config = BaseConfig(APP_ENV=env)
            assert config.ENV == env


class TestConfig:
    """Tests for Config class."""

    def test_config_default_values(self):
        """Test that Config has sensible defaults."""
        config = Config(
            APP_ENV='test',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        assert config.DEBUG is False
        assert config.TESTING is False
        assert config.LOGLEVEL == 'INFO'
        assert config.ACCESS_TOKEN_EXPIRE == 3600

    def test_config_mime_type(self):
        """Test that MIME_TYPE is set correctly."""
        config = Config(
            APP_ENV='test',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        assert config.MIME_TYPE == 'application/json'

    def test_config_reset_token_expire_default(self):
        """Test RESET_TOKEN_EXPIRE default value."""
        config = Config(
            APP_ENV='test',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        # 3 days in seconds
        assert config.RESET_TOKEN_EXPIRE == 60 * 60 * 24 * 3

    def test_config_rabbitmq_virtual_host_default(self):
        """Test RABBITMQ_VIRTUAL_HOST default value."""
        config = Config(
            APP_ENV='test',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        assert config.RABBITMQ_VIRTUAL_HOST == '/'

    def test_config_queue_name_prefix_default(self):
        """Test QUEUE_NAME_PREFIX default value."""
        config = Config(
            APP_ENV='test',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        assert config.QUEUE_NAME_PREFIX == ''

    def test_config_email_service_queue_default(self):
        """Test EMAIL_SERVICE_PROCESSOR_QUEUE_NAME default value."""
        config = Config(
            APP_ENV='test',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        assert config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME == 'email-transmitter'

    def test_default_user_password_development(self):
        """Test DEFAULT_USER_PASSWORD in development."""
        config = Config(
            APP_ENV='development',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        assert config.DEFAULT_USER_PASSWORD == 'Default@Password123'

    def test_default_user_password_production(self):
        """Test DEFAULT_USER_PASSWORD in production generates random."""
        config = Config(
            APP_ENV='production',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        password = config.DEFAULT_USER_PASSWORD
        # Should be 12 characters random string
        assert len(password) == 12
        assert password.isalnum()

    def test_default_user_password_production_varies(self):
        """Test that production password is random."""
        config = Config(
            APP_ENV='production',
            POSTGRES_HOST='localhost',
            POSTGRES_PORT=5432,
            POSTGRES_USER='test',
            POSTGRES_PASSWORD='test',  # NOSONAR - Test data
            POSTGRES_DB='testdb',
            RABBITMQ_HOST='localhost',
            RABBITMQ_PORT=5672,
            RABBITMQ_USER='guest',
            RABBITMQ_PASSWORD='guest',  # NOSONAR - Test data
            AUTH_JWT_SECRET='test-secret'
        )

        # Get multiple passwords - they should be different
        passwords = [config.DEFAULT_USER_PASSWORD for _ in range(5)]
        # At least some should be different (statistically very unlikely to be all same)
        assert len(set(passwords)) > 1


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_returns_config_instance(self):
        """Test that get_config returns Config instance."""
        config = get_config()

        assert isinstance(config, Config)

    def test_get_config_uses_environment_variables(self):
        """Test that get_config reads from environment."""
        # This will use the environment variables set in conftest.py
        config = get_config()

        assert config.APP_ENV is not None
