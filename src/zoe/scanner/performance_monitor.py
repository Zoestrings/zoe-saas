"""Shared Token Performance Monitoring & Milestone Alert Engine.

Monitors scanned tokens continuously against their validated baseline scan price,
evaluates positive multiples (2x, 3x, 4x, 5x, 10x...) and negative declines (-10%...-90%),
tracks high-water-mark drawdown separately, enforces strict idempotency/deduplication,
and isolates records by tenant (`user_id` / `organization_id` / `project_id`).
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
import uuid

from zoe.tools.scanner import detect_chain, fetch_dexscreener_market_data

logger = logging.getLogger("zoe.scanner.performance_monitor")

DEFAULT_POSITIVE_THRESHOLDS: List[float] = [2.0, 3.0, 4.0, 5.0, 10.0, 20.0, 50.0, 100.0]
DEFAULT_NEGATIVE_THRESHOLDS: List[float] = [-10.0, -20.0, -30.0, -50.0, -70.0, -90.0]

_MONITOR_MUTEX = threading.Lock()


def get_monitor_db_path() -> Path:
    env_dir = os.getenv("DATA_DIR", "").strip()
    if env_dir:
        return Path(env_dir) / "saas_dev.db"
    root = Path(__file__).resolve().parent.parent.parent.parent
    candidate = root / "saas-dashboard" / "backend" / "saas_dev.db"
    if candidate.exists():
        return candidate
    return root / "data" / "saas_dev.db"


def ensure_performance_schema(conn: sqlite3.Connection) -> None:
    """Create monitored_tokens, token_performance_alerts, and performance_monitor_settings tables."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitored_tokens (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            user_id TEXT NOT NULL,
            scan_id TEXT,
            blockchain TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            token_name TEXT NOT NULL,
            token_symbol TEXT NOT NULL,
            baseline_price REAL NOT NULL,
            baseline_timestamp TEXT NOT NULL,
            current_price REAL NOT NULL,
            highest_observed_price REAL NOT NULL,
            current_multiple REAL NOT NULL DEFAULT 1.0,
            percentage_change REAL NOT NULL DEFAULT 0.0,
            drawdown_from_high_pct REAL NOT NULL DEFAULT 0.0,
            market_cap REAL,
            liquidity_usd REAL,
            data_source TEXT NOT NULL DEFAULT 'DexScreener',
            data_freshness TEXT NOT NULL DEFAULT 'live',
            monitoring_status TEXT NOT NULL DEFAULT 'active',
            positive_thresholds_json TEXT NOT NULL,
            negative_thresholds_json TEXT NOT NULL,
            drawdown_threshold_pct REAL,
            realert_cooldown_seconds INTEGER NOT NULL DEFAULT 0,
            last_checked_at TEXT NOT NULL,
            last_successful_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, blockchain, contract_address)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_monitored_user ON monitored_tokens(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_monitored_status ON monitored_tokens(monitoring_status)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS token_performance_alerts (
            id TEXT PRIMARY KEY,
            monitoring_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            user_id TEXT NOT NULL,
            blockchain TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            token_name TEXT NOT NULL,
            token_symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            threshold_value REAL NOT NULL,
            baseline_price REAL NOT NULL,
            observed_price REAL NOT NULL,
            observed_multiple REAL NOT NULL,
            observed_percentage_change REAL NOT NULL,
            market_cap REAL,
            provider TEXT NOT NULL DEFAULT 'DexScreener',
            message TEXT NOT NULL,
            idempotency_key TEXT UNIQUE NOT NULL,
            notification_status TEXT NOT NULL DEFAULT 'pending',
            read_status INTEGER NOT NULL DEFAULT 0,
            event_timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (monitoring_id) REFERENCES monitored_tokens(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_alerts_user ON token_performance_alerts(user_id, read_status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_alerts_mon ON token_performance_alerts(monitoring_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS performance_monitor_settings (
            id TEXT PRIMARY KEY,
            default_positive_thresholds_json TEXT NOT NULL,
            default_negative_thresholds_json TEXT NOT NULL,
            max_monitored_free INTEGER NOT NULL DEFAULT 5,
            max_monitored_pro INTEGER NOT NULL DEFAULT 50,
            polling_interval_seconds INTEGER NOT NULL DEFAULT 300,
            updated_at TEXT NOT NULL
        )
        """
    )
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO performance_monitor_settings (
            id, default_positive_thresholds_json, default_negative_thresholds_json,
            max_monitored_free, max_monitored_pro, polling_interval_seconds, updated_at
        ) VALUES ('global', ?, ?, 5, 50, 300, ?)
        """,
        (json.dumps(DEFAULT_POSITIVE_THRESHOLDS), json.dumps(DEFAULT_NEGATIVE_THRESHOLDS), now_iso),
    )
    conn.commit()


def get_platform_monitoring_settings(conn: sqlite3.Connection) -> Dict[str, Any]:
    ensure_performance_schema(conn)
    row = conn.execute(
        """
        SELECT default_positive_thresholds_json, default_negative_thresholds_json,
               max_monitored_free, max_monitored_pro, polling_interval_seconds, updated_at
        FROM performance_monitor_settings WHERE id = 'global'
        """
    ).fetchone()
    if not row:
        return {
            "default_positive_thresholds": DEFAULT_POSITIVE_THRESHOLDS,
            "default_negative_thresholds": DEFAULT_NEGATIVE_THRESHOLDS,
            "max_monitored_free": 5,
            "max_monitored_pro": 50,
            "polling_interval_seconds": 300,
        }
    return {
        "default_positive_thresholds": json.loads(row[0]),
        "default_negative_thresholds": json.loads(row[1]),
        "max_monitored_free": int(row[2]),
        "max_monitored_pro": int(row[3]),
        "polling_interval_seconds": int(row[4]),
        "updated_at": str(row[5]),
    }


def register_token_monitoring(
    user_id: str,
    contract_address: str,
    market_snapshot: Dict[str, Any],
    user_plan: str = "free",
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    scan_id: Optional[str] = None,
    positive_thresholds: Optional[List[float]] = None,
    negative_thresholds: Optional[List[float]] = None,
    drawdown_threshold_pct: Optional[float] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Register a successfully scanned token for persistent performance monitoring.

    Rejects invalid contract addresses and missing/zero prices.
    Enforces per-plan monitoring limits.
    """
    clean_ca = (contract_address or "").strip()
    chain_type = detect_chain(clean_ca)
    if not chain_type or chain_type == "unknown":
        raise ValueError(f"Invalid contract address '{clean_ca}': cannot register monitoring.")

    if market_snapshot.get("found") is False:
        raise ValueError("Cannot register monitoring from a failed market snapshot.")

    blockchain = str(market_snapshot.get("chain_id") or chain_type or "solana").lower()
    raw_price = market_snapshot.get("price_usd")
    if raw_price is None or float(raw_price) <= 0.0:
        raise ValueError("Cannot register monitoring without a valid positive baseline market price.")

    baseline_price = float(raw_price)
    token_name = str(market_snapshot.get("name") or "Unknown Token").strip()
    token_symbol = str(market_snapshot.get("symbol") or clean_ca[:6]).strip()
    market_cap = float(market_snapshot["market_cap"]) if market_snapshot.get("market_cap") is not None else None
    liquidity_usd = float(market_snapshot["liquidity_usd"]) if market_snapshot.get("liquidity_usd") is not None else None
    org_id = organization_id or f"org_{str(user_id)[:12]}"

    own_conn = False
    if conn is None:
        db_path = get_monitor_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=15.0)
        own_conn = True

    try:
        ensure_performance_schema(conn)
        settings = get_platform_monitoring_settings(conn)

        # Check plan monitoring limit (unless updating an existing record for same user+token)
        existing = conn.execute(
            "SELECT id FROM monitored_tokens WHERE user_id = ? AND blockchain = ? AND contract_address = ?",
            (str(user_id), blockchain, clean_ca),
        ).fetchone()

        if not existing:
            active_cnt = int(
                conn.execute(
                    "SELECT COUNT(*) FROM monitored_tokens WHERE user_id = ? AND monitoring_status IN ('active', 'paused')",
                    (str(user_id),),
                ).fetchone()[0]
            )
            limit = settings["max_monitored_pro"] if user_plan in ("pro", "enterprise") else settings["max_monitored_free"]
            if active_cnt >= limit:
                raise PermissionError(
                    f"Monitoring limit reached ({active_cnt}/{limit} tokens for '{user_plan}' plan). Upgrade plan or remove old tokens."
                )

        pos_thresh = sorted(set(float(x) for x in (positive_thresholds or settings["default_positive_thresholds"]) if float(x) > 1.0))
        neg_thresh = sorted(set(float(x) for x in (negative_thresholds or settings["default_negative_thresholds"]) if float(x) < 0.0), reverse=True)

        now_iso = datetime.now(timezone.utc).isoformat()
        mon_id = str(existing[0]) if existing else f"mon_{uuid.uuid4().hex[:14]}"

        if existing:
            conn.execute(
                """
                UPDATE monitored_tokens
                SET monitoring_status = 'active',
                    positive_thresholds_json = ?,
                    negative_thresholds_json = ?,
                    drawdown_threshold_pct = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(pos_thresh), json.dumps(neg_thresh), drawdown_threshold_pct, now_iso, mon_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO monitored_tokens (
                    id, organization_id, project_id, user_id, scan_id, blockchain, contract_address,
                    token_name, token_symbol, baseline_price, baseline_timestamp,
                    current_price, highest_observed_price, current_multiple, percentage_change,
                    drawdown_from_high_pct, market_cap, liquidity_usd, data_source, data_freshness,
                    monitoring_status, positive_thresholds_json, negative_thresholds_json,
                    drawdown_threshold_pct, last_checked_at, last_successful_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1.0, 0.0, 0.0, ?, ?, 'DexScreener', 'live', 'active', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mon_id,
                    org_id,
                    project_id,
                    str(user_id),
                    scan_id,
                    blockchain,
                    clean_ca,
                    token_name,
                    token_symbol,
                    baseline_price,
                    now_iso,
                    baseline_price,
                    baseline_price,
                    market_cap,
                    liquidity_usd,
                    json.dumps(pos_thresh),
                    json.dumps(neg_thresh),
                    drawdown_threshold_pct,
                    now_iso,
                    now_iso,
                    now_iso,
                    now_iso,
                ),
            )
        conn.commit()
        return get_monitored_token_by_id(mon_id, conn=conn)
    finally:
        if own_conn:
            conn.close()


def get_monitored_token_by_id(monitoring_id: str, conn: sqlite3.Connection) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT id, organization_id, project_id, user_id, scan_id, blockchain, contract_address,
               token_name, token_symbol, baseline_price, baseline_timestamp, current_price,
               highest_observed_price, current_multiple, percentage_change, drawdown_from_high_pct,
               market_cap, liquidity_usd, data_source, data_freshness, monitoring_status,
               positive_thresholds_json, negative_thresholds_json, drawdown_threshold_pct,
               last_checked_at, last_successful_at, created_at, updated_at
        FROM monitored_tokens WHERE id = ?
        """,
        (monitoring_id,),
    ).fetchone()
    if not row:
        return {}
    return {
        "id": str(row[0]),
        "monitoring_id": str(row[0]),
        "organization_id": str(row[1]),
        "project_id": row[2],
        "user_id": str(row[3]),
        "scan_id": row[4],
        "blockchain": str(row[5]),
        "contract_address": str(row[6]),
        "token_name": str(row[7]),
        "token_symbol": str(row[8]),
        "baseline_price": float(row[9]),
        "baseline_timestamp": str(row[10]),
        "current_price": float(row[11]),
        "highest_observed_price": float(row[12]),
        "current_multiple": float(row[13]),
        "percentage_change": float(row[14]),
        "drawdown_from_high_pct": float(row[15]),
        "market_cap": float(row[16]) if row[16] is not None else None,
        "liquidity_usd": float(row[17]) if row[17] is not None else None,
        "data_source": str(row[18]),
        "data_freshness": str(row[19]),
        "monitoring_status": str(row[20]),
        "positive_thresholds": json.loads(row[21]),
        "negative_thresholds": json.loads(row[22]),
        "drawdown_threshold_pct": float(row[23]) if row[23] is not None else None,
        "last_checked_at": str(row[24]),
        "last_successful_at": str(row[25]),
        "created_at": str(row[26]),
        "updated_at": str(row[27]),
        "performance_label": "Unrealized price performance since scan baseline",
    }


def evaluate_price_update(
    monitoring_id: str,
    observed_price: Optional[float],
    conn: sqlite3.Connection,
    market_cap: Optional[float] = None,
    liquidity_usd: Optional[float] = None,
    provider: str = "DexScreener",
    is_stale: bool = False,
) -> List[Dict[str, Any]]:
    """Evaluate a validated price update against a monitored token's thresholds.

    Guarantees:
    - Never evaluates against missing, zero, or stale prices.
    - Recognizes all crossed milestones in a single price jump (e.g. 1.5x -> 4.5x triggers 2x, 3x, 4x).
    - Enforces strict idempotency keys (`UNIQUE`) so fluctuating prices never spam duplicate alerts.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    if observed_price is None or float(observed_price) <= 0.0 or is_stale:
        conn.execute(
            "UPDATE monitored_tokens SET data_freshness = ?, last_checked_at = ?, updated_at = ? WHERE id = ?",
            ("stale" if is_stale else "provider_error", now_iso, now_iso, monitoring_id),
        )
        conn.commit()
        return []

    price = float(observed_price)

    with _MONITOR_MUTEX:
        rec = get_monitored_token_by_id(monitoring_id, conn)
        if not rec or rec.get("monitoring_status") != "active":
            return []

        baseline = float(rec["baseline_price"])
        if baseline <= 0.0:
            return []

        # Unrounded calculations prior to threshold evaluation
        multiple = price / baseline
        pct_change = ((price - baseline) / baseline) * 100.0
        highest_price = max(float(rec["highest_observed_price"]), price)
        drawdown_pct = ((price - highest_price) / highest_price) * 100.0 if highest_price > 0 else 0.0

        conn.execute(
            """
            UPDATE monitored_tokens
            SET current_price = ?, highest_observed_price = ?, current_multiple = ?,
                percentage_change = ?, drawdown_from_high_pct = ?,
                market_cap = COALESCE(?, market_cap),
                liquidity_usd = COALESCE(?, liquidity_usd),
                data_source = ?, data_freshness = 'live',
                last_checked_at = ?, last_successful_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                price,
                highest_price,
                multiple,
                pct_change,
                drawdown_pct,
                market_cap,
                liquidity_usd,
                provider,
                now_iso,
                now_iso,
                now_iso,
                monitoring_id,
            ),
        )

        created_alerts: List[Dict[str, Any]] = []

        # 1. Positive Milestones (e.g. 2x, 3x, 4x, 5x, 10x...)
        for thresh in sorted(rec["positive_thresholds"]):
            if multiple >= float(thresh):
                idemp_key = f"{monitoring_id}:pos:{thresh}"
                alert_id = f"pa_{uuid.uuid4().hex[:14]}"
                msg = (
                    f"Token milestone reached: {rec['token_symbol']} has reached {multiple:.2f}x "
                    f"since monitoring began, crossing the {thresh:g}x milestone "
                    f"(unrealized +{pct_change:.1f}% from baseline ${baseline:.6g})."
                )
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO token_performance_alerts (
                        id, monitoring_id, organization_id, project_id, user_id,
                        blockchain, contract_address, token_name, token_symbol,
                        alert_type, threshold_value, baseline_price, observed_price,
                        observed_multiple, observed_percentage_change, market_cap,
                        provider, message, idempotency_key, notification_status,
                        read_status, event_timestamp, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'positive_milestone', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'dispatched', 0, ?, ?)
                    """,
                    (
                        alert_id,
                        monitoring_id,
                        rec["organization_id"],
                        rec["project_id"],
                        rec["user_id"],
                        rec["blockchain"],
                        rec["contract_address"],
                        rec["token_name"],
                        rec["token_symbol"],
                        float(thresh),
                        baseline,
                        price,
                        multiple,
                        pct_change,
                        market_cap,
                        provider,
                        msg,
                        idemp_key,
                        now_iso,
                        now_iso,
                    ),
                )
                if cur.rowcount > 0:
                    created_alerts.append({
                        "id": alert_id,
                        "monitoring_id": monitoring_id,
                        "alert_type": "positive_milestone",
                        "threshold_value": float(thresh),
                        "token_symbol": rec["token_symbol"],
                        "blockchain": rec["blockchain"],
                        "observed_price": price,
                        "observed_multiple": multiple,
                        "observed_percentage_change": pct_change,
                        "message": msg,
                        "event_timestamp": now_iso,
                    })

        # 2. Negative Decline Thresholds (e.g. -10%, -20%, -30%, -50%...)
        for neg_thresh in sorted(rec["negative_thresholds"], reverse=True):
            if pct_change <= float(neg_thresh):
                idemp_key = f"{monitoring_id}:neg:{neg_thresh}"
                alert_id = f"pa_{uuid.uuid4().hex[:14]}"
                abs_drop = abs(pct_change)
                msg = (
                    f"Price decline alert: {rec['token_symbol']} is down {abs_drop:.1f}% "
                    f"from its monitoring baseline (${baseline:.6g} -> ${price:.6g})."
                )
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO token_performance_alerts (
                        id, monitoring_id, organization_id, project_id, user_id,
                        blockchain, contract_address, token_name, token_symbol,
                        alert_type, threshold_value, baseline_price, observed_price,
                        observed_multiple, observed_percentage_change, market_cap,
                        provider, message, idempotency_key, notification_status,
                        read_status, event_timestamp, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'negative_decline', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'dispatched', 0, ?, ?)
                    """,
                    (
                        alert_id,
                        monitoring_id,
                        rec["organization_id"],
                        rec["project_id"],
                        rec["user_id"],
                        rec["blockchain"],
                        rec["contract_address"],
                        rec["token_name"],
                        rec["token_symbol"],
                        float(neg_thresh),
                        baseline,
                        price,
                        multiple,
                        pct_change,
                        market_cap,
                        provider,
                        msg,
                        idemp_key,
                        now_iso,
                        now_iso,
                    ),
                )
                if cur.rowcount > 0:
                    created_alerts.append({
                        "id": alert_id,
                        "monitoring_id": monitoring_id,
                        "alert_type": "negative_decline",
                        "threshold_value": float(neg_thresh),
                        "token_symbol": rec["token_symbol"],
                        "blockchain": rec["blockchain"],
                        "observed_price": price,
                        "observed_multiple": multiple,
                        "observed_percentage_change": pct_change,
                        "message": msg,
                        "event_timestamp": now_iso,
                    })

        # 3. Optional High-Water-Mark Drawdown Alert (supplementary)
        dd_thresh = rec.get("drawdown_threshold_pct")
        if dd_thresh is not None and drawdown_pct <= -abs(float(dd_thresh)):
            idemp_key = f"{monitoring_id}:dd:{dd_thresh}:{round(highest_price, 10)}"
            alert_id = f"pa_{uuid.uuid4().hex[:14]}"
            msg = (
                f"Drawdown alert: {rec['token_symbol']} has pulled back {abs(drawdown_pct):.1f}% "
                f"from its highest observed price (${highest_price:.6g} -> ${price:.6g})."
            )
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO token_performance_alerts (
                    id, monitoring_id, organization_id, project_id, user_id,
                    blockchain, contract_address, token_name, token_symbol,
                    alert_type, threshold_value, baseline_price, observed_price,
                    observed_multiple, observed_percentage_change, market_cap,
                    provider, message, idempotency_key, notification_status,
                    read_status, event_timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'drawdown', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'dispatched', 0, ?, ?)
                """,
                (
                    alert_id,
                    monitoring_id,
                    rec["organization_id"],
                    rec["project_id"],
                    rec["user_id"],
                    rec["blockchain"],
                    rec["contract_address"],
                    rec["token_name"],
                    rec["token_symbol"],
                    -abs(float(dd_thresh)),
                    baseline,
                    price,
                    multiple,
                    pct_change,
                    market_cap,
                    provider,
                    msg,
                    idemp_key,
                    now_iso,
                    now_iso,
                ),
            )
            if cur.rowcount > 0:
                created_alerts.append({
                    "id": alert_id,
                    "monitoring_id": monitoring_id,
                    "alert_type": "drawdown",
                    "threshold_value": -abs(float(dd_thresh)),
                    "token_symbol": rec["token_symbol"],
                    "blockchain": rec["blockchain"],
                    "observed_price": price,
                    "observed_multiple": multiple,
                    "observed_percentage_change": pct_change,
                    "message": msg,
                    "event_timestamp": now_iso,
                })

        conn.commit()
        return created_alerts


async def run_performance_monitoring_cycle(
    conn: Optional[sqlite3.Connection] = None,
    user_id_filter: Optional[str] = None,
    market_fetcher: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    """Shared background worker cycle fetching prices once per unique token and evaluating all subscribers."""
    own_conn = False
    if conn is None:
        db_path = get_monitor_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=15.0)
        own_conn = True

    all_new_alerts: List[Dict[str, Any]] = []
    fetcher = market_fetcher or fetch_dexscreener_market_data

    try:
        ensure_performance_schema(conn)
        sql = "SELECT id, contract_address FROM monitored_tokens WHERE monitoring_status = 'active'"
        params: List[Any] = []
        if user_id_filter:
            sql += " AND user_id = ?"
            params.append(str(user_id_filter))

        rows = conn.execute(sql, tuple(params)).fetchall()
        if not rows:
            return []

        # Deduplicate market-data lookups across unique contract addresses
        by_ca: Dict[str, List[str]] = {}
        for mon_id, ca in rows:
            by_ca.setdefault(str(ca), []).append(str(mon_id))

        for ca, mon_ids in by_ca.items():
            try:
                mkt = await fetcher(ca)
                price = mkt.get("price_usd") if mkt and mkt.get("found") else None
                mcap = mkt.get("market_cap") if mkt else None
                liq = mkt.get("liquidity_usd") if mkt else None
                for mon_id in mon_ids:
                    alerts = evaluate_price_update(
                        monitoring_id=mon_id,
                        observed_price=price,
                        conn=conn,
                        market_cap=mcap,
                        liquidity_usd=liq,
                        provider="DexScreener",
                        is_stale=bool(mkt.get("is_stale")) if mkt else False,
                    )
                    all_new_alerts.extend(alerts)
            except Exception as exc:
                logger.warning("Market fetch failed for %s during performance cycle: %s", ca, exc)
                for mon_id in mon_ids:
                    evaluate_price_update(monitoring_id=mon_id, observed_price=None, conn=conn)
            await asyncio.sleep(0.15)  # Respect DexScreener rate limits

        return all_new_alerts
    finally:
        if own_conn:
            conn.close()
