from datetime import datetime
from pathlib import Path
import asyncio
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from zoe.utils.logging import get_logger

logger = get_logger("zoe.telegram.adapter")


@runtime_checkable
class TelegramAdapter(Protocol):
    """Protocol defining the Telegram operations used by Zoe."""

    async def get_updates(self, offset: int, timeout: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch unconfirmed updates from Telegram starting at offset."""
        ...

    async def delete_webhook(self) -> bool:
        """Ensure no webhook is registered before polling begins."""
        ...

    async def set_bot_commands(self, bot_name: str = "Zoe") -> bool:
        """Register the official bot commands menu in Telegram."""
        ...

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_to_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send a message to a Telegram chat."""
        ...

    async def get_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Get membership details for a user in a chat."""
        ...

    async def download_file(self, file_id: str, destination_path: Union[str, Path]) -> Path:
        """Download a Telegram file by file_id to the destination path."""
        ...

    async def delete_message(self, chat_id: Union[str, int], message_id: int) -> bool:
        """Delete a message from a chat."""
        ...

    def delete_message_sync(self, chat_id: Union[str, int], message_id: int) -> bool:
        """Synchronously delete a message from a chat."""
        ...

    async def restrict_chat_member(
        self,
        chat_id: Union[str, int],
        user_id: Union[str, int],
        until_date: Optional[Union[int, datetime]] = None,
        permissions: Optional[Any] = None,
    ) -> bool:
        """Restrict/mute a chat member."""
        ...

    def restrict_chat_member_sync(
        self,
        chat_id: Union[str, int],
        user_id: Union[str, int],
        until_date: Optional[Union[int, datetime]] = None,
        permissions: Optional[Any] = None,
    ) -> bool:
        """Synchronously restrict/mute a chat member."""
        ...


class PTBTelegramAdapter:
    """Production Telegram adapter wrapping python-telegram-bot Bot class."""

    def __init__(self, bot_token: str, request_timeout: float = 45.0) -> None:
        from telegram import Bot
        from telegram.request import HTTPXRequest
        req = HTTPXRequest(
            read_timeout=request_timeout,
            write_timeout=request_timeout,
            connect_timeout=15.0,
            pool_timeout=15.0,
        )
        self._bot = Bot(token=bot_token, request=req)

    async def download_file(self, file_id: str, destination_path: Union[str, Path]) -> Path:
        """Download file from Telegram Bot API to destination path."""
        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tg_file = await self._bot.get_file(file_id)
        await tg_file.download_to_drive(custom_path=str(dest))
        return dest

    async def get_updates(self, offset: int, timeout: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        updates = await self._bot.get_updates(offset=offset, timeout=timeout, limit=limit)
        return [u.to_dict() for u in updates]

    async def delete_webhook(self) -> bool:
        return await self._bot.delete_webhook()

    async def set_bot_commands(self, bot_name: str = "Zoe") -> bool:
        """Register the official command menu with Telegram Bot API."""
        from telegram import BotCommand
        commands = [
            BotCommand("ask", f"Ask {bot_name} about trending tokens, a ticker, or a caller in this chat"),
            BotCommand("credits", f"Check your {bot_name} credit balance"),
            BotCommand("add_credits", f"Get a link to top up your {bot_name} credits"),
            BotCommand("ca", "Show this community's contract address"),
            BotCommand("setca", "Admins: save this community's contract address"),
            BotCommand("price", "Get live token price, market cap & liquidity"),
            BotCommand("links", "Official website, Twitter, Telegram & TikTok"),
            BotCommand("help", "Show all commands"),
        ]
        try:
            res = await self._bot.set_my_commands(commands)
            logger.info("Successfully registered Telegram bot command menu for %s.", bot_name)
            return bool(res)
        except Exception as exc:
            logger.error("Failed to register Telegram bot commands: %s", exc)
            return False

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_to_message_id: Optional[int] = None,
        inline_keyboard: Optional[List[List[Dict[str, str]]]] = None,
    ) -> Dict[str, Any]:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.error import Forbidden, RetryAfter, TelegramError
        try:
            kwargs: Dict[str, Any] = {}
            if reply_to_message_id is not None:
                # In private DMs (positive chat_id), avoid reply_to_message_id so Telegram
                # does not display a quote bubble with the user's initials ('JK')
                is_dm = not str(chat_id).startswith("-")
                if not is_dm:
                    kwargs["reply_to_message_id"] = int(reply_to_message_id)
                    kwargs["allow_sending_without_reply"] = True

            if inline_keyboard:
                kb_rows = []
                for row in inline_keyboard:
                    kb_row = []
                    for btn in row:
                        btn_text = btn.get("text", "")
                        btn_url = btn.get("url")
                        btn_cb = btn.get("callback_data")
                        if btn_url:
                            kb_row.append(InlineKeyboardButton(text=btn_text, url=btn_url))
                        elif btn_cb:
                            kb_row.append(InlineKeyboardButton(text=btn_text, callback_data=btn_cb))
                    if kb_row:
                        kb_rows.append(kb_row)
                if kb_rows:
                    kwargs["reply_markup"] = InlineKeyboardMarkup(kb_rows)

            msg = await self._bot.send_message(chat_id=chat_id, text=text, **kwargs)
            return msg.to_dict()
        except RetryAfter as e:
            logger.warning("Telegram 429 Rate limited. Retry after %s seconds.", e.retry_after)
            raise
        except Forbidden as e:
            logger.error(
                "Telegram 403 Forbidden: Bot was removed or lacks permission for chat %s: %s",
                chat_id,
                e,
            )
            raise
        except TelegramError as e:
            if "replied" in str(e).lower() and kwargs.get("reply_to_message_id"):
                logger.warning("Referenced message %s not found in chat %s; resending directly without reply.", kwargs.get("reply_to_message_id"), chat_id)
                retry_kwargs = {k: v for k, v in kwargs.items() if k != "reply_to_message_id"}
                try:
                    msg = await self._bot.send_message(chat_id=chat_id, text=text, **retry_kwargs)
                    return msg.to_dict()
                except Exception as retry_exc:
                    logger.error("Failed direct retry after replied message missing: %s", retry_exc)
            logger.error("Telegram error sending message to chat %s: %s", chat_id, e)
            raise

    async def get_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        member = await self._bot.get_chat_member(chat_id=chat_id, user_id=int(user_id))
        return member.to_dict()

    async def delete_message(self, chat_id: Union[str, int], message_id: int) -> bool:
        """Delete a message from a chat using the Telegram Bot API."""
        from telegram.error import TelegramError
        try:
            cid = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
            res = await self._bot.delete_message(chat_id=cid, message_id=int(message_id))
            logger.info("Deleted message %s from chat %s.", message_id, chat_id)
            return bool(res)
        except TelegramError as e:
            logger.warning(
                "Telegram error deleting message %s in chat %s: %s (Ensure bot has 'Delete Messages' admin permission)",
                message_id,
                chat_id,
                e,
            )
            return False
        except Exception as exc:
            logger.warning("Unexpected error deleting message %s in chat %s: %s", message_id, chat_id, exc)
            return False

    def delete_message_sync(self, chat_id: Union[str, int], message_id: int) -> bool:
        """Synchronously delete a message from a chat."""
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(self.delete_message(chat_id, message_id))).result()
        except Exception as exc:
            logger.warning("Error in delete_message_sync: %s", exc)
            return False

    async def restrict_chat_member(
        self,
        chat_id: Union[str, int],
        user_id: Union[str, int],
        until_date: Optional[Union[int, datetime]] = None,
        permissions: Optional[Any] = None,
    ) -> bool:
        """Mute / restrict a chat member from sending messages."""
        from telegram import ChatPermissions
        from telegram.error import TelegramError
        try:
            cid = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
            uid = int(user_id) if str(user_id).isdigit() else user_id
            perms = permissions or ChatPermissions(can_send_messages=False)
            res = await self._bot.restrict_chat_member(
                chat_id=cid,
                user_id=uid,
                permissions=perms,
                until_date=until_date,
            )
            logger.info("Restricted member %s in chat %s until %s.", user_id, chat_id, until_date)
            return bool(res)
        except TelegramError as e:
            logger.warning(
                "Telegram error restricting member %s in chat %s: %s (Ensure bot has 'Ban Users' admin permission)",
                user_id,
                chat_id,
                e,
            )
            return False
        except Exception as exc:
            logger.warning("Unexpected error restricting member %s in chat %s: %s", user_id, chat_id, exc)
            return False

    def restrict_chat_member_sync(
        self,
        chat_id: Union[str, int],
        user_id: Union[str, int],
        until_date: Optional[Union[int, datetime]] = None,
        permissions: Optional[Any] = None,
    ) -> bool:
        """Synchronously restrict/mute a chat member."""
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(self.restrict_chat_member(chat_id, user_id, until_date, permissions))).result()
        except Exception as exc:
            logger.warning("Error in restrict_chat_member_sync: %s", exc)
            return False
