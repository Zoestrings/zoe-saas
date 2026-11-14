"""Internal Engine API and dynamic BotManager supervisor for Zoe Bot Engine."""

import asyncio
from datetime import datetime, timezone
import hmac
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Dict, List, Optional
import yaml

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from zoe.utils.logging import get_logger

logger = get_logger("zoe.engine.api")

# Regex validators for security and path traversal protection
PROJECT_ID_PATTERN = re.compile(r"^[a-z0-9-]{3,40}$")
BOT_TOKEN_PATTERN = re.compile(r"^\d{8,12}:[A-Za-z0-9_-]{32,}$")
TOKEN_ADDRESS_PATTERN = re.compile(r"^(0x[a-fA-F0-9]{40}|[A-Za-z0-9]{32,64})$")


def redact_token(token: Optional[str]) -> str:
    """Safely redact secret tokens in logs and responses."""
    if not token or len(token) < 10:
        return "[REDACTED]"
    return f"{token[:4]}...{token[-4:]}"


def sanitize_project_id(raw_name: str) -> str:
    """Generate a clean slug for project_id matching ^[a-z0-9-]{3,40}$."""
    slug = re.sub(r"[^a-z0-9]+", "-", raw_name.lower().strip()).strip("-")
    if len(slug) < 3:
        slug = f"project-{slug}"
    return slug[:40]


class SpawnBotRequest(BaseModel):
    project_id: str = Field(..., description="Project slug (3-40 lowercase alphanumeric chars or dashes)")
    bot_token: str = Field(..., description="Telegram Bot Token from @BotFather")
    group_id: Optional[str] = Field(None, description="Telegram group ID to lock to (optional)")
    token_address: str = Field(..., description="Token contract address (Solana or EVM)")
    token_symbol: Optional[str] = Field(None, description="Token ticker symbol, e.g. $TOKEN")
    name: Optional[str] = Field(None, description="Human readable project name")
    knowledge_base: Optional[str] = Field(None, description="Optional raw text facts for immediate RAG ingestion")


class PatchBotRequest(BaseModel):
    group_id: Optional[str] = Field(None, description="Updated Telegram group ID")
    token_address: Optional[str] = Field(None, description="Updated token contract address")


class BotStatusResponse(BaseModel):
    project_id: str
    status: str
    group_id: Optional[str] = None
    token_address: Optional[str] = None
    started_at: Optional[str] = None
    error: Optional[str] = None
    ingestion_status: Optional[str] = None


class BotManager:
    """Manages dynamic bot lifecycles, supervised polling tasks, and state tracking."""

    def __init__(self, shared_model: Optional[Any] = None) -> None:
        self.tasks: Dict[str, asyncio.Task] = {}
        self.shutdown_events: Dict[str, asyncio.Event] = {}
        self.statuses: Dict[str, str] = {}  # starting | running | error | stopped
        self.errors: Dict[str, Optional[str]] = {}
        self.started_at: Dict[str, str] = {}
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.ingestion_statuses: Dict[str, str] = {}
        self.shared_model = shared_model

    def get_status(self, project_id: str) -> Dict[str, Any]:
        cfg = self.configs.get(project_id, {})
        return {
            "project_id": project_id,
            "status": self.statuses.get(project_id, "stopped"),
            "group_id": str(cfg.get("telegram", {}).get("group_id", "")),
            "token_address": str(cfg.get("token", {}).get("address", "")),
            "started_at": self.started_at.get(project_id),
            "error": self.errors.get(project_id),
            "ingestion_status": self.ingestion_statuses.get(project_id, "none"),
        }

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        all_ids = set(self.tasks.keys()) | set(self.statuses.keys())
        return [self.get_status(p_id) for p_id in sorted(all_ids)]

    async def stop_bot(self, project_id: str) -> bool:
        """Gracefully stop a running bot task."""
        if project_id in self.shutdown_events:
            self.shutdown_events[project_id].set()

        task = self.tasks.get(project_id)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        self.statuses[project_id] = "stopped"
        logger.info("Bot '%s' was stopped cleanly.", project_id)
        return True

    async def spawn_bot(
        self,
        project_id: str,
        bot_token: str,
        token_address: str,
        group_id: Optional[str] = None,
        token_symbol: Optional[str] = None,
        name: Optional[str] = None,
        knowledge_base: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically configure and launch a supervised bot poller."""
        # 1. Validation
        if not PROJECT_ID_PATTERN.match(project_id):
            raise ValueError(f"Invalid project_id '{project_id}'. Must match ^[a-z0-9-]{{3,40}}$")
        if not BOT_TOKEN_PATTERN.match(bot_token):
            raise ValueError("Invalid bot_token format.")
        if not TOKEN_ADDRESS_PATTERN.match(token_address):
            raise ValueError("Invalid token_address format.")

        norm_group = group_id.strip() if group_id and group_id.strip() else ""
        if not norm_group:
            logger.warning("[SPAWN WARNING] Bot '%s' spawned in unlocked mode (no group_id assigned).", project_id)

        # 2. Idempotency: if already running with same token and group, return existing status
        if project_id in self.tasks and not self.tasks[project_id].done():
            existing_cfg = self.configs.get(project_id, {})
            existing_group = str(existing_cfg.get("telegram", {}).get("group_id", ""))
            if existing_group == norm_group and self.statuses.get(project_id) == "running":
                logger.info("Bot '%s' is already running with matching configuration.", project_id)
                return self.get_status(project_id)
            # Otherwise stop existing to restart with new parameters
            logger.info("Restarting bot '%s' with updated parameters...", project_id)
            await self.stop_bot(project_id)

        # 3. Prepare Config Dictionaries
        proj_name = name.strip() if name and name.strip() else project_id
        symbol = token_symbol.strip() if token_symbol and token_symbol.strip() else "$TOKEN"
        if not symbol.startswith("$"):
            symbol = f"${symbol}"

        config_data = {
            "project": {
                "id": project_id,
                "name": proj_name,
                "active": 1,
            },
            "telegram": {
                "group_id": norm_group,
                "poll_interval_seconds": 0.1,
            },
            "token": {
                "symbol": symbol,
                "address": token_address.strip(),
                "chain": "solana" if not token_address.startswith("0x") else "evm",
            },
        }

        secrets_data = {
            "bot_token": bot_token.strip(),
            "hmac_key": f"zoe_{project_id}_hmac_secret_key_32_characters_minimum",
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        }

        # 4. Atomic file creation (temp file + os.replace)
        config_dir = Path("config/projects")
        secrets_dir = Path("config/secrets")
        config_dir.mkdir(parents=True, exist_ok=True)
        secrets_dir.mkdir(parents=True, exist_ok=True)

        cfg_target = config_dir / f"{project_id}.yaml"
        sec_target = secrets_dir / f"{project_id}.secrets.yaml"

        files_written = []
        try:
            # Write config YAML atomically
            with tempfile.NamedTemporaryFile("w", dir=config_dir, delete=False, encoding="utf-8") as tf:
                yaml.dump(config_data, tf)
                temp_cfg = Path(tf.name)
            os.replace(temp_cfg, cfg_target)
            files_written.append(cfg_target)

            # Write secrets YAML atomically with 0600 permissions
            with tempfile.NamedTemporaryFile("w", dir=secrets_dir, delete=False, encoding="utf-8") as tf:
                yaml.dump(secrets_data, tf)
                temp_sec = Path(tf.name)
            try:
                os.chmod(temp_sec, 0o600)
            except Exception:
                pass
            os.replace(temp_sec, sec_target)
            files_written.append(sec_target)
        except Exception as write_err:
            # Rollback any written files on disk failure
            for f in files_written:
                if f.exists():
                    f.unlink()
            raise RuntimeError(f"Failed to atomically persist bot configs: {write_err}")

        # 5. Handle optional Knowledge Base text (asynchronous ingestion)
        from zoe.settings import get_data_dir
        data_dir = get_data_dir()
        if knowledge_base and knowledge_base.strip():
            kb_dir = data_dir / "knowledge"
            kb_dir.mkdir(parents=True, exist_ok=True)
            kb_file = kb_dir / f"{project_id}_info.txt"
            with open(kb_file, "w", encoding="utf-8") as f:
                f.write(knowledge_base.strip())

            self.ingestion_statuses[project_id] = "ingesting"
            asyncio.create_task(self._run_bg_ingest(project_id, kb_file))

        # 6. Instantiate and Launch Supervised Poller
        self.statuses[project_id] = "starting"
        self.errors[project_id] = None
        self.started_at[project_id] = datetime.now(timezone.utc).isoformat()
        self.configs[project_id] = config_data

        shutdown_ev = asyncio.Event()
        self.shutdown_events[project_id] = shutdown_ev

        # Launch supervisor task in background
        task = asyncio.create_task(
            self._supervisor_loop(
                project_id=project_id,
                config_data=config_data,
                secrets_data=secrets_data,
                shutdown_event=shutdown_ev,
            )
        )
        self.tasks[project_id] = task

        logger.info(
            "Bot '%s' spawned successfully with token %s and group '%s'.",
            project_id,
            redact_token(bot_token),
            norm_group,
        )
        return self.get_status(project_id)

    async def _run_bg_ingest(self, project_id: str, doc_path: Path) -> None:
        """Run knowledge ingestion in background without blocking bot startup."""
        try:
            from zoe.knowledge.ingestion import ingest_document
            from zoe.settings import get_data_dir
            d_dir = get_data_dir()
            res = await asyncio.to_thread(
                ingest_document,
                filepath=doc_path,
                project_id=project_id,
                db_path=d_dir / "official_knowledge" / "official_knowledge.db",
                index_dir=d_dir / "indexes",
                model=self.shared_model,
            )
            self.ingestion_statuses[project_id] = f"indexed ({res.chunk_count} chunks)"
            logger.info("Background ingestion completed for '%s': %d chunks.", project_id, res.chunk_count)
        except Exception as exc:
            self.ingestion_statuses[project_id] = f"error: {str(exc)}"
            logger.error("Background ingestion failed for '%s': %s", project_id, exc)

    async def _supervisor_loop(
        self,
        project_id: str,
        config_data: Dict[str, Any],
        secrets_data: Dict[str, Any],
        shutdown_event: asyncio.Event,
    ) -> None:
        """Supervised polling loop with exponential backoff and crash recovery."""
        from scripts.run_all_bots import BotInstance, run_bot_worker
        from zoe.db.connections import (
            open_community_memory_db,
            open_official_knowledge_db,
            open_operational_db,
        )
        from zoe.inbox.inbox_service import ensure_project_registered
        from zoe.llm.factory import get_llm_client
        from zoe.settings import get_data_dir
        from zoe.telegram.adapter import PTBTelegramAdapter

        data_dir = get_data_dir()
        retries = 0
        max_retries = 10
        delay = 2.0

        while not shutdown_event.is_set() and retries < max_retries:
            db_conns = {}
            try:
                # Open isolated DB connections
                db_conns["operational"] = open_operational_db(data_dir / "operational" / "operational.db")
                db_conns["knowledge"] = open_official_knowledge_db(data_dir / "official_knowledge" / "official_knowledge.db")
                db_conns["community_memory"] = open_community_memory_db(data_dir / "community_memory" / "community_memory.db")

                ensure_project_registered(
                    db_conns["operational"],
                    project_id=project_id,
                    name=config_data.get("project", {}).get("name", project_id),
                    telegram_group_id=str(config_data.get("telegram", {}).get("group_id", "")),
                )

                adapter = PTBTelegramAdapter(
                    bot_token=secrets_data["bot_token"],
                    hmac_key=secrets_data["hmac_key"],
                    poll_interval=float(config_data.get("telegram", {}).get("poll_interval_seconds", 0.1)),
                )
                await adapter.start()

                llm = get_llm_client(project_id)

                instance = BotInstance(
                    project_id=project_id,
                    config=config_data,
                    secrets=secrets_data,
                    db_conns=db_conns,
                    adapter=adapter,
                    llm_client=llm,
                    model=self.shared_model,
                )

                self.statuses[project_id] = "running"
                self.errors[project_id] = None
                retries = 0  # reset retries on successful connection

                await run_bot_worker(instance, shutdown_event)

                await adapter.stop()
                break  # Normal shutdown
            except asyncio.CancelledError:
                break
            except Exception as exc:
                retries += 1
                self.statuses[project_id] = "error"
                self.errors[project_id] = str(exc)
                logger.error(
                    "Bot supervisor caught error in '%s' (attempt %d/%d): %s. Backing off %.1fs...",
                    project_id,
                    retries,
                    max_retries,
                    exc,
                    delay,
                )
                try:
                    await asyncio.wait_for(shutdown_event.wait(), timeout=delay)
                    break
                except asyncio.TimeoutError:
                    pass
                delay = min(delay * 2.0, 60.0)
            finally:
                for conn in db_conns.values():
                    try:
                        conn.close()
                    except Exception:
                        pass

        if retries >= max_retries:
            self.statuses[project_id] = "error"
            logger.critical("Bot '%s' exceeded max crash retries (%d). Supervisor stopped.", project_id, max_retries)
        else:
            self.statuses[project_id] = "stopped"


# Global singleton instance managed by run_all_bots orchestrator
bot_manager = BotManager()

# --- Engine FastAPI Application ---
engine_app = FastAPI(title="Zoe Bot Engine Internal API", version="1.0.0")


def verify_engine_key(x_engine_key: Optional[str] = Header(None, alias="X-Engine-Key")) -> None:
    """Validate inter-service authentication secret."""
    secret = os.getenv("ENGINE_SHARED_SECRET", "").strip()
    if not secret:
        # If no secret is configured in local dev, allow request with security warning
        logger.warning("ENGINE_SHARED_SECRET is not configured! Engine API is unprotected.")
        return

    if not x_engine_key or not hmac.compare_digest(x_engine_key.strip(), secret):
        logger.warning("Unauthorized Engine API request rejected (invalid X-Engine-Key).")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Engine-Key header",
        )


@engine_app.get("/health")
def health() -> Dict[str, Any]:
    """Engine health status and bot counts."""
    statuses = bot_manager.get_all_statuses()
    running_count = sum(1 for s in statuses if s["status"] == "running")
    return {
        "status": "ok",
        "active_bots": running_count,
        "total_bots": len(statuses),
        "bots": [s["project_id"] for s in statuses],
    }


@engine_app.get("/api/bots/{project_id}/status", response_model=BotStatusResponse, dependencies=[Depends(verify_engine_key)])
def get_bot_status(project_id: str) -> Dict[str, Any]:
    """Retrieve runtime state and telemetry for a specific bot."""
    if not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project_id pattern")
    return bot_manager.get_status(project_id)


@engine_app.post("/api/spawn-bot", response_model=BotStatusResponse, dependencies=[Depends(verify_engine_key)])
async def spawn_bot_endpoint(req: SpawnBotRequest) -> Dict[str, Any]:
    """Spawn or update a live bot instance dynamically."""
    try:
        res = await bot_manager.spawn_bot(
            project_id=req.project_id,
            bot_token=req.bot_token,
            token_address=req.token_address,
            group_id=req.group_id,
            token_symbol=req.token_symbol,
            name=req.name,
            knowledge_base=req.knowledge_base,
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@engine_app.patch("/api/bots/{project_id}", response_model=BotStatusResponse, dependencies=[Depends(verify_engine_key)])
async def patch_bot_endpoint(project_id: str, req: PatchBotRequest) -> Dict[str, Any]:
    """Hot-reload bot configuration (e.g. locking group_id or changing token_address)."""
    if not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project_id pattern")

    cfg_file = Path(f"config/projects/{project_id}.yaml")
    sec_file = Path(f"config/secrets/{project_id}.secrets.yaml")
    if not cfg_file.exists() or not sec_file.exists():
        raise HTTPException(status_code=404, detail=f"Bot '{project_id}' not found")

    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    with open(sec_file, "r", encoding="utf-8") as f:
        sec = yaml.safe_load(f) or {}

    if req.group_id is not None:
        cfg.setdefault("telegram", {})["group_id"] = req.group_id.strip()
    if req.token_address is not None:
        cfg.setdefault("token", {})["address"] = req.token_address.strip()

    # Re-save YAML
    with open(cfg_file, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    # Spawn/restart bot with updated parameters
    res = await bot_manager.spawn_bot(
        project_id=project_id,
        bot_token=sec.get("bot_token", ""),
        token_address=cfg.get("token", {}).get("address", ""),
        group_id=cfg.get("telegram", {}).get("group_id"),
        token_symbol=cfg.get("token", {}).get("symbol"),
        name=cfg.get("project", {}).get("name"),
    )
    return res


@engine_app.delete("/api/bots/{project_id}", dependencies=[Depends(verify_engine_key)])
async def delete_bot_endpoint(project_id: str) -> Dict[str, Any]:
    """Stop bot and remove secrets configuration."""
    if not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project_id pattern")

    await bot_manager.stop_bot(project_id)

    # Remove secrets to ensure safe decommissioning
    sec_file = Path(f"config/secrets/{project_id}.secrets.yaml")
    if sec_file.exists():
        try:
            sec_file.unlink()
        except Exception:
            pass

    return {"project_id": project_id, "status": "stopped", "message": "Bot stopped and secrets purged"}
