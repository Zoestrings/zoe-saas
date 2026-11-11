"""Live interactive bot runner connecting Telegram polling, Groq LLM, and live delivery."""

import argparse
import asyncio
import json
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any, Optional

from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.inbox.inbox_service import ensure_project_registered, init_polling_state
from zoe.llm.factory import get_llm_client
from zoe.outbox.service import drain_outbox
from zoe.settings import load_project_config, load_project_secrets, validate_config
from zoe.telegram.adapter import PTBTelegramAdapter
from zoe.telegram.polling_loop import PollingLoop
from zoe.utils.logging import get_logger
from zoe.worker.claim import claim_next_inbox_row
from zoe.worker.pipeline import process_message, trigger_proactive_intervention

logger = get_logger("zoe.live_runner")


async def run_step(
    project_id: str,
    loop: PollingLoop,
    adapter: PTBTelegramAdapter,
    conns: dict[str, sqlite3.Connection],
    llm_client,
    model: Optional[Any] = None,
) -> int:
    """Execute one full end-to-end iteration: poll -> process -> reply."""
    conn_op = conns["operational"]

    # 1. Fetch any new Telegram updates
    persist_res = await loop.step()
    if persist_res.inserted_count > 0:
        logger.info("Received %d new update(s) from Telegram.", persist_res.inserted_count)

    # 2. Process all pending inbox messages concurrently with non-blocking I/O
    claims = []
    while True:
        claim = claim_next_inbox_row(conn_op, project_id=project_id, worker_id="live_runner")
        if not claim:
            break
        claims.append(claim)

    processed_count = 0
    for claim_item in claims:
        text_preview = claim_item.get("text", "")[:40]
        logger.info("Processing inbox msg %d: '%s'...", claim_item["id"], text_preview)
        try:
            res = await asyncio.to_thread(
                process_message,
                inbox_row=claim_item,
                db_conns=None,
                llm_client=llm_client,
                model=model,
                simulated=False,
            )
            logger.info(
                "Inbox msg %d processed: decision=%s, reason=%s, responded=%s",
                claim_item["id"],
                res.decision.decision,
                res.decision.reason,
                res.responded,
            )
            processed_count += 1
        except Exception as exc:
            logger.error("Error processing inbox msg %d: %s", claim_item["id"], exc)

    # 3. Autonomous Proactive Radar check (JARVIS Mode)
    if processed_count > 0:
        try:
            proactive_outbox = trigger_proactive_intervention(
                project_id=project_id,
                group_id=loop.configured_group_id,
                db_conns=conns,
                llm_client=llm_client,
                model=model,
                simulated=False,
            )
            if proactive_outbox:
                logger.info("Autonomous JARVIS proactive response queued to outbox: msg %d", proactive_outbox)
        except Exception as exc:
            logger.debug("Proactive intervention check: %s", exc)

    # 4. Drain outbox and send live responses to Telegram
    delivered = await drain_outbox(
        conn=conn_op,
        project_id=project_id,
        adapter=adapter,
        worker_id="live_drain",
    )
    if delivered > 0:
        logger.info("Successfully delivered %d live response(s) to Telegram!", delivered)

    return persist_res.inserted_count + processed_count + delivered


async def main() -> None:
    parser = argparse.ArgumentParser(description="Zoe Live Bot Runner")
    parser.add_argument("--project", default="live_test", help="Project ID to run")
    parser.add_argument("--once", action="store_true", help="Run a single polling step and exit")
    parser.add_argument("--interval", type=float, default=0.1, help="Polling interval in seconds")
    args = parser.parse_args()

    project_id = args.project
    config = load_project_config(project_id)
    secrets = load_project_secrets(project_id)
    validate_config(config, secrets)

    group_id = config.get("telegram", {}).get("group_id", "")
    bot_token = secrets.get("bot_token")
    hmac_key = secrets.get("hmac_key", "default_hmac_key_32_characters_minimum")

    adapter = PTBTelegramAdapter(bot_token=bot_token, request_timeout=30.0)
    llm = get_llm_client(project_id)

    conn_op = open_operational_db("data/operational/operational.db")
    conn_kb = open_official_knowledge_db(
        config.get("knowledge", {}).get("db_path", "data/official_knowledge/official_knowledge.db")
    )
    conn_mem = open_community_memory_db(
        config.get("memory", {}).get("db_path", "data/community_memory/community_memory.db")
    )

    ensure_project_registered(
        conn_op,
        project_id=project_id,
        name=config.get("project", {}).get("name", "Zoe"),
        telegram_group_id=group_id,
        config_json=json.dumps(config),
    )
    init_polling_state(conn_op, project_id)

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }

    # Pre-warm embedding model in background thread so polling starts immediately
    logger.info("Initializing knowledge embedding model in background thread...")
    model = None

    def _warmup_worker():
        nonlocal model
        try:
            from zoe.knowledge.model import get_embedding_model
            model = get_embedding_model()
            logger.info("Knowledge embedding model ready.")
        except Exception as exc:
            logger.warning("Could not pre-warm embedding model: %s", exc)

    import threading
    threading.Thread(target=_warmup_worker, daemon=True).start()

    loop = PollingLoop(
        project_id=project_id,
        adapter=adapter,
        db_conn=conn_op,
        configured_group_id=group_id,
        hmac_key=hmac_key,
        poll_timeout=2,
        allow_gap_recovery=True,
    )
    loop.init_state()

    # Register Telegram bot command menu on startup
    try:
        from zoe.telegram.bot import init_bot
        await init_bot(adapter)
    except Exception as cmd_exc:
        logger.warning("Could not register bot command menu on startup: %s", cmd_exc)

    logger.info("Zoe Live Bot runner started for project '%s' (group %s).", project_id, group_id)

    if args.once:
        await run_step(project_id, loop, adapter, conns, llm, model=model)
    else:
        logger.info("Listening for messages... Press Ctrl+C to stop.")
        try:
            while True:
                activity = 0
                try:
                    activity = await run_step(project_id, loop, adapter, conns, llm, model=model)
                except Exception as e:
                    logger.error("Error in runner iteration: %s", str(e))
                next_sleep = 0.01 if activity > 0 else args.interval
                await asyncio.sleep(next_sleep)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Runner stopped by operator.")
        finally:
            conn_op.close()
            conn_kb.close()
            conn_mem.close()


if __name__ == "__main__":
    asyncio.run(main())

