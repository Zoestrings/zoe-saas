"""External Developer API v1 Routes (Pillar 4 & 6).

Provides authenticated REST endpoints for external developers:
- POST /api/v1/chat  (2 credits)
- POST /api/v1/scan  (15 credits)
- POST /api/v1/audit (50 credits)

All endpoints authenticate via `Authorization: Bearer zoe_sk_...` hashed keys,
enforce atomic credit deduction, and log every request to `api_usage_logs`.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import logging
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from zoe.billing.credit_manager import CreditManager
from zoe.llm.factory import get_llm_client
from zoe.tools.scanner import scan_token

logger = logging.getLogger("zoe.api_v1")

router = APIRouter(prefix="/api/v1", tags=["Developer API v1"])


def _hash_api_key(raw_key: str) -> str:
    """Return SHA-256 hex digest of an API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _get_dev_db_conn() -> sqlite3.Connection:
    data_dir = os.getenv("DATA_DIR", "").strip()
    if data_dir:
        db_path = Path(data_dir) / "saas_dev.db"
    else:
        backend_dir = Path(__file__).resolve().parent.parent
        db_path = backend_dir / "saas_dev.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path), timeout=10.0)


def _get_supabase_client() -> Optional[Any]:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key or "your-project" in url:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def _log_api_usage(api_key_id: str, endpoint: str, credits_used: int, status_code: int) -> None:
    """Persist API usage telemetry to Supabase `api_usage_logs` and local SQLite."""
    now_iso = datetime.now(timezone.utc).isoformat()
    log_id = str(uuid.uuid4())

    client = _get_supabase_client()
    if client:
        try:
            client.table("api_usage_logs").insert({
                "id": log_id,
                "api_key_id": api_key_id,
                "endpoint": endpoint,
                "credits_used": credits_used,
                "status_code": status_code,
                "created_at": now_iso,
            }).execute()
        except Exception as exc:
            logger.debug("Supabase api_usage_logs insert failed: %s", exc)

    try:
        conn = _get_dev_db_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dev_api_usage_logs (
                id TEXT PRIMARY KEY,
                api_key_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                credits_used INTEGER NOT NULL,
                status_code INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO dev_api_usage_logs (id, api_key_id, endpoint, credits_used, status_code, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (log_id, api_key_id, endpoint, credits_used, status_code, now_iso),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.debug("SQLite dev_api_usage_logs insert failed: %s", exc)


async def verify_api_key(request: Request) -> Dict[str, str]:
    """FastAPI dependency validating `Authorization: Bearer zoe_sk_...` against hashed keys."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected: Bearer zoe_sk_...",
        )

    raw_key = auth_header[len("Bearer "):].strip()
    if not raw_key.startswith("zoe_sk_") or len(raw_key) < 16:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Zoe API key format.",
        )

    key_hash = _hash_api_key(raw_key)

    # 1. Check Supabase `api_keys` if configured
    client = _get_supabase_client()
    if client:
        try:
            res = (
                client.table("api_keys")
                .select("id, user_id, is_active")
                .eq("key_hash", key_hash)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                row = res.data[0]
                return {"api_key_id": str(row["id"]), "user_id": str(row["user_id"])}
        except Exception as exc:
            logger.debug("Supabase API key lookup error: %s", exc)

    # 2. Check local SQLite `dev_api_keys`
    try:
        conn = _get_dev_db_conn()
        cur = conn.execute(
            "SELECT id, user_id, is_active FROM dev_api_keys WHERE key_hash = ? AND is_active = 1 LIMIT 1",
            (key_hash,),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {"api_key_id": str(row[0]), "user_id": str(row[1])}
    except Exception as exc:
        logger.debug("SQLite API key lookup error: %s", exc)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or revoked Zoe API key.",
    )


class V1ChatRequest(BaseModel):
    prompt: str
    project_id: Optional[str] = "default"


class V1ScanRequest(BaseModel):
    contract_address: str


class V1AuditRequest(BaseModel):
    code: str


@router.post("/chat", response_model=Dict[str, Any])
async def api_v1_chat(
    payload: V1ChatRequest,
    key_ctx: Dict[str, str] = Depends(verify_api_key),
):
    """External Developer Chat endpoint (2 credits per request)."""
    clean_prompt = (payload.prompt or "").strip()
    if not clean_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    user_id = key_ctx["user_id"]
    api_key_id = key_ctx["api_key_id"]
    cost = 2

    ok, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=cost,
        action_type="api_v1_chat",
        metadata={"api_key_id": api_key_id, "project_id": payload.project_id},
    )
    if not ok:
        _log_api_usage(api_key_id, "/api/v1/chat", 0, 402)
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=msg)

    try:
        project_id = (payload.project_id or "default").strip()
        llm = get_llm_client(project_id)
        system_prompt = (
            "You are Zoe, a Web3 Intelligence Engine serving an external developer API request. "
            "Provide concise, accurate, factual answers without financial advice."
        )
        if getattr(llm, "name", "") == "mock":
            # Enrich with live price if asking about a known token
            answer = f"Zoe Intelligence API response for: {clean_prompt}"
        else:
            answer = await asyncio.to_thread(
                llm.generate,
                system_prompt=system_prompt,
                user_prompt=clean_prompt,
                max_tokens=400,
            )

        _log_api_usage(api_key_id, "/api/v1/chat", cost, 200)
        return {
            "response": answer,
            "project_id": project_id,
            "credits_used": cost,
            "credits_remaining": remaining,
        }
    except Exception as exc:
        if tx_id:
            CreditManager.refund_credits(user_id, tx_id, f"API v1 chat failure: {exc}")
        _log_api_usage(api_key_id, "/api/v1/chat", 0, 500)
        raise HTTPException(status_code=500, detail=f"Chat inference failed: {exc}")


@router.post("/scan", response_model=Dict[str, Any])
async def api_v1_scan(
    payload: V1ScanRequest,
    key_ctx: Dict[str, str] = Depends(verify_api_key),
):
    """External Developer Token Scanner endpoint (15 credits per request)."""
    ca = (payload.contract_address or "").strip()
    if not ca:
        raise HTTPException(status_code=400, detail="contract_address is required.")

    user_id = key_ctx["user_id"]
    api_key_id = key_ctx["api_key_id"]
    cost = 15

    ok, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=cost,
        action_type="api_v1_scan",
        metadata={"api_key_id": api_key_id, "contract_address": ca},
    )
    if not ok:
        _log_api_usage(api_key_id, "/api/v1/scan", 0, 402)
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=msg)

    try:
        report = await scan_token(ca)
        _log_api_usage(api_key_id, "/api/v1/scan", cost, 200)
        return {
            "report": report,
            "credits_used": cost,
            "credits_remaining": remaining,
        }
    except Exception as exc:
        if tx_id:
            CreditManager.refund_credits(user_id, tx_id, f"API v1 scan failure: {exc}")
        _log_api_usage(api_key_id, "/api/v1/scan", 0, 500)
        raise HTTPException(status_code=500, detail=f"Token scan failed: {exc}")


@router.post("/audit", response_model=Dict[str, Any])
async def api_v1_audit(
    payload: V1AuditRequest,
    key_ctx: Dict[str, str] = Depends(verify_api_key),
):
    """External Developer Smart Contract Auditor endpoint (50 credits per request)."""
    code = (payload.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Smart contract code cannot be empty.")

    user_id = key_ctx["user_id"]
    api_key_id = key_ctx["api_key_id"]
    cost = 50

    ok, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=cost,
        action_type="api_v1_audit",
        metadata={"api_key_id": api_key_id, "code_length": len(code)},
    )
    if not ok:
        _log_api_usage(api_key_id, "/api/v1/audit", 0, 402)
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=msg)

    try:
        # Static vulnerability heuristics + LLM security review
        findings: List[str] = []
        if re.search(r"\.call\s*\{?\s*value", code) or "tx.origin" in code:
            findings.append("Potential reentrancy or unsafe tx.origin authorization pattern detected.")
        if "selfdestruct" in code or "delegatecall" in code:
            findings.append("High-privilege opcode (selfdestruct/delegatecall) present — verify strict access control.")
        if "unchecked" in code:
            findings.append("Unchecked arithmetic block detected — verify overflow/underflow safety.")

        llm = get_llm_client("default")
        if getattr(llm, "name", "") != "mock":
            audit_summary = await asyncio.to_thread(
                llm.generate,
                system_prompt="You are a Smart Contract Security Auditor. Identify vulnerabilities, access control risks, and remediation steps concisely.",
                user_prompt=f"Audit this smart contract snippet:\n\n{code[:6000]}",
                max_tokens=500,
            )
        else:
            audit_summary = (
                "Static & Heuristic Security Audit completed. "
                + ("Findings: " + " | ".join(findings) if findings else "No critical heuristic patterns flagged; perform full unit/fuzz testing before mainnet deployment.")
            )

        _log_api_usage(api_key_id, "/api/v1/audit", cost, 200)
        return {
            "audit_summary": audit_summary,
            "static_findings": findings,
            "credits_used": cost,
            "credits_remaining": remaining,
        }
    except Exception as exc:
        if tx_id:
            CreditManager.refund_credits(user_id, tx_id, f"API v1 audit failure: {exc}")
        _log_api_usage(api_key_id, "/api/v1/audit", 0, 500)
        raise HTTPException(status_code=500, detail=f"Smart contract audit failed: {exc}")
