"""Custom Price Alerts and Wallet Following Engine (Phase 4).

Manages custom target price triggers (above/below), whale wallet transaction following,
and persistent alerts storage with Supabase RLS and SQLite fallback.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import uuid

import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.alerts")


def get_alerts_db_conn() -> sqlite3.Connection:
    """Connect to local sqlite fallback database and ensure alert tables exist."""
    db_path = Path("saas-dashboard/backend/dev_db.sqlite")
    if not db_path.exists():
        alt_path = Path("dev_db.sqlite")
        if alt_path.exists():
            db_path = alt_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_price_alerts (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            telegram_user_id TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            target_price REAL NOT NULL,
            direction TEXT CHECK (direction IN ('above', 'below')),
            token_name TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_wallet_follows (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            telegram_user_id TEXT NOT NULL,
            wallet_address TEXT NOT NULL,
            last_tx_signature TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(project_id, telegram_user_id, wallet_address)
        )
        """
    )
    conn.commit()
    return conn


def get_supabase_client():
    """Retrieve Supabase client if configured."""
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if url and key and "placeholder" not in url:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception as exc:
            logger.debug("Supabase init failed in alerts: %s", exc)
    return None


def add_price_alert(
    project_id: str,
    telegram_user_id: str,
    contract_address: str,
    target_price: float,
    direction: str,
    token_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a new custom price alert for a user."""
    clean_ca = contract_address.strip()
    clean_uid = str(telegram_user_id).strip()
    clean_dir = direction.strip().lower()
    if clean_dir not in ("above", "below"):
        clean_dir = "above"
    name = token_name or "Token"
    alert_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "id": alert_id,
        "project_id": project_id,
        "telegram_user_id": clean_uid,
        "contract_address": clean_ca,
        "target_price": float(target_price),
        "direction": clean_dir,
        "token_name": name,
        "active": True,
        "created_at": now_iso,
    }

    sb_client = get_supabase_client()
    if sb_client:
        try:
            sb_client.table("price_alerts").insert({
                "id": alert_id,
                "project_id": project_id,
                "telegram_user_id": clean_uid,
                "contract_address": clean_ca,
                "target_price": float(target_price),
                "direction": clean_dir,
                "active": True,
                "created_at": now_iso,
            }).execute()
        except Exception as exc:
            logger.debug("Supabase price_alerts insert error: %s", exc)

    conn = get_alerts_db_conn()
    try:
        conn.execute(
            """
            INSERT INTO dev_price_alerts (id, project_id, telegram_user_id, contract_address, target_price, direction, token_name, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (alert_id, project_id, clean_uid, clean_ca, float(target_price), clean_dir, name, now_iso),
        )
        conn.commit()
    except Exception as exc:
        logger.debug("Dev DB price_alerts insert error: %s", exc)

    logger.info("Added price alert %s for user %s on %s %s $%.4f", alert_id, clean_uid, clean_ca, clean_dir, target_price)
    return record


def deactivate_price_alerts(
    project_id: str,
    telegram_user_id: str,
    contract_address: str,
) -> int:
    """Deactivate price alerts for a specific user and contract address."""
    clean_ca = contract_address.strip()
    clean_uid = str(telegram_user_id).strip()
    deactivated = 0

    sb_client = get_supabase_client()
    if sb_client:
        try:
            sb_client.table("price_alerts").update({"active": False}).eq("project_id", project_id).eq("telegram_user_id", clean_uid).eq("contract_address", clean_ca).execute()
        except Exception as exc:
            logger.debug("Supabase deactivate price_alerts error: %s", exc)

    conn = get_alerts_db_conn()
    try:
        cur = conn.execute(
            "UPDATE dev_price_alerts SET active = 0 WHERE project_id = ? AND telegram_user_id = ? AND contract_address = ? AND active = 1",
            (project_id, clean_uid, clean_ca),
        )
        deactivated = cur.rowcount
        conn.commit()
    except Exception as exc:
        logger.debug("Dev DB deactivate price_alerts error: %s", exc)

    return deactivated


def add_wallet_follow(
    project_id: str,
    telegram_user_id: str,
    wallet_address: str,
) -> Dict[str, Any]:
    """Register a new wallet follow target for a user."""
    clean_w = wallet_address.strip()
    clean_uid = str(telegram_user_id).strip()
    follow_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "id": follow_id,
        "project_id": project_id,
        "telegram_user_id": clean_uid,
        "wallet_address": clean_w,
        "last_tx_signature": None,
        "active": True,
        "created_at": now_iso,
    }

    sb_client = get_supabase_client()
    if sb_client:
        try:
            sb_client.table("wallet_follows").upsert({
                "project_id": project_id,
                "telegram_user_id": clean_uid,
                "wallet_address": clean_w,
                "active": True,
                "created_at": now_iso,
            }, on_conflict="project_id,telegram_user_id,wallet_address").execute()
        except Exception as exc:
            logger.debug("Supabase wallet_follows upsert error: %s", exc)

    conn = get_alerts_db_conn()
    try:
        conn.execute(
            """
            INSERT INTO dev_wallet_follows (id, project_id, telegram_user_id, wallet_address, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(project_id, telegram_user_id, wallet_address) DO UPDATE SET active = 1
            """,
            (follow_id, project_id, clean_uid, clean_w, now_iso),
        )
        conn.commit()
    except Exception as exc:
        logger.debug("Dev DB wallet_follows upsert error: %s", exc)

    logger.info("Added wallet follow for user %s on wallet %s", clean_uid, clean_w)
    return record


def deactivate_wallet_follow(
    project_id: str,
    telegram_user_id: str,
    wallet_address: str,
) -> int:
    """Deactivate wallet follow for a user and wallet."""
    clean_w = wallet_address.strip()
    clean_uid = str(telegram_user_id).strip()
    deactivated = 0

    sb_client = get_supabase_client()
    if sb_client:
        try:
            sb_client.table("wallet_follows").update({"active": False}).eq("project_id", project_id).eq("telegram_user_id", clean_uid).eq("wallet_address", clean_w).execute()
        except Exception as exc:
            logger.debug("Supabase deactivate wallet_follows error: %s", exc)

    conn = get_alerts_db_conn()
    try:
        cur = conn.execute(
            "UPDATE dev_wallet_follows SET active = 0 WHERE project_id = ? AND telegram_user_id = ? AND wallet_address = ? AND active = 1",
            (project_id, clean_uid, clean_w),
        )
        deactivated = cur.rowcount
        conn.commit()
    except Exception as exc:
        logger.debug("Dev DB deactivate wallet_follows error: %s", exc)

    return deactivated


def get_active_price_alerts() -> List[Dict[str, Any]]:
    """Query all active custom price alerts."""
    alerts: List[Dict[str, Any]] = []
    sb_client = get_supabase_client()
    if sb_client:
        try:
            res = sb_client.table("price_alerts").select("*").eq("active", True).execute()
            if res.data:
                alerts = res.data
        except Exception as exc:
            logger.debug("Supabase active price_alerts error: %s", exc)

    if not alerts:
        conn = get_alerts_db_conn()
        try:
            cur = conn.execute(
                "SELECT id, project_id, telegram_user_id, contract_address, target_price, direction, token_name FROM dev_price_alerts WHERE active = 1"
            )
            for r in cur.fetchall():
                alerts.append({
                    "id": r[0],
                    "project_id": r[1],
                    "telegram_user_id": r[2],
                    "contract_address": r[3],
                    "target_price": float(r[4]),
                    "direction": r[5],
                    "token_name": r[6] or "Token",
                })
        except Exception as exc:
            logger.debug("Dev DB active price_alerts error: %s", exc)

    return alerts


def mark_price_alert_triggered(alert_id: str) -> None:
    """Deactivate price alert after it fires."""
    sb_client = get_supabase_client()
    if sb_client:
        try:
            sb_client.table("price_alerts").update({"active": False}).eq("id", alert_id).execute()
        except Exception:
            pass

    conn = get_alerts_db_conn()
    try:
        conn.execute("UPDATE dev_price_alerts SET active = 0 WHERE id = ?", (alert_id,))
        conn.commit()
    except Exception:
        pass


def get_active_wallet_follows() -> List[Dict[str, Any]]:
    """Query all active wallet follows."""
    follows: List[Dict[str, Any]] = []
    sb_client = get_supabase_client()
    if sb_client:
        try:
            res = sb_client.table("wallet_follows").select("*").eq("active", True).execute()
            if res.data:
                follows = res.data
        except Exception as exc:
            logger.debug("Supabase active wallet_follows error: %s", exc)

    if not follows:
        conn = get_alerts_db_conn()
        try:
            cur = conn.execute(
                "SELECT id, project_id, telegram_user_id, wallet_address, last_tx_signature FROM dev_wallet_follows WHERE active = 1"
            )
            for r in cur.fetchall():
                follows.append({
                    "id": r[0],
                    "project_id": r[1],
                    "telegram_user_id": r[2],
                    "wallet_address": r[3],
                    "last_tx_signature": r[4],
                })
        except Exception as exc:
            logger.debug("Dev DB active wallet_follows error: %s", exc)

    return follows


def update_wallet_follow_signature(follow_id: str, signature: str) -> None:
    """Update last seen signature for a wallet follow."""
    sb_client = get_supabase_client()
    if sb_client:
        try:
            sb_client.table("wallet_follows").update({"last_tx_signature": signature}).eq("id", follow_id).execute()
        except Exception:
            pass

    conn = get_alerts_db_conn()
    try:
        conn.execute("UPDATE dev_wallet_follows SET last_tx_signature = ? WHERE id = ?", (signature, follow_id))
        conn.commit()
    except Exception:
        pass
