from dataclasses import dataclass
from typing import Optional

from zoe.telegram.adapter import TelegramAdapter
from zoe.utils.logging import get_logger

logger = get_logger("zoe.telegram.moderator_verify")


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: Optional[str] = None


async def verify_moderator_channel(
    adapter: TelegramAdapter,
    group_id: str,
    moderator_user_id: str,
) -> VerificationResult:
    """Verify at the Telegram API level that the bot has membership and administrator privileges

    in the designated moderator channel. Does NOT send any preflight messages.
    """
    try:
        member = await adapter.get_chat_member(chat_id=group_id, user_id=moderator_user_id)
    except Exception as e:
        logger.error(f"Failed to query chat member status for {moderator_user_id} in {group_id}: {e}")
        return VerificationResult(ok=False, reason=f"API error querying chat member: {e}")

    status = member.get("status")
    if status not in {"administrator", "creator"}:
        return VerificationResult(
            ok=False,
            reason=f"Bot or moderator user does not have administrator privileges in channel (current status: '{status}').",
        )

    return VerificationResult(ok=True, reason="Administrator privileges confirmed.")

