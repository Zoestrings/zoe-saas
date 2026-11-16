"""Telegram event handlers for Autonomous Group Moderation & New Member Welcoming.

Handles ChatMemberUpdated events and new_chat_members service messages.
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
from zoe.conversation.prompt_builder import get_project_display_name, get_project_name
from zoe.telegram.adapter import TelegramAdapter
from zoe.utils.logging import get_logger

logger = get_logger("zoe.telegram.handlers")


def build_welcome_message(name: str, project_name: str) -> str:
    """Build the official welcome greeting for new community members."""
    clean_name = name.strip() if name and name.strip() else "there"
    clean_proj = project_name.strip() if project_name and project_name.strip() else "the project"
    return (
        f"Welcome to the crew, {clean_name}! "
        f"I'm Zoe, the AI Community Manager for {clean_proj}. "
        f"Ask me anything about the project or type /help to see my commands."
    )


def extract_new_members_from_update(update: Union[Dict[str, Any], Any]) -> List[Dict[str, Any]]:
    """Extract new members joining from either dict update or PTB Update object."""
    new_users: List[Dict[str, Any]] = []

    # 1. Dictionary representation (from PollingLoop get_updates)
    if isinstance(update, dict):
        # A. ChatMemberUpdated event ("chat_member")
        if "chat_member" in update:
            cm = update["chat_member"]
            old_status = str(cm.get("old_chat_member", {}).get("status", "")).lower()
            new_status = str(cm.get("new_chat_member", {}).get("status", "")).lower()
            chat_id = str(cm.get("chat", {}).get("id", ""))
            user = cm.get("new_chat_member", {}).get("user") or cm.get("from", {})

            # Transition from non-member (left, kicked, restricted) to active member
            if old_status in {"left", "kicked", "restricted"} and new_status in {"member", "administrator", "creator"}:
                if not user.get("is_bot"):
                    new_users.append({
                        "chat_id": chat_id,
                        "user_id": user.get("id"),
                        "first_name": user.get("first_name") or user.get("username") or "there",
                        "username": user.get("username"),
                    })

        # B. Service message ("new_chat_members")
        msg = update.get("message")
        if isinstance(msg, dict) and "new_chat_members" in msg:
            chat_id = str(msg.get("chat", {}).get("id", ""))
            for u in msg.get("new_chat_members", []):
                if not u.get("is_bot"):
                    new_users.append({
                        "chat_id": chat_id,
                        "user_id": u.get("id"),
                        "first_name": u.get("first_name") or u.get("username") or "there",
                        "username": u.get("username"),
                    })

    # 2. PTB Update object
    elif hasattr(update, "chat_member") and update.chat_member:
        cm = update.chat_member
        old_status = str(getattr(cm.old_chat_member, "status", "")).lower()
        new_status = str(getattr(cm.new_chat_member, "status", "")).lower()
        chat_id = str(getattr(cm.chat, "id", ""))
        user = getattr(cm.new_chat_member, "user", None) or getattr(cm, "from_user", None)

        if old_status in {"left", "kicked", "restricted", "chatmemberstatus.left"} and new_status in {
            "member", "administrator", "creator", "chatmemberstatus.member", "chatmemberstatus.administrator"
        }:
            if user and not getattr(user, "is_bot", False):
                new_users.append({
                    "chat_id": chat_id,
                    "user_id": getattr(user, "id", None),
                    "first_name": getattr(user, "first_name", None) or getattr(user, "username", None) or "there",
                    "username": getattr(user, "username", None),
                })

    elif hasattr(update, "message") and update.message and getattr(update.message, "new_chat_members", None):
        chat_id = str(getattr(update.message.chat, "id", ""))
        for u in update.message.new_chat_members:
            if not getattr(u, "is_bot", False):
                new_users.append({
                    "chat_id": chat_id,
                    "user_id": getattr(u, "id", None),
                    "first_name": getattr(u, "first_name", None) or getattr(u, "username", None) or "there",
                    "username": getattr(u, "username", None),
                })

    return new_users


async def handle_chat_member_updated(
    update: Union[Dict[str, Any], Any],
    adapter: Any,
    project_id: str = "zoe",
    configured_group_id: Optional[str] = None,
) -> List[str]:
    """Handle new members joining the group by posting a customized welcome message.

    Returns the list of welcome messages successfully dispatched.
    """
    new_members = extract_new_members_from_update(update)
    if not new_members:
        return []

    # Resolve project display name
    proj_display = (
        get_project_display_name(project_id)
        or get_project_name(project_id)
        or "the project"
    )

    dispatched_messages: List[str] = []
    for member in new_members:
        chat_id = member.get("chat_id")
        if not chat_id:
            continue

        welcome_text = build_welcome_message(
            name=member.get("first_name", "there"),
            project_name=proj_display,
        )

        try:
            logger.info("Welcoming new member '%s' (ID %s) to chat %s...", member.get("first_name"), member.get("user_id"), chat_id)
            if hasattr(adapter, "send_message"):
                fn = adapter.send_message
                if asyncio.iscoroutinefunction(fn):
                    await fn(chat_id=chat_id, text=welcome_text)
                else:
                    fn(chat_id=chat_id, text=welcome_text)
            dispatched_messages.append(welcome_text)
        except Exception as exc:
            logger.warning("Could not dispatch welcome message in chat %s: %s (Check bot send permissions)", chat_id, exc)

    return dispatched_messages


def register_moderation_handlers(application: Any, project_id: str = "zoe") -> None:
    """Register ChatMemberUpdated and new_chat_members handlers with python-telegram-bot Application."""
    try:
        from telegram.ext import ChatMemberHandler, MessageHandler, filters

        async def _chat_member_cb(update: Any, context: Any) -> None:
            await handle_chat_member_updated(update, adapter=context.bot, project_id=project_id)

        async def _service_msg_cb(update: Any, context: Any) -> None:
            await handle_chat_member_updated(update, adapter=context.bot, project_id=project_id)

        application.add_handler(ChatMemberHandler(_chat_member_cb, ChatMemberHandler.CHAT_MEMBER))
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, _service_msg_cb))
        logger.info("Registered ChatMemberUpdated moderation handlers for project '%s'.", project_id)
    except Exception as exc:
        logger.warning("Failed to register PTB application moderation handlers: %s", exc)
