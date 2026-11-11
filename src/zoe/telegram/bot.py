"""Telegram bot lifecycle and command registration module."""

from typing import Any
from zoe.telegram.adapter import TelegramAdapter
from zoe.utils.logging import get_logger

logger = get_logger("zoe.telegram.bot")


async def init_bot(adapter: TelegramAdapter, bot_name: str = "Zoe") -> bool:
    """Initialize bot adapter and register command menu with Telegram."""
    try:
        logger.info("Initializing bot and registering official command menu for %s...", bot_name)
        success = await adapter.set_bot_commands(bot_name=bot_name)
        if success:
            logger.info("Bot command menu registered successfully for %s.", bot_name)
        return success
    except Exception as exc:
        logger.error("Failed to register bot commands on startup for %s: %s", bot_name, exc)
        return False

