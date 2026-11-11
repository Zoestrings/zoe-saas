from typing import Any, Dict, List, Optional


class MockTelegramAdapter:
    """Mock implementation of TelegramAdapter for unit and integration testing."""

    def __init__(self, updates: Optional[List[Dict[str, Any]]] = None) -> None:
        self.updates: List[Dict[str, Any]] = updates or []
        self.sent_messages: List[Dict[str, Any]] = []
        self.chat_members: Dict[tuple, Dict[str, Any]] = {}
        self.webhook_deleted: bool = False
        self.error_to_raise: Optional[Exception] = None
        self.get_updates_call_count: int = 0
        self.last_offset_requested: Optional[int] = None

    def add_update(self, update: Dict[str, Any]) -> None:
        self.updates.append(update)

    def add_updates(self, updates: List[Dict[str, Any]]) -> None:
        self.updates.extend(updates)

    def set_error(self, exc: Optional[Exception]) -> None:
        self.error_to_raise = exc

    def set_chat_member(self, chat_id: str, user_id: str, member_data: Dict[str, Any]) -> None:
        self.chat_members[(str(chat_id), str(user_id))] = member_data

    async def get_updates(self, offset: int, timeout: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        self.get_updates_call_count += 1
        self.last_offset_requested = offset

        if self.error_to_raise is not None:
            err = self.error_to_raise
            self.error_to_raise = None
            raise err

        # Return updates with update_id >= offset up to limit
        filtered = [u for u in self.updates if u.get("update_id", 0) >= offset]
        return filtered[:limit]

    async def delete_webhook(self) -> bool:
        self.webhook_deleted = True
        return True

    async def set_bot_commands(self, bot_name: str = "Zoe") -> bool:
        self.bot_commands_set = True
        self.bot_name = bot_name
        return True

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_to_message_id: Optional[int] = None,
        inline_keyboard: Optional[List[List[Dict[str, str]]]] = None,
    ) -> Dict[str, Any]:
        msg: Dict[str, Any] = {
            "message_id": len(self.sent_messages) + 1,
            "chat": {"id": chat_id},
            "text": text,
        }
        if reply_to_message_id is not None:
            msg["reply_to_message"] = {"message_id": reply_to_message_id}
        if inline_keyboard is not None:
            msg["inline_keyboard"] = inline_keyboard
        self.sent_messages.append(msg)
        return msg

    async def get_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        key = (str(chat_id), str(user_id))
        if key in self.chat_members:
            return self.chat_members[key]
        # Default mock admin member
        return {
            "status": "administrator",
            "user": {"id": int(user_id), "is_bot": False},
            "can_post_messages": True,
        }

