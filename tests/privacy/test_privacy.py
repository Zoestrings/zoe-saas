import asyncio
import io
import logging
from pathlib import Path
import pytest
import sqlite3

from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import ensure_project_registered, init_polling_state
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.telegram.polling_loop import PollingLoop
from zoe.utils.logging import SanitizingFormatter, get_logger

PROJECT_ID = "privacy_proj"
GROUP_ID = "-1001234567890"
HMAC_KEY = "privacy_test_secret_salt_key"
RAW_SENSITIVE_USER_ID = 8877665544


def setup_privacy_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "privacy_operational.db"
    conn = open_operational_db(db_path)
    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_operational.sql"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    ensure_project_registered(conn, PROJECT_ID, telegram_group_id=GROUP_ID)
    init_polling_state(conn, PROJECT_ID)
    return conn


@pytest.mark.automated
def test_db_contains_no_raw_telegram_id(tmp_path: Path) -> None:
    conn = setup_privacy_db(tmp_path)

    raw_update = {
        "update_id": 999,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": int(GROUP_ID)},
            "from": {"id": RAW_SENSITIVE_USER_ID, "is_bot": False, "first_name": "SecretUser"},
            "text": "Secret user message content",
        },
    }

    adapter = MockTelegramAdapter([raw_update])
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)
    asyncio.run(loop.step())

    target_str = str(RAW_SENSITIVE_USER_ID)

    # Full table scan of inbox_messages
    cur = conn.cursor()
    cur.execute("SELECT * FROM inbox_messages")
    for row in cur.fetchall():
        row_str = " ".join(str(val) for val in row if val is not None)
        assert target_str not in row_str, f"Found raw Telegram user ID in inbox_messages: {row}"

    # Full table scan of update_receipts
    cur.execute("SELECT * FROM update_receipts")
    for row in cur.fetchall():
        row_str = " ".join(str(val) for val in row if val is not None)
        assert target_str not in row_str, f"Found raw Telegram user ID in update_receipts: {row}"

    # Full table scan of polling_state
    cur.execute("SELECT * FROM polling_state")
    for row in cur.fetchall():
        row_str = " ".join(str(val) for val in row if val is not None)
        assert target_str not in row_str, f"Found raw Telegram user ID in polling_state: {row}"

    conn.close()


@pytest.mark.automated
def test_logs_contain_no_raw_telegram_id(tmp_path: Path) -> None:
    conn = setup_privacy_db(tmp_path)

    # Attach string stream handler with SanitizingFormatter to root and zoe loggers
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(SanitizingFormatter())

    logger = get_logger("zoe")
    logger.addHandler(handler)

    raw_update = {
        "update_id": 1000,
        "message": {
            "message_id": 2,
            "date": 1700000000,
            "chat": {"id": int(GROUP_ID)},
            "from": {"id": RAW_SENSITIVE_USER_ID, "is_bot": False, "first_name": "SecretUser"},
            "text": "Logging test message",
        },
    }

    adapter = MockTelegramAdapter([raw_update])
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    try:
        asyncio.run(loop.step())
        logged_output = log_stream.getvalue()
        target_str = str(RAW_SENSITIVE_USER_ID)
        assert target_str not in logged_output, f"Raw Telegram user ID appeared in logs: {logged_output}"
    finally:
        logger.removeHandler(handler)
        conn.close()

