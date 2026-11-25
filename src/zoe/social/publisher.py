"""Social Publishing Agent: Campaigns, Drafts, Human Approval, Scheduling & Dispatch."""

import abc
from datetime import datetime, timezone
import json
import logging
import sqlite3
import threading
from typing import Any, Dict, List, Optional
import uuid

import httpx

from zoe.social.compliance import assert_x_feature_enabled

logger = logging.getLogger("zoe.social.publisher")

_PUBLISH_MUTEX = threading.Lock()

VALID_POST_STATUSES = {
    "draft",
    "pending_approval",
    "approved",
    "scheduled",
    "published",
    "rejected",
    "failed",
}


def ensure_social_growth_schema(conn: sqlite3.Connection) -> None:
    """Create tables for Social Publishing, Web3 Research, Growth & Market Acquisition."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS social_campaigns (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            name TEXT NOT NULL,
            objective TEXT NOT NULL DEFAULT '',
            target_audience TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_soc_camp_user ON social_campaigns(user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS social_posts (
            id TEXT PRIMARY KEY,
            campaign_id TEXT,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            platform TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            scheduled_for TEXT,
            published_at TEXT,
            approved_by TEXT,
            rejection_reason TEXT,
            ai_generated INTEGER NOT NULL DEFAULT 0,
            credits_charged INTEGER NOT NULL DEFAULT 0,
            external_post_id TEXT,
            error_message TEXT,
            idempotency_key TEXT UNIQUE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_soc_posts_user ON social_posts(user_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_soc_posts_sched ON social_posts(status, scheduled_for)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS social_accounts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            account_handle TEXT NOT NULL,
            encrypted_credentials TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, platform, account_handle)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS web3_research_reports (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            category TEXT NOT NULL,
            query TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            sources_json TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_w3_res_user ON web3_research_reports(user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS research_watchlists (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            topic_or_project TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'ecosystem',
            last_checked_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, topic_or_project)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS growth_opportunities (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'campaign_opportunity',
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'open',
            notes TEXT NOT NULL DEFAULT '',
            source_attribution TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_growth_user ON growth_opportunities(user_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS market_acquisition_leads (
            id TEXT PRIMARY KEY,
            project_name TEXT NOT NULL,
            ecosystem TEXT NOT NULL DEFAULT 'solana',
            contact_channel TEXT NOT NULL DEFAULT '',
            stage TEXT NOT NULL DEFAULT 'identified',
            notes TEXT NOT NULL DEFAULT '',
            created_by_admin TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


class BaseSocialPublisher(abc.ABC):
    """Provider-agnostic social publishing interface."""

    @property
    @abc.abstractmethod
    def platform(self) -> str:
        pass

    @abc.abstractmethod
    async def publish(self, content: str, title: str = "", credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass


class ManualExportPublisher(BaseSocialPublisher):
    @property
    def platform(self) -> str:
        return "manual_export"

    async def publish(self, content: str, title: str = "", credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"ok": True, "external_post_id": f"export_{uuid.uuid4().hex[:12]}", "mode": "manual_export"}


class DiscordWebhookPublisher(BaseSocialPublisher):
    @property
    def platform(self) -> str:
        return "discord_webhook"

    async def publish(self, content: str, title: str = "", credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        webhook_url = (credentials or {}).get("webhook_url", "").strip()
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            raise ValueError("Valid Discord webhook_url is required to publish to Discord.")
        payload = {"content": f"**{title}**\n{content}".strip() if title else content}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code not in (200, 204):
                raise RuntimeError(f"Discord webhook returned HTTP {resp.status_code}")
        return {"ok": True, "external_post_id": f"discord_{uuid.uuid4().hex[:10]}", "mode": "discord_webhook"}


class TelegramChannelPublisher(BaseSocialPublisher):
    @property
    def platform(self) -> str:
        return "telegram_channel"

    async def publish(self, content: str, title: str = "", credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        bot_token = (credentials or {}).get("bot_token", "").strip()
        chat_id = (credentials or {}).get("chat_id", "").strip()
        if not bot_token or not chat_id:
            raise ValueError("Telegram bot_token and chat_id are required to publish to a Telegram channel.")
        text = f"*{title}*\n\n{content}".strip() if title else content
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )
            data = resp.json()
            if resp.status_code != 200 or not data.get("ok"):
                raise RuntimeError(f"Telegram API error: {data.get('description', resp.status_code)}")
            msg_id = str(data.get("result", {}).get("message_id", ""))
        return {"ok": True, "external_post_id": msg_id or f"tg_{uuid.uuid4().hex[:10]}", "mode": "telegram_channel"}


class XPublisherAdapter(BaseSocialPublisher):
    """Official X OAuth2 publisher — strictly disabled unless X_API_ENABLED=true."""

    @property
    def platform(self) -> str:
        return "x"

    async def publish(self, content: str, title: str = "", credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        assert_x_feature_enabled("x_api")
        raise NotImplementedError("X OAuth2 live publishing requires verified X Developer v2 tokens.")


PUBLISHER_REGISTRY: Dict[str, BaseSocialPublisher] = {
    "manual_export": ManualExportPublisher(),
    "discord_webhook": DiscordWebhookPublisher(),
    "telegram_channel": TelegramChannelPublisher(),
    "x": XPublisherAdapter(),
}


async def generate_ai_post_draft(topic: str, platform: str = "telegram_channel", tone: str = "informative") -> Dict[str, str]:
    """Generate a compliant, transparent AI social post draft using LLMRouter with deterministic fallback."""
    clean_topic = topic.strip()
    if not clean_topic:
        raise ValueError("Topic is required to generate a post draft.")

    prompt = (
        f"Write a concise, factual {tone} Web3 community update for {platform} about: {clean_topic}. "
        "Do not make price guarantees or financial promises. Keep it clear and ready for human review."
    )
    try:
        from zoe.llm.router import LLMRouter
        router = LLMRouter()
        resp = await router.generate(prompt=prompt, max_tokens=280)
        text = (resp.text if hasattr(resp, "text") else str(resp)).strip()
        if text:
            return {"title": f"{clean_topic[:60]}", "content": text, "ai_disclosure": "AI-assisted draft (human review required)"}
    except Exception as exc:
        logger.info("LLMRouter unavailable for draft generation, using structured template: %s", exc)

    fallback = (
        f"Update on {clean_topic}: Key ecosystem developments, verified on-chain metrics, and community milestones. "
        f"(AI-assisted draft for {platform} — please review and approve before publishing.)"
    )
    return {"title": clean_topic[:60], "content": fallback, "ai_disclosure": "AI-assisted draft (human review required)"}


async def publish_post_record(
    post_id: str,
    conn: sqlite3.Connection,
    credentials: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Publish an approved or scheduled post idempotently."""
    with _PUBLISH_MUTEX:
        row = conn.execute(
            "SELECT id, platform, title, content, status, external_post_id FROM social_posts WHERE id = ?",
            (post_id,),
        ).fetchone()
        if not row:
            raise ValueError("Post not found")
        platform, title, content, current_status, ext_id = str(row[1]), str(row[2]), str(row[3]), str(row[4]), row[5]
        if current_status == "published" and ext_id:
            return {"post_id": post_id, "status": "published", "external_post_id": ext_id, "deduplicated": True}
        if current_status not in ("approved", "scheduled"):
            raise ValueError(f"Post must be 'approved' or 'scheduled' before publishing (current: '{current_status}').")

    publisher = PUBLISHER_REGISTRY.get(platform)
    if publisher is None:
        raise ValueError(f"Unsupported publishing platform: {platform}")

    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        res = await publisher.publish(content=content, title=title, credentials=credentials)
        conn.execute(
            """
            UPDATE social_posts
            SET status = 'published', published_at = ?, external_post_id = ?, error_message = NULL, updated_at = ?
            WHERE id = ?
            """,
            (now_iso, res["external_post_id"], now_iso, post_id),
        )
        conn.commit()
        return {"post_id": post_id, "status": "published", "external_post_id": res["external_post_id"]}
    except Exception as exc:
        conn.execute(
            "UPDATE social_posts SET status = 'failed', error_message = ?, updated_at = ? WHERE id = ?",
            (str(exc), now_iso, post_id),
        )
        conn.commit()
        raise


async def dispatch_due_scheduled_posts(conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Background worker step: publish scheduled posts whose scheduled_for <= now."""
    own_conn = False
    if conn is None:
        from zoe.scanner.performance_monitor import get_monitor_db_path
        db_path = get_monitor_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=15.0)
        own_conn = True

    results: List[Dict[str, Any]] = []
    try:
        ensure_social_growth_schema(conn)
        now_iso = datetime.now(timezone.utc).isoformat()
        rows = conn.execute(
            """
            SELECT id, user_id, platform
            FROM social_posts
            WHERE status = 'scheduled' AND scheduled_for IS NOT NULL AND scheduled_for <= ?
            ORDER BY scheduled_for ASC LIMIT 25
            """,
            (now_iso,),
        ).fetchall()
        for r in rows:
            pid = str(r[0])
            try:
                out = await publish_post_record(pid, conn)
                results.append(out)
            except Exception as exc:
                logger.warning("Scheduled post %s failed to publish: %s", pid, exc)
                results.append({"post_id": pid, "status": "failed", "error": str(exc)})
        return results
    finally:
        if own_conn:
            conn.close()
