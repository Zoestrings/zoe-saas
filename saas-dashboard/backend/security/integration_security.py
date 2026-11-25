"""Stage B: Integration Credential Security (AES-256-GCM) & Tenant Ownership Verification.

Guarantees:
1. All Telegram bot tokens and Discord secrets are encrypted at rest with AES-256-GCM.
2. Deterministic SHA-256 token hashes allow duplicate bot checks without exposing plaintext.
3. `sanitize_integration_record()` strips all encrypted blobs and hashes before returning any API response.
4. `verify_integration_ownership()` enforces strict multi-tenant isolation.
"""

import base64
import hashlib
import os
import sqlite3
from typing import Any, Callable, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status


def _derive_aes256_key() -> bytes:
    """Derive a 32-byte (256-bit) AES key from ENCRYPTION_KEY."""
    raw = os.getenv("ENCRYPTION_KEY", "").strip()
    if not raw or raw == "your-fernet-encryption-key":
        # Generate persistent process-scoped secret if missing in dev
        raw = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        os.environ["ENCRYPTION_KEY"] = raw
    return hashlib.sha256(raw.encode("utf-8")).digest()


def encrypt_credential_aes256(plaintext: str) -> str:
    """Encrypt a sensitive credential using AES-256-GCM with random 96-bit nonce."""
    clean = (plaintext or "").strip()
    if not clean:
        raise ValueError("Credential cannot be empty.")
    key = _derive_aes256_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, clean.encode("utf-8"), None)
    payload = base64.urlsafe_b64encode(nonce + ct).decode("utf-8")
    return f"aes256gcm:{payload}"


def decrypt_credential_aes256(ciphertext: str) -> str:
    """Decrypt an AES-256-GCM encrypted credential."""
    if not ciphertext:
        raise ValueError("Ciphertext cannot be empty.")
    if not ciphertext.startswith("aes256gcm:"):
        raise ValueError("Unsupported credential encryption format.")
    b64_part = ciphertext[len("aes256gcm:"):]
    raw = base64.urlsafe_b64decode(b64_part.encode("utf-8"))
    nonce, ct = raw[:12], raw[12:]
    key = _derive_aes256_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def hash_credential(plaintext: str) -> str:
    """Return SHA-256 hex digest of a credential for duplicate detection."""
    return hashlib.sha256((plaintext or "").strip().encode("utf-8")).hexdigest()


def sanitize_integration_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Strip all sensitive token/secret fields so credentials NEVER reach the frontend."""
    forbidden_keys = {
        "encrypted_token",
        "token_hash",
        "encrypted_secret",
        "bot_token",
        "telegram_bot_token",
        "client_secret",
        "discord_token",
    }
    return {k: v for k, v in record.items() if k not in forbidden_keys}


def verify_integration_ownership(
    integration_id: str,
    user_id: str,
    user_role: str = "project_owner",
    supabase_client: Optional[Any] = None,
    dev_db_getter: Optional[Callable[[], sqlite3.Connection]] = None,
) -> Dict[str, Any]:
    """Verify that `integration_id` exists and belongs to `user_id` (unless `super_admin`).

    Returns the sanitized integration record or raises 401/403/404.
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
        )

    record: Optional[Dict[str, Any]] = None

    if supabase_client is not None:
        try:
            res = (
                supabase_client.table("platform_integrations")
                .select("*")
                .eq("id", str(integration_id))
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                record = dict(res.data[0])
        except Exception:
            record = None

    if record is None and dev_db_getter is not None:
        conn = dev_db_getter()
        cur = conn.execute(
            """
            SELECT id, organization_id, project_id, owner_id, platform, bot_username,
                   bot_external_id, status, permissions_json, created_at, updated_at
            FROM platform_integrations
            WHERE id = ?
            LIMIT 1
            """,
            (str(integration_id),),
        )
        row = cur.fetchone()
        if row:
            record = {
                "id": str(row[0]),
                "organization_id": str(row[1]),
                "project_id": str(row[2]),
                "owner_id": str(row[3]),
                "platform": str(row[4]),
                "bot_username": row[5],
                "bot_external_id": row[6],
                "status": str(row[7]),
                "permissions_json": row[8],
                "created_at": str(row[9]),
                "updated_at": str(row[10]),
            }

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found.",
        )

    if user_role != "super_admin" and str(record.get("owner_id")) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this integration.",
        )

    return sanitize_integration_record(record)
