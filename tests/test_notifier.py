"""Tests para el módulo de notificaciones Telegram."""
import pytest
from unittest.mock import MagicMock, patch

from notifier import TelegramNotifier


class MockConfig:
    telegram_bot_token = 'test_token_123'
    telegram_chat_id = '987654321'
    notify_on_success = True


def test_send_success():
    notifier = TelegramNotifier(MockConfig())
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        result = notifier.send("Test message")
        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['json']['chat_id'] == '987654321'
        assert call_kwargs['json']['text'] == 'Test message'


def test_send_no_token():
    config = MockConfig()
    config.telegram_bot_token = ''
    notifier = TelegramNotifier(config)
    result = notifier.send("Test message")
    assert result is False


def test_send_no_chat_id():
    config = MockConfig()
    config.telegram_chat_id = ''
    notifier = TelegramNotifier(config)
    result = notifier.send("Test message")
    assert result is False


def test_send_request_failure():
    notifier = TelegramNotifier(MockConfig())
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Connection error")
        result = notifier.send("Test message")
        assert result is False


def test_send_http_error():
    notifier = TelegramNotifier(MockConfig())
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 401")
        mock_post.return_value = mock_response
        result = notifier.send("Test message")
        assert result is False
