"""Tests for Zoe SaaS Dashboard backend authentication and project management."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os

from main import app, encrypt_token, decrypt_token, get_current_user


client = TestClient(app)


def test_health_check():
    """Verify backend health endpoint is online."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_unauthenticated_get_projects_returns_401():
    """Test that GET /api/projects strictly rejects unauthenticated requests with 401."""
    response = client.get("/api/projects")
    assert response.status_code == 401
    assert "Missing or invalid authentication token" in response.json()["detail"]


def test_unauthenticated_post_projects_returns_401():
    """Test that POST /api/projects strictly rejects unauthenticated requests with 401."""
    payload = {
        "name": "Alpha Community",
        "telegram_bot_token": "123456789:ABCDEF1234567890abcdef",
        "telegram_group_id": "-100123456789",
    }
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 401
    assert "Missing or invalid authentication token" in response.json()["detail"]


def test_invalid_bearer_token_returns_401():
    """Test that requests with an invalid Bearer token receive 401 Unauthorized."""
    headers = {"Authorization": "Bearer invalid_or_expired_jwt_token_12345"}
    response = client.get("/api/projects", headers=headers)
    assert response.status_code == 401


def test_fernet_token_encryption_roundtrip():
    """Test that Telegram bot tokens are correctly encrypted and can be decrypted."""
    raw_bot_token = "8123456789:AAFlmO4_kLqU9ZexampleTokenSecret"
    encrypted = encrypt_token(raw_bot_token)

    # Encrypted token must never match the plaintext
    assert encrypted != raw_bot_token
    assert len(encrypted) > 40

    # Decryption must restore the original token exactly
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_bot_token


def test_authenticated_create_project_encrypts_token():
    """Test that an authenticated user can create a project and token is encrypted."""
    # Mock current authenticated user
    mock_user = {"id": "11111111-2222-3333-4444-555555555555", "email": "test@example.com"}

    # Mock Supabase table operations
    mock_supabase = MagicMock()
    inserted_payloads = []

    def mock_insert(payload):
        inserted_payloads.append(payload)
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[{
            "id": "project-uuid-1234",
            "owner_id": payload["owner_id"],
            "name": payload["name"],
            "telegram_group_id": payload["telegram_group_id"],
            "created_at": "2026-11-11T00:00:00Z"
        }])
        return mock_query

    mock_supabase.table.return_value.insert = mock_insert

    # Override dependency and Supabase client
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        with patch("main.get_supabase", return_value=mock_supabase), patch("main.call_engine", return_value={"status": "ok", "project_id": "project-uuid-1234"}):
            raw_secret_token = "987654321:AAE_Secr3tB0tT0k3n_Test"
            res = client.post(
                "/api/projects",
                json={
                    "name": "One Love Sailing",
                    "telegram_bot_token": raw_secret_token,
                    "telegram_group_id": "-5214407126",
                    "token_address": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"
                }
            )
            assert res.status_code == 201
            data = res.json()
            assert data["name"] == "One Love Sailing"
            assert "one-love-sailing" in data["id"]

            # Verify the token passed to Supabase insert was encrypted
            assert len(inserted_payloads) == 1
            saved_token = inserted_payloads[0]["telegram_bot_token"]
            assert saved_token != raw_secret_token
            # Verify decrypting it restores the original token
            assert decrypt_token(saved_token) == raw_secret_token
    finally:
        app.dependency_overrides.clear()


def test_knowledge_endpoints_require_authentication():
    """Verify that knowledge endpoints reject unauthenticated requests with 401."""
    res_list = client.get("/api/projects/sample-project/documents")
    assert res_list.status_code == 401

    res_del = client.delete("/api/projects/sample-project/documents/sample.txt")
    assert res_del.status_code == 401

    res_url = client.post("/api/projects/sample-project/ingest-url", json={"url": "https://example.com"})
    assert res_url.status_code == 401

    res_text = client.post("/api/projects/sample-project/ingest-text", json={"text": "sample text"})
    assert res_text.status_code == 401

    res_settings = client.get("/api/projects/sample-project/settings")
    assert res_settings.status_code == 401


def test_knowledge_endpoints_enforce_owner_authorization():
    """Verify that accessing another user's project knowledge returns 403 Forbidden."""
    # User A tries to access User B's project
    user_a = {"id": "user-a-1111", "email": "usera@example.com"}
    app.dependency_overrides[get_current_user] = lambda: user_a

    # Mock Supabase returning project owned by user-b-2222
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "user-b-project", "owner_id": "user-b-2222"}]
    )

    try:
        with patch("main.get_supabase", return_value=mock_supabase):
            res = client.get("/api/projects/user-b-project/documents")
            assert res.status_code == 403
            assert "Access denied" in res.json()["detail"]

            res_del = client.delete("/api/projects/user-b-project/documents/sample.txt")
            assert res_del.status_code == 403

            res_url = client.post("/api/projects/user-b-project/ingest-url", json={"url": "https://example.com"})
            assert res_url.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_unauthenticated_logs_and_analytics_returns_401():
    """Verify that unauthenticated requests to logs and analytics return 401."""
    res_logs = client.get("/api/projects/onelove/logs")
    assert res_logs.status_code == 401

    res_analytics = client.get("/api/projects/onelove/analytics")
    assert res_analytics.status_code == 401


def test_authenticated_get_project_logs():
    """Verify authenticated project owner can fetch conversation logs."""
    user = {"id": "owner-123", "email": "owner@example.com", "role": "super_admin"}
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        res = client.get("/api/projects/onelove/logs")
        assert res.status_code == 200
        logs = res.json()
        assert isinstance(logs, list)
    finally:
        app.dependency_overrides.clear()


def test_authenticated_get_project_analytics():
    """Verify authenticated project owner can fetch analytics metrics."""
    user = {"id": "owner-123", "email": "owner@example.com", "role": "super_admin"}
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        res = client.get("/api/projects/onelove/analytics")
        assert res.status_code == 200
        data = res.json()
        assert "project_id" in data
        assert "total_messages" in data
        assert "total_tokens" in data
        assert "estimated_cost_usd" in data
        assert "ca_scans" in data
    finally:
        app.dependency_overrides.clear()


