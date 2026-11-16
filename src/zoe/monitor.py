"""Continuous Monitoring Worker for Zoe Watchlist & Liquidity Alerts (Mega-Module 5).

Runs periodic background audit loops (every 15 minutes) checking all watched tokens
against DexScreener for sudden liquidity drain (>20% drop) and price crashes.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

import httpx

from zoe.tools.scanner import fetch_dexscreener_market_data
from zoe.utils.logging import get_logger

logger = get_logger("zoe.monitor")


def get_dev_db_conn() -> sqlite3.Connection:
    """Connect to local sqlite fallback database."""
    db_path = Path("saas-dashboard/backend/dev_db.sqlite")
    if not db_path.exists():
        # Check backend relative path
        alt_path = Path("dev_db.sqlite")
        if alt_path.exists():
            db_path = alt_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_watchlists (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            token_name TEXT,
            initial_liquidity REAL,
            initial_price REAL,
            last_checked_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, contract_address)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_alerts (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            contract_address TEXT NOT NULL,
            token_name TEXT,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            old_value REAL,
            new_value REAL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def get_supabase_client():
    """Retrieve Supabase client if environment credentials exist."""
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if url and key and "placeholder" not in url:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception as exc:
            logger.debug("Supabase init failed in monitor: %s", exc)
    return None


async def check_watchlist_tokens() -> List[Dict[str, Any]]:
    """Scan all watchlisted tokens for liquidity drop > 20% and trigger alerts."""
    logger.info("Starting Watchlist monitoring cycle...")
    alerts_triggered: List[Dict[str, Any]] = []
    tokens_to_check: List[Dict[str, Any]] = []

    client = get_supabase_client()
    if client:
        try:
            res = client.table("watchlists").select("*").execute()
            if res.data:
                tokens_to_check = res.data
        except Exception as exc:
            logger.warning("Failed to fetch watchlists from Supabase: %s", exc)

    if not tokens_to_check:
        try:
            conn = get_dev_db_conn()
            cur = conn.execute(
                "SELECT id, user_id, contract_address, token_name, initial_liquidity, initial_price, last_checked_at, created_at FROM dev_watchlists"
            )
            rows = cur.fetchall()
            for r in rows:
                tokens_to_check.append({
                    "id": r[0],
                    "user_id": r[1],
                    "contract_address": r[2],
                    "token_name": r[3],
                    "initial_liquidity": float(r[4]) if r[4] is not None else None,
                    "initial_price": float(r[5]) if r[5] is not None else None,
                    "last_checked_at": r[6],
                    "created_at": r[7],
                })
        except Exception as exc:
            logger.warning("Failed to fetch watchlists from dev DB: %s", exc)

    if not tokens_to_check:
        logger.info("Watchlist is empty. No tokens to monitor.")
        return []

    now_iso = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        for item in tokens_to_check:
            ca = item.get("contract_address")
            if not ca:
                continue

            name = item.get("token_name") or "Token"
            init_liq = item.get("initial_liquidity")
            init_price = item.get("initial_price")

            try:
                market = await fetch_dexscreener_market_data(ca, client=http_client)
            except Exception as exc:
                logger.warning("DexScreener fetch error for watched CA %s: %s", ca, exc)
                continue

            current_liq = market.get("liquidity_usd")
            current_price = market.get("price_usd")

            # Alert Condition: Current liquidity < 80% of initial liquidity (>20% drop)
            if init_liq and current_liq is not None and init_liq > 0:
                threshold = 0.8 * float(init_liq)
                if float(current_liq) < threshold:
                    drop_pct = ((float(init_liq) - float(current_liq)) / float(init_liq)) * 100.0
                    msg = (
                        f"🚨 LIQUIDITY DUMP DETECTED for {name} ({ca[:4]}...{ca[-4:]})! "
                        f"Initial: ${float(init_liq):,.2f} -> Current: ${float(current_liq):,.2f} (-{drop_pct:.1f}%)"
                    )
                    logger.warning("[ALERT TRIGGERED] %s", msg)

                    alert_record = {
                        "id": str(uuid.uuid4()),
                        "user_id": item.get("user_id"),
                        "contract_address": ca,
                        "token_name": name,
                        "alert_type": "LIQUIDITY_DUMP",
                        "message": msg,
                        "old_value": float(init_liq),
                        "new_value": float(current_liq),
                        "created_at": now_iso,
                    }
                    alerts_triggered.append(alert_record)

                    # Persist alert to Supabase or dev DB
                    if client:
                        try:
                            client.table("alerts").insert(alert_record).execute()
                        except Exception as exc:
                            logger.debug("Supabase alert insert failed: %s", exc)
                    try:
                        conn = get_dev_db_conn()
                        conn.execute(
                            """
                            INSERT INTO dev_alerts (id, user_id, contract_address, token_name, alert_type, message, old_value, new_value, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                alert_record["id"],
                                alert_record["user_id"],
                                ca,
                                name,
                                alert_record["alert_type"],
                                msg,
                                float(init_liq),
                                float(current_liq),
                                now_iso,
                            ),
                        )
                        conn.commit()
                    except Exception as exc:
                        logger.debug("Dev DB alert insert error: %s", exc)

            # Update last_checked_at
            if client:
                try:
                    client.table("watchlists").update({"last_checked_at": now_iso}).eq("id", item["id"]).execute()
                except Exception:
                    pass
            try:
                conn = get_dev_db_conn()
                conn.execute(
                    "UPDATE dev_watchlists SET last_checked_at = ? WHERE id = ?",
                    (now_iso, item["id"]),
                )
                conn.commit()
            except Exception:
                pass

    logger.info("Watchlist monitoring complete. %d alerts triggered.", len(alerts_triggered))
    return alerts_triggered


async def run_monitoring_loop(interval_seconds: int = 900) -> None:
    """Continuous background loop checking watchlists at specified interval (default 15 mins)."""
    logger.info("Watchlist Continuous Monitoring daemon active (interval: %ds).", interval_seconds)
    while True:
        try:
            await check_watchlist_tokens()
        except asyncio.CancelledError:
            logger.info("Watchlist monitor loop cancelled.")
            break
        except Exception as exc:
            logger.error("Watchlist monitor loop error: %s", exc, exc_info=True)
        await asyncio.sleep(interval_seconds)

