"""
Comprehensive tests for common/tasks/send_message.py
"""
import pytest
import json
from unittest.mock import MagicMock, patch, call
import pika
from pika.exchange_type import ExchangeType
from common.tasks.send_message import (
    get_connection_parameters,
    establish_connection,
    MessageSender
)


@pytest.fixture
def mock_config():
    """Mock the config module."""
    with patch('common.tasks.send_message.config') as mock_cfg:
        mock_cfg.RABBITMQ_HOST = "localhost"
        mock_cfg.RABBITMQ_PORT = 5672
        mock_cfg.RABBITMQ_VIRTUAL_HOST = "/"
        mock_cfg.RABBITMQ_USER = "guest"
        mock_cfg.RABBITMQ_PASSWORD = "guest"
        yield mock_cfg


class TestConnectionFunctions:
    """Tests for connection helper functions."""

    def test_get_connection_parameters(self, mock_config):
        """Test getting RabbitMQ connection parameters."""
        # Execute
        params = get_connection_parameters()

        # Verify
        assert isinstance(params, pika.ConnectionParameters)
        assert params.host == "localhost"
        assert params.port == 5672
        assert params.virtual_host == "/"

    @patch('common.tasks.send_message.pika.BlockingConnection')
    def test_establish_connection_success(self, mock_blocking_connection, mock_config):
        """Test successful connection establishment."""
        # Setup
        mock_connection = MagicMock()
        mock_blocking_connection.return_value = mock_connection
        params = MagicMock()

        # Execute
        connection = establish_connection(params, max_retries=3)

        # Verify
        assert connection == mock_connection
        mock_blocking_connection.assert_called_once_with(params)

    @patch('common.tasks.send_message.pika.BlockingConnection')
    @patch('common.tasks.send_message.time.sleep')
    def test_establish_connection_retry_then_success(self, mock_sleep, mock_blocking_connection, mock_config):
        """Test connection with retry then success."""
        # Setup
        mock_connection = MagicMock()
        mock_blocking_connection.side_effect = [
            Exception("Connection failed"),
            mock_connection
        ]
        params = MagicMock()

        # Execute
        connection = establish_connection(params, max_retries=3)

        # Verify
        assert connection == mock_connection
        assert mock_blocking_connection.call_count == 2
        mock_sleep.assert_called_once()

    @patch('common.tasks.send_message.pika.BlockingConnection')
    @patch('common.tasks.send_message.time.sleep')
    def test_establish_connection_max_retries_exceeded(self, mock_sleep, mock_blocking_connection, mock_config):
        """Test connection fails after max retries."""
        # Setup
        mock_blocking_connection.side_effect = Exception("Connection failed")
        params = MagicMock()

        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            establish_connection(params, max_retries=2)

        assert "Connection failed" in str(exc_info.value)
        assert mock_blocking_connection.call_count == 2


class TestMessageSender:
    """Tests for MessageSender class."""

    def test_message_sender_initialization(self, mock_config):
        """Test MessageSender initialization."""
        # Execute
        sender = MessageSender()

        # Verify
        assert sender.parameters is not None
        assert isinstance(sender.parameters, pika.ConnectionParameters)

    @patch('common.tasks.send_message.establish_connection')
    def test_send_message_success(self, mock_establish_connection, mock_config):
        """Test successful message sending."""
        # Setup
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_connection.return_value = mock_connection

        sender = MessageSender()
        test_data = {"event": "TEST_EVENT", "data": {"key": "value"}}

        # Execute
        sender.send_message("test-queue", test_data)

        # Verify
        mock_channel.queue_declare.assert_called_once_with(queue="test-queue", durable=True)
        mock_channel.basic_publish.assert_called_once()

        # Verify publish arguments
        publish_call = mock_channel.basic_publish.call_args
        assert publish_call[1]['exchange'] == ""
        assert publish_call[1]['routing_key'] == "test-queue"
        assert json.loads(publish_call[1]['body'].decode()) == test_data

    @patch('common.tasks.send_message.establish_connection')
    def test_send_message_with_custom_properties(self, mock_establish_connection, mock_config):
        """Test sending message with custom properties."""
        # Setup
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_connection.return_value = mock_connection

        sender = MessageSender()
        test_data = {"event": "TEST_EVENT"}
        custom_properties = pika.BasicProperties(delivery_mode=1)

        # Execute
        sender.send_message("test-queue", test_data, properties=custom_properties)

        # Verify
        publish_call = mock_channel.basic_publish.call_args
        assert publish_call[1]['properties'] == custom_properties

    @patch('common.tasks.send_message.establish_connection')
    def test_send_message_with_exchange(self, mock_establish_connection, mock_config):
        """Test sending message with custom exchange."""
        # Setup
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_connection.return_value = mock_connection

        sender = MessageSender()
        test_data = {"event": "TEST_EVENT"}

        # Execute
        sender.send_message("test-queue", test_data, exchange_name="test-exchange")

        # Verify
        mock_channel.exchange_declare.assert_called_once_with(
            exchange="test-exchange",
            exchange_type=ExchangeType.topic.value,
            durable=True
        )
        publish_call = mock_channel.basic_publish.call_args
        assert publish_call[1]['exchange'] == "test-exchange"

    @patch('common.tasks.send_message.establish_connection')
    def test_send_message_without_exchange(self, mock_establish_connection, mock_config):
        """Test sending message without custom exchange (default)."""
        # Setup
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_connection.return_value = mock_connection

        sender = MessageSender()
        test_data = {"event": "TEST_EVENT"}

        # Execute
        sender.send_message("test-queue", test_data, exchange_name=None)

        # Verify
        mock_channel.exchange_declare.assert_not_called()
        publish_call = mock_channel.basic_publish.call_args
        assert publish_call[1]['exchange'] == ""

    @patch('common.tasks.send_message.establish_connection')
    def test_send_message_default_properties(self, mock_establish_connection, mock_config):
        """Test sending message with default properties."""
        # Setup
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_connection.return_value = mock_connection

        sender = MessageSender()
        test_data = {"event": "TEST_EVENT"}

        # Execute
        sender.send_message("test-queue", test_data)

        # Verify - properties should be set with delivery_mode=2
        publish_call = mock_channel.basic_publish.call_args
        properties = publish_call[1]['properties']
        assert properties.delivery_mode == 2

    @patch('common.tasks.send_message.establish_connection')
    def test_send_message_with_complex_data(self, mock_establish_connection, mock_config):
        """Test sending message with complex data structure."""
        # Setup
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=False)
        mock_establish_connection.return_value = mock_connection

        sender = MessageSender()
        test_data = {
            "event": "COMPLEX_EVENT",
            "data": {
                "user_id": "123",
                "items": [1, 2, 3],
                "metadata": {"key": "value"}
            }
        }

        # Execute
        sender.send_message("test-queue", test_data)

        # Verify
        publish_call = mock_channel.basic_publish.call_args
        decoded_body = json.loads(publish_call[1]['body'].decode())
        assert decoded_body == test_data
