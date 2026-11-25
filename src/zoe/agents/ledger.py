"""Internal Agent Ledger & Micro-Transaction System (Pillar 3 & 4).

Enables autonomous agents to bill and spend user credits when invoking
premium intelligence tools (Scanner, X Intel, OSINT, Web Search) and
records every micro-transaction for the Super Admin Agent Revenue Ledger.
"""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional
import uuid

from zoe.billing.credit_manager import CreditManager

logger = logging.getLogger("zoe.agents.ledger")

_LEDGER_LOCK = threading.Lock()
_LAST_LEDGER_ALERT: Dict[str, str] = {}
_IN_MEMORY_LEDGER: List[Dict[str, Any]] = []


def _get_dev_db_path() -> Path:
    env_dir = os.getenv("DATA_DIR", "").strip()
    if env_dir:
        return Path(env_dir) / "saas_dev.db"
    root = Path(__file__).resolve().parent.parent.parent.parent
    candidate = root / "saas-dashboard" / "backend" / "saas_dev.db"
    if candidate.exists():
        return candidate
    return root / "data" / "saas_dev.db"


def _ensure_ledger_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_agent_ledger (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            credit_cost INTEGER NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dev_agent_ledger_created ON dev_agent_ledger(created_at DESC)"
    )
    conn.commit()


def _resolve_billing_user_id(project_id: str, user_id: Optional[str] = None) -> str:
    """Resolve the owner/user ID to bill for an agent tool call."""
    if user_id and str(user_id).strip():
        return str(user_id).strip()

    try:
        db_path = _get_dev_db_path()
        if db_path.exists():
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            cur = conn.execute(
                "SELECT owner_id FROM dev_projects WHERE id = ? OR name = ?",
                (str(project_id), str(project_id)),
            )
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return str(row[0])
    except Exception:
        pass

    return f"project:{project_id}"


def _record_ledger_entry(
    project_id: str,
    user_id: str,
    agent_name: str,
    tool_name: str,
    credit_cost: int,
    status: str,
    message: str,
) -> Dict[str, Any]:
    """Persist an agent micro-transaction to SQLite and memory ring buffer."""
    entry = {
        "id": f"agl_{uuid.uuid4().hex[:12]}",
        "project_id": str(project_id),
        "user_id": str(user_id),
        "agent_name": agent_name,
        "tool_name": tool_name,
        "credit_cost": int(credit_cost),
        "status": status,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with _LEDGER_LOCK:
        _IN_MEMORY_LEDGER.insert(0, entry)
        if len(_IN_MEMORY_LEDGER) > 100:
            _IN_MEMORY_LEDGER.pop()

    try:
        db_path = _get_dev_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        _ensure_ledger_table(conn)
        conn.execute(
            """
            INSERT INTO dev_agent_ledger (
                id, project_id, user_id, agent_name, tool_name, credit_cost, status, message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry["id"],
                entry["project_id"],
                entry["user_id"],
                entry["agent_name"],
                entry["tool_name"],
                entry["credit_cost"],
                entry["status"],
                entry["message"],
                entry["created_at"],
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.debug("Could not persist dev_agent_ledger row: %s", exc)

    return entry


def get_last_ledger_alert(project_id: str) -> Optional[str]:
    """Retrieve the most recent insufficient-credit alert for a project."""
    with _LEDGER_LOCK:
        return _LAST_LEDGER_ALERT.get(str(project_id))


def get_agent_ledger_entries(limit: int = 25) -> List[Dict[str, Any]]:
    """Return recent agent-to-tool micro-transactions for the Super Admin Ledger."""
    try:
        db_path = _get_dev_db_path()
        if db_path.exists():
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            _ensure_ledger_table(conn)
            cur = conn.execute(
                """
                SELECT id, project_id, user_id, agent_name, tool_name, credit_cost, status, message, created_at
                FROM dev_agent_ledger
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = [
                {
                    "id": str(r[0]),
                    "project_id": str(r[1]),
                    "user_id": str(r[2]),
                    "agent_name": str(r[3]),
                    "tool_name": str(r[4]),
                    "credit_cost": int(r[5]),
                    "status": str(r[6]),
                    "message": str(r[7]),
                    "created_at": str(r[8]),
                }
                for r in cur.fetchall()
            ]
            conn.close()
            if rows:
                return rows
    except Exception as exc:
        logger.debug("Failed to query dev_agent_ledger: %s", exc)

    with _LEDGER_LOCK:
        return list(_IN_MEMORY_LEDGER[:limit])


async def charge_user_for_tool(
    project_id: str,
    tool_name: str,
    credit_cost: int,
    agent_name: str = "Research Agent",
    user_id: Optional[str] = None,
) -> bool:
    """Charge a user/project owner atomically before an agent executes a premium tool.

    Returns True if authorized and charged; returns False and records an alert if insufficient credits.
    """
    if credit_cost < 0:
        return False

    billing_uid = _resolve_billing_user_id(project_id, user_id=user_id)
    ok, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=billing_uid,
        amount=credit_cost,
        action_type=f"agent_tool_{tool_name}",
        metadata={
            "project_id": str(project_id),
            "agent_name": agent_name,
            "tool_name": tool_name,
        },
    )

    if ok:
        summary = f"{agent_name} charged {credit_cost} credits for {tool_name}"
        _record_ledger_entry(
            project_id=str(project_id),
            user_id=billing_uid,
            agent_name=agent_name,
            tool_name=tool_name,
            credit_cost=credit_cost,
            status="charged",
            message=summary,
        )
        with _LEDGER_LOCK:
            _LAST_LEDGER_ALERT.pop(str(project_id), None)
        return True

    alert_msg = f"🔒 Insufficient credits. The {agent_name} needs {credit_cost} credits to access live {tool_name} data."
    logger.warning("Agent ledger blocked %s -> %s for %s: %s", agent_name, tool_name, billing_uid, msg)
    _record_ledger_entry(
        project_id=str(project_id),
        user_id=billing_uid,
        agent_name=agent_name,
        tool_name=tool_name,
        credit_cost=credit_cost,
        status="blocked",
        message=alert_msg,
    )
    with _LEDGER_LOCK:
        _LAST_LEDGER_ALERT[str(project_id)] = alert_msg
    return False
