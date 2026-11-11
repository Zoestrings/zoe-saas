import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
import uuid

from zoe.clock.clock import format_timestamp
from zoe.utils.errors import BotRemovedAlert, ChatMigrationAlert
from zoe.utils.logging import get_logger

logger = get_logger("zoe.telegram.normalizer")

# Media attributes that cause a message to be discarded per Spec §6.5
# Note: "voice" is now supported and transcribed via Whisper
MEDIA_FIELDS = {
    "photo",
    "video",
    "audio",
    "document",
    "sticker",
    "animation",
    "video_note",
    "contact",
    "location",
    "venue",
    "poll",
    "dice",
    "game",
}

FORWARD_FIELDS = {
    "forward_date",
    "forward_from",
    "forward_from_chat",
    "forward_from_message_id",
    "forward_signature",
    "forward_sender_name",
    "forward_origin",
}

_discard_counts: Dict[str, Dict[str, int]] = {}


def get_discard_counts(project_id: str) -> Dict[str, int]:
    """Return in-memory discard counts for a project."""
    return dict(_discard_counts.get(project_id, {}))


def record_discard(project_id: str, reason: str) -> None:
    """Increment the in-memory discard counter for a project."""
    if project_id not in _discard_counts:
        _discard_counts[project_id] = {}
    _discard_counts[project_id][reason] = _discard_counts[project_id].get(reason, 0) + 1


def compute_pseudonym(user_id: Union[int, str], hmac_key: str) -> str:
    """Compute HMAC-SHA256 pseudonym from raw Telegram user ID.

    The raw user ID never leaves the normalizer.
    """
    if not hmac_key:
        raise ValueError("hmac_key cannot be empty for pseudonym generation.")
    return hmac.new(
        hmac_key.encode("utf-8"),
        str(user_id).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def is_matching_group_id(chat_id: str, configured_group_id: Optional[str]) -> bool:
    """Return True if chat_id matches configured_group_id.
    
    Accepts:
    1. Empty/None/wildcard configured_group_id (accepts any group the bot is in).
    2. Exact string match (e.g. '-5214407126' == '-5214407126').
    3. Supergroup vs basic group prefix conversion (e.g. '-1005214407126' vs '-5214407126').
    """
    if not configured_group_id or not str(configured_group_id).strip() or str(configured_group_id).strip() in ("0", "None", "any", "*"):
        return True
    
    cid = str(chat_id).strip()
    cfg = str(configured_group_id).strip()
    if cid == cfg:
        return True
        
    digits_cid = cid.lstrip("-")
    if digits_cid.startswith("100"):
        digits_cid = digits_cid[3:]
    digits_cfg = cfg.lstrip("-")
    if digits_cfg.startswith("100"):
        digits_cfg = digits_cfg[3:]
        
    return digits_cid == digits_cfg


@dataclass(frozen=True)
class NormalizedMessage:
    project_id: str
    telegram_update_id: int
    group_id: str
    telegram_message_id: int
    pseudonymous_user_id: str
    text: str
    reply_to_message_id: Optional[int]
    is_forward: bool
    timestamp: str  # "YYYY-MM-DD HH:MM:SS" UTC
    is_voice: bool = False


def _download_and_transcribe_sync(
    voice_dict: Dict[str, Any],
    project_id: str,
    update_id: int,
    message_id: int,
    adapter: Optional[Any] = None,
    transcriber: Optional[Callable[[Path], str]] = None,
    whisper_client: Optional[Any] = None,
    tmp_dir: Union[str, Path] = "data/tmp",
) -> Optional[str]:
    """Download voice note to tmp_dir, transcribe using Whisper API, and clean up temp file."""
    if "transcription" in voice_dict and voice_dict["transcription"]:
        return str(voice_dict["transcription"]).strip()

    file_id = voice_dict.get("file_id")
    if not file_id:
        logger.warning("Voice object missing file_id: %s", voice_dict)
        return None

    dir_path = Path(tmp_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    temp_file = dir_path / f"voice_{project_id}_{update_id}_{message_id}_{uuid.uuid4().hex[:8]}.ogg"

    try:
        # Download
        if adapter is not None:
            if hasattr(adapter, "download_file_sync"):
                adapter.download_file_sync(file_id, temp_file)
            elif hasattr(adapter, "download_file"):
                fn = adapter.download_file
                if asyncio.iscoroutinefunction(fn):
                    # Run coroutine synchronously
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as pool:
                                pool.submit(lambda: asyncio.run(fn(file_id, temp_file))).result()
                        else:
                            loop.run_until_complete(fn(file_id, temp_file))
                    except Exception:
                        asyncio.run(fn(file_id, temp_file))
                else:
                    fn(file_id, temp_file)
        else:
            if not temp_file.exists():
                temp_file.write_bytes(b"mock voice data")

        # Transcribe
        if transcriber is not None:
            return transcriber(temp_file)
        else:
            from zoe.transcription.whisper import transcribe_audio_file
            return transcribe_audio_file(temp_file, client=whisper_client)
    except Exception as exc:
        logger.error("Failed to transcribe voice note for update %d: %s", update_id, exc)
        return None
    finally:
        # Ensure temporary file deletion in try/finally
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning("Failed to delete temp audio file %s: %s", temp_file, e)


async def _download_and_transcribe_async(
    voice_dict: Dict[str, Any],
    project_id: str,
    update_id: int,
    message_id: int,
    adapter: Optional[Any] = None,
    transcriber: Optional[Callable[[Path], str]] = None,
    whisper_client: Optional[Any] = None,
    tmp_dir: Union[str, Path] = "data/tmp",
) -> Optional[str]:
    """Async download and transcribe voice note with try/finally cleanup."""
    if "transcription" in voice_dict and voice_dict["transcription"]:
        return str(voice_dict["transcription"]).strip()

    file_id = voice_dict.get("file_id")
    if not file_id:
        logger.warning("Voice object missing file_id: %s", voice_dict)
        return None

    dir_path = Path(tmp_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    temp_file = dir_path / f"voice_{project_id}_{update_id}_{message_id}_{uuid.uuid4().hex[:8]}.ogg"

    try:
        # Download
        if adapter is not None:
            if hasattr(adapter, "download_file"):
                fn = adapter.download_file
                if asyncio.iscoroutinefunction(fn):
                    await fn(file_id, temp_file)
                else:
                    fn(file_id, temp_file)
            elif hasattr(adapter, "download_file_sync"):
                adapter.download_file_sync(file_id, temp_file)
        else:
            if not temp_file.exists():
                temp_file.write_bytes(b"mock voice data")

        # Transcribe
        if transcriber is not None:
            if asyncio.iscoroutinefunction(transcriber):
                return await transcriber(temp_file)
            return transcriber(temp_file)
        else:
            from zoe.transcription.whisper import transcribe_audio_file_async
            return await transcribe_audio_file_async(temp_file, client=whisper_client)
    except Exception as exc:
        logger.error("Failed to transcribe voice note for update %d: %s", update_id, exc)
        return None
    finally:
        # Ensure temporary file deletion in try/finally
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning("Failed to delete temp audio file %s: %s", temp_file, e)


def normalize_update(
    project_id: str,
    update: Dict[str, Any],
    configured_group_id: str,
    hmac_key: str,
    adapter: Optional[Any] = None,
    transcriber: Optional[Callable[[Path], str]] = None,
    whisper_client: Optional[Any] = None,
    tmp_dir: Union[str, Path] = "data/tmp",
) -> Optional[NormalizedMessage]:
    """Normalize a raw Telegram update dict into a NormalizedMessage or discard it per Spec §6.5.

    Supports both standard typed text and Telegram voice notes.
    Seals the raw Telegram user ID inside this function.
    """
    update_id = update.get("update_id", 0)

    # 1. Bot status updates (my_chat_member)
    if "my_chat_member" in update:
        mcm = update["my_chat_member"]
        new_status = mcm.get("new_chat_member", {}).get("status")
        if new_status in {"kicked", "left"}:
            record_discard(project_id, "bot_removed")
            logger.warning(
                f"Bot status updated in chat {mcm.get('chat', {}).get('id')}: status '{new_status}'"
            )
            return None
        record_discard(project_id, "my_chat_member")
        return None

    # 2. Edited messages
    if "edited_message" in update or "edited_channel_post" in update:
        record_discard(project_id, "edited_message")
        return None

    # 3. Channel posts
    if "channel_post" in update:
        record_discard(project_id, "channel_post")
        return None

    # 4. Standard message extraction
    message = update.get("message")
    if not isinstance(message, dict):
        record_discard(project_id, "non_message_update")
        return None

    # 5. Chat migration
    if "migrate_to_chat_id" in message:
        new_chat_id = message["migrate_to_chat_id"]
        record_discard(project_id, "chat_migration")
        raise ChatMigrationAlert(f"Chat migrated to {new_chat_id}; do not automatically follow.")

    # 6. Unconfigured chat (if a specific group_id is configured, enforce tenant isolation for groups while allowing direct DMs)
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    is_private_dm = not chat_id.startswith("-")
    if not is_private_dm and not is_matching_group_id(chat_id, configured_group_id):
        chat_hash = hashlib.sha256(chat_id.encode("utf-8")).hexdigest()[:12]
        logger.info(f"Discarding update from unconfigured chat {chat_id} (chat_hash={chat_hash}, configured_group_id={configured_group_id})")
        record_discard(project_id, "unconfigured_chat")
        return None

    # 7. Sender checks: anonymous-admin or bot
    sender = message.get("from")
    if sender is None:
        record_discard(project_id, "anonymous_admin")
        return None

    if sender.get("is_bot") is True:
        record_discard(project_id, "bot_message")
        return None

    # 8. Media checks (non-voice media discarded)
    if any(field in message for field in MEDIA_FIELDS):
        record_discard(project_id, "media_message")
        return None

    # 9. Dual-Input: Text extraction or Voice transcription
    text = message.get("text")
    is_voice = False
    if text is None and "voice" in message:
        is_voice = True
        msg_id_val = int(message.get("message_id", 0))
        text = _download_and_transcribe_sync(
            voice_dict=message["voice"],
            project_id=project_id,
            update_id=update_id,
            message_id=msg_id_val,
            adapter=adapter,
            transcriber=transcriber,
            whisper_client=whisper_client,
            tmp_dir=tmp_dir,
        )

    if text is None or not isinstance(text, str) or not text.strip():
        record_discard(project_id, "empty_or_non_text")
        return None

    # 10. Forward check
    is_forward = any(field in message for field in FORWARD_FIELDS)

    # 11. Reply-to check
    reply_to = message.get("reply_to_message")
    reply_to_message_id = (
        reply_to.get("message_id") if isinstance(reply_to, dict) else None
    )

    # 12. Timestamp normalization (UTC "YYYY-MM-DD HH:MM:SS")
    raw_date = message.get("date")
    if isinstance(raw_date, (int, float)):
        dt = datetime.fromtimestamp(raw_date, tz=timezone.utc)
        timestamp = format_timestamp(dt)
    elif isinstance(raw_date, str):
        timestamp = raw_date
    else:
        timestamp = format_timestamp(datetime.now(timezone.utc))

    # 13. HMAC pseudonymization (raw user ID is sealed here)
    raw_user_id = sender.get("id")
    if raw_user_id is None:
        record_discard(project_id, "missing_user_id")
        return None

    pseudonymous_user_id = compute_pseudonym(raw_user_id, hmac_key)

    return NormalizedMessage(
        project_id=project_id,
        telegram_update_id=update_id,
        group_id=chat_id,
        telegram_message_id=int(message["message_id"]),
        pseudonymous_user_id=pseudonymous_user_id,
        text=text,
        reply_to_message_id=reply_to_message_id,
        is_forward=is_forward,
        timestamp=timestamp,
        is_voice=is_voice,
    )


async def normalize_update_async(
    project_id: str,
    update: Dict[str, Any],
    configured_group_id: str,
    hmac_key: str,
    adapter: Optional[Any] = None,
    transcriber: Optional[Callable[[Path], str]] = None,
    whisper_client: Optional[Any] = None,
    tmp_dir: Union[str, Path] = "data/tmp",
) -> Optional[NormalizedMessage]:
    """Async variant of normalize_update with non-blocking voice download and transcription."""
    update_id = update.get("update_id", 0)

    # 1. Bot status updates (my_chat_member)
    if "my_chat_member" in update:
        mcm = update["my_chat_member"]
        new_status = mcm.get("new_chat_member", {}).get("status")
        if new_status in {"kicked", "left"}:
            record_discard(project_id, "bot_removed")
            logger.warning(
                f"Bot status updated in chat {mcm.get('chat', {}).get('id')}: status '{new_status}'"
            )
            return None
        record_discard(project_id, "my_chat_member")
        return None

    # 2. Edited messages
    if "edited_message" in update or "edited_channel_post" in update:
        record_discard(project_id, "edited_message")
        return None

    # 3. Channel posts
    if "channel_post" in update:
        record_discard(project_id, "channel_post")
        return None

    # 4. Standard message extraction
    message = update.get("message")
    if not isinstance(message, dict):
        record_discard(project_id, "non_message_update")
        return None

    # 5. Chat migration
    if "migrate_to_chat_id" in message:
        new_chat_id = message["migrate_to_chat_id"]
        record_discard(project_id, "chat_migration")
        raise ChatMigrationAlert(f"Chat migrated to {new_chat_id}; do not automatically follow.")

    # 6. Unconfigured chat (if a specific group_id is configured, enforce tenant isolation for groups while allowing direct DMs)
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    is_private_dm = not chat_id.startswith("-")
    if not is_private_dm and not is_matching_group_id(chat_id, configured_group_id):
        chat_hash = hashlib.sha256(chat_id.encode("utf-8")).hexdigest()[:12]
        logger.info(f"Discarding update from unconfigured chat {chat_id} (chat_hash={chat_hash}, configured_group_id={configured_group_id})")
        record_discard(project_id, "unconfigured_chat")
        return None

    # 7. Sender checks: anonymous-admin or bot
    sender = message.get("from")
    if sender is None:
        record_discard(project_id, "anonymous_admin")
        return None

    if sender.get("is_bot") is True:
        record_discard(project_id, "bot_message")
        return None

    # 8. Media checks (non-voice media discarded)
    if any(field in message for field in MEDIA_FIELDS):
        record_discard(project_id, "media_message")
        return None

    # 9. Dual-Input: Text extraction or Voice transcription
    text = message.get("text")
    is_voice = False
    if text is None and "voice" in message:
        is_voice = True
        msg_id_val = int(message.get("message_id", 0))
        text = await _download_and_transcribe_async(
            voice_dict=message["voice"],
            project_id=project_id,
            update_id=update_id,
            message_id=msg_id_val,
            adapter=adapter,
            transcriber=transcriber,
            whisper_client=whisper_client,
            tmp_dir=tmp_dir,
        )

    if text is None or not isinstance(text, str) or not text.strip():
        record_discard(project_id, "empty_or_non_text")
        return None

    # 10. Forward check
    is_forward = any(field in message for field in FORWARD_FIELDS)

    # 11. Reply-to check
    reply_to = message.get("reply_to_message")
    reply_to_message_id = (
        reply_to.get("message_id") if isinstance(reply_to, dict) else None
    )

    # 12. Timestamp normalization (UTC "YYYY-MM-DD HH:MM:SS")
    raw_date = message.get("date")
    if isinstance(raw_date, (int, float)):
        dt = datetime.fromtimestamp(raw_date, tz=timezone.utc)
        timestamp = format_timestamp(dt)
    elif isinstance(raw_date, str):
        timestamp = raw_date
    else:
        timestamp = format_timestamp(datetime.now(timezone.utc))

    # 13. HMAC pseudonymization (raw user ID is sealed here)
    raw_user_id = sender.get("id")
    if raw_user_id is None:
        record_discard(project_id, "missing_user_id")
        return None

    pseudonymous_user_id = compute_pseudonym(raw_user_id, hmac_key)

    return NormalizedMessage(
        project_id=project_id,
        telegram_update_id=update_id,
        group_id=chat_id,
        telegram_message_id=int(message["message_id"]),
        pseudonymous_user_id=pseudonymous_user_id,
        text=text,
        reply_to_message_id=reply_to_message_id,
        is_forward=is_forward,
        timestamp=timestamp,
        is_voice=is_voice,
    )

