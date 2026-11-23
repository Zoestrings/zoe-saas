"""Discord adapter for Zoe autonomous agent platform.

Enables cross-platform execution on Discord servers while preserving the unified
Zoe intelligence engine, RAG pipeline, scanner, and memory stores.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
import discord

from zoe.telegram.normalizer import NormalizedMessage, compute_pseudonym
from zoe.utils.logging import get_logger

logger = get_logger("zoe.discord.adapter")


class DiscordSentMessage:
    """Represents a successfully sent Discord message."""

    def __init__(self, message_id: int, channel_id: int):
        self.message_id = message_id
        self.channel_id = channel_id


class DiscordAdapter:
    """Adapter bridging Discord gateway events to Zoe NormalizedMessage format."""

    def __init__(
        self,
        bot_token: str,
        project_id: str,
        channel_id: Optional[Union[str, int]] = None,
        hmac_key: str = "default_hmac_key_32_characters_minimum",
        on_message_callback: Optional[Callable[[NormalizedMessage], Any]] = None,
    ) -> None:
        self.bot_token = bot_token.strip()
        self.project_id = project_id
        self.configured_channel_id = str(channel_id).strip() if channel_id else None
        self.hmac_key = hmac_key
        self.on_message_callback = on_message_callback

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True

        self.client = discord.Client(intents=intents)
        self._is_ready = asyncio.Event()
        self._bg_task: Optional[asyncio.Task] = None
        self._incoming_queue: asyncio.Queue[NormalizedMessage] = asyncio.Queue()

        self._setup_events()

    def _setup_events(self) -> None:
        @self.client.event
        async def on_ready():
            logger.info(
                "Discord bot connected as %s (ID: %s) for project %s",
                self.client.user,
                self.client.user.id if self.client.user else "unknown",
                self.project_id,
            )
            self._is_ready.set()

        @self.client.event
        async def on_message(message: discord.Message):
            # 1. Ignore own messages or messages from bots
            if not self.client.user or message.author.id == self.client.user.id:
                return
            if message.author.bot:
                return

            # 2. Check channel restriction if configured
            channel_str = str(message.channel.id)
            if self.configured_channel_id and self.configured_channel_id not in (
                "",
                "0",
                "None",
                "any",
                "*",
            ):
                if channel_str != self.configured_channel_id:
                    return

            # 3. Normalize into NormalizedMessage
            pseudo_id = compute_pseudonym(message.author.id, self.hmac_key)
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            reply_to = None
            if message.reference and message.reference.message_id:
                reply_to = int(message.reference.message_id)

            normalized = NormalizedMessage(
                project_id=self.project_id,
                telegram_update_id=int(message.id),
                group_id=channel_str,
                telegram_message_id=int(message.id),
                pseudonymous_user_id=pseudo_id,
                text=message.content or "",
                reply_to_message_id=reply_to,
                is_forward=False,
                timestamp=now_str,
                is_voice=False,
                raw_user_id=message.author.id,
                username=message.author.name,
                platform="discord",
            )

            await self._incoming_queue.put(normalized)

            if self.on_message_callback:
                try:
                    res = self.on_message_callback(normalized)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as cb_err:
                    logger.error("Error in Discord on_message_callback: %s", cb_err)

    async def start(self) -> None:
        """Start the Discord client in a background asyncio task."""
        if self._bg_task and not self._bg_task.done():
            return

        async def _run():
            try:
                await self.client.start(self.bot_token)
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.error("Discord client encountered an error: %s", exc)

        self._bg_task = asyncio.create_task(_run())
        try:
            await asyncio.wait_for(self._is_ready.wait(), timeout=15.0)
            logger.info("DiscordAdapter ready for project %s", self.project_id)
        except asyncio.TimeoutError:
            logger.warning("Discord client login timed out (15s); continuing in background...")

    async def stop(self) -> None:
        """Gracefully disconnect and stop the Discord adapter."""
        if not self.client.is_closed():
            await self.client.close()
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
        self._is_ready.clear()
        logger.info("DiscordAdapter stopped for project %s", self.project_id)

    async def get_next_message(self, timeout: float = 1.0) -> Optional[NormalizedMessage]:
        """Fetch next incoming message from the buffer queue."""
        try:
            return await asyncio.wait_for(self._incoming_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        reply_to_message_id: Optional[Union[str, int]] = None,
        inline_keyboard: Optional[Any] = None,
    ) -> DiscordSentMessage:
        """Send a message to a Discord channel, optionally replying to a message."""
        channel_id_int = int(chat_id)
        channel = self.client.get_channel(channel_id_int)
        if channel is None:
            channel = await self.client.fetch_channel(channel_id_int)

        # Discord 2000 character limit safeguard
        clean_text = text[:1990] if len(text) > 2000 else text

        reference = None
        if reply_to_message_id:
            try:
                reference = discord.MessageReference(
                    message_id=int(reply_to_message_id),
                    channel_id=channel_id_int,
                )
            except Exception:
                reference = None

        # Format buttons into Discord embeds or plain text links if provided
        sent = await channel.send(
            content=clean_text,
            reference=reference,
        )
        return DiscordSentMessage(message_id=sent.id, channel_id=channel.id)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

