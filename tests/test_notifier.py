"""Tests para el módulo de notificaciones Telegram."""
import pytest
from unittest.mock import MagicMock, patch, call

from notifier import TelegramNotifier


class MockConfig:
    telegram_bot_token = 'test_token_123'
    telegram_chat_id = '987654321'
    notify_on_success = True


class TestTelegramNotifier:
    def test_send_success_returns_true(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.raise_for_status.return_value = None
            assert notifier.send("Test") is True

    def test_send_posts_to_correct_url(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.raise_for_status.return_value = None
            notifier.send("Test")
            url = mock_post.call_args[0][0]
            assert 'test_token_123' in url
            assert 'sendMessage' in url

    def test_send_payload_contains_chat_id_and_text(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.raise_for_status.return_value = None
            notifier.send("Hello world")
            payload = mock_post.call_args[1]['json']
            assert payload['chat_id'] == '987654321'
            assert payload['text'] == 'Hello world'

    def test_send_uses_markdown_parse_mode(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.raise_for_status.return_value = None
            notifier.send("Test")
            payload = mock_post.call_args[1]['json']
            assert payload['parse_mode'] == 'Markdown'

    def test_send_no_token_returns_false(self):
        config = MockConfig()
        config.telegram_bot_token = ''
        assert TelegramNotifier(config).send("Test") is False

    def test_send_no_chat_id_returns_false(self):
        config = MockConfig()
        config.telegram_chat_id = ''
        assert TelegramNotifier(config).send("Test") is False

    def test_send_both_empty_returns_false(self):
        config = MockConfig()
        config.telegram_bot_token = ''
        config.telegram_chat_id = ''
        assert TelegramNotifier(config).send("Test") is False

    def test_send_connection_error_returns_false(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection refused")
            result = notifier.send("Test", retries=0)
            assert result is False

    def test_send_http_error_returns_false(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            resp = MagicMock()
            resp.raise_for_status.side_effect = Exception("HTTP 401")
            mock_post.return_value = resp
            assert notifier.send("Test", retries=0) is False

    def test_send_retries_on_failure(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post, patch('time.sleep'):
            mock_post.side_effect = Exception("flaky network")
            notifier.send("Test", retries=2)
            assert mock_post.call_count == 3

    def test_send_succeeds_on_second_attempt(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post, patch('time.sleep'):
            fail = MagicMock(side_effect=Exception("flaky"))
            success = MagicMock()
            success.raise_for_status.return_value = None
            mock_post.side_effect = [Exception("flaky"), success]
            result = notifier.send("Test", retries=2)
            assert result is True

    def test_send_zero_retries_calls_once(self):
        notifier = TelegramNotifier(MockConfig())
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("error")
            notifier.send("Test", retries=0)
            assert mock_post.call_count == 1
