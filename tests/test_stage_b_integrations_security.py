"""Automated Tests for Stage B: Integration Database Schema, AES-256 Encryption, & Tenant Isolation."""

from pathlib import Path
import sys
import pytest
from fastapi import HTTPException

backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import init_db
import main as backend_main
from security.integration_security import (
    decrypt_credential_aes256,
    encrypt_credential_aes256,
    hash_credential,
    sanitize_integration_record,
)


def test_aes256_encryption_and_hashing():
    """Verify AES-256-GCM encryption roundtrip and deterministic SHA-256 hashing."""
    secret_token = "7123456789:AAH_super_secret_bot_token_xyz"
    encrypted = encrypt_credential_aes256(secret_token)
    assert encrypted.startswith("aes256gcm:")
    assert secret_token not in encrypted

    decrypted = decrypt_credential_aes256(encrypted)
    assert decrypted == secret_token

    h1 = hash_credential(secret_token)
    h2 = hash_credential(f"  {secret_token}  ")
    assert h1 == h2
    assert len(h1) == 64


def test_sanitize_integration_record_strips_secrets():
    """Verify no token or secret field can ever appear in API responses."""
    raw = {
        "id": "int_1",
        "project_id": "proj_1",
        "platform": "telegram",
        "bot_username": "ZoeTestBot",
        "encrypted_token": "aes256gcm:abc",
        "token_hash": "deadbeef",
        "encrypted_secret": "aes256gcm:def",
        "bot_token": "123:plaintext",
        "client_secret": "discord_secret",
    }
    clean = sanitize_integration_record(raw)
    assert clean["id"] == "int_1"
    assert clean["bot_username"] == "ZoeTestBot"
    for forbidden in ("encrypted_token", "token_hash", "encrypted_secret", "bot_token", "client_secret"):
        assert forbidden not in clean


def test_stage_b_schema_and_verify_integration_ownership(tmp_path: Path, monkeypatch):
    """Verify SQLite/Postgres DDL tables and strict cross-tenant ownership enforcement."""
    # 1. Verify PostgreSQL DDL contains all 4 tables
    for tbl in (
        "public.platform_integrations",
        "public.telegram_communities",
        "public.discord_servers",
        "public.integration_activity_logs",
    ):
        assert tbl in init_db.SQL_POSTGRES_INIT

    # 2. Initialize isolated SQLite dev DB
    db_file = tmp_path / "saas_dev.db"
    monkeypatch.setattr(backend_main, "DEV_DB_PATH", db_file)
    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    conn = backend_main.get_dev_db()

    conn.execute(
        "INSERT INTO dev_projects (id, owner_id, name, telegram_bot_token, created_at) VALUES ('proj_a', 'owner_a', 'Alpha', 'enc', '2026-11-25T00:00:00Z')"
    )
    conn.execute(
        """
        INSERT INTO platform_integrations (
            id, organization_id, project_id, owner_id, platform, bot_username,
            encrypted_token, token_hash, status, created_at, updated_at
        ) VALUES (
            'int_alpha_1', 'org_a', 'proj_a', 'owner_a', 'telegram', 'AlphaBot',
            'aes256gcm:secret', 'hash123', 'connected', '2026-11-25T00:00:00Z', '2026-11-25T00:00:00Z'
        )
        """
    )
    conn.commit()

    # Rightful owner succeeds and receives sanitized record
    rec = backend_main.verify_integration_ownership("int_alpha_1", "owner_a", "project_owner")
    assert rec["id"] == "int_alpha_1"
    assert "encrypted_token" not in rec
    assert "token_hash" not in rec

    # Cross-tenant owner B gets 403 Forbidden
    with pytest.raises(HTTPException) as exc_403:
        backend_main.verify_integration_ownership("int_alpha_1", "owner_b", "project_owner")
    assert exc_403.value.status_code == 403

    # Super Admin succeeds
    admin_rec = backend_main.verify_integration_ownership("int_alpha_1", "admin_1", "super_admin")
    assert admin_rec["id"] == "int_alpha_1"

    # Missing integration returns 404
    with pytest.raises(HTTPException) as exc_404:
        backend_main.verify_integration_ownership("nonexistent_id", "owner_a", "project_owner")
    assert exc_404.value.status_code == 404
