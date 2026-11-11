"""Database connections and retry utilities for SQLite concurrency."""

import functools
import os
import random
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, TypeVar, Union

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
