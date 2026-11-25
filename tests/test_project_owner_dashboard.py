"""Project Owner Dashboard Acceptance & Tenant-Isolation Tests."""

from pathlib import Path
import sqlite3
import sys

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "saas-dashboard" / "backend"))

from routes.platform_modules import build_platform_modules_router  # noqa: E402
from zoe.platform_core import ensure_platform_core_schema  # noqa: E402


def test_project_owner_overview_and_analytics_strict_tenant_isolation(tmp_path):
    db_path = tmp_path / "owner_dash_test.db"

    class _Ctx:
        def __enter__(self):
            self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
            ensure_platform_core_schema(self.conn)
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS dev_projects (id TEXT PRIMARY KEY, owner_id TEXT, name TEXT, status TEXT)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS dev_entitlements (user_id TEXT PRIMARY KEY, plan TEXT, credits INTEGER)"
            )
            self.conn.execute("INSERT OR IGNORE INTO dev_projects VALUES ('p-a', 'owner-a', 'Alpha', 'active')")
            self.conn.execute("INSERT OR IGNORE INTO dev_entitlements VALUES ('owner-a', 'pro', 120)")
            self.conn.execute("INSERT OR IGNORE INTO dev_entitlements VALUES ('owner-b', 'free', 15)")
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
    client = TestClient(app)

    # Owner A sees their own project and Pro credits
    ov_a = client.get("/api/owner/overview")
    assert ov_a.status_code == 200
    assert ov_a.json()["projects"]["total"] == 1
    assert ov_a.json()["billing"]["plan"] == "pro"
    assert ov_a.json()["billing"]["credits"] == 120

    an_a = client.get("/api/owner/analytics")
    assert an_a.status_code == 200
    assert an_a.json()["overview"]["projects"]["active"] == 1

    # Owner A cannot access Super Admin routes
    assert client.get("/api/admin/audit-logs").status_code == 403
    assert client.get("/api/admin/users").status_code == 403

    # Owner B sees 0 projects and their own Free plan (15 credits)
    user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@other.io"}
    ov_b = client.get("/api/owner/overview")
    assert ov_b.status_code == 200
    assert ov_b.json()["projects"]["total"] == 0
    assert ov_b.json()["billing"]["plan"] == "free"
    assert ov_b.json()["billing"]["credits"] == 15
