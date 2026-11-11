"""Unit tests verifying multi-bot tenant addressing isolation and collision prevention."""

import pytest
from zoe.conversation.classifier import ClassificationResult
from zoe.participation.decision import should_respond, is_other_bot_addressed, _is_bot_addressed
from zoe.telegram.normalizer import NormalizedMessage


def create_msg(project_id: str, text: str, group_id: str = "-5214407126") -> NormalizedMessage:
    return NormalizedMessage(
        project_id=project_id,
        telegram_update_id=1,
        group_id=group_id,
        telegram_message_id=100,
        pseudonymous_user_id="user_123",
        text=text,
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 10:00:00",
    )


def test_onelove_mention_addressed_to_onelove_only():
    """When user mentions @OneLoveManager_bot, onelove responds and live_test remains silent."""
    text = "@OneLoveManager_bot hey"
    cls = ClassificationResult(category="casual", confidence=0.9, reason="casual")

    # live_test bot check
    msg_live = create_msg("live_test", text)
    dec_live = should_respond(msg_live, cls, bot_name="Zoe", respond_to_casual=True)
    assert dec_live.should_respond is False
    assert dec_live.decision == "remain_silent"
    assert dec_live.reason == "other_bot_addressed"

    # onelove bot check
    msg_love = create_msg("onelove", text)
    dec_love = should_respond(msg_love, cls, bot_name="Zoe", respond_to_casual=True)
    assert dec_love.should_respond is True
    assert dec_love.decision == "respond"


def test_zoe_mention_addressed_to_live_test_only():
    """When user mentions @zoecommunity_bot, live_test responds and onelove remains silent."""
    text = "@zoecommunity_bot hey"
    cls = ClassificationResult(category="casual", confidence=0.9, reason="casual")

    # onelove bot check
    msg_love = create_msg("onelove", text)
    dec_love = should_respond(msg_love, cls, bot_name="Zoe", respond_to_casual=True)
    assert dec_love.should_respond is False
    assert dec_love.decision == "remain_silent"
    assert dec_love.reason == "other_bot_addressed"

    # live_test bot check
    msg_live = create_msg("live_test", text)
    dec_live = should_respond(msg_live, cls, bot_name="Zoe", respond_to_casual=True)
    assert dec_live.should_respond is True
    assert dec_live.decision == "respond"


def test_cross_project_handle_isolation():
    """When user mentions @OneLoveManager_bot, live_test stays silent. When mentioning @zoecommunity_bot, onelove stays silent."""
    cls = ClassificationResult(category="direct_question", confidence=0.9, reason="price_query")

    # @OneLoveManager_bot price inquiry
    msg_love = create_msg("live_test", "@OneLoveManager_bot what is the price?")
    dec_live = should_respond(msg_love, cls, bot_name="Zoe")
    assert dec_live.should_respond is False
    assert dec_live.reason == "other_bot_addressed"

    # @zoecommunity_bot price inquiry
    msg_zoe = create_msg("onelove", "@zoecommunity_bot what is the price?")
    dec_love = should_respond(msg_zoe, cls, bot_name="Zoe")
    assert dec_love.should_respond is False
    assert dec_love.reason == "other_bot_addressed"


def test_dm_is_always_addressed():
    """In private chats (DMs), the bot always responds directly to the user."""
    cls = ClassificationResult(category="casual", confidence=0.9, reason="casual")
    msg_dm = create_msg("onelove", "why arent you responding on the group?", group_id="7136342824")

    dec_dm = should_respond(msg_dm, cls, bot_name="Zoe")
    assert dec_dm.should_respond is True
    assert dec_dm.decision == "respond"
