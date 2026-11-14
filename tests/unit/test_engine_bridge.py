"""Test suite verifying Dashboard -> Engine Bridge, BotManager, and internal APIs."""

import asyncio
import os
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from zoe.api import engine_app, bot_manager, redact_token, sanitize_project_id


@pytest.fixture(autouse=True)
def setup_engine_env(monkeypatch, tmp_path):
    """Setup isolated test environment."""
    test_secret = "test_engine_secret_key_1234567890"
    monkeypatch.setenv("ENGINE_SHARED_SECRET", test_secret)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))

    # Isolate config and data dirs
    os.makedirs(tmp_path / "data" / "operational", exist_ok=True)
    os.makedirs(tmp_path / "data" / "official_knowledge", exist_ok=True)
    os.makedirs(tmp_path / "data" / "community_memory", exist_ok=True)
    os.makedirs(tmp_path / "data" / "indexes", exist_ok=True)

    yield test_secret


def test_token_redaction():
    assert redact_token(None) == "[REDACTED]"
    assert redact_token("1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ") == "1234...wxyZ"


def test_sanitize_project_id():
    assert sanitize_project_id("One Love AI") == "one-love-ai"
    assert sanitize_project_id("!!!Test Token!!!") == "test-token"
    assert sanitize_project_id("a") == "project-a"


def test_engine_auth_enforcement(setup_engine_env):
    client = TestClient(engine_app)
    valid_secret = setup_engine_env

    # 1. Missing header -> 401
    resp = client.get("/api/bots/test-proj/status")
    assert resp.status_code == 401

    # 2. Invalid header -> 401
    resp = client.get("/api/bots/test-proj/status", headers={"X-Engine-Key": "wrong-secret"})
    assert resp.status_code == 401

    # 3. Valid header -> succeeds (or 200/404)
    resp = client.get("/api/bots/test-proj/status", headers={"X-Engine-Key": valid_secret})
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"


def test_engine_health_endpoint():
    client = TestClient(engine_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "active_bots" in data


def test_spawn_bot_validation(setup_engine_env):
    client = TestClient(engine_app)
    headers = {"X-Engine-Key": setup_engine_env}

    # Invalid project_id (path traversal attempt)
    resp = client.post(
        "/api/spawn-bot",
        headers=headers,
        json={
            "project_id": "../../etc/passwd",
            "bot_token": "1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZabcdef",
            "token_address": "0x1234567890123456789012345678901234567890",
        },
    )
    assert resp.status_code == 400

    # Invalid bot token format
    resp = client.post(
        "/api/spawn-bot",
        headers=headers,
        json={
            "project_id": "valid-bot",
            "bot_token": "not-a-token",
            "token_address": "0x1234567890123456789012345678901234567890",
        },
    )
    assert resp.status_code == 400


def test_spawn_bot_unlocked_and_patch(setup_engine_env, monkeypatch):
    client = TestClient(engine_app)
    headers = {"X-Engine-Key": setup_engine_env}

    # Mock BotManager._supervisor_loop so it doesn't try live Telegram networking in unit test
    async def mock_supervisor(project_id, config_data, secrets_data, shutdown_event):
        bot_manager.statuses[project_id] = "running"
        await shutdown_event.wait()

    monkeypatch.setattr(bot_manager, "_supervisor_loop", mock_supervisor)

    # 1. Spawn without group_id (unlocked mode)
    resp = client.post(
        "/api/spawn-bot",
        headers=headers,
        json={
            "project_id": "nexus-token",
            "bot_token": "9876543210:ABCdefGhIJKlmNoPQRsTUVwxyZabcdef",
            "token_address": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon",
            "name": "Nexus Token AI",
            "group_id": None,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == "nexus-token"
    assert data["group_id"] == ""
    assert data["status"] in ("starting", "running")

    # 2. Patch to lock to group
    patch_resp = client.patch(
        "/api/bots/nexus-token",
        headers=headers,
        json={"group_id": "-10099887766"},
    )
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    assert patch_data["group_id"] == "-10099887766"

    # 3. Delete / Stop
    del_resp = client.delete("/api/bots/nexus-token", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "stopped"

    # Verify status reflects stopped
    st_resp = client.get("/api/bots/nexus-token/status", headers=headers)
    assert st_resp.json()["status"] == "stopped"
