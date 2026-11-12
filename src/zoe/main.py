import asyncio
from pathlib import Path
import sys

from zoe.db.connections import (
    ensure_databases_initialized,
    open_operational_db,
    open_official_knowledge_db,
    open_community_memory_db,
)
from zoe.settings import load_project_config, load_project_secrets, validate_config
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.telegram.polling_loop import PollingLoop
from zoe.utils.logging import get_logger

logger = get_logger("zoe.main")


def init_operational_db(conn, schema_path: Path) -> None:
    """Apply schema_operational.sql to operational.db."""
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()


def main(project_id: str = "example_project") -> int:
    ensure_databases_initialized("data")
    config = load_project_config(project_id)
    secrets = load_project_secrets(project_id)
    validate_config(config, secrets)

    operational_db_path = Path("data/operational/operational.db")
    knowledge_db_path = Path(
        config.get("knowledge", {}).get("db_path", "data/official_knowledge/official_knowledge.db")
    )
    memory_db_path = Path(
        config.get("memory", {}).get("db_path", "data/community_memory/community_memory.db")
    )

    conn_op = open_operational_db(operational_db_path)
    conn_kb = open_official_knowledge_db(knowledge_db_path)
    conn_mem = open_community_memory_db(memory_db_path)

    schema_path = Path(__file__).resolve().parent / "db" / "schema_operational.sql"
    init_operational_db(conn_op, schema_path)

    logger.info("Stage 1 skeleton ready")

    # Stage 2 smoke test: single iteration with MockTelegramAdapter
    group_id = config.get("telegram", {}).get("group_id", "-1001234567890")
    hmac_key = secrets.get("security", {}).get("hmac_key", "stage2_smoke_test_hmac_key")

    fixture_update = {
        "update_id": 101,
        "message": {
            "message_id": 501,
            "date": 1700000000,
            "chat": {"id": int(group_id) if group_id.startswith("-") and group_id[1:].isdigit() else group_id},
            "from": {"id": 999888777, "is_bot": False, "first_name": "TestUser"},
            "text": "Smoke test message for Stage 2 polling loop",
        },
    }

    mock_adapter = MockTelegramAdapter([fixture_update])
    loop = PollingLoop(
        project_id=project_id,
        adapter=mock_adapter,
        db_conn=conn_op,
        configured_group_id=group_id,
        hmac_key=hmac_key,
    )
    loop.init_state()

    result = asyncio.run(loop.step())
    logger.info(
        f"Stage 2 smoke polling step completed: inserted={result.inserted_count}, "
        f"skipped={result.skipped_duplicate_count}, offset={result.final_offset}"
    )

    conn_op.close()
    conn_kb.close()
    conn_mem.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
