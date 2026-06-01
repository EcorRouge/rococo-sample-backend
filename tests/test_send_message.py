"""
Unit tests for common/tasks/send_message.py
"""
import pytest
import pika
import json
from unittest.mock import MagicMock, patch, call
from common.tasks.send_message import (
    get_connection_parameters,
    establish_connection,
    MessageSender
)


class TestGetConnectionParameters:
    """Tests for get_connection_parameters function."""

    @patch('common.tasks.send_message.config')
    def test_get_connection_parameters_returns_correct_type(self, mock_config):
        """Test that get_connection_parameters returns ConnectionParameters."""
        mock_config.RABBITMQ_HOST = 'localhost'
        mock_config.RABBITMQ_PORT = 5672
        mock_config.RABBITMQ_VIRTUAL_HOST = '/'
        mock_config.RABBITMQ_USER = 'guest'
        mock_config.RABBITMQ_PASSWORD = 'guest'  # NOSONAR - Test data

        result = get_connection_parameters()

        assert isinstance(result, pika.ConnectionParameters)
        assert result.host == 'localhost'
        assert result.port == 5672

    @patch('common.tasks.send_message.config')
    def test_get_connection_parameters_uses_config_values(self, mock_config):
        """Test that get_connection_parameters uses values from config."""
        mock_config.RABBITMQ_HOST = 'test-host'
        mock_config.RABBITMQ_PORT = 5673
        mock_config.RABBITMQ_VIRTUAL_HOST = '/test'
        mock_config.RABBITMQ_USER = 'testuser'
        mock_config.RABBITMQ_PASSWORD = 'testpass'  # NOSONAR - Test data

        result = get_connection_parameters()

        assert result.host == 'test-host'
        assert result.port == 5673
        assert result.virtual_host == '/test'


class TestEstablishConnection:
    """Tests for establish_connection function."""

    @patch('common.tasks.send_message.pika.BlockingConnection')
    def test_establish_connection_success_first_try(self, mock_connection_class):
        """Test successful connection on first try."""
        mock_connection = MagicMock()
        mock_connection_class.return_value = mock_connection

        parameters = MagicMock()
        result = establish_connection(parameters)

        assert result == mock_connection
        mock_connection_class.assert_called_once_with(parameters)

    @patch('common.tasks.send_message.time.sleep')
    @patch('common.tasks.send_message.pika.BlockingConnection')
    def test_establish_connection_retry_success(self, mock_connection_class, mock_sleep):
        """Test connection succeeds after retries."""
        mock_connection = MagicMock()
        # Fail twice, then succeed
        mock_connection_class.side_effect = [Exception("Connection failed"), Exception("Connection failed"), mock_connection]

        parameters = MagicMock()
        result = establish_connection(parameters, max_retries=10)

        assert result == mock_connection
        assert mock_connection_class.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('common.tasks.send_message.time.sleep')
    @patch('common.tasks.send_message.pika.BlockingConnection')
    def test_establish_connection_max_retries_exceeded(self, mock_connection_class, mock_sleep):
        """Test connection fails after max retries."""
        mock_connection_class.side_effect = Exception("Connection failed")

        parameters = MagicMock()

        with pytest.raises(Exception) as exc_info:
            establish_connection(parameters, max_retries=3)

        assert "Connection failed" in str(exc_info.value)
        assert mock_connection_class.call_count == 3

    @patch('common.tasks.send_message.time.sleep')
    @patch('common.tasks.send_message.pika.BlockingConnection')
    def test_establish_connection_exponential_backoff(self, mock_connection_class, mock_sleep):
        """Test that connection retries use exponential backoff."""
        mock_connection = MagicMock()
        # Fail three times, then succeed
        mock_connection_class.side_effect = [
            Exception("Failed 1"),
            Exception("Failed 2"),
            Exception("Failed 3"),
            mock_connection
        ]

        parameters = MagicMock()
        result = establish_connection(parameters, max_retries=10)

        # Verify exponential backoff: 2^1, 2^2, 2^3
        sleep_calls = [call(2), call(4), call(8)]
        mock_sleep.assert_has_calls(sleep_calls)

    @patch('common.tasks.send_message.pika.BlockingConnection')
    def test_establish_connection_zero_retries(self, mock_connection_class):
        """Test establish_connection with max_retries=0 (while loop exits immediately)."""
        parameters = MagicMock()

        # With max_retries=0, the while loop condition is false from the start
        # This should return None since the loop never executes
        result = establish_connection(parameters, max_retries=0)

        # No connection attempt should be made
        mock_connection_class.assert_not_called()
        assert result is None


class TestMessageSenderInitialization:
    """Tests for MessageSender initialization."""

    @patch('common.tasks.send_message.get_connection_parameters')
    def test_init_creates_parameters(self, mock_get_params):
        """Test that __init__ creates connection parameters."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        sender = MessageSender()

        assert sender.parameters == mock_params
        mock_get_params.assert_called_once()


class TestSendMessage:
    """Tests for send_message method."""

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_success(self, mock_get_params, mock_establish_conn):
        """Test successful message sending."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        data = {'key': 'value', 'event': 'test_event'}
        sender.send_message('test_queue', data)

        # Verify channel operations
        mock_channel.queue_declare.assert_called_once_with(queue='test_queue', durable=True)
        mock_channel.basic_publish.assert_called_once()

        # Verify message body
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['routing_key'] == 'test_queue'
        assert json.loads(call_args[1]['body'].decode()) == data

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_with_exchange(self, mock_get_params, mock_establish_conn):
        """Test message sending with custom exchange."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        data = {'key': 'value'}
        sender.send_message('test_queue', data, exchange_name='test_exchange')

        # Verify exchange declaration
        mock_channel.exchange_declare.assert_called_once_with(
            exchange='test_exchange',
            exchange_type='topic',
            durable=True
        )

        # Verify message published to exchange
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['exchange'] == 'test_exchange'

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_without_exchange(self, mock_get_params, mock_establish_conn):
        """Test message sending without exchange (default exchange)."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        data = {'key': 'value'}
        sender.send_message('test_queue', data)

        # Verify no exchange declaration
        mock_channel.exchange_declare.assert_not_called()

        # Verify message published to default exchange
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['exchange'] == ''

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_with_custom_properties(self, mock_get_params, mock_establish_conn):
        """Test message sending with custom properties."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        custom_props = pika.BasicProperties(delivery_mode=1, content_type='application/json')
        data = {'key': 'value'}
        sender.send_message('test_queue', data, properties=custom_props)

        # Verify custom properties used
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['properties'] == custom_props

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_default_properties(self, mock_get_params, mock_establish_conn):
        """Test message sending uses default properties when none provided."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        data = {'key': 'value'}
        sender.send_message('test_queue', data)

        # Verify default properties (delivery_mode=2 for persistent)
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['properties'].delivery_mode == 2

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_json_serialization(self, mock_get_params, mock_establish_conn):
        """Test that message data is properly JSON serialized."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        data = {'string': 'value', 'number': 42, 'bool': True, 'list': [1, 2, 3]}
        sender.send_message('test_queue', data)

        # Verify message is JSON encoded
        call_args = mock_channel.basic_publish.call_args
        body = call_args[1]['body']
        decoded = json.loads(body.decode())
        assert decoded == data

    @patch('common.tasks.send_message.establish_connection')
    @patch('common.tasks.send_message.get_connection_parameters')
    def test_send_message_connection_context_manager(self, mock_get_params, mock_establish_conn):
        """Test that connection is used as context manager."""
        mock_params = MagicMock()
        mock_get_params.return_value = mock_params

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_conn.return_value = mock_connection

        sender = MessageSender()
        sender.send_message('test_queue', {'key': 'value'})

        # Verify context manager methods were called
        mock_connection.__enter__.assert_called_once()
        mock_connection.__exit__.assert_called_once()
