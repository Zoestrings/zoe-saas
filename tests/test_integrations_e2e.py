"""Stage G Automated Tests: Telegram & Discord Integration Management."""

from pathlib import Path
import sys
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import main as backend_main


@pytest.fixture
def int_client(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "saas_dev.db"
    monkeypatch.setattr(backend_main, "DEV_DB_PATH", db_file)
    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    conn = backend_main.get_dev_db()
    conn.execute(
        "INSERT INTO dev_projects (id, owner_id, name, telegram_bot_token, created_at) VALUES ('proj_owner_a', 'owner_a', 'Alpha', 'enc', '2026-11-25T00:00:00Z')"
    )
    conn.commit()
    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: {
        "id": "owner_a",
        "email": "a@zoe.ai",
        "role": "project_owner",
    }
    client = TestClient(backend_main.app)
    yield client
    backend_main.app.dependency_overrides.clear()


def test_invalid_telegram_token_rejected(int_client):
    """Invalid Telegram token format or failed getMe must be rejected with 400."""
    resp = int_client.post(
        "/api/integrations/telegram/add",
        json={"project_id": "proj_owner_a", "bot_token": "bad_token"},
    )
    assert resp.status_code == 400


def test_telegram_add_duplicate_prevention_token_secrecy_and_cross_tenant(int_client):
    """Verify valid getMe adds bot, prevents duplicates, hides token, and blocks cross-tenant disconnect."""
    valid_token = "7123456789:AAH_valid_test_token_1234567890"
    with patch("routes.integrations.validate_telegram_token_get_me", new=AsyncMock(return_value={"id": 7123456789, "username": "ZoeAlphaBot"})):
        resp = int_client.post(
            "/api/integrations/telegram/add",
            json={"project_id": "proj_owner_a", "bot_token": valid_token, "chat_id": "-100999"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bot_username"] == "ZoeAlphaBot"
        # Token secrecy: raw/encrypted/hash must NEVER appear in API response
        raw_str = str(data)
        assert valid_token not in raw_str
        assert "encrypted_token" not in data
        assert "token_hash" not in data

        # Duplicate bot prevention
        dup_resp = int_client.post(
            "/api/integrations/telegram/add",
            json={"project_id": "proj_owner_a", "bot_token": valid_token},
        )
        assert dup_resp.status_code == 409

        # Cross-tenant access denial
        backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: {
            "id": "owner_b",
            "email": "b@zoe.ai",
            "role": "project_owner",
        }
        list_b = int_client.get("/api/integrations/telegram/list")
        assert list_b.status_code == 200
        assert list_b.json() == []

        disc_b = int_client.post(f"/api/integrations/telegram/{data['id']}/disconnect")
        assert disc_b.status_code == 403


def test_discord_oauth_start_and_callback(int_client):
    """Verify Discord OAuth2 start returns authorize URL and callback persists sanitized server."""
    start_resp = int_client.get("/api/integrations/discord/oauth/start?project_id=proj_owner_a")
    assert start_resp.status_code == 200
    assert "discord.com/api/oauth2/authorize" in start_resp.json()["oauth_url"]

    cb_resp = int_client.get(
        "/api/integrations/discord/oauth/callback?code=test_code&state=proj_owner_a:owner_a&guild_id=98765&guild_name=AlphaGuild"
    )
    assert cb_resp.status_code == 200
    assert cb_resp.json()["guild_name"] == "AlphaGuild"
    assert "encrypted_secret" not in cb_resp.json()
