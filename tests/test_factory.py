"""
Unit tests for common/repositories/factory.py
"""
import pytest
from unittest.mock import MagicMock, patch


class TestGetFlaskPooledDb:
    """Tests for get_flask_pooled_db function."""

    @patch('flask.current_app')
    @patch('flask.has_app_context')
    def test_returns_pooled_db_when_available(self, mock_has_context, mock_current_app):
        """Test that pooled_db is returned when Flask context is available."""
        from common.repositories.factory import get_flask_pooled_db

        mock_has_context.return_value = True
        mock_pooled_db = MagicMock()
        mock_current_app.extensions = {'pooled_db': mock_pooled_db}

        result = get_flask_pooled_db()

        assert result == mock_pooled_db

    @patch('flask.has_app_context')
    def test_returns_none_when_no_flask_context(self, mock_has_context):
        """Test that None is returned when no Flask context."""
        from common.repositories.factory import get_flask_pooled_db

        mock_has_context.return_value = False

        result = get_flask_pooled_db()

        assert result is None

    @patch('flask.current_app')
    @patch('flask.has_app_context')
    def test_returns_none_when_pooled_db_not_registered(self, mock_has_context, mock_current_app):
        """Test that None is returned when pooled_db extension is not registered."""
        from common.repositories.factory import get_flask_pooled_db

        mock_has_context.return_value = True
        mock_current_app.extensions = {}

        result = get_flask_pooled_db()

        assert result is None

    def test_returns_none_when_import_error(self):
        """Test that None is returned when Flask is not installed."""
        from common.repositories.factory import get_flask_pooled_db

        with patch.dict('sys.modules', {'flask': None}):
            result = get_flask_pooled_db()
            assert result is None


class TestMessageAdapterType:
    """Tests for MessageAdapterType enum."""

    def test_rabbitmq_value(self):
        """Test RabbitMQ enum value."""
        from common.repositories.factory import MessageAdapterType

        assert MessageAdapterType.RABBITMQ.value == "rabbitmq"

    def test_sqs_value(self):
        """Test SQS enum value."""
        from common.repositories.factory import MessageAdapterType

        assert MessageAdapterType.SQS.value == "sqs"

    def test_repr(self):
        """Test __repr__ method returns string value."""
        from common.repositories.factory import MessageAdapterType

        assert repr(MessageAdapterType.RABBITMQ) == "rabbitmq"
        assert repr(MessageAdapterType.SQS) == "sqs"


class TestRepoType:
    """Tests for RepoType enum."""

    def test_auto_generated_values(self):
        """Test that enum values are auto-generated as lowercase names."""
        from common.repositories.factory import RepoType

        assert RepoType.PERSON.value == "person"
        assert RepoType.ORGANIZATION.value == "organization"
        assert RepoType.EMAIL.value == "email"
        assert RepoType.LOGIN_METHOD.value == "login_method"
        assert RepoType.PERSON_ORGANIZATION_ROLE.value == "person_organization_role"


class TestGetConnectionResolver:
    """Tests for get_connection_resolver function."""

    @patch('common.repositories.factory.get_flask_pooled_db')
    def test_returns_get_connection_when_pooled_db_available(self, mock_get_pooled_db):
        """Test that get_connection is returned when pooled_db is available."""
        from common.repositories.factory import get_connection_resolver

        mock_pooled_db = MagicMock()
        mock_get_pooled_db.return_value = mock_pooled_db

        result = get_connection_resolver()

        assert result == mock_pooled_db.get_connection

    @patch('common.repositories.factory.get_flask_pooled_db')
    def test_returns_none_when_no_pooled_db(self, mock_get_pooled_db):
        """Test that None is returned when no pooled_db."""
        from common.repositories.factory import get_connection_resolver

        mock_get_pooled_db.return_value = None

        result = get_connection_resolver()

        assert result is None


class TestGetConnectionCloser:
    """Tests for get_connection_closer function."""

    @patch('common.repositories.factory.get_flask_pooled_db')
    def test_returns_noop_when_pooled_db_available(self, mock_get_pooled_db):
        """Test that a no-op function is returned when pooled_db is available."""
        from common.repositories.factory import get_connection_closer

        mock_pooled_db = MagicMock()
        mock_get_pooled_db.return_value = mock_pooled_db

        result = get_connection_closer()

        # Should return a callable that does nothing
        assert callable(result)
        # Calling should not raise
        result('arg1', kwarg='value')

    @patch('common.repositories.factory.get_flask_pooled_db')
    def test_returns_none_when_no_pooled_db(self, mock_get_pooled_db):
        """Test that None is returned when no pooled_db."""
        from common.repositories.factory import get_connection_closer

        mock_get_pooled_db.return_value = None

        result = get_connection_closer()

        assert result is None


class TestRepositoryFactory:
    """Tests for RepositoryFactory class."""

    @patch('common.repositories.factory.PostgreSQLAdapter')
    @patch('common.repositories.factory.get_connection_resolver')
    @patch('common.repositories.factory.get_connection_closer')
    def test_get_db_connection(self, mock_closer, mock_resolver, mock_adapter, mock_config):
        """Test get_db_connection creates PostgreSQLAdapter."""
        from common.repositories.factory import RepositoryFactory

        factory = RepositoryFactory(mock_config)
        factory.get_db_connection()

        mock_adapter.assert_called_once_with(
            mock_config.POSTGRES_HOST,
            int(mock_config.POSTGRES_PORT),
            mock_config.POSTGRES_USER,
            mock_config.POSTGRES_PASSWORD,
            mock_config.POSTGRES_DB,
            connection_resolver=mock_resolver.return_value,
            connection_closer=mock_closer.return_value
        )

    @patch('common.repositories.factory.RabbitMqConnection')
    def test_get_adapter(self, mock_rabbitmq, mock_config):
        """Test get_adapter creates RabbitMQ connection."""
        from common.repositories.factory import RepositoryFactory

        factory = RepositoryFactory(mock_config)
        factory.get_adapter()

        mock_rabbitmq.assert_called_once()

    @patch('common.repositories.factory.RabbitMqConnection')
    @patch('common.repositories.factory.PostgreSQLAdapter')
    def test_get_repository_person(self, mock_adapter, mock_rabbitmq, mock_config):
        """Test get_repository for PERSON type."""
        from common.repositories.factory import RepositoryFactory, RepoType

        factory = RepositoryFactory(mock_config)
        mock_person_repo = MagicMock()

        with patch.dict(RepositoryFactory._repositories, {RepoType.PERSON: mock_person_repo}):
            with patch('flask.g') as mock_g:
                mock_g.current_user_id = 'user-123'
                factory.get_repository(RepoType.PERSON, person_id='person-123')

        mock_person_repo.assert_called_once()

    @patch('common.repositories.factory.RabbitMqConnection')
    @patch('common.repositories.factory.PostgreSQLAdapter')
    def test_get_repository_invalid_type_raises(self, mock_adapter, mock_rabbitmq, mock_config):
        """Test get_repository raises ValueError for invalid type."""
        from common.repositories.factory import RepositoryFactory

        factory = RepositoryFactory(mock_config)

        # Create a mock enum that's not in _repositories
        mock_repo_type = MagicMock()
        mock_repo_type.value = 'invalid'

        with pytest.raises(ValueError) as exc_info:
            factory.get_repository(mock_repo_type)

        assert "No repository found" in str(exc_info.value)

    @patch('common.repositories.factory.RabbitMqConnection')
    @patch('common.repositories.factory.PostgreSQLAdapter')
    def test_get_repository_with_flask_g_person_id(self, mock_adapter, mock_rabbitmq, mock_config):
        """Test get_repository gets person_id from Flask g when not provided."""
        from common.repositories.factory import RepositoryFactory, RepoType

        factory = RepositoryFactory(mock_config)
        mock_org_repo = MagicMock()

        with patch.dict(RepositoryFactory._repositories, {RepoType.ORGANIZATION: mock_org_repo}):
            with patch('flask.g') as mock_g:
                mock_g.current_user_id = 'flask-user-id'
                factory.get_repository(RepoType.ORGANIZATION)

        mock_org_repo.assert_called_once()

    @patch('common.repositories.factory.RabbitMqConnection')
    @patch('common.repositories.factory.PostgreSQLAdapter')
    def test_get_repository_handles_import_error_for_flask(self, mock_adapter, mock_rabbitmq, mock_config):
        """Test get_repository handles ImportError when Flask is not available."""
        from common.repositories.factory import RepositoryFactory, RepoType

        factory = RepositoryFactory(mock_config)
        mock_email_repo = MagicMock()

        with patch.dict(RepositoryFactory._repositories, {RepoType.EMAIL: mock_email_repo}):
            with patch.dict('sys.modules', {'flask': None}):
                factory.get_repository(RepoType.EMAIL)

        mock_email_repo.assert_called_once()
