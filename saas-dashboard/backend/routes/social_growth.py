"""Social Intelligence, Social Publishing, Web3 Research & Growth Intelligence API Routes."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Callable, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from security.integration_security import decrypt_credential_aes256, encrypt_credential_aes256
from zoe.billing.credit_manager import CreditManager, DEFAULT_ACTION_COSTS
from zoe.social.compliance import assert_x_feature_enabled, get_social_compliance_status
from zoe.social.growth_intel import compute_growth_analytics, get_permitted_social_trends
from zoe.social.publisher import (
    ensure_social_growth_schema,
    generate_ai_post_draft,
    publish_post_record,
)
from zoe.social.research_engine import run_web3_research

logger = logging.getLogger("zoe.api.social_growth")


class CampaignCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    objective: str = ""
    target_audience: str = ""
    project_id: Optional[str] = None


class PostCreateRequest(BaseModel):
    campaign_id: Optional[str] = None
    project_id: Optional[str] = None
    platform: str = Field(default="manual_export")
    title: str = ""
    content: str = Field(..., min_length=1, max_length=4000)


class PostGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    platform: str = "telegram_channel"
    tone: str = "informative"
    campaign_id: Optional[str] = None
    project_id: Optional[str] = None


class PostRejectRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500)


class PostScheduleRequest(BaseModel):
    scheduled_for: str = Field(..., min_length=10, max_length=64)


class SocialAccountCreateRequest(BaseModel):
    platform: str = Field(..., min_length=1, max_length=40)
    account_handle: str = Field(..., min_length=2, max_length=120)
    credentials: Dict[str, Any] = Field(default_factory=dict)


class Web3ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=300)
    category: str = "ecosystem"
    project_id: Optional[str] = None


class WatchlistCreateRequest(BaseModel):
    topic_or_project: str = Field(..., min_length=2, max_length=150)
    category: str = "ecosystem"


class GrowthOpportunityCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=160)
    category: str = "campaign_opportunity"
    priority: str = "medium"
    notes: str = ""
    source_attribution: str = ""
    project_id: Optional[str] = None


class GrowthOpportunityUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class MarketAcquisitionCreateRequest(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=150)
    ecosystem: str = "solana"
    contact_channel: str = ""
    stage: str = "identified"
    notes: str = ""


def _charge_action_credits(user_id: str, action_type: str, role: str) -> int:
    if role == "super_admin":
        return 0
    cost = int(DEFAULT_ACTION_COSTS.get(action_type, 2))
    ok, msg, _balance, _tx = CreditManager.deduct_credits(
        user_id=str(user_id),
        amount=cost,
        action_type=action_type,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits for '{action_type}' ({cost} required): {msg}",
        )
    return cost


def _post_row_to_dict(r: Any) -> Dict[str, Any]:
    return {
        "id": r[0],
        "campaign_id": r[1],
        "user_id": r[2],
        "organization_id": r[3],
        "project_id": r[4],
        "platform": r[5],
        "title": r[6],
        "content": r[7],
        "status": r[8],
        "scheduled_for": r[9],
        "published_at": r[10],
        "approved_by": r[11],
        "rejection_reason": r[12],
        "ai_generated": bool(r[13]),
        "credits_charged": int(r[14] or 0),
        "external_post_id": r[15],
        "error_message": r[16],
        "created_at": r[17],
        "updated_at": r[18],
    }


def build_social_growth_router(
    get_current_user: Callable[..., Any],
    require_super_admin: Callable[..., Any],
    get_dev_db: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(tags=["Social Intelligence & Growth Engine"])

    @router.get("/api/social/compliance-status")
    async def social_compliance_status(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        return get_social_compliance_status()

    # ── Campaigns ──────────────────────────────────────────────────────────────
    @router.post("/api/social/campaigns")
    async def create_campaign(
        payload: CampaignCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        cid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT INTO social_campaigns (id, user_id, organization_id, project_id, name, objective, target_audience, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (cid, user_id, org_id, payload.project_id, payload.name.strip(), payload.objective, payload.target_audience, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "campaign": {"id": cid, "name": payload.name.strip(), "objective": payload.objective, "target_audience": payload.target_audience, "status": "active", "created_at": now_iso}}

    @router.get("/api/social/campaigns")
    async def list_campaigns(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            rows = conn.execute(
                "SELECT id, user_id, organization_id, project_id, name, objective, target_audience, status, created_at, updated_at FROM social_campaigns WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return {
            "campaigns": [
                {
                    "id": r[0], "user_id": r[1], "organization_id": r[2], "project_id": r[3],
                    "name": r[4], "objective": r[5], "target_audience": r[6], "status": r[7],
                    "created_at": r[8], "updated_at": r[9],
                }
                for r in rows
            ]
        }

    # ── Posts & AI Drafts ──────────────────────────────────────────────────────
    @router.post("/api/social/posts")
    async def create_post_draft(
        payload: PostCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        if payload.platform == "x":
            try:
                assert_x_feature_enabled("x_api")
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        pid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT INTO social_posts (
                    id, campaign_id, user_id, organization_id, project_id, platform,
                    title, content, status, ai_generated, credits_charged, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, 0, ?, ?)
                """,
                (pid, payload.campaign_id, user_id, org_id, payload.project_id, payload.platform, payload.title, payload.content, now_iso, now_iso),
            )
            conn.commit()
            row = conn.execute(
                "SELECT id, campaign_id, user_id, organization_id, project_id, platform, title, content, status, scheduled_for, published_at, approved_by, rejection_reason, ai_generated, credits_charged, external_post_id, error_message, created_at, updated_at FROM social_posts WHERE id = ?",
                (pid,),
            ).fetchone()
        return {"status": "ok", "post": _post_row_to_dict(row)}

    @router.post("/api/social/posts/generate")
    async def generate_social_post_draft_endpoint(
        payload: PostGenerateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        org_id = str(current_user.get("organization_id") or user_id)

        credits_used = _charge_action_credits(user_id, "social_draft", role)
        draft = await generate_ai_post_draft(topic=payload.topic, platform=payload.platform, tone=payload.tone)

        pid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT INTO social_posts (
                    id, campaign_id, user_id, organization_id, project_id, platform,
                    title, content, status, ai_generated, credits_charged, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', 1, ?, ?, ?)
                """,
                (pid, payload.campaign_id, user_id, org_id, payload.project_id, payload.platform, draft["title"], draft["content"], credits_used, now_iso, now_iso),
            )
            conn.commit()
            row = conn.execute(
                "SELECT id, campaign_id, user_id, organization_id, project_id, platform, title, content, status, scheduled_for, published_at, approved_by, rejection_reason, ai_generated, credits_charged, external_post_id, error_message, created_at, updated_at FROM social_posts WHERE id = ?",
                (pid,),
            ).fetchone()
        return {"status": "ok", "post": _post_row_to_dict(row), "ai_disclosure": draft["ai_disclosure"]}

    @router.get("/api/social/posts")
    async def list_posts(
        status_filter: Optional[str] = Query(default=None),
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            q = """
                SELECT id, campaign_id, user_id, organization_id, project_id, platform, title, content,
                       status, scheduled_for, published_at, approved_by, rejection_reason, ai_generated,
                       credits_charged, external_post_id, error_message, created_at, updated_at
                FROM social_posts WHERE user_id = ?
            """
            params: List[Any] = [user_id]
            if status_filter:
                q += " AND status = ?"
                params.append(status_filter)
            q += " ORDER BY created_at DESC"
            rows = conn.execute(q, params).fetchall()
        return {"posts": [_post_row_to_dict(r) for r in rows]}

    def _assert_post_owner(conn: Any, post_id: str, user_id: str, role: str) -> Any:
        row = conn.execute("SELECT user_id, status, platform FROM social_posts WHERE id = ?", (post_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if str(row[0]) != user_id and role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return row

    @router.post("/api/social/posts/{post_id}/submit")
    async def submit_post_for_approval(
        post_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            _assert_post_owner(conn, post_id, user_id, role)
            conn.execute("UPDATE social_posts SET status = 'pending_approval', updated_at = ? WHERE id = ?", (now_iso, post_id))
            conn.commit()
        return {"status": "ok", "post_id": post_id, "new_status": "pending_approval"}

    @router.post("/api/social/posts/{post_id}/approve")
    async def approve_post(
        post_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        approver = str(current_user.get("email") or user_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            _assert_post_owner(conn, post_id, user_id, role)
            conn.execute(
                "UPDATE social_posts SET status = 'approved', approved_by = ?, rejection_reason = NULL, updated_at = ? WHERE id = ?",
                (approver, now_iso, post_id),
            )
            conn.commit()
        return {"status": "ok", "post_id": post_id, "new_status": "approved", "approved_by": approver}

    @router.post("/api/social/posts/{post_id}/reject")
    async def reject_post(
        post_id: str,
        payload: PostRejectRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            _assert_post_owner(conn, post_id, user_id, role)
            conn.execute(
                "UPDATE social_posts SET status = 'rejected', rejection_reason = ?, updated_at = ? WHERE id = ?",
                (payload.reason, now_iso, post_id),
            )
            conn.commit()
        return {"status": "ok", "post_id": post_id, "new_status": "rejected"}

    @router.post("/api/social/posts/{post_id}/schedule")
    async def schedule_post(
        post_id: str,
        payload: PostScheduleRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            row = _assert_post_owner(conn, post_id, user_id, role)
            if str(row[1]) != "approved":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Human approval is required before scheduling a post.",
                )
            conn.execute(
                "UPDATE social_posts SET status = 'scheduled', scheduled_for = ?, updated_at = ? WHERE id = ?",
                (payload.scheduled_for, now_iso, post_id),
            )
            conn.commit()
        return {"status": "ok", "post_id": post_id, "new_status": "scheduled", "scheduled_for": payload.scheduled_for}

    @router.post("/api/social/posts/{post_id}/publish-now")
    async def publish_post_now(
        post_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            row = _assert_post_owner(conn, post_id, user_id, role)
            platform = str(row[2])
            creds: Optional[Dict[str, Any]] = None
            acc = conn.execute(
                "SELECT encrypted_credentials FROM social_accounts WHERE user_id = ? AND platform = ? AND is_active = 1 LIMIT 1",
                (user_id, platform),
            ).fetchone()
            if acc and acc[0]:
                creds = json.loads(decrypt_credential_aes256(str(acc[0])))
            try:
                res = await publish_post_record(post_id, conn, credentials=creds)
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        return res

    @router.delete("/api/social/posts/{post_id}")
    async def delete_post(
        post_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            _assert_post_owner(conn, post_id, user_id, role)
            conn.execute("DELETE FROM social_posts WHERE id = ?", (post_id,))
            conn.commit()
        return {"status": "deleted", "post_id": post_id}

    # ── Encrypted Social Accounts (No Secret Exposure) ─────────────────────────
    @router.post("/api/social/accounts")
    async def connect_social_account(
        payload: SocialAccountCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        platform = payload.platform.strip().lower()
        if platform == "x":
            try:
                assert_x_feature_enabled("x_api")
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        aid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        encrypted = encrypt_credential_aes256(json.dumps(payload.credentials))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT INTO social_accounts (id, user_id, organization_id, platform, account_handle, encrypted_credentials, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(user_id, platform, account_handle) DO UPDATE SET
                    encrypted_credentials = excluded.encrypted_credentials,
                    is_active = 1,
                    updated_at = excluded.updated_at
                """,
                (aid, user_id, org_id, platform, payload.account_handle.strip(), encrypted, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "account": {"platform": platform, "account_handle": payload.account_handle.strip(), "is_active": True}}

    @router.get("/api/social/accounts")
    async def list_social_accounts(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            rows = conn.execute(
                "SELECT id, platform, account_handle, is_active, created_at FROM social_accounts WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return {
            "accounts": [
                {"id": r[0], "platform": r[1], "account_handle": r[2], "is_active": bool(r[3]), "created_at": r[4]}
                for r in rows
            ]
        }

    # ── Web3 Research Engine & Watchlists ──────────────────────────────────────
    @router.post("/api/research/web3")
    async def create_web3_research(
        payload: Web3ResearchRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        org_id = str(current_user.get("organization_id") or user_id)
        _charge_action_credits(user_id, "web3_research", role)
        with get_dev_db() as conn:
            report = await run_web3_research(
                user_id=user_id,
                organization_id=org_id,
                query=payload.query,
                category=payload.category,
                project_id=payload.project_id,
                conn=conn,
            )
        return {"status": "ok", "report": report}

    @router.get("/api/research/web3")
    async def list_web3_research(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            rows = conn.execute(
                "SELECT id, category, query, title, summary, sources_json, data_json, created_at FROM web3_research_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
                (user_id,),
            ).fetchall()
        return {
            "reports": [
                {
                    "id": r[0], "category": r[1], "query": r[2], "title": r[3],
                    "summary": r[4], "sources": json.loads(r[5]), "data": json.loads(r[6]),
                    "created_at": r[7],
                }
                for r in rows
            ]
        }

    @router.post("/api/research/watchlists")
    async def add_research_watchlist(
        payload: WatchlistCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        wid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO research_watchlists (id, user_id, organization_id, topic_or_project, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (wid, user_id, org_id, payload.topic_or_project.strip(), payload.category.strip(), now_iso),
            )
            conn.commit()
        return {"status": "ok", "topic_or_project": payload.topic_or_project.strip()}

    @router.get("/api/research/watchlists")
    async def list_research_watchlists(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            rows = conn.execute(
                "SELECT id, topic_or_project, category, last_checked_at, created_at FROM research_watchlists WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return {
            "watchlists": [
                {"id": r[0], "topic_or_project": r[1], "category": r[2], "last_checked_at": r[3], "created_at": r[4]}
                for r in rows
            ]
        }

    @router.delete("/api/research/watchlists/{watchlist_id}")
    async def delete_research_watchlist(
        watchlist_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            row = conn.execute("SELECT user_id FROM research_watchlists WHERE id = ?", (watchlist_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found")
            if str(row[0]) != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            conn.execute("DELETE FROM research_watchlists WHERE id = ?", (watchlist_id,))
            conn.commit()
        return {"status": "deleted", "id": watchlist_id}

    # ── Social Intelligence & Growth Intelligence (Tenant-Isolated) ────────────
    @router.get("/api/social/intelligence/trends")
    async def social_intelligence_trends(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            return get_permitted_social_trends(user_id, conn)

    @router.post("/api/growth/opportunities")
    async def create_growth_opportunity(
        payload: GrowthOpportunityCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        oid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT INTO growth_opportunities (
                    id, user_id, organization_id, project_id, title, category,
                    priority, status, notes, source_attribution, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?)
                """,
                (oid, user_id, org_id, payload.project_id, payload.title.strip(), payload.category, payload.priority, payload.notes, payload.source_attribution, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "opportunity": {"id": oid, "title": payload.title.strip(), "category": payload.category, "priority": payload.priority, "status": "open"}}

    @router.get("/api/growth/opportunities")
    async def list_growth_opportunities(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            rows = conn.execute(
                "SELECT id, title, category, priority, status, notes, source_attribution, created_at, updated_at FROM growth_opportunities WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return {
            "opportunities": [
                {
                    "id": r[0], "title": r[1], "category": r[2], "priority": r[3],
                    "status": r[4], "notes": r[5], "source_attribution": r[6],
                    "created_at": r[7], "updated_at": r[8],
                }
                for r in rows
            ]
        }

    @router.patch("/api/growth/opportunities/{opp_id}")
    async def update_growth_opportunity(
        opp_id: str,
        payload: GrowthOpportunityUpdateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            row = conn.execute("SELECT user_id FROM growth_opportunities WHERE id = ?", (opp_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
            if str(row[0]) != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            now_iso = datetime.now(timezone.utc).isoformat()
            if payload.status is not None:
                conn.execute("UPDATE growth_opportunities SET status = ?, updated_at = ? WHERE id = ?", (payload.status, now_iso, opp_id))
            if payload.priority is not None:
                conn.execute("UPDATE growth_opportunities SET priority = ?, updated_at = ? WHERE id = ?", (payload.priority, now_iso, opp_id))
            if payload.notes is not None:
                conn.execute("UPDATE growth_opportunities SET notes = ?, updated_at = ? WHERE id = ?", (payload.notes, now_iso, opp_id))
            conn.commit()
        return {"status": "ok", "id": opp_id}

    @router.get("/api/growth/analytics")
    async def get_growth_analytics(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            return compute_growth_analytics(user_id, conn)

    # ── Super Admin Only: Internal Market Acquisition Engine ───────────────────
    @router.get("/api/admin/market-acquisition")
    async def list_market_acquisition_leads(
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            rows = conn.execute(
                "SELECT id, project_name, ecosystem, contact_channel, stage, notes, created_by_admin, created_at, updated_at FROM market_acquisition_leads ORDER BY created_at DESC"
            ).fetchall()
        return {
            "leads": [
                {
                    "id": r[0], "project_name": r[1], "ecosystem": r[2], "contact_channel": r[3],
                    "stage": r[4], "notes": r[5], "created_by_admin": r[6],
                    "created_at": r[7], "updated_at": r[8],
                }
                for r in rows
            ],
            "compliance": get_social_compliance_status(),
        }

    @router.post("/api/admin/market-acquisition")
    async def create_market_acquisition_lead(
        payload: MarketAcquisitionCreateRequest,
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        lid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        admin_id = str(current_user.get("email") or current_user.get("id"))
        with get_dev_db() as conn:
            ensure_social_growth_schema(conn)
            conn.execute(
                """
                INSERT INTO market_acquisition_leads (id, project_name, ecosystem, contact_channel, stage, notes, created_by_admin, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (lid, payload.project_name.strip(), payload.ecosystem, payload.contact_channel, payload.stage, payload.notes, admin_id, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "lead": {"id": lid, "project_name": payload.project_name.strip(), "stage": payload.stage}}

    return router
