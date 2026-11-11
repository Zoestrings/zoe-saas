"""Participation Engine determining whether Zoe should respond to a message."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import sqlite3
from typing import Any, List, Optional, Union

from zoe.clock.clock import format_timestamp, now, parse_timestamp
from zoe.conversation.classifier import ClassificationResult
from zoe.conversation.intent import (
    PROJECT_QUESTION_KEYWORDS,
    IntentResult,
    detect_contract_address,
    detect_intent,
    is_tagging_other_human,
)
from zoe.telegram.normalizer import NormalizedMessage
from zoe.utils.logging import get_logger

logger = get_logger("zoe.participation.decision")


@dataclass(frozen=True)
class ParticipationDecision:
    decision: str  # 'respond', 'remain_silent', 'escalate', 'ignore'
    should_respond: bool
    reason: str
    cooldown_remaining_seconds: float = 0.0


FOLLOW_UP_REACTIONS_PATTERN = re.compile(
    r"^\s*(?:really|for\s+real|are\s+you\s+sure|fr|wait\s+really|thanks|thank\s+you|ty|thx|wow|nice|awesome|cool)\??\s*$",
    re.IGNORECASE,
)


def get_bot_handles(project_id: Optional[str] = None, bot_name: str = "zoe") -> tuple:
    p_id = (project_id or "").lower().strip()
    b_name = (bot_name or "zoe").lower().strip()

    if p_id == "onelove" or "onelove" in b_name:
        self_names = {
            "onelove", "@onelove", "one love", "onelovemanager_bot", "@onelovemanager_bot",
            "captain robbie", "robbie", "captain", "$onelove"
        }
        other_bot_handles = {
            "zoecommunity_bot", "@zoecommunity_bot", "zoetest123_bot", "@zoetest123_bot",
            "zoesbot", "@zoesbot"
        }
    else:
        self_names = {
            "zoe", "@zoe", "zoecommunity_bot", "@zoecommunity_bot", "zoetest123_bot", "@zoetest123_bot",
            "zoesbot", "@zoesbot", "hummingbird", "fly", "$fly"
        }
        other_bot_handles = {
            "onelovemanager_bot", "@onelovemanager_bot"
        }
    return self_names, other_bot_handles


def is_other_bot_addressed(text: str, project_id: Optional[str] = None, bot_name: str = "zoe") -> bool:
    """Detect if the message explicitly addresses another project's bot handle in a shared group."""
    if not text:
        return False
    _, other_bot_handles = get_bot_handles(project_id, bot_name)
    for handle in other_bot_handles:
        clean = handle.lstrip("@").lower()
        pattern = rf"(?:^|\b)(?:@{re.escape(clean)}|{re.escape(clean)})\b"
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _is_bot_addressed(
    text: str,
    bot_name: str = "zoe",
    extra_names: Optional[List[str]] = None,
    project_id: Optional[str] = None,
) -> bool:
    if not text:
        return False

    self_names, other_names = get_bot_handles(project_id, bot_name)

    # If the message explicitly mentions the OTHER bot and NOT our bot, we are NOT addressed
    if is_other_bot_addressed(text, project_id, bot_name):
        return False

    b_lower = (bot_name or "zoe").lower().strip()
    b_compact = b_lower.replace(" ", "").replace("_", "")
    all_names = set(self_names)
    clean = b_lower.lstrip("@")
    all_names.add(clean)
    all_names.add(b_compact)
    for part in clean.split():
        if len(part) > 2 and part not in ("bot", "the", "one"):
            all_names.add(part)
    if extra_names:
        for en in extra_names:
            if en:
                all_names.add(en.lower().lstrip("@"))

    for name in all_names:
        clean_name = name.lstrip("@").lower()
        pattern = rf"(?:^|\b)(?:@{re.escape(clean_name)}|{re.escape(clean_name)})\b"
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def should_respond(
    message: NormalizedMessage,
    classification: ClassificationResult,
    recent_zoe_messages: Optional[List[str]] = None,
    last_response_time: Optional[Union[str, datetime]] = None,
    current_time: Optional[datetime] = None,
    db_conn: Optional[sqlite3.Connection] = None,
    rate_limit_seconds: float = 20.0,
    bot_name: str = "zoe",
    respond_to_casual: bool = False,
    intent: Optional[Union[str, IntentResult]] = None,
    llm_client: Optional[Any] = None,
) -> ParticipationDecision:
    """Evaluate whether to respond based on classification, intent, mentions, and group rate limits.

    Always records the decision in participation_log if db_conn is provided.
    """
    curr_dt = current_time if current_time is not None else now()

    # 1. Cooldown / Rate Limit Check (Strictly scoped per project_id and group_id)
    if last_response_time is None and db_conn is not None:
        try:
            cur = db_conn.cursor()
            cur.execute(
                """
                SELECT MAX(created_at) FROM participation_log
                WHERE project_id = ? AND group_id = ? AND decision = 'respond'
                """,
                (message.project_id, message.group_id),
            )
            row = cur.fetchone()
            if row and row[0]:
                last_response_time = row[0]
        except Exception:
            pass

    cooldown_remaining = 0.0
    elapsed = 999999.0
    if last_response_time is not None:
        last_dt = (
            parse_timestamp(last_response_time)
            if isinstance(last_response_time, str)
            else last_response_time
        )
        elapsed = (curr_dt - last_dt).total_seconds()
        if 0 < elapsed < rate_limit_seconds:
            cooldown_remaining = rate_limit_seconds - elapsed

    is_private_chat = not str(message.group_id).startswith("-")
    other_bot_addressed = not is_private_chat and is_other_bot_addressed(
        message.text, project_id=message.project_id, bot_name=bot_name
    )
    bot_addressed = is_private_chat or _is_bot_addressed(
        message.text, bot_name, project_id=message.project_id
    )
    is_reply_to_zoe = bool(
        message.reply_to_message_id is not None
        and recent_zoe_messages
        and str(message.reply_to_message_id) in [str(m) for m in recent_zoe_messages]
    )
    if not bot_addressed and is_reply_to_zoe:
        bot_addressed = True

    is_follow_up = bool(
        classification.reason == "follow_up_confirmation"
        or bool(FOLLOW_UP_REACTIONS_PATTERN.search(message.text))
    )
    is_continuous_flow = is_reply_to_zoe or is_follow_up

    # Detect intent
    if intent is None:
        detected = detect_intent(message.text, llm_client=llm_client)
        intent_str = detected.intent
    elif isinstance(intent, IntentResult):
        intent_str = intent.intent
    else:
        intent_str = str(intent)

    # 2. Decision Logic
    decision_str = "remain_silent"
    reason_code = "default_silent"
    do_respond = False

    cat = classification.category
    has_price_query = bool(re.search(r"\b(?:price|chart|liquidity)\b", message.text, re.IGNORECASE))

    is_command = message.text.strip().startswith("/")

    if other_bot_addressed:
        # Message was addressed to another project's bot in a shared group
        decision_str = "remain_silent"
        reason_code = "other_bot_addressed"
        do_respond = False

    elif is_command:
        # Explicit bot slash command (/ca, /price, /help, /ask, /start)
        decision_str = "respond"
        reason_code = "command_addressed"
        do_respond = True

    elif cat == "spam":
        decision_str = "ignore"
        reason_code = "spam_filtered"
        do_respond = False

    elif cat == "escalation_trigger":
        decision_str = "escalate"
        reason_code = classification.reason or "escalation_requested"
        do_respond = False

    elif cooldown_remaining > 0 and not is_private_chat and not bot_addressed:
        # Strict Global Lock: Zoe cannot send another unprompted message within rate_limit_seconds (20s) in groups.
        # Direct mentions/tags (bot_addressed) bypass group cooldown so user questions are never ignored.
        decision_str = "remain_silent"
        reason_code = "rate_limit_cooldown"
        do_respond = False

    elif intent_str == "casual_chat":
        # Zoe must remain completely silent during casual chat if tagging another human,
        # or unless her exact bot username is tagged, someone replies directly to her message,
        # or respond_to_casual is explicitly enabled for general greetings (without human tags).
        tagged_human = is_tagging_other_human(message.text, [bot_name])
        if bot_addressed or is_reply_to_zoe:
            decision_str = "respond"
            reason_code = "general_chat_addressed" if cat == "irrelevant" else "casual_addressed"
            do_respond = True
        elif not tagged_human and respond_to_casual and cooldown_remaining == 0:
            decision_str = "respond"
            reason_code = "casual_answered"
            do_respond = True
        else:
            decision_str = "remain_silent"
            reason_code = "casual_unaddressed"
            do_respond = False

    elif has_price_query:
        # Strict Price Routing: Respond and route to DexScreener
        decision_str = "respond"
        reason_code = "strict_price_routing"
        do_respond = True

    elif is_continuous_flow:
        # Ongoing conversational flow when cooldown has elapsed
        decision_str = "respond"
        do_respond = True
        if cat == "casual":
            reason_code = "casual_addressed" if is_reply_to_zoe else "casual_answered"
        elif cat == "direct_question":
            reason_code = "follow_up_answered" if is_follow_up else "direct_question_answered"
        else:
            reason_code = "continuous_flow_answered"

    elif intent_str == "crypto_intelligence" or bool(detect_contract_address(message.text)):
        # Contract address pasted in chat - on-demand crypto intelligence responds
        decision_str = "respond"
        reason_code = "ca_detected"
        do_respond = True

    elif bot_addressed:
        # Directly addressed or tagged
        decision_str = "respond"
        if cat == "casual":
            reason_code = "casual_addressed"
        elif cat == "direct_question":
            reason_code = "direct_question_answered"
        else:
            reason_code = "general_chat_addressed"
        do_respond = True

    elif intent_str in ("project_question", "project_misinformation"):
        # Autonomous Participation Engine: Respond immediately without being tagged
        decision_str = "respond"
        if intent_str == "project_misinformation":
            reason_code = "autonomous_project_intervention"
        elif cat == "direct_question":
            reason_code = "direct_question_answered"
        else:
            reason_code = "autonomous_question_answered"
        do_respond = True

    elif intent_str == "members_talking":
        # In private chat, there are no other members: user is talking directly to the bot
        if is_private_chat:
            decision_str = "respond"
            reason_code = "private_chat_direct"
            do_respond = True
        else:
            has_project_kw = any(pat.search(message.text) for pat in PROJECT_QUESTION_KEYWORDS)
            if has_project_kw and elapsed > 30.0:
                decision_str = "respond"
                reason_code = "autonomous_members_project_intervention"
                do_respond = True
            else:
                decision_str = "remain_silent"
                reason_code = "members_talking_silent"
                do_respond = False

    elif cat == "direct_question":
        decision_str = "respond"
        reason_code = "direct_question_answered"
        do_respond = True

    elif cat == "project_discussion":
        decision_str = "respond"
        reason_code = "project_discussion_answered"
        do_respond = True

    elif is_private_chat and cat != "spam":
        decision_str = "respond"
        reason_code = "private_chat_direct"
        do_respond = True

    elif cat == "irrelevant":
        decision_str = "remain_silent"
        reason_code = "topic_irrelevant"
        do_respond = False

    else:
        decision_str = "remain_silent"
        reason_code = "default_silent"
        do_respond = False

    decision = ParticipationDecision(
        decision=decision_str,
        should_respond=do_respond,
        reason=reason_code,
        cooldown_remaining_seconds=max(0.0, cooldown_remaining),
    )

    # 3. Log decision into participation_log if db connection is provided
    if db_conn is not None:
        try:
            created_str = format_timestamp(curr_dt)
            db_conn.execute(
                """
                INSERT INTO participation_log (
                    project_id, group_id, telegram_message_id, decision, reason_code, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.project_id,
                    message.group_id,
                    message.telegram_message_id,
                    decision.decision,
                    decision.reason,
                    created_str,
                ),
            )
            db_conn.commit()
        except Exception as e:
            logger.error("Failed to write to participation_log: %s", str(e))

    return decision

