"""Comprehensive acceptance tests for Token Performance Monitoring & Real-Time Dashboard Alerts."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import sys
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "saas-dashboard" / "backend"))

from zoe.scanner.performance_monitor import (  # noqa: E402
    ensure_performance_schema,
    evaluate_price_update,
    get_monitored_token_by_id,
    register_token_monitoring,
    run_performance_monitoring_cycle,
)


VALID_SOL_CA = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
VALID_SOL_CA_2 = "So11111111111111111111111111111111111111112"
VALID_EVM_CA = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"


def _make_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "perf_test.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    ensure_performance_schema(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_entitlements (
            user_id TEXT PRIMARY KEY,
            plan TEXT NOT NULL DEFAULT 'free',
            credits INTEGER NOT NULL DEFAULT 50,
            expires_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def _snapshot(price: float = 0.001, symbol: str = "BONK", name: str = "Bonk", chain: str = "solana") -> dict:
    return {
        "found": True,
        "price_usd": price,
        "market_cap": 1_000_000.0,
        "liquidity_usd": 250_000.0,
        "symbol": symbol,
        "name": name,
        "chain_id": chain,
    }


def test_1_to_3_register_valid_reject_invalid_and_capture_baseline(tmp_path):
    conn = _make_db(tmp_path)

    # 1 & 3. Successful scan registers monitoring with exact baseline price
    rec = register_token_monitoring(
        user_id="owner-a",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        conn=conn,
    )
    assert rec["baseline_price"] == pytest.approx(0.001)
    assert rec["blockchain"] == "solana"
    assert rec["monitoring_status"] == "active"

    # 2. Invalid CA or missing/zero price cannot be monitored
    with pytest.raises(ValueError):
        register_token_monitoring(
            user_id="owner-a",
            contract_address="not-a-valid-address",
            market_snapshot=_snapshot(0.001),
            conn=conn,
        )
    with pytest.raises(ValueError):
        register_token_monitoring(
            user_id="owner-a",
            contract_address=VALID_EVM_CA,
            market_snapshot={"found": True, "price_usd": 0.0},
            conn=conn,
        )
    with pytest.raises(ValueError):
        register_token_monitoring(
            user_id="owner-a",
            contract_address=VALID_EVM_CA,
            market_snapshot={"found": False, "price_usd": 0.001},
            conn=conn,
        )


def test_4_to_6_positive_milestones_and_multi_milestone_jump(tmp_path):
    conn = _make_db(tmp_path)
    rec = register_token_monitoring(
        user_id="owner-a",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        conn=conn,
    )
    mid = rec["monitoring_id"]

    # 1.5x -> no milestone yet
    assert evaluate_price_update(mid, 0.0015, conn) == []

    # 4. Crossing 2x creates 2x alert
    alerts_2x = evaluate_price_update(mid, 0.0021, conn)
    assert len(alerts_2x) == 1
    assert alerts_2x[0]["alert_type"] == "positive_milestone"
    assert alerts_2x[0]["threshold_value"] == 2.0

    # 5 & 6. Jumping from 2.1x directly to 4.5x catches BOTH 3x and 4x!
    alerts_jump = evaluate_price_update(mid, 0.0045, conn)
    thresholds = sorted(a["threshold_value"] for a in alerts_jump)
    assert thresholds == [3.0, 4.0]


def test_7_and_8_negative_declines_and_drawdown(tmp_path):
    conn = _make_db(tmp_path)
    rec = register_token_monitoring(
        user_id="owner-a",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        drawdown_threshold_pct=25.0,
        conn=conn,
    )
    mid = rec["monitoring_id"]

    # 7. Dropping 20% creates -10% and -20% alerts
    alerts_20 = evaluate_price_update(mid, 0.0008, conn)
    neg_thresholds = sorted(a["threshold_value"] for a in alerts_20 if a["alert_type"] == "negative_decline")
    assert neg_thresholds == [-20.0, -10.0]

    # 8. Dropping 50% creates -30% and -50% alerts
    alerts_50 = evaluate_price_update(mid, 0.0005, conn)
    neg_thresholds_50 = sorted(a["threshold_value"] for a in alerts_50 if a["alert_type"] == "negative_decline")
    assert neg_thresholds_50 == [-50.0, -30.0]


def test_9_and_10_deduplication_and_no_recovery_spam(tmp_path):
    conn = _make_db(tmp_path)
    rec = register_token_monitoring(
        user_id="owner-a",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        conn=conn,
    )
    mid = rec["monitoring_id"]

    # Reach 2.1x -> triggers 2x once
    first = evaluate_price_update(mid, 0.0021, conn)
    assert len(first) == 1

    # 9. Repeated price updates around 2x do not duplicate
    assert evaluate_price_update(mid, 0.0022, conn) == []

    # 10. Drop to 1.8x then recover to 2.1x -> no duplicate 2x spam
    assert evaluate_price_update(mid, 0.0018, conn) == []
    assert evaluate_price_update(mid, 0.0021, conn) == []


def test_11_and_12_stale_and_provider_failures_do_not_alert(tmp_path):
    conn = _make_db(tmp_path)
    rec = register_token_monitoring(
        user_id="owner-a",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        conn=conn,
    )
    mid = rec["monitoring_id"]

    # 11. Stale price does not generate alert
    assert evaluate_price_update(mid, 0.0002, conn, is_stale=True) == []
    state = get_monitored_token_by_id(mid, conn)
    assert state["data_freshness"] == "stale"

    # 12. Provider failure (None or 0.0) does not generate false crash alert
    assert evaluate_price_update(mid, None, conn) == []
    assert evaluate_price_update(mid, 0.0, conn) == []
    state2 = get_monitored_token_by_id(mid, conn)
    assert state2["data_freshness"] == "provider_error"
    assert state2["current_price"] == pytest.approx(0.001)


def test_17_and_18_entitlement_and_monitoring_limits(tmp_path):
    conn = _make_db(tmp_path)
    conn.execute("UPDATE performance_monitor_settings SET max_monitored_free = 1 WHERE id = 'global'")
    conn.commit()

    register_token_monitoring(
        user_id="free-user",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="free",
        conn=conn,
    )
    # 18. Exceeding free plan limit (1) raises PermissionError
    with pytest.raises(PermissionError, match="limit"):
        register_token_monitoring(
            user_id="free-user",
            contract_address=VALID_SOL_CA_2,
            market_snapshot=_snapshot(100.0, symbol="SOL", name="Solana"),
            user_plan="free",
            conn=conn,
        )

    # 17. Pro plan allows more tokens
    pro_rec = register_token_monitoring(
        user_id="pro-user",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        conn=conn,
    )
    assert pro_rec["monitoring_id"]


def test_19_concurrent_monitoring_jobs_no_duplicates(tmp_path):
    conn = _make_db(tmp_path)
    rec = register_token_monitoring(
        user_id="owner-a",
        contract_address=VALID_SOL_CA,
        market_snapshot=_snapshot(0.001),
        user_plan="pro",
        conn=conn,
    )
    mid = rec["monitoring_id"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: evaluate_price_update(mid, 0.0025, conn), range(4)))

    total_created = sum(len(r) for r in results)
    assert total_created == 1


def test_13_to_16_api_tenant_isolation_super_admin_and_offline_alerts(tmp_path, monkeypatch):
    import main as backend_main

    test_db_path = tmp_path / "api_perf.db"
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    # Point backend_main.get_dev_db to our isolated test DB
    def _override_get_dev_db():
        conn = sqlite3.connect(str(test_db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        ensure_performance_schema(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dev_entitlements (
                user_id TEXT PRIMARY KEY,
                plan TEXT NOT NULL DEFAULT 'pro',
                credits INTEGER NOT NULL DEFAULT 50,
                expires_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.commit()
        return conn

    class _Ctx:
        def __enter__(self):
            self.conn = _override_get_dev_db()
            return self.conn

        def __exit__(self, *args):
            self.conn.close()

    monkeypatch.setattr(backend_main, "get_dev_db", lambda: _Ctx())

    # Rebuild router with monkeypatched get_dev_db
    from routes.performance_alerts import build_performance_alerts_router
    from fastapi import FastAPI

    current_user_box = {"user": {"id": "owner-a", "role": "project_owner", "email": "a@example.com"}}

    def _get_user():
        return current_user_box["user"]

    def _require_admin():
        if current_user_box["user"]["role"] != "super_admin":
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin only")
        return current_user_box["user"]

    test_app = FastAPI()
    test_app.include_router(build_performance_alerts_router(_get_user, _require_admin, lambda: _Ctx()))
    client = TestClient(test_app)

    # Register token for Owner A at $0.001
    with patch("routes.performance_alerts.fetch_dexscreener_market_data", new=AsyncMock(return_value=_snapshot(0.001))):
        res = client.post("/api/scanner/monitor", json={"contract_address": VALID_SOL_CA})
        assert res.status_code == 200
        mon_a_id = res.json()["monitored_token"]["monitoring_id"]

    # Simulate background price jump to 2.5x while Owner A is offline
    with _Ctx() as conn:
        asyncio.run(
            run_performance_monitoring_cycle(
                conn=conn,
                market_fetcher=AsyncMock(return_value=_snapshot(0.0025)),
            )
        )

    # 15. Offline user logs back in and sees missed alerts in Notification Centre
    alerts_a = client.get("/api/scanner/performance-alerts")
    assert alerts_a.status_code == 200
    assert alerts_a.json()["unread_count"] == 1
    assert alerts_a.json()["alerts"][0]["threshold_value"] == 2.0

    # 13. Switch to Project Owner B -> cannot see or mutate Owner A's monitoring or alerts
    current_user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@example.com"}
    assert client.get("/api/scanner/monitored").json()["count"] == 0
    assert client.get("/api/scanner/performance-alerts").json()["alerts"] == []
    assert client.patch(f"/api/scanner/monitored/{mon_a_id}", json={"monitoring_status": "paused"}).status_code == 403
    assert client.get("/api/scanner/monitored?all_tenants=true").status_code == 403
    assert client.get("/api/admin/performance-monitoring").status_code == 403

    # 14. Switch to Super Admin -> can inspect global monitoring records & update defaults
    current_user_box["user"] = {"id": "admin-1", "role": "super_admin", "email": "admin@zoe.ai"}
    admin_res = client.get("/api/admin/performance-monitoring")
    assert admin_res.status_code == 200
    assert admin_res.json()["summary"]["total_monitored_tokens"] == 1
    assert admin_res.json()["summary"]["total_positive_alerts"] == 1
