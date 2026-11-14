"""Multi-Tenant Bot Orchestrator running multiple independent Telegram bots from a single Python process."""

import argparse
import asyncio
from contextlib import AsyncExitStack
import json
from pathlib import Path
import signal
import sqlite3
import sys
from typing import Any, Dict, List, Optional

from zoe.db.connections import (
    ensure_databases_initialized,
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.inbox.inbox_service import ensure_project_registered, init_polling_state
from zoe.knowledge.model import prewarm_model
from zoe.llm.factory import get_llm_client
from zoe.outbox.service import drain_outbox
from zoe.settings import load_project_config, load_project_secrets, validate_config
from zoe.telegram.adapter import PTBTelegramAdapter
from zoe.telegram.polling_loop import PollingLoop
from zoe.utils.logging import get_logger, set_current_project
from zoe.worker.claim import claim_next_inbox_row
from zoe.worker.pipeline import process_message

logger = get_logger("zoe.orchestrator")


class BotInstance:
    """Encapsulates runtime state for a single tenant bot."""

    def __init__(
        self,
        project_id: str,
        config: Dict[str, Any],
        secrets: Dict[str, Any],
        db_conns: Dict[str, sqlite3.Connection],
        adapter: Any,
        llm_client: Any,
        model: Any,
    ) -> None:
        self.project_id = project_id
        self.config = config
        self.secrets = secrets
        self.db_conns = db_conns
        self.adapter = adapter
        self.llm_client = llm_client
        self.model = model
        self.group_id = str(config.get("telegram", {}).get("group_id", ""))
        self.hmac_key = str(secrets.get("hmac_key", "default_hmac_key_32_characters_minimum"))
        self.poll_interval = float(config.get("telegram", {}).get("poll_interval_seconds", 0.1))

        self.polling_loop = PollingLoop(
            project_id=self.project_id,
            adapter=self.adapter,
            db_conn=self.db_conns["operational"],
            configured_group_id=self.group_id,
            hmac_key=self.hmac_key,
            poll_timeout=2,
            allow_gap_recovery=True,
        )
        self.polling_loop.init_state()

    async def step(self) -> int:
        """Run one polling, processing, and delivery cycle for this bot."""
        conn_op = self.db_conns["operational"]

        # 1. Poll updates
        persist_res = await self.polling_loop.step()
        if persist_res.inserted_count > 0:
            logger.info("Received %d new update(s) from Telegram.", persist_res.inserted_count)

        # 2. Process pending inbox items
        processed_count = 0
        while True:
            claim = claim_next_inbox_row(conn_op, project_id=self.project_id, worker_id=f"orch_{self.project_id}")
            if not claim:
                break

            text_preview = claim.get("text", "")[:40]
            logger.info("Processing inbox msg %d: '%s'...", claim["id"], text_preview)

            res = await asyncio.to_thread(
                process_message,
                inbox_row=claim,
                db_conns=None,
                llm_client=self.llm_client,
                model=self.model,
                simulated=False,
            )
            processed_count += 1
            logger.info(
                "Inbox msg %d processed: decision=%s, reason=%s, responded=%s",
                claim["id"],
                res.decision.decision,
                res.decision.reason,
                res.responded,
            )

        # 3. Drain outbox
        delivered = await drain_outbox(
            conn=conn_op,
            project_id=self.project_id,
            adapter=self.adapter,
            worker_id=f"drain_{self.project_id}",
        )
        if delivered > 0:
            logger.info("Successfully delivered %d live response(s) to Telegram!", delivered)

        return persist_res.inserted_count + processed_count + delivered


async def run_bot_worker(bot: BotInstance, shutdown_event: asyncio.Event) -> None:
    """Supervised worker loop with fault isolation and backoff restart."""
    set_current_project(bot.project_id)
    logger.info("Bot worker started for project '%s' (group %s).", bot.project_id, bot.group_id)

    # Register Telegram bot command menu on startup
    try:
        from zoe.conversation.prompt_builder import get_project_display_name
        from zoe.telegram.bot import init_bot
        bot_display = get_project_display_name(bot.project_id) or "Zoe"
        await init_bot(bot.adapter, bot_name=bot_display)
    except Exception as cmd_exc:
        logger.warning("Could not register bot command menu on startup for '%s': %s", bot.project_id, cmd_exc)

    backoff_delay = 1.0
    max_backoff = 30.0

    while not shutdown_event.is_set():
        activity = 0
        try:
            set_current_project(bot.project_id)
            activity = await bot.step()
            backoff_delay = 1.0  # Reset on successful iteration
        except asyncio.CancelledError:
            break
        except Exception as exc:
            set_current_project(bot.project_id)
            logger.error(
                "Unhandled error in bot '%s': %s. Retrying with backoff in %.1fs...",
                bot.project_id,
                str(exc),
                backoff_delay,
                exc_info=True,
            )
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=backoff_delay)
                break
            except asyncio.TimeoutError:
                pass
            backoff_delay = min(backoff_delay * 2.0, max_backoff)

        # Responsive polling delay: if work was processed/delivered, loop immediately (0.01s)
        next_wait = 0.01 if activity > 0 else bot.poll_interval
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=next_wait)
            break
        except asyncio.TimeoutError:
            pass

    logger.info("Bot worker stopped cleanly for project '%s'.", bot.project_id)


def ensure_knowledge_indexes(model: Optional[Any] = None) -> None:
    """Auto-ingest project knowledge if FAISS index files do not exist."""
    import shutil
    from zoe.knowledge.ingestion import ingest_document
    from zoe.settings import get_data_dir

    data_dir = get_data_dir()
    project_docs = [
        ("onelove", "onelove_info.txt"),
        ("live_test", "hummingbird_info.txt"),
    ]
    for project_id, filename in project_docs:
        target_knowledge_dir = data_dir / "knowledge"
        target_knowledge_dir.mkdir(parents=True, exist_ok=True)
        target_doc_path = target_knowledge_dir / filename

        # Search candidates if document is missing from target volume
        if not target_doc_path.exists():
            candidates = [
                Path("data/knowledge") / filename,
                Path("/app/data/knowledge") / filename,
                Path(__file__).resolve().parent.parent / "data" / "knowledge" / filename,
            ]
            for cand in candidates:
                if cand.exists():
                    try:
                        shutil.copy2(cand, target_doc_path)
                        logger.info("Auto-seeded %s to %s", cand, target_doc_path)
                        break
                    except Exception as copy_err:
                        logger.warning("Could not copy %s to %s: %s", cand, target_doc_path, copy_err)

        doc_path = target_doc_path if target_doc_path.exists() else None
        index_file = data_dir / "indexes" / project_id / "index.faiss"
        needs_ingestion = False
        if not index_file.exists() or index_file.stat().st_size == 0:
            needs_ingestion = True
        elif doc_path and doc_path.exists() and doc_path.stat().st_mtime > index_file.stat().st_mtime:
            needs_ingestion = True

        if needs_ingestion:
            if doc_path and doc_path.exists():
                msg_start = f"[INGESTION] Building FAISS index for {project_id.upper()}..."
                print(msg_start, flush=True)
                logger.info(msg_start)
                try:
                    res = ingest_document(
                        filepath=doc_path,
                        project_id=project_id,
                        db_path=data_dir / "official_knowledge" / "official_knowledge.db",
                        index_dir=data_dir / "indexes",
                        model=model,
                    )
                    msg_done = f"[INGESTION] Successfully ingested {res.chunk_count} chunks for {project_id.upper()}."
                    print(msg_done, flush=True)
                    logger.info(msg_done)
                except Exception as exc:
                    msg_err = f"[INGESTION ERROR] Failed to ingest {doc_path} for '{project_id}': {exc}"
                    print(msg_err, flush=True)
                    logger.error(msg_err)
            else:
                msg_warn = f"[INGESTION WARNING] Knowledge document '{filename}' not found for '{project_id}'. Skipping index generation."
                print(msg_warn, flush=True)
                logger.warning(msg_warn)
        else:
            logger.info("Knowledge index exists and is up to date for project '%s' (%d bytes).", project_id, index_file.stat().st_size)


def discover_projects(config_dir: str = "config/projects") -> List[str]:
    """Scan directory for valid project configuration files."""
    path = Path(config_dir)
    if not path.exists():
        return []
    projects = []
    for file in sorted(path.glob("*.yaml")):
        project_id = file.stem
        projects.append(project_id)
    return projects


async def start_orchestrator(
    config_dir: str = "config/projects",
    project_filter: Optional[List[str]] = None,
    shared_model: Optional[Any] = None,
    mock_adapters: Optional[Dict[str, Any]] = None,
    mock_llms: Optional[Dict[str, Any]] = None,
    run_once: bool = False,
) -> None:
    """Initialize and coordinate all active multi-tenant bots."""
    set_current_project("orchestrator")
    logger.info("Starting Zoe Multi-Tenant Bot Orchestrator...")

    from zoe.settings import get_data_dir
    data_dir = get_data_dir()
    logger.info("Using data directory: %s", data_dir.resolve())

    # 0. Auto-initialize SQLite databases and apply schemas if missing
    ensure_databases_initialized(data_dir)

    # 1. Discover all project configs
    all_projects = discover_projects(config_dir)
    if project_filter:
        all_projects = [p for p in all_projects if p in project_filter]

    if not all_projects:
        logger.warning("No projects found to orchestrate in '%s'.", config_dir)
        return

    logger.info("Discovered %d project configuration(s): %s", len(all_projects), all_projects)

    # 2. Singleton Embedding Model (Shared RAM foot-print)
    model = shared_model
    if model is None:
        logger.info("Pre-warming shared singleton embedding model...")
        model = prewarm_model()
        logger.info("Shared embedding model ready in RAM.")

    # 2b. Auto-Ingest Knowledge if FAISS indexes are missing on cold start
    ensure_knowledge_indexes(model=model)

    # 3. Setup shutdown coordinator
    shutdown_event = asyncio.Event()

    def handle_signal():
        set_current_project("orchestrator")
        logger.info("Shutdown signal received. Initiating graceful shutdown for all bots...")
        shutdown_event.set()

    # Wire signal handlers if supported (non-Windows / main thread)
    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)
    except (NotImplementedError, AttributeError):
        pass

    async with AsyncExitStack() as stack:
        bot_instances: List[BotInstance] = []

        for p_id in all_projects:
            set_current_project(p_id)
            try:
                cfg = load_project_config(p_id)
                sec = load_project_secrets(p_id)
                validate_config(cfg, sec)
            except Exception as e:
                logger.warning("Skipping project '%s' due to invalid config/secrets: %s", p_id, str(e))
                continue

            if not cfg.get("project", {}).get("active", 1):
                logger.info("Project '%s' is marked inactive in config; skipping.", p_id)
                continue

            # DB Connections with WAL mode & busy timeout
            conn_op = open_operational_db(data_dir / "operational" / "operational.db")
            conn_kb = open_official_knowledge_db(
                cfg.get("knowledge", {}).get("db_path") or (data_dir / "official_knowledge" / "official_knowledge.db")
            )
            conn_mem = open_community_memory_db(
                cfg.get("memory", {}).get("db_path") or (data_dir / "community_memory" / "community_memory.db")
            )

            stack.callback(conn_op.close)
            stack.callback(conn_kb.close)
            stack.callback(conn_mem.close)

            ensure_project_registered(
                conn_op,
                project_id=p_id,
                name=cfg.get("project", {}).get("name", p_id),
                telegram_group_id=str(cfg.get("telegram", {}).get("group_id", "")),
                config_json=json.dumps(cfg),
            )
            init_polling_state(conn_op, p_id)

            db_conns = {
                "operational": conn_op,
                "knowledge": conn_kb,
                "memory": conn_mem,
            }

            # Adapter selection
            if mock_adapters and p_id in mock_adapters:
                adapter = mock_adapters[p_id]
            else:
                token = sec.get("bot_token")
                if not token:
                    logger.warning("Project '%s' missing bot_token; skipping live polling.", p_id)
                    continue
                adapter = PTBTelegramAdapter(bot_token=token, request_timeout=30.0)

            # LLM Client selection
            if mock_llms and p_id in mock_llms:
                llm = mock_llms[p_id]
            else:
                llm = get_llm_client(p_id)

            instance = BotInstance(
                project_id=p_id,
                config=cfg,
                secrets=sec,
                db_conns=db_conns,
                adapter=adapter,
                llm_client=llm,
                model=model,
            )
            bot_instances.append(instance)

        if not bot_instances:
            set_current_project("orchestrator")
            logger.warning("No runnable bot instances initialized.")
            return

        set_current_project("orchestrator")
        logger.info("Successfully initialized %d bot instance(s). Spawning workers...", len(bot_instances))

        # Wire BotManager singleton so all bots are observable via GET /health and internal API
        from datetime import datetime, timezone
        import uvicorn
        from zoe.api import bot_manager, engine_app
        bot_manager.shared_model = model

        for bot in bot_instances:
            bot_manager.statuses[bot.project_id] = "running"
            bot_manager.configs[bot.project_id] = bot.config
            bot_manager.started_at[bot.project_id] = datetime.now(timezone.utc).isoformat()
            bot_manager.shutdown_events[bot.project_id] = shutdown_event

        if run_once:
            # Single iteration across all bots
            for bot in bot_instances:
                set_current_project(bot.project_id)
                await bot.step()
            return

        # Spawn concurrent supervised tasks for initial bots
        tasks = []
        for bot in bot_instances:
            t = asyncio.create_task(run_bot_worker(bot, shutdown_event))
            bot_manager.tasks[bot.project_id] = t
            tasks.append(t)

        # Launch Engine FastAPI on port 8080 concurrently
        uvi_config = uvicorn.Config(engine_app, host="0.0.0.0", port=8080, log_level="warning")
        uvi_server = uvicorn.Server(uvi_config)
        logger.info("Starting Zoe Engine Internal API on http://0.0.0.0:8080...")
        api_task = asyncio.create_task(uvi_server.serve())
        tasks.append(api_task)

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except (KeyboardInterrupt, asyncio.CancelledError):
            handle_signal()
            uvi_server.should_exit = True
            await asyncio.gather(*tasks, return_exceptions=True)

        set_current_project("orchestrator")
        logger.info("All bot workers terminated. Clean shutdown complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Tenant Bot Orchestrator")
    parser.add_argument("--projects", nargs="*", help="Specific project IDs to run")
    parser.add_argument("--once", action="store_true", help="Run a single step for all bots and exit")
    args = parser.parse_args()

    try:
        asyncio.run(
            start_orchestrator(
                project_filter=args.projects,
                run_once=args.once,
            )
        )
    except KeyboardInterrupt:
        print("\nOrchestrator stopped by operator.")
        sys.exit(0)


if __name__ == "__main__":
    main()

