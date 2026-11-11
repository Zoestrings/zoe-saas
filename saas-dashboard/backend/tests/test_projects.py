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
        with patch("main.get_supabase", return_value=mock_supabase):
            raw_secret_token = "987654321:AAE_Secr3tB0tT0k3n_Test"
            res = client.post(
                "/api/projects",
                json={
                    "name": "One Love Sailing",
                    "telegram_bot_token": raw_secret_token,
                    "telegram_group_id": "-5214407126"
                }
            )
            assert res.status_code == 201
            data = res.json()
            assert data["name"] == "One Love Sailing"
            assert data["id"] == "project-uuid-1234"

            # Verify the token passed to Supabase insert was encrypted
            assert len(inserted_payloads) == 1
            saved_token = inserted_payloads[0]["telegram_bot_token"]
            assert saved_token != raw_secret_token
            # Verify decrypting it restores the original token
            assert decrypt_token(saved_token) == raw_secret_token
    finally:
        app.dependency_overrides.clear()

