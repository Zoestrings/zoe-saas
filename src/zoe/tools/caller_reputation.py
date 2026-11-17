"""Caller Reputation and Leaderboards Engine (Phase 3).

Tracks community member token calls, records entry spot prices from DexScreener,
monitors All-Time Highs (ATH) and multipliers, and generates community leaderboards.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import uuid

import httpx

from zoe.tools.scanner import fetch_dexscreener_market_data
from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.caller_reputation")


def get_reputation_db_conn() -> sqlite3.Connection:
    """Connect to local sqlite fallback database and ensure caller schema exists."""
    db_path = Path("saas-dashboard/backend/dev_db.sqlite")
    if not db_path.exists():
        alt_path = Path("dev_db.sqlite")
        if alt_path.exists():
            db_path = alt_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_callers (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            telegram_user_id TEXT NOT NULL,
            username TEXT,
            total_calls INTEGER DEFAULT 0,
            successful_calls INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0,
            best_multiplier REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            UNIQUE(project_id, telegram_user_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_token_calls (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            caller_id TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            token_name TEXT,
            call_price REAL NOT NULL,
            ath_price REAL DEFAULT 0.0,
            ath_multiplier REAL DEFAULT 1.0,
            status TEXT DEFAULT 'tracking',
            called_at TEXT NOT NULL
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
            logger.debug("Supabase init failed in caller reputation: %s", exc)
    return None


def record_token_call(
    project_id: str,
    telegram_user_id: str,
    contract_address: str,
    username: Optional[str] = None,
    token_name: Optional[str] = None,
    call_price: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Record an incoming contract address mention as a community token call.
    
    1. Upserts caller record in callers table.
    2. Fetches DexScreener spot price if call_price not supplied.
    3. Inserts token_calls tracking record with ath_price = call_price and multiplier = 1.0.
    """
    if not project_id or not telegram_user_id or not contract_address:
        return None

    clean_ca = contract_address.strip()
    clean_user_id = str(telegram_user_id).strip()
    clean_username = username.strip() if username else f"user_{clean_user_id[:6]}"
    if clean_username.startswith("@"):
        clean_username = clean_username[1:]

    # Resolve token name and current price if missing
    resolved_name = token_name
    resolved_price = call_price

    if resolved_price is None or resolved_price <= 0 or not resolved_name:
        try:
            from zoe.tools.crypto_intel import get_token_intel_sync
            intel = get_token_intel_sync(ca=clean_ca)
            if isinstance(intel, dict):
                if not resolved_name:
                    resolved_name = intel.get("name") or intel.get("symbol")
                if resolved_price is None or resolved_price <= 0:
                    try:
                        resolved_price = float(intel.get("price_usd") or 0.0)
                    except (ValueError, TypeError):
                        resolved_price = 0.0
        except Exception as exc:
            logger.debug("Could not resolve market intel for call %s: %s", clean_ca, exc)

    if not resolved_name:
        resolved_name = "Token"
    if resolved_price is None or resolved_price < 0:
        resolved_price = 0.0

    now_iso = datetime.now(timezone.utc).isoformat()
    caller_id = None
    total_calls = 1

    # 1. Upsert into Supabase
    sb_client = get_supabase_client()
    if sb_client:
        try:
            # Check existing caller
            res = (
                sb_client.table("callers")
                .select("*")
                .eq("project_id", project_id)
                .eq("telegram_user_id", clean_user_id)
                .execute()
            )
            if res.data and len(res.data) > 0:
                caller_row = res.data[0]
                caller_id = caller_row["id"]
                total_calls = int(caller_row.get("total_calls") or 0) + 1
                sb_client.table("callers").update({
                    "total_calls": total_calls,
                    "username": clean_username,
                }).eq("id", caller_id).execute()
            else:
                caller_id = str(uuid.uuid4())
                sb_client.table("callers").insert({
                    "id": caller_id,
                    "project_id": project_id,
                    "telegram_user_id": clean_user_id,
                    "username": clean_username,
                    "total_calls": 1,
                    "successful_calls": 0,
                    "win_rate": 0.0,
                    "best_multiplier": 1.0,
                    "created_at": now_iso,
                }).execute()
        except Exception as exc:
            logger.debug("Supabase caller upsert failed: %s", exc)

    # 2. Upsert into local SQLite dev DB
    conn = get_reputation_db_conn()
    try:
        cur = conn.execute(
            "SELECT id, total_calls FROM dev_callers WHERE project_id = ? AND telegram_user_id = ?",
            (project_id, clean_user_id),
        )
        row = cur.fetchone()
        if row:
            if not caller_id:
                caller_id = row[0]
            total_calls = int(row[1]) + 1
            conn.execute(
                "UPDATE dev_callers SET total_calls = ?, username = ? WHERE project_id = ? AND telegram_user_id = ?",
                (total_calls, clean_username, project_id, clean_user_id),
            )
        else:
            if not caller_id:
                caller_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO dev_callers (id, project_id, telegram_user_id, username, total_calls, successful_calls, win_rate, best_multiplier, created_at)
                VALUES (?, ?, ?, ?, 1, 0, 0.0, 1.0, ?)
                """,
                (caller_id, project_id, clean_user_id, clean_username, now_iso),
            )
        conn.commit()
    except Exception as exc:
        logger.debug("Dev DB caller upsert failed: %s", exc)

    if not caller_id:
        caller_id = str(uuid.uuid4())

    call_record_id = str(uuid.uuid4())
    call_record = {
        "id": call_record_id,
        "project_id": project_id,
        "caller_id": caller_id,
        "contract_address": clean_ca,
        "token_name": resolved_name,
        "call_price": float(resolved_price),
        "ath_price": float(resolved_price),
        "ath_multiplier": 1.0,
        "status": "tracking",
        "called_at": now_iso,
    }

    # Insert into Supabase token_calls
    if sb_client:
        try:
            sb_client.table("token_calls").insert(call_record).execute()
        except Exception as exc:
            logger.debug("Supabase token_calls insert error: %s", exc)

    # Insert into dev_token_calls
    try:
        conn.execute(
            """
            INSERT INTO dev_token_calls (id, project_id, caller_id, contract_address, token_name, call_price, ath_price, ath_multiplier, status, called_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1.0, 'tracking', ?)
            """,
            (
                call_record_id,
                project_id,
                caller_id,
                clean_ca,
                resolved_name,
                float(resolved_price),
                float(resolved_price),
                now_iso,
            ),
        )
        conn.commit()
    except Exception as exc:
        logger.debug("Dev DB token_calls insert error: %s", exc)

    logger.info("Recorded token call %s for caller %s (User %s) at price $%.6f", clean_ca, clean_username, clean_user_id, float(resolved_price))
    return call_record


def get_leaderboard_text(project_id: str, limit: int = 5) -> str:
    """Query top callers for a project ordered by best_multiplier descending and format message."""
    callers: List[Dict[str, Any]] = []

    sb_client = get_supabase_client()
    if sb_client:
        try:
            res = (
                sb_client.table("callers")
                .select("*")
                .eq("project_id", project_id)
                .order("best_multiplier", desc=True)
                .limit(limit)
                .execute()
            )
            if res.data:
                callers = res.data
        except Exception as exc:
            logger.debug("Supabase leaderboard query failed: %s", exc)

    if not callers:
        conn = get_reputation_db_conn()
        try:
            cur = conn.execute(
                """
                SELECT telegram_user_id, username, best_multiplier, total_calls, win_rate, successful_calls
                FROM dev_callers
                WHERE project_id = ?
                ORDER BY best_multiplier DESC, total_calls DESC
                LIMIT ?
                """,
                (project_id, limit),
            )
            for r in cur.fetchall():
                callers.append({
                    "telegram_user_id": r[0],
                    "username": r[1],
                    "best_multiplier": float(r[2]) if r[2] is not None else 1.0,
                    "total_calls": int(r[3]) if r[3] is not None else 0,
                    "win_rate": float(r[4]) if r[4] is not None else 0.0,
                    "successful_calls": int(r[5]) if r[5] is not None else 0,
                })
        except Exception as exc:
            logger.debug("Dev DB leaderboard query failed: %s", exc)

    lines = ["🏆 Top Callers in this Community"]
    if not callers:
        lines.append("No calls recorded yet. Drop a token CA to make the first call! 🚀")
    else:
        for idx, c in enumerate(callers, start=1):
            uname = c.get("username") or f"caller_{str(c.get('telegram_user_id'))[:5]}"
            if not uname.startswith("@"):
                uname = f"@{uname}"
            mult = float(c.get("best_multiplier") or 1.0)
            calls_cnt = int(c.get("total_calls") or 0)
            lines.append(f"{idx}. {uname} - {mult:.1f}x ({calls_cnt} call{'s' if calls_cnt != 1 else ''})")

    lines.append("\nOnly verified on-chain calls are tracked.")
    return "\n".join(lines)


async def update_ath_for_calls(client: Optional[httpx.AsyncClient] = None) -> List[Dict[str, Any]]:
    """Scan tracking calls, update ATH prices from DexScreener, and recalculate caller win rates."""
    logger.info("Starting Caller ATH update cycle...")
    tracking_calls: List[Dict[str, Any]] = []

    sb_client = get_supabase_client()
    if sb_client:
        try:
            res = sb_client.table("token_calls").select("*").eq("status", "tracking").execute()
            if res.data:
                tracking_calls = res.data
        except Exception as exc:
            logger.debug("Supabase tracking token_calls query: %s", exc)

    if not tracking_calls:
        conn = get_reputation_db_conn()
        try:
            cur = conn.execute(
                """
                SELECT id, project_id, caller_id, contract_address, token_name, call_price, ath_price, ath_multiplier, status, called_at
                FROM dev_token_calls
                WHERE status = 'tracking'
                """
            )
            for r in cur.fetchall():
                tracking_calls.append({
                    "id": r[0],
                    "project_id": r[1],
                    "caller_id": r[2],
                    "contract_address": r[3],
                    "token_name": r[4],
                    "call_price": float(r[5]) if r[5] is not None else 0.0,
                    "ath_price": float(r[6]) if r[6] is not None else 0.0,
                    "ath_multiplier": float(r[7]) if r[7] is not None else 1.0,
                    "status": r[8],
                    "called_at": r[9],
                })
        except Exception as exc:
            logger.debug("Dev DB tracking token_calls query: %s", exc)

    if not tracking_calls:
        logger.info("No active token calls in tracking state.")
        return []

    updated_calls: List[Dict[str, Any]] = []
    affected_callers: Dict[Tuple[str, str], str] = {}  # (project_id, caller_id)

    async with httpx.AsyncClient(timeout=10.0) as local_http:
        http_client = client or local_http
        for call in tracking_calls:
            ca = call.get("contract_address")
            if not ca:
                continue

            try:
                market = await fetch_dexscreener_market_data(ca, client=http_client)
            except Exception as exc:
                logger.debug("DexScreener fetch failed for CA %s: %s", ca, exc)
                continue

            current_price = market.get("price_usd")
            if current_price is None or current_price <= 0:
                continue

            call_price = float(call.get("call_price") or 0.0)
            ath_price = float(call.get("ath_price") or call_price)

            if float(current_price) > ath_price:
                new_ath = float(current_price)
                new_mult = (new_ath / call_price) if call_price > 0 else 1.0

                # Update token_calls record
                if sb_client:
                    try:
                        sb_client.table("token_calls").update({
                            "ath_price": new_ath,
                            "ath_multiplier": round(new_mult, 2),
                        }).eq("id", call["id"]).execute()
                    except Exception:
                        pass
                try:
                    conn = get_reputation_db_conn()
                    conn.execute(
                        "UPDATE dev_token_calls SET ath_price = ?, ath_multiplier = ? WHERE id = ?",
                        (new_ath, round(new_mult, 2), call["id"]),
                    )
                    conn.commit()
                except Exception:
                    pass

                call["ath_price"] = new_ath
                call["ath_multiplier"] = round(new_mult, 2)
                updated_calls.append(call)
                affected_callers[(call["project_id"], call["caller_id"])] = call["caller_id"]

    # Recalculate caller win_rate and best_multiplier
    for (p_id, c_id) in affected_callers.keys():
        all_calls_for_caller: List[Dict[str, Any]] = []
        if sb_client:
            try:
                res_c = sb_client.table("token_calls").select("ath_multiplier").eq("caller_id", c_id).execute()
                if res_c.data:
                    all_calls_for_caller = res_c.data
            except Exception:
                pass
        if not all_calls_for_caller:
            try:
                conn = get_reputation_db_conn()
                cur_c = conn.execute("SELECT ath_multiplier FROM dev_token_calls WHERE caller_id = ?", (c_id,))
                all_calls_for_caller = [{"ath_multiplier": float(r[0])} for r in cur_c.fetchall()]
            except Exception:
                pass

        if all_calls_for_caller:
            total = len(all_calls_for_caller)
            wins = sum(1 for c in all_calls_for_caller if float(c.get("ath_multiplier") or 1.0) > 1.5)
            win_rate = round((wins / total) * 100.0, 1) if total > 0 else 0.0
            best_mult = round(max((float(c.get("ath_multiplier") or 1.0) for c in all_calls_for_caller), default=1.0), 2)

            if sb_client:
                try:
                    sb_client.table("callers").update({
                        "total_calls": total,
                        "successful_calls": wins,
                        "win_rate": win_rate,
                        "best_multiplier": best_mult,
                    }).eq("id", c_id).execute()
                except Exception:
                    pass
            try:
                conn = get_reputation_db_conn()
                conn.execute(
                    "UPDATE dev_callers SET total_calls = ?, successful_calls = ?, win_rate = ?, best_multiplier = ? WHERE id = ?",
                    (total, wins, win_rate, best_mult, c_id),
                )
                conn.commit()
            except Exception:
                pass

    logger.info("Caller ATH update complete. %d calls updated.", len(updated_calls))
    return updated_calls
