"""Tests for scanner role-aware routing, tenant isolation, and Super Admin boundaries."""

from pathlib import Path
import json
import sqlite3
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "saas-dashboard" / "backend"))

import main as backend_main  # noqa: E402


def _setup_dev_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "scanner_routing_test.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_investigations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            token_name TEXT,
            risk_level TEXT,
            report_json TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def test_unauthenticated_scanner_endpoints_return_401():
    client = TestClient(backend_main.app)
    res_get = client.get("/api/investigations")
    assert res_get.status_code == 401

    res_post = client.post("/api/investigate", json={"contract_address": "0x1234567890abcdef"})
    assert res_post.status_code == 401


def test_investigation_history_tenant_isolation_and_super_admin_global_view(tmp_path, monkeypatch):
    conn = _setup_dev_db(tmp_path)
    conn.execute(
        "INSERT INTO dev_investigations VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "inv-a",
            "owner-a",
            "0xAAA",
            "AlphaToken",
            "LOW",
            json.dumps({"ca": "0xAAA", "name": "AlphaToken", "risk_level": "LOW"}),
            "2026-11-25T10:00:00Z",
        ),
    )
    conn.execute(
        "INSERT INTO dev_investigations VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "inv-b",
            "owner-b",
            "0xBBB",
            "BetaToken",
            "HIGH",
            json.dumps({"ca": "0xBBB", "name": "BetaToken", "risk_level": "HIGH"}),
            "2026-11-25T11:00:00Z",
        ),
    )
    conn.commit()

    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    monkeypatch.setattr(backend_main, "get_dev_db", lambda: conn)

    user_box = {"user": {"id": "owner-a", "role": "project_owner", "email": "a@proj.io"}}
    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: user_box["user"]

    try:
        client = TestClient(backend_main.app)

        # 1. Project Owner A sees only Owner A's scan history
        res_a = client.get("/api/investigations")
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert len(data_a) == 1
        assert data_a[0]["id"] == "inv-a"
        assert data_a[0]["user_id"] == "owner-a"

        # 2. Project Owner A cannot request cross-tenant history
        res_forbidden = client.get("/api/investigations?all_tenants=true")
        assert res_forbidden.status_code == 403

        # 3. Project Owner B sees only Owner B's scan history
        user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@proj.io"}
        res_b = client.get("/api/investigations")
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert len(data_b) == 1
        assert data_b[0]["id"] == "inv-b"

        # 4. Super Admin with all_tenants=true sees global scan history
        user_box["user"] = {"id": "admin-1", "role": "super_admin", "email": "admin@zoe.ai"}
        res_admin_global = client.get("/api/investigations?all_tenants=true")
        assert res_admin_global.status_code == 200
        global_ids = {item["id"] for item in res_admin_global.json()}
        assert global_ids == {"inv-a", "inv-b"}

        # 5. Super Admin without all_tenants sees only their own scans (0 here)
        res_admin_own = client.get("/api/investigations")
        assert res_admin_own.status_code == 200
        assert res_admin_own.json() == []
    finally:
        backend_main.app.dependency_overrides.clear()
        conn.close()


def test_post_investigate_persists_under_authenticated_session_user(tmp_path, monkeypatch):
    conn = _setup_dev_db(tmp_path)
    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    monkeypatch.setattr(backend_main, "get_dev_db", lambda: conn)

    async def _fake_scan(ca: str):
        return {
            "valid": True,
            "ca": ca,
            "name": "OwnerScannedToken",
            "symbol": "OST",
            "risk": {"level": "LOW", "score": 12},
        }

    async def _fake_x_sentiment(target: str):
        return {"sentiment": "Neutral", "summary": "Test", "top_narratives": [], "bullish_factors": [], "bearish_factors": []}

    async def _fake_events(target: str):
        return []

    import zoe.tools.scanner as scanner_mod
    import zoe.tools.x_intel as x_intel_mod
    import zoe.tools.catalyst as catalyst_mod

    monkeypatch.setattr(scanner_mod, "scan_solana_token", _fake_scan)
    monkeypatch.setattr(x_intel_mod, "analyze_x_sentiment", _fake_x_sentiment)
    monkeypatch.setattr(catalyst_mod, "get_upcoming_events", _fake_events)

    user_box = {"user": {"id": "owner-a", "role": "project_owner", "email": "a@proj.io"}}
    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: user_box["user"]

    try:
        client = TestClient(backend_main.app)
        res = client.post(
            "/api/investigate",
            json={"contract_address": "0xOwnerToken123"},
        )
        assert res.status_code == 200
        assert res.json()["name"] == "OwnerScannedToken"

        # Verify persisted under owner-a, not visible to owner-b
        res_a = client.get("/api/investigations")
        assert res_a.status_code == 200
        assert len(res_a.json()) == 1
        assert res_a.json()[0]["contract_address"] == "0xOwnerToken123"
        assert res_a.json()[0]["user_id"] == "owner-a"

        user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@proj.io"}
        res_b = client.get("/api/investigations")
        assert res_b.status_code == 200
        assert res_b.json() == []
    finally:
        backend_main.app.dependency_overrides.clear()
        conn.close()


def test_frontend_layouts_enforce_role_aware_shell_and_owner_routes():
    frontend_src = ROOT / "saas-dashboard" / "frontend" / "src"

    for route in ("investigate", "watchlist", "community"):
        layout_text = (frontend_src / "app" / route / "layout.tsx").read_text(encoding="utf-8")
        assert "RoleAwareShell" in layout_text
        assert "AdminSidebar" not in layout_text
        assert "AdminHeader" not in layout_text

    shell_text = (frontend_src / "components" / "layout" / "role-aware-shell.tsx").read_text(encoding="utf-8")
    assert 'router.replace("/login")' in shell_text
    assert "isSuperAdmin()" in shell_text
    assert "<OwnerLayout>" in shell_text
    assert "<AdminSidebar />" in shell_text

    owner_investigate = frontend_src / "app" / "owner" / "investigate" / "page.tsx"
    assert owner_investigate.exists()
    assert "InvestigatePage" in owner_investigate.read_text(encoding="utf-8")

    owner_layout = (frontend_src / "app" / "owner" / "layout.tsx").read_text(encoding="utf-8")
    assert 'href: "/owner/investigate"' in owner_layout

    owner_dashboard = (frontend_src / "app" / "owner" / "dashboard" / "page.tsx").read_text(encoding="utf-8")
    assert 'href="/owner/investigate"' in owner_dashboard

    owner_billing = (frontend_src / "app" / "owner" / "billing" / "page.tsx").read_text(encoding="utf-8")
    assert 'href="/owner/investigate"' in owner_billing
