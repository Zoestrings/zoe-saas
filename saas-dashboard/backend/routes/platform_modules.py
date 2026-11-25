"""Platform Modules API: Super Admin Controls, Team RBAC, Invoices, NFT Growth & Investor Intelligence."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Callable, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from zoe.platform_core import ensure_platform_core_schema, record_audit_log

logger = logging.getLogger("zoe.api.platform_modules")


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(project_owner|super_admin|suspended)$")


class AIConfigUpdateRequest(BaseModel):
    primary_provider: str = Field(..., min_length=2, max_length=40)
    fallback_provider: str = Field(..., min_length=2, max_length=40)
    default_model: str = Field(..., min_length=2, max_length=120)
    max_tokens: int = Field(default=1024, ge=128, le=8192)


class TeamInviteRequest(BaseModel):
    member_email: str = Field(..., min_length=3, max_length=150)
    role: str = Field(default="viewer", pattern="^(admin|editor|viewer)$")


class TeamMemberUpdateRequest(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(admin|editor|viewer)$")
    status: Optional[str] = Field(default=None, pattern="^(invited|active|revoked)$")


class InvoiceGenerateRequest(BaseModel):
    amount_usdt: float = Field(..., gt=0)
    plan: str = Field(..., min_length=2, max_length=40)
    reference_tx: Optional[str] = None


class NFTCollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    symbol: str = ""
    chain: str = "solana"
    contract_address: str = ""
    mint_campaign_name: str = ""
    mint_status: str = "planned"


class NFTCollectionUpdateRequest(BaseModel):
    mint_status: Optional[str] = None
    verified_floor_price: Optional[float] = None
    verified_sales_count: Optional[int] = None


class NFTLeadCreateRequest(BaseModel):
    collection_id: Optional[str] = None
    handle_or_wallet: str = Field(..., min_length=2, max_length=160)
    source: str = "community_opt_in"
    notes: str = ""


class InvestorPipelineCreateRequest(BaseModel):
    investor_name: str = Field(..., min_length=2, max_length=150)
    firm_type: str = "vc"
    stage: str = "research"
    focus_sectors: str = ""
    notes: str = ""
    project_id: Optional[str] = None


class InvestorPipelineUpdateRequest(BaseModel):
    stage: Optional[str] = None
    notes: Optional[str] = None


class MarketDiscoverRequest(BaseModel):
    ecosystem: str = "solana"
    sector: str = "defi"


def build_platform_modules_router(
    get_current_user: Callable[..., Any],
    require_super_admin: Callable[..., Any],
    get_dev_db: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(tags=["Platform Core, Team RBAC, NFT Growth & Investor Intelligence"])

    # ── Super Admin: Audit Logs, Global Integrations, Users, AI Config ─────────
    @router.get("/api/admin/audit-logs")
    async def list_admin_audit_logs(
        limit: int = Query(default=100, ge=1, le=500),
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            rows = conn.execute(
                """
                SELECT id, actor_id, actor_email, actor_role, action, target_type, target_id, details_json, created_at
                FROM audit_logs ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return {
            "logs": [
                {
                    "id": r[0], "actor_id": r[1], "actor_email": r[2], "actor_role": r[3],
                    "action": r[4], "target_type": r[5], "target_id": r[6],
                    "details": json.loads(r[7]) if r[7] else {}, "created_at": r[8],
                }
                for r in rows
            ]
        }

    @router.get("/api/admin/integrations/overview")
    async def admin_global_integrations_overview(
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        """Sanitized global Telegram & Discord integration inventory (zero credentials exposed)."""
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            items: List[Dict[str, Any]] = []
            try:
                rows = conn.execute(
                    """
                    SELECT id, owner_id, project_id, platform, bot_username, status, last_error, created_at, updated_at
                    FROM platform_integrations ORDER BY updated_at DESC LIMIT 100
                    """
                ).fetchall()
                for r in rows:
                    items.append(
                        {
                            "id": r[0],
                            "owner_id": r[1],
                            "project_id": r[2],
                            "platform": r[3],
                            "bot_username": r[4],
                            "status": r[5],
                            "last_error": r[6],
                            "created_at": r[7],
                            "updated_at": r[8],
                        }
                    )
            except Exception:
                items = []

        telegram_count = sum(1 for i in items if i["platform"] == "telegram")
        discord_count = sum(1 for i in items if i["platform"] == "discord")
        unhealthy = sum(1 for i in items if i["status"] not in ("active", "connected", "verified"))
        return {
            "summary": {
                "total_integrations": len(items),
                "telegram_count": telegram_count,
                "discord_count": discord_count,
                "unhealthy_count": unhealthy,
            },
            "integrations": items,
        }

    @router.get("/api/admin/users")
    async def admin_list_users(
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            users: List[Dict[str, Any]] = []
            try:
                rows = conn.execute("SELECT id, email, role, created_at FROM dev_users ORDER BY created_at DESC LIMIT 100").fetchall()
                for r in rows:
                    ent = conn.execute("SELECT plan, credits FROM dev_entitlements WHERE user_id = ?", (str(r[0]),)).fetchone()
                    users.append(
                        {
                            "id": r[0],
                            "email": r[1],
                            "role": r[2],
                            "created_at": r[3],
                            "plan": ent[0] if ent else "free",
                            "credits": int(ent[1]) if ent and ent[1] is not None else 50,
                        }
                    )
            except Exception:
                users = []
        return {"users": users}

    @router.post("/api/admin/users/{target_user_id}/role")
    async def admin_update_user_role(
        target_user_id: str,
        payload: UserRoleUpdateRequest,
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            try:
                conn.execute("UPDATE dev_users SET role = ? WHERE id = ?", (payload.role, target_user_id))
                conn.commit()
            except Exception as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            record_audit_log(
                conn,
                actor_id=str(current_user.get("id")),
                actor_email=current_user.get("email"),
                actor_role="super_admin",
                action="update_user_role",
                target_type="user",
                target_id=target_user_id,
                details={"new_role": payload.role},
            )
        return {"status": "ok", "user_id": target_user_id, "role": payload.role}

    @router.get("/api/admin/ai-config")
    async def get_admin_ai_config(
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            row = conn.execute(
                "SELECT primary_provider, fallback_provider, default_model, max_tokens, updated_by, updated_at FROM ai_provider_configs WHERE id = 'global'"
            ).fetchone()
        return {
            "primary_provider": row[0],
            "fallback_provider": row[1],
            "default_model": row[2],
            "max_tokens": int(row[3]),
            "updated_by": row[4],
            "updated_at": row[5],
        }

    @router.post("/api/admin/ai-config")
    async def update_admin_ai_config(
        payload: AIConfigUpdateRequest,
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        admin_email = str(current_user.get("email") or current_user.get("id"))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            conn.execute(
                """
                UPDATE ai_provider_configs
                SET primary_provider = ?, fallback_provider = ?, default_model = ?, max_tokens = ?, updated_by = ?, updated_at = ?
                WHERE id = 'global'
                """,
                (payload.primary_provider, payload.fallback_provider, payload.default_model, payload.max_tokens, admin_email, now_iso),
            )
            conn.commit()
            record_audit_log(
                conn,
                actor_id=str(current_user.get("id")),
                actor_email=admin_email,
                actor_role="super_admin",
                action="update_ai_config",
                target_type="ai_provider_configs",
                target_id="global",
                details=payload.model_dump(),
            )
        return {"status": "ok", "config": payload.model_dump()}

    @router.post("/api/admin/market-acquisition/discover")
    async def admin_discover_prospects(
        payload: MarketDiscoverRequest,
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        """Super Admin internal prospect discovery & pitch brief (strictly isolated from customer Investor Intelligence)."""
        eco = payload.ecosystem.strip().lower()
        sec = payload.sector.strip().lower()
        pitch_template = (
            f"Hi {eco.title()} {sec.title()} team — Zoe Intelligence helps Web3 projects automate "
            "Telegram/Discord community operations with RAG-verified official docs, real-time token security scanning, "
            "and milestone alerts. Open to a 14-day pilot?"
        )
        return {
            "ecosystem": eco,
            "sector": sec,
            "recommended_channels": ["Official Website Contact", "Discord Partner Desk", "Ecosystem Grants Directory"],
            "pitch_template": pitch_template,
        }

    # ── Project Owner: Team Members & Permissions ──────────────────────────────
    @router.get("/api/owner/team")
    async def list_owner_team(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            rows = conn.execute(
                "SELECT id, organization_id, owner_user_id, member_email, member_user_id, role, status, created_at FROM organization_members WHERE owner_user_id = ? OR organization_id = ? ORDER BY created_at DESC",
                (user_id, org_id),
            ).fetchall()
        return {
            "members": [
                {
                    "id": r[0], "organization_id": r[1], "owner_user_id": r[2],
                    "member_email": r[3], "member_user_id": r[4], "role": r[5],
                    "status": r[6], "created_at": r[7],
                }
                for r in rows
            ]
        }

    @router.post("/api/owner/team/invite")
    async def invite_team_member(
        payload: TeamInviteRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        if str(current_user.get("team_role", "owner")) == "viewer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot invite team members")
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        mid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            conn.execute(
                """
                INSERT INTO organization_members (id, organization_id, owner_user_id, member_email, role, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'invited', ?, ?)
                ON CONFLICT(organization_id, member_email) DO UPDATE SET role = excluded.role, status = 'invited', updated_at = excluded.updated_at
                """,
                (mid, org_id, user_id, payload.member_email.strip().lower(), payload.role, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "member": {"id": mid, "member_email": payload.member_email.strip().lower(), "role": payload.role, "status": "invited"}}

    @router.patch("/api/owner/team/{member_id}")
    async def update_team_member(
        member_id: str,
        payload: TeamMemberUpdateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            row = conn.execute("SELECT owner_user_id FROM organization_members WHERE id = ?", (member_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
            if str(row[0]) != user_id and role != "super_admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            now_iso = datetime.now(timezone.utc).isoformat()
            if payload.role:
                conn.execute("UPDATE organization_members SET role = ?, updated_at = ? WHERE id = ?", (payload.role, now_iso, member_id))
            if payload.status:
                conn.execute("UPDATE organization_members SET status = ?, updated_at = ? WHERE id = ?", (payload.status, now_iso, member_id))
            conn.commit()
        return {"status": "ok", "id": member_id}

    @router.delete("/api/owner/team/{member_id}")
    async def remove_team_member(
        member_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            row = conn.execute("SELECT owner_user_id FROM organization_members WHERE id = ?", (member_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
            if str(row[0]) != user_id and role != "super_admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            conn.execute("DELETE FROM organization_members WHERE id = ?", (member_id,))
            conn.commit()
        return {"status": "deleted", "id": member_id}

    # ── Billing Invoices ───────────────────────────────────────────────────────
    @router.get("/api/billing/invoices")
    async def list_billing_invoices(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            rows = conn.execute(
                "SELECT id, amount_usdt, plan, status, reference_tx, issued_at FROM invoices WHERE user_id = ? ORDER BY issued_at DESC",
                (user_id,),
            ).fetchall()
        return {
            "invoices": [
                {"id": r[0], "amount_usdt": float(r[1]), "plan": r[2], "status": r[3], "reference_tx": r[4], "issued_at": r[5]}
                for r in rows
            ]
        }

    @router.post("/api/billing/invoices/generate")
    async def generate_billing_invoice(
        payload: InvoiceGenerateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        iid = f"INV-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            conn.execute(
                "INSERT INTO invoices (id, user_id, organization_id, amount_usdt, plan, status, reference_tx, issued_at) VALUES (?, ?, ?, ?, ?, 'paid', ?, ?)",
                (iid, user_id, org_id, payload.amount_usdt, payload.plan, payload.reference_tx, now_iso),
            )
            conn.commit()
        return {"status": "ok", "invoice": {"id": iid, "amount_usdt": payload.amount_usdt, "plan": payload.plan, "issued_at": now_iso}}

    # ── NFT Growth & Sales (Submodule of Growth Engine, No Fabricated Sales) ───
    @router.get("/api/nft-growth/collections")
    async def list_nft_collections(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            rows = conn.execute(
                """
                SELECT id, chain, contract_address, name, symbol, mint_campaign_name, mint_status,
                       verified_floor_price, verified_sales_count, referral_code, created_at
                FROM nft_collections WHERE user_id = ? ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return {
            "collections": [
                {
                    "id": r[0], "chain": r[1], "contract_address": r[2], "name": r[3],
                    "symbol": r[4], "mint_campaign_name": r[5], "mint_status": r[6],
                    "verified_floor_price": r[7], "verified_sales_count": int(r[8]),
                    "referral_code": r[9], "created_at": r[10],
                }
                for r in rows
            ]
        }

    @router.post("/api/nft-growth/collections")
    async def create_nft_collection(
        payload: NFTCollectionCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        cid = str(uuid.uuid4())
        ref = f"ZOE-{uuid.uuid4().hex[:6].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            conn.execute(
                """
                INSERT INTO nft_collections (
                    id, user_id, organization_id, chain, contract_address, name, symbol,
                    mint_campaign_name, mint_status, referral_code, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cid, user_id, org_id, payload.chain, payload.contract_address.strip(), payload.name.strip(), payload.symbol.strip(), payload.mint_campaign_name, payload.mint_status, ref, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "collection": {"id": cid, "name": payload.name.strip(), "referral_code": ref, "verified_sales_count": 0}}

    @router.patch("/api/nft-growth/collections/{col_id}")
    async def update_nft_collection(
        col_id: str,
        payload: NFTCollectionUpdateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            row = conn.execute("SELECT user_id FROM nft_collections WHERE id = ?", (col_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
            if str(row[0]) != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            now_iso = datetime.now(timezone.utc).isoformat()
            if payload.mint_status is not None:
                conn.execute("UPDATE nft_collections SET mint_status = ?, updated_at = ? WHERE id = ?", (payload.mint_status, now_iso, col_id))
            if payload.verified_floor_price is not None:
                conn.execute("UPDATE nft_collections SET verified_floor_price = ?, updated_at = ? WHERE id = ?", (payload.verified_floor_price, now_iso, col_id))
            if payload.verified_sales_count is not None:
                conn.execute("UPDATE nft_collections SET verified_sales_count = ?, updated_at = ? WHERE id = ?", (payload.verified_sales_count, now_iso, col_id))
            conn.commit()
        return {"status": "ok", "id": col_id}

    @router.get("/api/nft-growth/leads")
    async def list_nft_leads(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            rows = conn.execute(
                "SELECT id, collection_id, handle_or_wallet, source, status, notes, created_at FROM nft_buyer_leads WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return {
            "leads": [
                {"id": r[0], "collection_id": r[1], "handle_or_wallet": r[2], "source": r[3], "status": r[4], "notes": r[5], "created_at": r[6]}
                for r in rows
            ]
        }

    @router.post("/api/nft-growth/leads")
    async def create_nft_lead(
        payload: NFTLeadCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        lid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            conn.execute(
                "INSERT INTO nft_buyer_leads (id, user_id, organization_id, collection_id, handle_or_wallet, source, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?)",
                (lid, user_id, org_id, payload.collection_id, payload.handle_or_wallet.strip(), payload.source, payload.notes, now_iso),
            )
            conn.commit()
        return {"status": "ok", "lead": {"id": lid, "handle_or_wallet": payload.handle_or_wallet.strip()}}

    # ── Customer-Facing Investor Intelligence (Strictly Tenant-Isolated) ───────
    @router.get("/api/investor-intelligence/pipeline")
    async def list_investor_pipeline(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            rows = conn.execute(
                """
                SELECT id, project_id, investor_name, firm_type, stage, focus_sectors, notes, last_contacted_at, created_at, updated_at
                FROM investor_pipelines WHERE user_id = ? ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return {
            "pipeline": [
                {
                    "id": r[0], "project_id": r[1], "investor_name": r[2], "firm_type": r[3],
                    "stage": r[4], "focus_sectors": r[5], "notes": r[6],
                    "last_contacted_at": r[7], "created_at": r[8], "updated_at": r[9],
                }
                for r in rows
            ]
        }

    @router.post("/api/investor-intelligence/pipeline")
    async def create_investor_pipeline_entry(
        payload: InvestorPipelineCreateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        org_id = str(current_user.get("organization_id") or user_id)
        iid = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            conn.execute(
                """
                INSERT INTO investor_pipelines (
                    id, user_id, organization_id, project_id, investor_name, firm_type,
                    stage, focus_sectors, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (iid, user_id, org_id, payload.project_id, payload.investor_name.strip(), payload.firm_type, payload.stage, payload.focus_sectors, payload.notes, now_iso, now_iso),
            )
            conn.commit()
        return {"status": "ok", "entry": {"id": iid, "investor_name": payload.investor_name.strip(), "stage": payload.stage}}

    @router.patch("/api/investor-intelligence/pipeline/{entry_id}")
    async def update_investor_pipeline_entry(
        entry_id: str,
        payload: InvestorPipelineUpdateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            row = conn.execute("SELECT user_id FROM investor_pipelines WHERE id = ?", (entry_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investor record not found")
            if str(row[0]) != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            now_iso = datetime.now(timezone.utc).isoformat()
            if payload.stage is not None:
                conn.execute("UPDATE investor_pipelines SET stage = ?, updated_at = ? WHERE id = ?", (payload.stage, now_iso, entry_id))
            if payload.notes is not None:
                conn.execute("UPDATE investor_pipelines SET notes = ?, updated_at = ? WHERE id = ?", (payload.notes, now_iso, entry_id))
            conn.commit()
        return {"status": "ok", "id": entry_id}

    @router.delete("/api/investor-intelligence/pipeline/{entry_id}")
    async def delete_investor_pipeline_entry(
        entry_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_platform_core_schema(conn)
            row = conn.execute("SELECT user_id FROM investor_pipelines WHERE id = ?", (entry_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investor record not found")
            if str(row[0]) != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            conn.execute("DELETE FROM investor_pipelines WHERE id = ?", (entry_id,))
            conn.commit()
        return {"status": "deleted", "id": entry_id}

    return router
