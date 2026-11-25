"""Automated Tests for Post-Audit Critical Fixes (RBAC, Real Metrics, DDL, LLM Cost Tracking)."""

from pathlib import Path
import sqlite3
import sys
from starlette.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import init_db
import main as backend_main
from zoe.llm.mock import MockLLMClient
from zoe.llm.router import LLMRouter


def test_admin_endpoints_enforce_super_admin_rbac(tmp_path: Path, monkeypatch):
    """Verify /api/admin/metrics, chart-data, recent-activity, system-health reject non-admins (403)."""
    db_file = tmp_path / "saas_dev.db"
    monkeypatch.setattr(backend_main, "DEV_DB_PATH", db_file)
    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    backend_main.get_dev_db()

    # Non-admin user
    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: {
        "id": "owner_1",
        "email": "owner@zoe.ai",
        "role": "project_owner",
    }
    client = TestClient(backend_main.app)

    for path in (
        "/api/admin/metrics",
        "/api/admin/chart-data",
        "/api/admin/recent-activity",
        "/api/admin/system-health",
    ):
        resp = client.get(path)
        assert resp.status_code == 403, f"Expected 403 for {path}, got {resp.status_code}"

    # Super Admin allowed, and empty DB returns 0 (no fake clamping)
    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: {
        "id": "admin_1",
        "email": "admin@zoe.ai",
        "role": "super_admin",
    }
    metrics_resp = client.get("/api/admin/metrics")
    assert metrics_resp.status_code == 200
    m = metrics_resp.json()
    assert m["total_projects"] == 0
    assert m["total_conversations"] == 0
    assert m["total_investigations"] == 0

    chart_resp = client.get("/api/admin/chart-data")
    assert chart_resp.status_code == 200
    assert all(d["value"] == 0 for d in chart_resp.json()["days"])

    act_resp = client.get("/api/admin/recent-activity")
    assert act_resp.status_code == 200
    assert act_resp.json()["activities"] == []

    backend_main.app.dependency_overrides.clear()


def test_init_db_contains_all_required_postgres_tables():
    """Verify SQL_POSTGRES_INIT includes entitlements, research_reports, api_keys, and api_usage_logs."""
    ddl = init_db.SQL_POSTGRES_INIT
    for tbl in (
        "public.entitlements",
        "public.research_reports",
        "public.api_keys",
        "public.api_usage_logs",
    ):
        assert tbl in ddl


def test_llm_router_records_token_and_cost_usage(tmp_path: Path, monkeypatch):
    """Verify LLMRouter.generate inserts prompt/completion tokens and cost into operational.db llm_usage."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    op_dir = tmp_path / "operational"
    op_dir.mkdir(parents=True, exist_ok=True)

    mock_primary = MockLLMClient(canned_response="Verified protocol liquidity is $250,000.")
    mock_primary.last_usage = {"prompt_tokens": 120, "completion_tokens": 18}
    router = LLMRouter(primary=mock_primary)

    out = router.generate("You are Zoe.", "Check liquidity.")
    assert "250,000" in out

    conn = sqlite3.connect(str(op_dir / "operational.db"))
    row = conn.execute(
        "SELECT provider, model, prompt_tokens, completion_tokens, estimated_cost_usd FROM llm_usage"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "mock"
    assert row[2] == 120
    assert row[3] == 18
    assert row[4] > 0
