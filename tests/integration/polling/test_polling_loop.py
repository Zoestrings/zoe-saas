import asyncio
from pathlib import Path
import pytest
import sqlite3

from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import ensure_project_registered, init_polling_state
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.telegram.polling_loop import PollingLoop
from zoe.utils.errors import PollingGapAlert

PROJECT_ID = "integration_proj"
GROUP_ID = "-1001234567890"
HMAC_KEY = "integration_test_secret_key"


def setup_test_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test_operational.db"
    conn = open_operational_db(db_path)
    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent
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


def make_raw_update(update_id: int, message_id: int, text: str = "Test msg", is_bot: bool = False) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "date": 1700000000,
            "chat": {"id": int(GROUP_ID)},
            "from": {"id": 11223344, "is_bot": is_bot, "first_name": "Bob"},
            "text": text,
        },
    }


@pytest.mark.automated
def test_polling_offset_advances_only_after_commit(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    updates = [make_raw_update(10, 1), make_raw_update(11, 2)]
    adapter = MockTelegramAdapter(updates)
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    res = asyncio.run(loop.step())
    assert res.inserted_count == 2
    assert res.final_offset == 12

    cur = conn.cursor()
    cur.execute("SELECT last_persisted_update_id, next_offset FROM polling_state WHERE project_id = ?", (PROJECT_ID,))
    last_id, next_off = cur.fetchone()
    assert last_id == 11
    assert next_off == 12
    conn.close()


@pytest.mark.automated
def test_crash_before_commit_preserves_offset(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    updates = [make_raw_update(10, 1)]
    adapter = MockTelegramAdapter(updates)
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    # Inject failure before commit by temporarily intercepting with a trigger
    conn.execute("CREATE TRIGGER fail_commit BEFORE UPDATE ON polling_state BEGIN SELECT RAISE(ABORT, 'Simulated DB failure before commit'); END;")

    with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError)):
        asyncio.run(loop.step())

    # Verify offset did NOT advance
    cur = conn.cursor()
    cur.execute("SELECT next_offset FROM polling_state WHERE project_id = ?", (PROJECT_ID,))
    assert cur.fetchone()[0] == 1

    # Remove the failure trigger and retry; verify redelivery succeeds without duplicates
    conn.execute("DROP TRIGGER fail_commit")
    res = asyncio.run(loop.step())
    assert res.inserted_count == 1
    assert res.final_offset == 11
    conn.close()


@pytest.mark.automated
def test_crash_after_commit_before_next_fetch(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    updates = [make_raw_update(10, 1), make_raw_update(11, 2)]
    adapter = MockTelegramAdapter(updates)
    loop1 = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    asyncio.run(loop1.step())

    # Simulate crash/restart: instantiate a fresh loop instance pointing to same DB
    loop2 = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)
    _, next_offset = loop2.get_polling_state()
    assert next_offset == 12

    # Provide next batch starting at offset 12
    adapter.add_update(make_raw_update(12, 3))
    res = asyncio.run(loop2.step())
    assert adapter.last_offset_requested == 12
    assert res.inserted_count == 1
    assert res.final_offset == 13
    conn.close()


@pytest.mark.automated
def test_duplicate_update_rejected(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    updates = [make_raw_update(20, 1), make_raw_update(20, 2)]  # duplicate update_id 20
    adapter = MockTelegramAdapter(updates)
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    res = asyncio.run(loop.step())
    assert res.inserted_count == 1
    assert res.skipped_duplicate_count == 1

    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM inbox_messages WHERE project_id = ?", (PROJECT_ID,))
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM update_receipts WHERE project_id = ?", (PROJECT_ID,))
    assert cur.fetchone()[0] == 1
    conn.close()


@pytest.mark.automated
def test_duplicate_message_rejected(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    # Different update_ids but same (project_id, group_id, telegram_message_id=99)
    updates = [make_raw_update(30, 99), make_raw_update(31, 99)]
    adapter = MockTelegramAdapter(updates)
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    res = asyncio.run(loop.step())
    assert res.inserted_count == 1
    assert res.skipped_duplicate_count == 1

    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM inbox_messages WHERE telegram_message_id = 99")
    assert cur.fetchone()[0] == 1
    conn.close()


@pytest.mark.automated
def test_update_receipt_inserted_same_transaction(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    updates = [make_raw_update(40, 1)]
    adapter = MockTelegramAdapter(updates)
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    # Force failure on update_receipts insertion via trigger
    conn.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON update_receipts BEGIN SELECT RAISE(ABORT, 'Receipt insertion failed'); END;")

    with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError)):
        asyncio.run(loop.step())

    # Entire transaction must have rolled back: no inbox_messages row and no polling_state advance
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM inbox_messages WHERE project_id = ?", (PROJECT_ID,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT next_offset FROM polling_state WHERE project_id = ?", (PROJECT_ID,))
    assert cur.fetchone()[0] == 1
    conn.close()


@pytest.mark.automated
def test_discarded_update_still_advances_offset(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    # Update from bot must be discarded, but offset must advance per Spec §6.3
    updates = [make_raw_update(50, 1, is_bot=True)]
    adapter = MockTelegramAdapter(updates)
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    res = asyncio.run(loop.step())
    assert res.inserted_count == 0
    assert res.final_offset == 51

    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM inbox_messages WHERE project_id = ?", (PROJECT_ID,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT last_persisted_update_id, next_offset FROM polling_state WHERE project_id = ?", (PROJECT_ID,))
    last_id, next_off = cur.fetchone()
    assert last_id == 50
    assert next_off == 51
    conn.close()


@pytest.mark.automated
def test_polling_gap_alert(tmp_path: Path) -> None:
    conn = setup_test_db(tmp_path)
    adapter = MockTelegramAdapter([make_raw_update(1, 1)])
    loop = PollingLoop(PROJECT_ID, adapter, conn, GROUP_ID, HMAC_KEY)

    # First update sets offset to 2
    asyncio.run(loop.step())

    # Second batch arrives with gap: update_id 10 when next_offset was 2
    adapter.add_update(make_raw_update(10, 2))

    with pytest.raises(PollingGapAlert) as exc_info:
        asyncio.run(loop.step())

    assert "missing 8 updates" in str(exc_info.value) or "expected update_id 2" in str(exc_info.value)
    conn.close()
