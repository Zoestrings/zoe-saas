"""Comprehensive tests for Social Intelligence, Social Publishing, Web3 Research, Growth & Compliance."""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "saas-dashboard" / "backend"))

from routes.social_growth import build_social_growth_router  # noqa: E402
from zoe.billing.credit_manager import CreditManager  # noqa: E402
from zoe.social.compliance import assert_x_feature_enabled, get_social_compliance_status  # noqa: E402
from zoe.social.publisher import dispatch_due_scheduled_posts, ensure_social_growth_schema  # noqa: E402


def _make_client(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "social_growth_test.db"
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    # Point CreditManager at tmp_path/saas_dev.db
    credit_db = tmp_path / "saas_dev.db"
    c_conn = sqlite3.connect(str(credit_db), check_same_thread=False)
    c_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_entitlements (
            user_id TEXT PRIMARY KEY,
            plan TEXT NOT NULL DEFAULT 'pro',
            credits INTEGER NOT NULL DEFAULT 100,
            expires_at TEXT,
            updated_at TEXT
        )
        """
    )
    c_conn.execute(
        "INSERT OR REPLACE INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES ('owner-a', 'pro', 50, '2026-11-25T00:00:00Z')"
    )
    c_conn.execute(
        "INSERT OR REPLACE INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES ('owner-b', 'free', 0, '2026-11-25T00:00:00Z')"
    )
    c_conn.commit()
    c_conn.close()
    monkeypatch.setattr(CreditManager, "_get_dev_db_path", classmethod(lambda cls: credit_db))

    class _Ctx:
        def __enter__(self):
            self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
            ensure_social_growth_schema(self.conn)
            return self.conn

        def __exit__(self, *args):
            self.conn.close()

    current_user_box = {"user": {"id": "owner-a", "role": "project_owner", "email": "a@example.com"}}

    def _get_user():
        return current_user_box["user"]

    def _require_admin():
        if current_user_box["user"]["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin required")
        return current_user_box["user"]

    app = FastAPI()
    app.include_router(build_social_growth_router(_get_user, _require_admin, lambda: _Ctx()))
    return TestClient(app), current_user_box, _Ctx


def test_x_compliance_flags_disabled_by_default(monkeypatch):
    monkeypatch.delenv("X_API_ENABLED", raising=False)
    monkeypatch.delenv("X_AUTO_REPLY_ENABLED", raising=False)
    monkeypatch.delenv("X_SCRAPING_ENABLED", raising=False)

    status = get_social_compliance_status()
    assert status["x_api_enabled"] is False
    assert status["x_auto_reply_enabled"] is False
    assert status["x_scraping_enabled"] is False

    for feat in ("x_api", "x_auto_reply", "x_scraping", "x_public_analytics"):
        with pytest.raises(PermissionError):
            assert_x_feature_enabled(feat)


def test_social_publishing_approval_schedule_dispatch_and_x_block(tmp_path, monkeypatch):
    client, user_box, ctx_factory = _make_client(tmp_path, monkeypatch)

    # X account connection & X post creation blocked by default compliance policy
    assert client.post("/api/social/accounts", json={"platform": "x", "account_handle": "@test", "credentials": {"token": "sec"}}).status_code == 403
    assert client.post("/api/social/posts", json={"platform": "x", "content": "Hello"}).status_code == 403

    # Encrypted Telegram account stored without exposing credentials
    acc_res = client.post(
        "/api/social/accounts",
        json={"platform": "telegram_channel", "account_handle": "@zoe_chan", "credentials": {"bot_token": "123:secret", "chat_id": "@zoe_chan"}},
    )
    assert acc_res.status_code == 200
    listed = client.get("/api/social/accounts").json()["accounts"]
    assert len(listed) == 1
    assert "encrypted_credentials" not in listed[0]
    assert "123:secret" not in str(listed[0])

    # Generate AI draft -> deducts 2 credits atomically (50 -> 48)
    gen_res = client.post("/api/social/posts/generate", json={"topic": "Solana Ecosystem Update", "platform": "manual_export"})
    assert gen_res.status_code == 200
    post_id = gen_res.json()["post"]["id"]
    assert gen_res.json()["post"]["credits_charged"] == 2
    assert gen_res.json()["post"]["status"] == "draft"

    # Cannot schedule before human approval
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    assert client.post(f"/api/social/posts/{post_id}/schedule", json={"scheduled_for": past_iso}).status_code == 400

    # Submit -> Approve -> Schedule -> Background dispatch
    assert client.post(f"/api/social/posts/{post_id}/submit").status_code == 200
    assert client.post(f"/api/social/posts/{post_id}/approve").status_code == 200
    assert client.post(f"/api/social/posts/{post_id}/schedule", json={"scheduled_for": past_iso}).status_code == 200

    with ctx_factory() as conn:
        dispatched = asyncio.run(dispatch_due_scheduled_posts(conn=conn))
        assert len(dispatched) == 1
        assert dispatched[0]["status"] == "published"
        # Re-running dispatch does not duplicate
        assert asyncio.run(dispatch_due_scheduled_posts(conn=conn)) == []

    # Insufficient credits returns 402
    user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@example.com"}
    assert client.post("/api/social/posts/generate", json={"topic": "No Credits"}).status_code == 402


def test_web3_research_growth_tenant_isolation_and_super_admin_separation(tmp_path, monkeypatch):
    client, user_box, _ = _make_client(tmp_path, monkeypatch)

    # Owner A creates Web3 research & growth opportunity
    res = client.post("/api/research/web3", json={"query": "Solana DeFi", "category": "defi_nft"})
    assert res.status_code == 200
    assert len(res.json()["report"]["sources"]) >= 1

    opp = client.post("/api/growth/opportunities", json={"title": "Q4 Community Campaign", "category": "campaign_opportunity", "priority": "high"})
    assert opp.status_code == 200
    opp_id = opp.json()["opportunity"]["id"]

    # Owner A cannot access Super Admin Market Acquisition Engine
    assert client.get("/api/admin/market-acquisition").status_code == 403
    assert client.post("/api/admin/market-acquisition", json={"project_name": "TargetCo"}).status_code == 403

    # Owner B cannot see or mutate Owner A's research or growth opportunities
    user_box["user"] = {"id": "owner-b", "role": "project_owner", "email": "b@example.com"}
    assert client.get("/api/research/web3").json()["reports"] == []
    assert client.get("/api/growth/opportunities").json()["opportunities"] == []
    assert client.patch(f"/api/growth/opportunities/{opp_id}", json={"status": "completed"}).status_code == 403

    # Super Admin can use Market Acquisition Engine
    user_box["user"] = {"id": "admin-1", "role": "super_admin", "email": "admin@zoe.ai"}
    adm = client.post("/api/admin/market-acquisition", json={"project_name": "Alpha Protocol", "ecosystem": "solana"})
    assert adm.status_code == 200
    assert len(client.get("/api/admin/market-acquisition").json()["leads"]) == 1
