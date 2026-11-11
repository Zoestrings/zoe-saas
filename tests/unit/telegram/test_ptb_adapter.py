import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from telegram.error import Forbidden, RetryAfter

from zoe.telegram.adapter import PTBTelegramAdapter


def test_ptb_adapter_handles_retry_after_429():
    with patch("telegram.Bot.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = RetryAfter(retry_after=42)
        adapter = PTBTelegramAdapter(bot_token="fake:token")

        with pytest.raises(RetryAfter) as exc_info:
            asyncio.run(adapter.send_message(chat_id="-100123", text="Test 429"))

        assert exc_info.value.retry_after == 42


def test_ptb_adapter_handles_forbidden_403():
    with patch("telegram.Bot.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Forbidden("Bot was kicked from the group")
        adapter = PTBTelegramAdapter(bot_token="fake:token")

        with pytest.raises(Forbidden) as exc_info:
            asyncio.run(adapter.send_message(chat_id="-100123", text="Test 403"))

        assert "kicked" in str(exc_info.value)
