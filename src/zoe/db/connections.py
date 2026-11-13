"""Database connections and retry utilities for SQLite concurrency."""

import functools
import os
import random
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

from zoe.utils.logging import get_logger

logger = get_logger("zoe.db.connections")

F = TypeVar("F", bound=Callable[..., Any])


def with_db_retry(
    max_retries: int = 5,
    initial_delay: float = 0.05,
    backoff_factor: float = 2.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """Decorator retrying database operations on sqlite3.OperationalError (locks/busy)."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as exc:
                    err_msg = str(exc).lower()
                    # Retry on locked or busy database conditions
                    if "locked" in err_msg or "busy" in err_msg:
                        last_exc = exc
                        sleep_time = delay * (1 + random.uniform(0, 0.5)) if jitter else delay
                        logger.warning(
                            "Database locked in %s (attempt %d/%d). Retrying in %.3fs...",
                            func.__name__,
                            attempt,
                            max_retries,
                            sleep_time,
                        )
                        time.sleep(sleep_time)
                        delay *= backoff_factor
                    else:
                        raise
            if last_exc:
                raise last_exc

        return wrapper  # type: ignore

    return decorator


def _configure_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")  # 10s wait before busy
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _ensure_parent_dir(path: Union[str, Path]) -> None:
    target_path = Path(path)
    if target_path.parent:
        target_path.parent.mkdir(parents=True, exist_ok=True)


def open_operational_db(path: Union[str, Path]) -> sqlite3.Connection:
    _ensure_parent_dir(path)
    conn = sqlite3.connect(str(path))
    conn = _configure_connection(conn)
    # Ensure operational schema exists on fresh environments (Docker/Cloud)
    try:
        schema_path = Path(__file__).resolve().parent / "schema_operational.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
    except Exception:
        pass
    try:
        cur = conn.execute("PRAGMA table_info(outbox_messages)")
        cols = [r[1] for r in cur.fetchall()]
        if cols and "inline_keyboard_json" not in cols:
            conn.execute("ALTER TABLE outbox_messages ADD COLUMN inline_keyboard_json TEXT")
            conn.commit()
    except Exception:
        pass
    return conn


def open_official_knowledge_db(path: Union[str, Path]) -> sqlite3.Connection:
    _ensure_parent_dir(path)
    conn = sqlite3.connect(str(path))
    conn = _configure_connection(conn)
    try:
        schema_path = Path(__file__).resolve().parent / "schema_knowledge.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
    except Exception:
        pass
    return conn


def open_community_memory_db(path: Union[str, Path]) -> sqlite3.Connection:
    _ensure_parent_dir(path)
    conn = sqlite3.connect(str(path))
    conn = _configure_connection(conn)
    try:
        schema_path = Path(__file__).resolve().parent / "schema_community_memory.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
    except Exception:
        pass
    return conn


def get_data_dir() -> Path:
    """Return root data directory, prioritizing DATA_DIR env var (e.g. mounted Railway volume)."""
    env_dir = os.getenv("DATA_DIR")
    if env_dir and env_dir.strip():
        p = Path(env_dir.strip())
        p.mkdir(parents=True, exist_ok=True)
        return p
    return Path("data")


def _seed_knowledge_docs_if_needed(base: Path) -> None:
    """Seed baseline knowledge files to the data directory if not already present."""
    target_knowledge = base / "knowledge"
    target_knowledge.mkdir(parents=True, exist_ok=True)

    candidates = [
        Path("data/knowledge"),
        Path("/app/data/knowledge"),
        Path(__file__).resolve().parent.parent.parent / "data" / "knowledge",
    ]
    import shutil
    for src in candidates:
        if src.exists():
            try:
                if src.resolve() == target_knowledge.resolve():
                    continue
            except Exception:
                pass
            for f in src.glob("*.txt"):
                dest = target_knowledge / f.name
                if not dest.exists():
                    try:
                        shutil.copy2(f, dest)
                        logger.info("Seeded baseline knowledge document %s to %s", f.name, dest)
                    except Exception as err:
                        logger.warning("Could not seed %s to %s: %s", f, dest, err)
            break


def ensure_databases_initialized(base_dir: Optional[Union[str, Path]] = None) -> None:
    """Check and ensure that operational, knowledge, and community SQLite databases exist with schemas applied."""
    if base_dir is None:
        base = get_data_dir()
    else:
        env_dir = os.getenv("DATA_DIR")
        if env_dir and env_dir.strip() and str(base_dir) == "data":
            base = Path(env_dir.strip())
        else:
            base = Path(base_dir)

    base.mkdir(parents=True, exist_ok=True)
    _seed_knowledge_docs_if_needed(base)

    op_path = base / "operational" / "operational.db"
    kb_path = base / "official_knowledge" / "official_knowledge.db"
    mem_path = base / "community_memory" / "community_memory.db"

    logger.info("Verifying and auto-initializing SQLite databases at %s...", base)
    conn1 = open_operational_db(op_path)
    conn1.close()
    conn2 = open_official_knowledge_db(kb_path)
    conn2.close()
    conn3 = open_community_memory_db(mem_path)
    conn3.close()
    logger.info("SQLite databases verified at operational.db, official_knowledge.db, and community_memory.db.")
