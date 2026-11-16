"""Unit tests for Mega-Module 8: Autonomous Telegram Moderation.

Tests:
1. Inbound Scam & Phishing Detection (Safety Validator)
2. Repeat Spammer & Flooding Detection (Participation Decision)
3. Welcome New Members (ChatMemberUpdated Handler)
4. Pipeline Auto-Delete & Muting with Mock Adapter
"""

import asyncio
import time
from typing import Any, Dict
import pytest

from zoe.participation.decision import (
    check_is_flooding,
    check_is_repeat_scam,
    record_scam_strike,
    record_user_message_history,
    reset_moderation_tracking,
    should_respond,
)
from zoe.conversation.classifier import ClassificationResult
from zoe.safety.validator import validate_inbound_message
from zoe.telegram.handlers import build_welcome_message, handle_chat_member_updated
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import (
    delete_telegram_message_safe,
    process_message,
    restrict_telegram_member_safe,
)


@pytest.fixture(autouse=True)
def clean_moderation_state():
    reset_moderation_tracking()
    yield
    reset_moderation_tracking()


def test_validate_inbound_message_detects_scam_links():
    # Scam links & suspicious airdrops
    res1 = validate_inbound_message("Check out our new free airdrop: https://bit.ly/scam-airdrop")
    assert not res1.is_safe
    assert res1.is_scam
    assert res1.violation_type == "scam_link"

    res2 = validate_inbound_message("Claim free tokens now at https://fake-crypto-site.xyz/claim-tokens")
    assert not res2.is_safe
    assert res2.is_scam
    assert res2.violation_type == "scam_link"

    # Clean message
    res_clean = validate_inbound_message("What is the current token price on DexScreener?")
    assert res_clean.is_safe
    assert not res_clean.is_scam


def test_validate_inbound_message_detects_phishing_and_credentials():
    # Seed phrase & private key theft
    res1 = validate_inbound_message("Please provide your 12 words seed phrase to restore your wallet.")
    assert not res1.is_safe
    assert res1.is_scam
    assert res1.violation_type == "phishing"

    res2 = validate_inbound_message("Sync your wallet using our decentralized node resolver.")
    assert not res2.is_safe
    assert res2.is_scam
    assert res2.violation_type == "phishing"


def test_validate_inbound_message_detects_fake_admin_impersonation():
    # Fake admin / support asking to DM
    res1 = validate_inbound_message("Hello, I am official support. Please send me a DM to resolve your issue.")
    assert not res1.is_safe
    assert res1.is_scam
    assert res1.violation_type == "fake_admin"

    res2 = validate_inbound_message("Admin here, DM our team to claim your missing tokens.")
    assert not res2.is_safe
    assert res2.is_scam
    assert res2.violation_type == "fake_admin"


def test_flooding_detection():
    group_id = "-100999"
    user_id = "user_alpha"
    text = "Buy this gem immediately!"

    # 1st, 2nd, 3rd messages: not flooding yet
    for _ in range(3):
        record_user_message_history(group_id, user_id, text)
        assert not check_is_flooding(group_id, user_id, text, threshold=3)

    # 4th identical message: exceeds threshold of 3 -> flooding!
    record_user_message_history(group_id, user_id, text)
    assert check_is_flooding(group_id, user_id, text, threshold=3)


def test_repeat_scam_detection():
    group_id = "-100888"
    user_id = "scammer_1"

    # First strike
    strikes = record_scam_strike(group_id, user_id)
    assert strikes == 1
    assert not check_is_repeat_scam(group_id, user_id, window_seconds=300.0, max_strikes=2)

    # Second strike within 5 minutes -> repeat scammer!
    strikes = record_scam_strike(group_id, user_id)
    assert strikes == 2
    assert check_is_repeat_scam(group_id, user_id, window_seconds=300.0, max_strikes=2)


def test_welcome_new_members_chat_member_updated():
    adapter = MockTelegramAdapter()
    update_dict: Dict[str, Any] = {
        "update_id": 555,
        "chat_member": {
            "chat": {"id": -1001234567890, "title": "One Love Community"},
            "from": {"id": 111, "first_name": "Satoshi"},
            "old_chat_member": {"status": "left", "user": {"id": 111, "first_name": "Satoshi"}},
            "new_chat_member": {"status": "member", "user": {"id": 111, "first_name": "Satoshi", "is_bot": False}},
        },
    }

    dispatched = asyncio.run(
        handle_chat_member_updated(
            update_dict,
            adapter=adapter,
            project_id="onelove",
        )
    )

    assert len(dispatched) == 1
    assert "Welcome to the crew, Satoshi!" in dispatched[0]
    assert "One Love" in dispatched[0]
    assert len(adapter.sent_messages) == 1
    assert adapter.sent_messages[0]["chat"]["id"] == "-1001234567890"


def test_welcome_new_members_service_message():
    adapter = MockTelegramAdapter()
    update_dict: Dict[str, Any] = {
        "update_id": 556,
        "message": {
            "message_id": 777,
            "chat": {"id": -1001234567890},
            "new_chat_members": [
                {"id": 222, "first_name": "Alice", "is_bot": False},
                {"id": 333, "first_name": "SpamBot", "is_bot": True},  # Bot should be ignored
            ],
        },
    }

    dispatched = asyncio.run(
        handle_chat_member_updated(
            update_dict,
            adapter=adapter,
            project_id="zoe",
        )
    )

    assert len(dispatched) == 1  # Only Alice
    assert "Welcome to the crew, Alice!" in dispatched[0]
    assert len(adapter.sent_messages) == 1


def test_pipeline_scam_message_deleted_and_warning_posted(tmp_path):
    adapter = MockTelegramAdapter()
    inbox_row = {
        "id": 101,
        "project_id": "zoe",
        "telegram_update_id": 9991,
        "group_id": "-1001234567890",
        "telegram_message_id": 4321,
        "pseudonymous_user_id": "bad_actor_99",
        "raw_user_id": 987654321,
        "text": "Claim free 10,000 USDT airdrop here: https://bit.ly/drain-wallet",
        "reply_to_message_id": None,
        "is_forward": 0,
        "message_timestamp": "2026-11-16 12:00:00",
        "state": "message_persisted",
    }

    op_db = tmp_path / "op.db"
    kb_db = tmp_path / "kb.db"
    mem_db = tmp_path / "mem.db"

    from zoe.db.connections import open_operational_db, open_official_knowledge_db, open_community_memory_db
    from zoe.inbox.inbox_service import ensure_project_registered
    conn_op = open_operational_db(op_db)
    conn_kb = open_official_knowledge_db(kb_db)
    conn_mem = open_community_memory_db(mem_db)

    ensure_project_registered(conn_op, "zoe")

    # Insert initial inbox row
    conn_op.execute(
        """
        INSERT INTO inbox_messages (
            id, project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (101, 'zoe', 9991, '-1001234567890', 4321, 'bad_actor_99', 'Claim free 10,000 USDT airdrop here: https://bit.ly/drain-wallet', NULL, 0, '2026-11-16 12:00:00', 'message_persisted', '2026-11-16 12:00:00', '2026-11-16 12:00:00')
        """
    )
    conn_op.commit()

    db_conns = {"operational": conn_op, "knowledge": conn_kb, "memory": conn_mem}

    res = process_message(
        inbox_row=inbox_row,
        db_conns=db_conns,
        simulated=False,
        adapter=adapter,
    )

    # 1. Message should be marked responded
    assert res.responded
    assert "⚠️ I removed a suspicious message" in res.response_text

    # 2. Adapter should have recorded deleted message
    assert len(adapter.deleted_messages) == 1
    assert adapter.deleted_messages[0]["message_id"] == 4321
    assert adapter.deleted_messages[0]["chat_id"] == "-1001234567890"

    # Clean up
    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_pipeline_repeat_scammer_gets_muted(tmp_path):
    adapter = MockTelegramAdapter()
    group_id = "-1001234567890"
    user_pseudo = "persistent_scammer"
    raw_uid = 999888777

    # Prime first strike
    record_scam_strike(group_id, user_pseudo)

    inbox_row = {
        "id": 102,
        "project_id": "zoe",
        "telegram_update_id": 9992,
        "group_id": group_id,
        "telegram_message_id": 4322,
        "pseudonymous_user_id": user_pseudo,
        "raw_user_id": raw_uid,
        "text": "Second scam attempt: Connect your wallet at https://fake-drainer.xyz/claim-now",
        "reply_to_message_id": None,
        "is_forward": 0,
        "message_timestamp": "2026-11-16 12:02:00",
        "state": "message_persisted",
    }

    op_db = tmp_path / "op2.db"
    from zoe.db.connections import open_operational_db
    from zoe.inbox.inbox_service import ensure_project_registered
    conn_op = open_operational_db(op_db)
    ensure_project_registered(conn_op, "zoe")
    conn_op.execute(
        """
        INSERT INTO inbox_messages (
            id, project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (102, 'zoe', 9992, '-1001234567890', 4322, 'persistent_scammer', 'Second scam attempt', NULL, 0, '2026-11-16 12:02:00', 'message_persisted', '2026-11-16 12:02:00', '2026-11-16 12:02:00')
        """
    )
    conn_op.commit()

    db_conns = {"operational": conn_op}

    res = process_message(
        inbox_row=inbox_row,
        db_conns=db_conns,
        simulated=False,
        adapter=adapter,
    )

    # 1. Message deleted
    assert len(adapter.deleted_messages) == 1
    assert adapter.deleted_messages[0]["message_id"] == 4322

    # 2. User restricted (muted) for 1 hour
    assert len(adapter.restricted_members) == 1
    assert adapter.restricted_members[0]["user_id"] == raw_uid
    assert adapter.restricted_members[0]["chat_id"] == group_id

    conn_op.close()


def test_permission_error_gracefully_caught():
    """Adapter delete and restrict should not crash if Telegram returns error."""
    class ForbiddenAdapter:
        def delete_message_sync(self, chat_id, message_id):
            raise RuntimeError("Telegram 403 Forbidden: Not enough rights to delete messages")

        def restrict_chat_member_sync(self, chat_id, user_id, until_date=None):
            raise RuntimeError("Telegram 400 Bad Request: Not enough rights to restrict members")

    f_adapter = ForbiddenAdapter()

    # Calling safe wrappers must return False and NOT raise
    assert not delete_telegram_message_safe(f_adapter, "-100123", 444)
    assert not restrict_telegram_member_safe(f_adapter, "-100123", 555)
