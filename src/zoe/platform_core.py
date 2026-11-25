"""Shared Platform Core: Audit Logs, Organization Team RBAC, Invoices, NFT Growth, Investor Intelligence & Scheduler Lock."""

from datetime import datetime, timedelta, timezone
import json
import logging
import sqlite3
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger("zoe.platform_core")


def ensure_platform_core_schema(conn: sqlite3.Connection) -> None:
    """Create platform_core tables if they do not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            actor_email TEXT,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_members (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            owner_user_id TEXT NOT NULL,
            member_email TEXT NOT NULL,
            member_user_id TEXT,
            role TEXT NOT NULL DEFAULT 'viewer',
            status TEXT NOT NULL DEFAULT 'invited',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(organization_id, member_email)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_org_mem_owner ON organization_members(owner_user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            amount_usdt REAL NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'paid',
            reference_tx TEXT,
            issued_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nft_collections (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            chain TEXT NOT NULL DEFAULT 'solana',
            contract_address TEXT NOT NULL DEFAULT '',
            name TEXT NOT NULL,
            symbol TEXT NOT NULL DEFAULT '',
            mint_campaign_name TEXT NOT NULL DEFAULT '',
            mint_status TEXT NOT NULL DEFAULT 'planned',
            verified_floor_price REAL,
            verified_sales_count INTEGER NOT NULL DEFAULT 0,
            referral_code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nft_col_user ON nft_collections(user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nft_buyer_leads (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            collection_id TEXT,
            handle_or_wallet TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'community_opt_in',
            status TEXT NOT NULL DEFAULT 'new',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS investor_pipelines (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            investor_name TEXT NOT NULL,
            firm_type TEXT NOT NULL DEFAULT 'vc',
            stage TEXT NOT NULL DEFAULT 'research',
            focus_sectors TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            last_contacted_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_inv_pipe_user ON investor_pipelines(user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_provider_configs (
            id TEXT PRIMARY KEY,
            primary_provider TEXT NOT NULL DEFAULT 'groq',
            fallback_provider TEXT NOT NULL DEFAULT 'gemini',
            default_model TEXT NOT NULL DEFAULT 'llama-3.3-70b-versatile',
            max_tokens INTEGER NOT NULL DEFAULT 1024,
            updated_by TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO ai_provider_configs (id, primary_provider, fallback_provider, default_model, max_tokens, updated_by, updated_at)
        VALUES ('global', 'groq', 'gemini', 'llama-3.3-70b-versatile', 1024, 'system', ?)
        """,
        (now_iso,),
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduler_locks (
            job_name TEXT PRIMARY KEY,
            locked_until TEXT NOT NULL,
            worker_id TEXT NOT NULL
        )
        """
    )
    conn.commit()


def record_audit_log(
    conn: sqlite3.Connection,
    actor_id: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    actor_email: Optional[str] = None,
) -> str:
    """Append an immutable audit log entry."""
    ensure_platform_core_schema(conn)
    log_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO audit_logs (id, actor_id, actor_email, actor_role, action, target_type, target_id, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            str(actor_id),
            actor_email,
            str(actor_role),
            action,
            target_type,
            target_id,
            json.dumps(details or {}),
            now_iso,
        ),
    )
    conn.commit()
    return log_id


def acquire_scheduler_lock(
    conn: sqlite3.Connection,
    job_name: str,
    worker_id: str = "worker-1",
    ttl_seconds: int = 60,
) -> bool:
    """Acquire an idempotent lease lock to prevent duplicate scheduled job runs across workers."""
    ensure_platform_core_schema(conn)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    until_iso = (now + timedelta(seconds=max(5, int(ttl_seconds)))).isoformat()

    row = conn.execute(
        "SELECT locked_until, worker_id FROM scheduler_locks WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row and str(row[0]) > now_iso and str(row[1]) != worker_id:
        return False

    conn.execute(
        """
        INSERT INTO scheduler_locks (job_name, locked_until, worker_id)
        VALUES (?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            locked_until = excluded.locked_until,
            worker_id = excluded.worker_id
        """,
        (job_name, until_iso, worker_id),
    )
    conn.commit()
    return True
