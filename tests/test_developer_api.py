"""Automated Tests for Pillar 4 & 6: Developer API Keys, v1 Endpoints, & Usage Telemetry."""

import hashlib
from pathlib import Path
import sqlite3
import sys
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import main as backend_main
from zoe.billing.credit_manager import CreditManager


@pytest.fixture
def dev_api_client(tmp_path: Path, monkeypatch):
    """TestClient with isolated SQLite DB and authenticated user override."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    db_file = tmp_path / "saas_dev.db"
    monkeypatch.setattr(backend_main, "DEV_DB_PATH", db_file)

    conn = backend_main.get_dev_db()
    CreditManager.ensure_schema(conn)
    conn.execute(
        "INSERT OR REPLACE INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES ('dev_user_001', 'free', 100, '2026-11-25T00:00:00Z')"
    )
    conn.commit()

    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: {
        "id": "dev_user_001",
        "email": "dev@zoe.ai",
        "role": "project_owner",
    }
    client = TestClient(backend_main.app)
    yield client, db_file
    backend_main.app.dependency_overrides.clear()


def test_developer_api_key_lifecycle_and_v1_endpoints(dev_api_client):
    """Verify key generation (hashed storage), /api/v1/chat, /scan, /audit, usage logs, and revocation."""
    client, db_file = dev_api_client

    # 1. Create API key
    create_resp = client.post("/api/developer/keys", json={"key_name": "Prod Trading Bot"})
    assert create_resp.status_code == 200
    created = create_resp.json()
    raw_key = created["api_key"]
    key_id = created["id"]
    assert raw_key.startswith("zoe_sk_")

    # Verify plaintext is NOT stored in DB (only SHA-256 hash)
    conn = sqlite3.connect(str(db_file))
    row = conn.execute("SELECT key_hash, key_prefix FROM dev_api_keys WHERE id = ?", (key_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    assert raw_key not in row[0]

    # 2. List keys returns prefix only
    list_resp = client.get("/api/developer/keys")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert "api_key" not in listed[0]
    assert "key_hash" not in listed[0]
    assert listed[0]["key_prefix"].startswith("zoe_sk_")

    headers = {"Authorization": f"Bearer {raw_key}"}

    # 3. Call POST /api/v1/chat (2 credits: 100 -> 98)
    chat_resp = client.post("/api/v1/chat", json={"prompt": "What is SOL?", "project_id": "default"}, headers=headers)
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["credits_used"] == 2
    assert chat_data["credits_remaining"] == 98

    # 4. Call POST /api/v1/scan (15 credits: 98 -> 83)
    with patch("routes.api_v1.scan_token", new=AsyncMock(return_value={"name": "Solana", "symbol": "SOL"})):
        scan_resp = client.post("/api/v1/scan", json={"contract_address": "So11111111111111111111111111111111111111112"}, headers=headers)
    assert scan_resp.status_code == 200
    assert scan_resp.json()["credits_used"] == 15
    assert scan_resp.json()["credits_remaining"] == 83

    # 5. Call POST /api/v1/audit (50 credits: 83 -> 33)
    audit_resp = client.post("/api/v1/audit", json={"code": "function withdraw() public { msg.sender.call{value: bal}(''); }"}, headers=headers)
    assert audit_resp.status_code == 200
    assert audit_resp.json()["credits_used"] == 50
    assert audit_resp.json()["credits_remaining"] == 33
    assert len(audit_resp.json()["static_findings"]) >= 1

    # 6. Check Usage Telemetry
    usage_resp = client.get("/api/developer/usage")
    assert usage_resp.status_code == 200
    usage = usage_resp.json()
    assert usage["total_requests"] == 3
    assert usage["total_credits_used"] == 67

    # 7. Revoke key -> subsequent v1 request rejected with 401
    rev_resp = client.delete(f"/api/developer/keys/{key_id}")
    assert rev_resp.status_code == 200
    blocked_resp = client.post("/api/v1/chat", json={"prompt": "test"}, headers=headers)
    assert blocked_resp.status_code == 401
