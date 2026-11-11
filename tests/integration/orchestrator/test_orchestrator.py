"""Integration tests for the Multi-Tenant Bot Orchestrator."""

import asyncio
from pathlib import Path
import sqlite3
import pytest

from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.inbox.inbox_service import ensure_project_registered, init_polling_state
from zoe.llm.mock import MockLLMClient
from scripts.run_all_bots import BotInstance


class MockTelegramAdapter:
    """Mock Telegram adapter for multi-tenant integration testing."""

    def __init__(self, updates: list) -> None:
        self.updates = list(updates)
        self.sent_messages = []

    async def get_updates(self, offset: int, timeout: int = 30, limit: int = 100):
        # Return queued updates once, then empty
        to_return = [u for u in self.updates if u.get("update_id", 0) >= offset]
        return to_return

    async def delete_webhook(self) -> bool:
        return True

    async def send_message(self, chat_id: str, text: str, reply_to_message_id=None):
        payload = {
            "message_id": 9999 + len(self.sent_messages),
            "chat": {"id": chat_id},
            "text": text,
        }
        self.sent_messages.append(payload)
        return payload


@pytest.fixture
def multi_tenant_env(tmp_path: Path):
    """Set up operational, knowledge, and memory databases."""
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_operational.sql").read_text(encoding="utf-8")
    conn_op.executescript(sql_op)

    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_knowledge.sql").read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_community_memory.sql").read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }

    return conns, op_path, kb_path, mem_path


@pytest.mark.anyio
async def test_multi_tenant_orchestrator_concurrent_bots(multi_tenant_env):
    """Verify multiple independent bots process messages simultaneously without cross-talk."""
    conns, _, _, _ = multi_tenant_env
    conn_op = conns["operational"]

    # Register Project A
    ensure_project_registered(conn_op, project_id="proj_a", name="Project A", telegram_group_id="-100111")
    init_polling_state(conn_op, "proj_a")

    # Register Project B
    ensure_project_registered(conn_op, project_id="proj_b", name="Project B", telegram_group_id="-100222")
    init_polling_state(conn_op, "proj_b")

    # Updates for Project A
    updates_a = [
        {
            "update_id": 101,
            "message": {
                "message_id": 501,
                "date": 1730000000,
                "chat": {"id": -100111, "type": "supergroup"},
                "from": {"id": 111111, "is_bot": False, "username": "alice"},
                "text": "What is the tokenomics for Project A?",
            },
        }
    ]

    # Updates for Project B
    updates_b = [
        {
            "update_id": 201,
            "message": {
                "message_id": 601,
                "date": 1730000000,
                "chat": {"id": -100222, "type": "supergroup"},
                "from": {"id": 222222, "is_bot": False, "username": "bob"},
                "text": "What is the roadmap for Project B?",
            },
        }
    ]

    adapter_a = MockTelegramAdapter(updates_a)
    adapter_b = MockTelegramAdapter(updates_b)

    llm_a = MockLLMClient(canned_response="Response from Bot A")
    llm_b = MockLLMClient(canned_response="Response from Bot B")

    bot_a = BotInstance(
        project_id="proj_a",
        config={
            "telegram": {"group_id": "-100111", "poll_interval_seconds": 0.1},
            "participation": {"respond_to_casual": True},
        },
        secrets={"hmac_key": "hmac_key_for_test_at_least_32_characters_long"},
        db_conns=conns,
        adapter=adapter_a,
        llm_client=llm_a,
        model=None,
    )

    bot_b = BotInstance(
        project_id="proj_b",
        config={
            "telegram": {"group_id": "-100222", "poll_interval_seconds": 0.1},
            "participation": {"respond_to_casual": True},
        },
        secrets={"hmac_key": "hmac_key_for_test_at_least_32_characters_long"},
        db_conns=conns,
        adapter=adapter_b,
        llm_client=llm_b,
        model=None,
    )

    # Fire both bots concurrently
    res_a, res_b = await asyncio.gather(bot_a.step(), bot_b.step())

    assert res_a == 1
    assert res_b == 1

    # Verify adapter deliveries
    assert len(adapter_a.sent_messages) == 1
    assert adapter_a.sent_messages[0]["text"] == "Response from Bot A"
    assert adapter_a.sent_messages[0]["chat"]["id"] == "-100111"

    assert len(adapter_b.sent_messages) == 1
    assert adapter_b.sent_messages[0]["text"] == "Response from Bot B"
    assert adapter_b.sent_messages[0]["chat"]["id"] == "-100222"

    # Verify operational DB integrity: no cross-contamination
    cur = conn_op.execute("SELECT project_id, group_id, text FROM inbox_messages ORDER BY id ASC")
    rows = cur.fetchall()
    assert len(rows) == 2
    assert rows[0] == ("proj_a", "-100111", "What is the tokenomics for Project A?")
    assert rows[1] == ("proj_b", "-100222", "What is the roadmap for Project B?")


@pytest.mark.anyio
async def test_multi_tenant_fault_isolation(multi_tenant_env):
    """Verify that an exception in Bot A does not crash Bot B."""
    conns, _, _, _ = multi_tenant_env
    conn_op = conns["operational"]

    ensure_project_registered(conn_op, project_id="failing_bot", name="Failing Bot", telegram_group_id="-100999")
    init_polling_state(conn_op, "failing_bot")

    ensure_project_registered(conn_op, project_id="healthy_bot", name="Healthy Bot", telegram_group_id="-100888")
    init_polling_state(conn_op, "healthy_bot")

    class CrashingAdapter:
        async def get_updates(self, *args, **kwargs):
            raise RuntimeError("Telegram network connection dropped in failing bot!")

    healthy_updates = [
        {
            "update_id": 301,
            "message": {
                "message_id": 701,
                "date": 1730000000,
                "chat": {"id": -100888, "type": "supergroup"},
                "from": {"id": 333333, "is_bot": False, "username": "charlie"},
                "text": "What is the roadmap for Healthy Bot?",
            },
        }
    ]
    healthy_adapter = MockTelegramAdapter(healthy_updates)
    healthy_llm = MockLLMClient(canned_response="Healthy Bot Online")

    failing_bot = BotInstance(
        project_id="failing_bot",
        config={
            "telegram": {"group_id": "-100999", "poll_interval_seconds": 0.1},
            "participation": {"respond_to_casual": True},
        },
        secrets={"hmac_key": "hmac_key_for_test_at_least_32_characters_long"},
        db_conns=conns,
        adapter=CrashingAdapter(),
        llm_client=MockLLMClient(),
        model=None,
    )

    healthy_bot = BotInstance(
        project_id="healthy_bot",
        config={
            "telegram": {"group_id": "-100888", "poll_interval_seconds": 0.1},
            "participation": {"respond_to_casual": True},
        },
        secrets={"hmac_key": "hmac_key_for_test_at_least_32_characters_long"},
        db_conns=conns,
        adapter=healthy_adapter,
        llm_client=healthy_llm,
        model=None,
    )

    # Failing bot raises
    with pytest.raises(RuntimeError):
        await failing_bot.step()

    # Healthy bot continues without being affected
    delivered = await healthy_bot.step()
    assert delivered == 1
    assert len(healthy_adapter.sent_messages) == 1
    assert healthy_adapter.sent_messages[0]["text"] == "Healthy Bot Online"
