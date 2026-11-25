"""18-Point Security, Tenant-Isolation, and Platform Core Acceptance Tests."""

from pathlib import Path
import sqlite3
import sys

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "saas-dashboard" / "backend"))

from routes.platform_modules import build_platform_modules_router  # noqa: E402
from zoe.platform_core import acquire_scheduler_lock, ensure_platform_core_schema  # noqa: E402


def _make_platform_client(tmp_path: Path):
    db_path = tmp_path / "platform_core_test.db"

    class _Ctx:
        def __enter__(self):
            self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
            ensure_platform_core_schema(self.conn)
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dev_users (
                    id TEXT PRIMARY KEY, email TEXT, role TEXT, created_at TEXT
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dev_entitlements (
                    user_id TEXT PRIMARY KEY, plan TEXT, credits INTEGER
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS platform_integrations (
                    id TEXT PRIMARY KEY, owner_id TEXT, project_id TEXT, platform TEXT,
                    bot_username TEXT, encrypted_token TEXT, status TEXT, last_error TEXT,
                    created_at TEXT, updated_at TEXT
                )
                """
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO dev_users VALUES ('owner-a', 'a@proj.io', 'project_owner', '2026-11-25T00:00:00Z')"
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO platform_integrations VALUES ('int-1', 'owner-a', 'p-1', 'telegram', '@zoe_a', 'aes256gcm:SECRET_BLOB', 'active', NULL, '2026-11-25T00:00:00Z', '2026-11-25T00:00:00Z')"
            )
            self.conn.commit()
            return self.conn

        def __exit__(self, *args):
            self.conn.close()

    user_box = {"user": {"id": "owner-a", "role": "project_owner", "email": "a@proj.io"}}

    def _get_user():
        return user_box["user"]

    def _require_admin():
        if user_box["user"]["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin required")
        return user_box["user"]

    app = FastAPI()
    app.include_router(build_platform_modules_router(_get_user, _require_admin, lambda: _Ctx()))
    return TestClient(app), user_box, _Ctx


def test_super_admin_global_controls_audit_logs_and_secret_stripping(tmp_path):
    client, user_box, _ = _make_platform_client(tmp_path)

    # Project owner rejected from all Super Admin endpoints
    assert client.get("/api/admin/audit-logs").status_code == 403
    assert client.get("/api/admin/integrations/overview").status_code == 403
    assert client.get("/api/admin/users").status_code == 403
    assert client.post("/api/admin/ai-config", json={"primary_provider": "groq", "fallback_provider": "gemini", "default_model": "llama-3.3-70b-versatile", "max_tokens": 1024}).status_code == 403

    # Super Admin authorized access
    user_box["user"] = {"id": "admin-1", "role": "super_admin", "email": "admin@zoe.ai"}
    int_res = client.get("/api/admin/integrations/overview")
    assert int_res.status_code == 200
    assert int_res.json()["summary"]["total_integrations"] == 1
    assert "SECRET_BLOB" not in int_res.text

    # AI config & User role updates write immutable audit logs
    assert client.post("/api/admin/ai-config", json={"primary_provider": "groq", "fallback_provider": "gemini", "default_model": "llama-3.3-70b-versatile", "max_tokens": 2048}).status_code == 200
    assert client.post("/api/admin/users/owner-a/role", json={"role": "suspended"}).status_code == 200

    logs = client.get("/api/admin/audit-logs").json()["logs"]
    actions = {l["action"] for l in logs}
    assert "update_ai_config" in actions
    assert "update_user_role" in actions


def test_team_rbac_nft_growth_invoices_and_investor_isolation(tmp_path):
    client, user_box, ctx_factory = _make_platform_client(tmp_path)

    # Owner A creates team invite, NFT collection, invoice, and private investor entry
    assert client.post("/api/owner/team/invite", json={"member_email": "dev@proj.io", "role": "editor"}).status_code == 200
    assert client.post("/api/nft-growth/collections", json={"name": "Zoe Genesis", "chain": "solana"}).status_code == 200
    assert client.post("/api/billing/invoices/generate", json={"amount_usdt": 49.0, "plan": "pro"}).status_code == 200
    inv = client.post("/api/investor-intelligence/pipeline", json={"investor_name": "Solana Ventures", "firm_type": "vc"})
    assert inv.status_code == 200
    inv_id = inv.json()["entry"]["id"]

    # Viewer role cannot invite team members
    user_box["user"] = {"id": "owner-a", "role": "project_owner", "email": "viewer@proj.io", "team_role": "viewer"}
    assert client.post("/api/owner/team/invite", json={"member_email": "x@proj.io", "role": "viewer"}).status_code == 403

    # Owner B cannot see or mutate Owner A's team, NFT collections, invoices, or investor pipeline
    user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@other.io"}
    assert client.get("/api/owner/team").json()["members"] == []
    assert client.get("/api/nft-growth/collections").json()["collections"] == []
    assert client.get("/api/billing/invoices").json()["invoices"] == []
    assert client.get("/api/investor-intelligence/pipeline").json()["pipeline"] == []
    assert client.patch(f"/api/investor-intelligence/pipeline/{inv_id}", json={"stage": "committed"}).status_code == 403
    assert client.delete(f"/api/investor-intelligence/pipeline/{inv_id}").status_code == 403

    # Scheduler lock prevents concurrent worker duplicate execution
    with ctx_factory() as conn:
        assert acquire_scheduler_lock(conn, "monitoring_cycle", worker_id="worker-1", ttl_seconds=60) is True
        assert acquire_scheduler_lock(conn, "monitoring_cycle", worker_id="worker-2", ttl_seconds=60) is False
