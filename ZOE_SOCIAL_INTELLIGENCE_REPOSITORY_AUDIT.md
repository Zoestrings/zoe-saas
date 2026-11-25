# Zoe Intelligence — Social Intelligence & Growth Engine: Phase 1 Repository Audit

**Audit Scope:** Strictly Read-Only Technical Audit & Implementation Readiness Assessment  
**Date:** 2026-11-25  
**Target Modules:** Social Publishing Agent, Web3 Research Engine, Social Intelligence, Growth Intelligence, and Compliant Social Integration Infrastructure.

---

## 1. Executive Summary
Zoe Intelligence already possesses a substantial multi-tenant SaaS backend (`FastAPI` + `Supabase` / `SQLite` dev fallback), a `Next.js 16.4.5` (`React 19.3.0`) multi-role dashboard, a centralized billing & entitlement engine (`EntitlementEngine` in `src/zoe/billing/credit_manager.py`), encrypted multi-tenant bot integration infrastructure (`saas-dashboard/backend/routes/integrations.py`, `security/integration_security.py`), an agent orchestration/registry layer (`src/zoe/agents/`), and Web3 scanning/monitoring (`src/zoe/tools/scanner.py`, `src/zoe/scanner/performance_monitor.py`).

However, **none** of the commercial **Social Publishing Agent** (content calendar, scheduling, human approval workflow, campaign organization), **Growth Intelligence**, **Investor Intelligence**, or **Market Acquisition Engine** modules exist as production features. Furthermore, existing X/Twitter code (`src/zoe/twitter/adapter.py`, `src/zoe/tools/x_intel.py`, `src/zoe/tools/x_scraper.py`) contains **policy-sensitive patterns** (unrestricted auto-replies and DuckDuckGo/HTML scraping of X profiles/discussions) that must be placed behind strict feature flags and disabled by default pending X Developer account clearance.

**Readiness Verdict:** **Ready for phased implementation**, provided Phase 1 remediation isolates/feature-flags non-compliant X auto-reply/scraping paths and all new modules strictly reuse the existing authentication, RBAC, AES-256 credential vault, `EntitlementEngine`, and background loop (`src/zoe/monitor.py`).

---

## 2. Existing Technology Stack
- **Frontend:** Next.js `16.4.5` (Turbopack), React `19.3.0`, TypeScript `^5`, Tailwind CSS `^4`, Radix UI (`@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-avatar`, `@radix-ui/react-label`, `@radix-ui/react-separator`, `@radix-ui/react-slot`), `@tanstack/react-table` `^8.21.3`, `recharts` `^3.11.1`, `lucide-react` `^1.70.0` (`saas-dashboard/frontend/package.json`).
- **Backend:** FastAPI (`saas-dashboard/backend/main.py` + `routes/api_v1.py`, `routes/integrations.py`, `routes/performance_alerts.py`), Pydantic, Uvicorn.
- **Databases:** Supabase (PostgreSQL + Auth + RLS) for production, with automatic SQLite (`saas_dev.db`) operational/development fallback via `get_dev_db()`.
- **AI / LLM Layer:** `src/zoe/llm/router.py` with `groq_provider.py`, `gemini_provider.py`, `rate_limiter.py`, and `mock.py`.
- **Web3 / Market Data:** DexScreener (`src/zoe/tools/dexscreener.py`, `scanner.py`), GoPlus Security (`scanner.py`), Solana RPC (`monitor.py`), DuckDuckGo OSINT (`ddgs` / `duckduckgo_search` in `web_search.py`, `x_intel.py`).
- **Social / Messaging:** `tweepy.Client` (`src/zoe/twitter/adapter.py`), Telegram (`src/zoe/telegram/*`), Discord (`src/zoe/discord/adapter.py`, OAuth2 in `routes/integrations.py`).
- **Deployment:** Railway (`railway.json`, `Dockerfile`) hosting `zoe-dashboard`, `zoe-saas`, `zoe-worker`; Next.js frontend configured for Vercel.

---

## 3. Repository Architecture
```text
zoe/
├── src/zoe/
│   ├── agents/                  # Registry, Ledger, Orchestrator, Workflows, Specialized Agents
│   ├── billing/                 # Centralized EntitlementEngine (credit_manager.py)
│   ├── conversation/            # Classifier, Intent, Router, Prompt Builder, Sentiment
│   ├── discord/ & telegram/     # Bot adapters, normalizers, polling loop, moderator verify
│   ├── knowledge/               # RAG ingestion, retriever, screening, model
│   ├── llm/                     # LLM Router + Groq / Gemini providers + rate limiter
│   ├── scanner/                 # Mindshare, momentum, narratives, performance_monitor, social, trending
│   ├── tools/                   # Scanner, wallet_intel, x_intel, x_scraper, crypto_news, trading_intel, nft_studio
│   ├── twitter/                 # Legacy Tweepy mention poller & auto-reply adapter
│   ├── worker/                  # Message pipeline (pipeline.py) & claim worker (claim.py)
│   └── monitor.py               # Shared asyncio background monitoring daemon
├── saas-dashboard/
│   ├── backend/
│   │   ├── main.py              # 95+ FastAPI endpoints, RBAC, billing, auth, SQLite init
│   │   ├── init_db.py           # PostgreSQL initialization DDL
│   │   ├── routes/              # api_v1.py, integrations.py, performance_alerts.py
│   │   └── security/            # integration_security.py (AES-256 Fernet encryption)
│   └── frontend/src/
│       ├── app/                 # 37 page.tsx routes (admin/*, owner/*, dashboard/*, investigate, developer, trading, nft-studio)
│       ├── components/          # layout/*, scanner/*, agents/*, ui/*
│       └── lib/api.ts           # Typed API client with JWT auth wrapper
├── scripts/                     # 12 SQL migration scripts + bot runners
└── tests/                       # Unit, integration, adversarial, E2E suites
```

---

## 4. Existing Feature Inventory & 5. Feature Implementation Status

| Feature | Classification | Evidence / Code References |
| --- | --- | --- |
| **Web3 Scanner (Solana + EVM)** | **1. Fully implemented & verified** | `src/zoe/tools/scanner.py` (`detect_chain`, `fetch_dexscreener_market_data`), `investigate/page.tsx`, `tests/test_scanner.py` |
| **Token Performance Monitoring & Alerts** | **1. Fully implemented & verified** | `src/zoe/scanner/performance_monitor.py`, `routes/performance_alerts.py`, `performance-alerts-panel.tsx`, `tests/test_token_performance_monitoring.py` |
| **Wallet Intelligence** | **1. Fully implemented & verified** | `src/zoe/tools/wallet_intel.py`, `src/zoe/monitor.py` |
| **Telegram Integration** | **1. Fully implemented & verified** | `routes/integrations.py` (`getMe` verification), `src/zoe/telegram/*`, `owner/integrations/telegram/page.tsx`, `tests/test_integrations_e2e.py` |
| **Discord Integration** | **1. Fully implemented & verified** | `routes/integrations.py` (OAuth2 + AES-256), `src/zoe/discord/adapter.py`, `owner/integrations/discord/page.tsx` |
| **Knowledge Base & RAG** | **2. Partially implemented** | `src/zoe/knowledge/ingestion.py`, `retriever.py`, `owner/dashboard/knowledge/page.tsx` (local embedding tests `test_chunking_bounds` hang without cached HF weights) |
| **AI Agents & Orchestrator** | **1. Fully implemented & verified** | `src/zoe/agents/registry.py`, `ledger.py`, `orchestrator.py`, `research_agent.py`, `dashboard/agents/page.tsx` |
| **AI Provider Abstraction** | **1. Fully implemented & verified** | `src/zoe/llm/router.py`, `groq_provider.py`, `gemini_provider.py`, `rate_limiter.py` |
| **Research & Crypto News** | **1. Fully implemented & verified** | `src/zoe/tools/crypto_news.py`, `news.py`, `agents/research_agent.py`, `scanner/reports.py` |
| **Watchlists & Price Alerts** | **1. Fully implemented & verified** | `src/zoe/tools/alerts.py`, `watchlist/page.tsx`, `scanner/alerts.py` |
| **Community Analytics** | **2. Partially implemented** | `community/page.tsx`, `dashboard/community/page.tsx`, `src/zoe/agents/analytics.py` |
| **Notifications (SSE + Polling)** | **1. Fully implemented & verified** | `routes/performance_alerts.py` (`/api/scanner/performance-alerts/stream`), `performance-alerts-panel.tsx` |
| **Subscription & Billing + Credits** | **1. Fully implemented & verified** | `src/zoe/billing/credit_manager.py` (`EntitlementEngine`), `main.py` (`/api/billing/*`), `admin/billing/page.tsx`, `owner/billing/page.tsx`, `tests/test_unified_billing.py`, `tests/test_credit_integrity.py` |
| **Super Admin Functionality** | **1. Fully implemented & verified** | `require_super_admin` in `main.py`, `admin/overview/page.tsx`, `admin/projects/page.tsx`, `admin/revenue/page.tsx`, `admin/billing/page.tsx` |
| **Project Owner Functionality** | **1. Fully implemented & verified** | `owner/dashboard/page.tsx`, `owner/project/page.tsx`, `owner/logs/page.tsx`, `owner/integrations/*` |
| **Social Intelligence (`XPublicAdapter`, `x_intel`)** | **2. Partially implemented (Policy-gated)** | `src/zoe/scanner/social.py`, `src/zoe/agents/specialized/social.py`, `src/zoe/tools/x_intel.py`, `src/zoe/tools/x_scraper.py` (uses DuckDuckGo scraping; X API unverified) |
| **Social Publishing (Calendar, Approval, Scheduling)** | **5. Planned, not implemented** | No content calendar, draft/approval state machine, or scheduled publisher exists (`src/zoe/twitter/adapter.py` only does mention polling + direct reply) |
| **Growth Engine** | **5. Planned, not implemented** | No `Growth` routes, models, or UI pages found |
| **Investor Intelligence** | **5. Planned, not implemented** | No `Investor Intelligence` routes, models, or UI pages found |
| **Market Acquisition Engine** | **5. Planned, not implemented** | No `Market Acquisition` routes, models, or UI pages found |

---

## 6. Frontend Audit
- **Framework & Routing:** Next.js `16.4.5` App Router (`37` `page.tsx` routes across `admin/*`, `owner/*`, `dashboard/*`, `developer/*`, `investigate`, `trading`, `nft-studio`, `watchlist`, `projects`, `settings`).
- **Navigation & Layout:** Role-separated sidebars (`admin-sidebar.tsx` and owner/dashboard layouts) with Tailwind CSS v4 dark-theme styling and Radix UI primitives.
- **API Integration & Auth:** Centralized `apiRequest` wrapper in `saas-dashboard/frontend/src/lib/api.ts` handling JWT Bearer headers and `NEXT_PUBLIC_API_URL`.
- **Notifications:** `PerformanceAlertsPanel` (`src/components/scanner/performance-alerts-panel.tsx`) already provides non-blocking floating popups via `EventSource` SSE + 15s polling fallback and a persistent Notification Centre. Social publishing/research alerts can reuse this exact pattern.

---

## 7. Backend Audit
- **Framework:** FastAPI (`saas-dashboard/backend/main.py` defines 95 route decorators, plus modular routers in `routes/api_v1.py`, `routes/integrations.py`, and `routes/performance_alerts.py`).
- **Background Workers:** `main.py` starts `run_monitoring_loop(interval_seconds=900)` and `run_buy_monitoring_loop(interval_seconds=30)` on FastAPI `@app.on_event("startup")`.
- **Queue / Worker:** `src/zoe/worker/claim.py` & `pipeline.py` handle atomic inbox claims, outbox delivery (`src/zoe/outbox/service.py`), and sweep finalization (`src/zoe/finalizer/sweep.py`).
- **Real-time Delivery:** SSE endpoint `/api/scanner/performance-alerts/stream` in `routes/performance_alerts.py`.

---

## 8. Database & Data Model Audit
- **Dual Persistence:** Production Supabase PostgreSQL (12 SQL scripts in `scripts/setup_*.sql` plus `saas-dashboard/backend/init_db.py`) and SQLite operational fallback (`saas_dev.db` via `get_dev_db()`).
- **Existing Key Tables:** `users`, `projects`, `investigations`, `watchlists`, `monitored_tokens`, `token_performance_alerts`, `performance_monitor_settings`, `platform_integrations`, `api_keys`, `api_usage_logs`, `dev_entitlements`, `credit_transactions`, `agent_ledger`, `research_reports`.
- **Missing Tables for New Modules:** `social_campaigns`, `content_drafts`, `scheduled_posts`, `post_approvals`, `social_accounts` (encrypted OAuth tokens), `research_briefs`, `growth_opportunities` / `leads`.

---

## 9. AI & Agent Architecture Audit
- **LLM Router (`src/zoe/llm/router.py`):** Abstracts Groq and Gemini providers with automatic fallback and rate limiting (`rate_limiter.py`).
- **Agent Framework (`src/zoe/agents/`):**
  - `BaseAgent` (`base.py`), `AgentRegistry` (`registry.py`), `AgentOrchestrator` (`orchestrator.py`), `AgentLedger` (`ledger.py`), `Workflows` (`workflows.py`).
  - Existing specialized agents (`src/zoe/agents/specialized/`): `community.py`, `dev_assistant.py`, `market.py`, `narrative.py`, `news.py`, `project_analysis.py`, `research.py`, `security.py`, `social.py`, `verification.py`.
  - **Reuse Finding:** `SocialIntelligenceAgent` (`social.py`), `NarrativeAgent` (`narrative.py`), and `ResearchAgent` (`research_agent.py`) already extend `BaseAgent` and integrate with `tools_registry.py` and `agent_ledger`. A new `SocialPublishingAgent` can follow this exact pattern without building a second agent framework.

---

## 10. Security & Tenant-Isolation Audit
- **Authentication & RBAC:** `get_current_user` (JWT validation) and `require_super_admin` (`role == "super_admin"` or configured `SUPER_ADMIN_EMAILS`) in `main.py`.
- **Credential Encryption:** `saas-dashboard/backend/security/integration_security.py` implements AES-256 Fernet encryption (`encrypt_secret`, `decrypt_secret`) for Telegram/Discord credentials; secrets are never returned to the frontend.
- **Tenant Isolation:** `routes/integrations.py` and `routes/performance_alerts.py` filter queries by `owner_id` / `user_id` and return `403 Forbidden` on cross-tenant mutation attempts.
- **Audit Gaps / Risks Identified:**
  1. **Legacy `test_billing.py` schema drift:** `test_user_entitlement_active_pro` fails in isolated SQLite fixtures lacking the `credits` column in `dev_entitlements`.
  2. **Public vs. Customer Separation:** `Market Acquisition Engine` (internal Zoe growth) must remain strictly isolated under `require_super_admin` and never share tables/endpoints with customer-facing `Investor Intelligence` or `Growth Intelligence`.
  3. **X Credentials:** Must never be exposed to Project Owners or stored in plaintext.

---

## 11. Billing & Credits Audit
- **Central Engine:** `EntitlementEngine` in `src/zoe/billing/credit_manager.py` plus `/api/billing/*` and `/api/admin/billing/*` in `main.py`.
- **Atomicity & Safety:** Credit deductions use atomic transactions (`tests/test_credit_integrity.py` and `tests/test_unified_billing.py` verified).
- **Reusability:** New Social Publishing (e.g., AI draft generation, campaign research) and Web3 Research reports can hook directly into `EntitlementEngine` for plan gating and atomic credit deduction without creating a second billing system.

---

## 12. Social Integration Readiness & 13. X API Compliance Restrictions
- **Current Adapters:**
  - `src/zoe/twitter/adapter.py` (`TwitterAdapter` using `tweepy.Client`) polls mentions and sends automated tweet replies.
  - `src/zoe/scanner/social.py` defines `BaseSocialAdapter` and `XPublicAdapter`.
  - `src/zoe/tools/x_intel.py` and `x_scraper.py` use DuckDuckGo (`ddgs`) and HTTP requests to scrape public X discussions/profiles.
- **X Developer Policy Compliance Gaps (Critical):**
  1. `TwitterAdapter` implements automated replies without an explicit feature flag disabling it by default.
  2. `x_intel.py` / `x_scraper.py` scrape X content via search/HTML rather than authorized APIs.
  3. **Required Safeguards Before Any Social Feature Activation:**
     - Add global & per-tenant feature flags (`X_API_ENABLED=false`, `X_AUTO_REPLY_ENABLED=false`, `X_SCRAPING_ENABLED=false`) disabled by default.
     - Prohibit browser automation, unofficial credentials, bulk replies/DMs, auto-likes/follows, model training on X data, and human misrepresentation.
     - Route Web3 Research and Social Intelligence primarily through permitted sources: official project docs/websites, GitHub, RSS/announcements, DexScreener, GoPlus, and authorized on-chain/API feeds.

---

## 14. Missing Infrastructure
1. **Content & Campaign Persistence:** Tables & models for drafts, approval workflows (`draft -> pending_approval -> approved -> scheduled -> published/rejected`), calendars, and campaigns.
2. **Scheduled Publishing Worker:** Idempotent due-post dispatcher integrated into `src/zoe/monitor.py` (with dry-run / manual export mode when external social APIs are disabled).
3. **Provider-Agnostic Social Publisher Interface:** Abstract `BaseSocialPublisher` (supporting LinkedIn, Farcaster, Telegram Channels, Discord Webhooks/Announcements, and feature-flagged X OAuth2 adapter).
4. **Feature Flag & Compliance Gate Service:** Centralized capability flags enforcing X policy restrictions server-side.
5. **Growth & Opportunity Pipeline:** Tenant-isolated CRM/opportunity model separate from internal Zoe Market Acquisition.

---

## 15. Technical Risks & Architectural Conflicts
1. **X Account Flag Escalation Risk:** Activating `TwitterAdapter` auto-replies or `x_scraper.py` in production could trigger permanent X API suspension.
2. **Multi-Worker Background Loop Duplication:** Running `run_monitoring_loop` inside FastAPI `@app.on_event("startup")` in `main.py` means scaling to multiple web workers would execute duplicate scheduled jobs unless locked or offloaded to `zoe-worker`.
3. **Stale Legacy Test Suite:** 46 older unit/pipeline tests fail due to `MockLLMClient` fixture drift and outdated prompt/rate-limit assertions, and 2 local embedding tests hang without cached model weights.

---

## 16. Recommended Implementation Architecture
- **Backend Router:** `saas-dashboard/backend/routes/social_growth.py` injected with `get_current_user`, `require_super_admin`, `get_dev_db`, and `EntitlementEngine`.
- **Domain Services (`src/zoe/social/`):**
  - `publisher.py`: `SocialPublisherService` + `BaseSocialPublisher` (Telegram Channel, Discord Announcement, Manual Export, and disabled-by-default `XPublisherAdapter`).
  - `calendar.py`: Draft lifecycle, human-in-the-loop approval state machine, and scheduled queue.
  - `research_engine.py`: Extends `src/zoe/agents/research_agent.py` using permitted sources (official docs, GitHub, DexScreener, GoPlus, RSS).
  - `growth_intel.py`: Campaign & market opportunity analysis strictly scoped by `organization_id` / `user_id`.
- **Frontend (`saas-dashboard/frontend/src/app/owner/social/` & `admin/growth/`):** Reuses existing sidebar, `apiRequest`, and `PerformanceAlertsPanel` notification patterns.

---

## 17. Dependencies & External Services Required
- **Existing (No new installs needed for core):** FastAPI, Pydantic, Next.js, Tailwind, `httpx`, `cryptography` (Fernet), Groq/Gemini LLM providers, DexScreener, GoPlus.
- **Optional Future External APIs (Feature-Flagged):** Official X API v2 OAuth 2.0 PKCE (only after X Developer account status is cleared), Farcaster Neynar API, LinkedIn Marketing/Share API, RSS/Atom feed parser (`feedparser`).

---

## 18. Estimated Implementation Complexity
- **Overall:** **Medium-High** (most foundational infrastructure—auth, RBAC, AES-256 vault, billing, SSE notifications, agent orchestrator—already exists and does not need to be rebuilt).

---

## 19. Recommended Development Phases & 20. Acceptance Criteria

1. **Phase 1B — Security, Compliance & Test Stabilization**
   - *Dependencies:* None.
   - *Acceptance Criteria:* Feature flags disable X auto-reply/scraping by default; `zoe-worker` / scheduler lock prevents duplicate job execution; `test_billing.py` schema fixture fixed.
2. **Phase 2 — Social Publishing Agent (Drafts, Calendar, Human Approval)**
   - *Dependencies:* Phase 1B, `EntitlementEngine`, `src/zoe/llm/router.py`.
   - *Acceptance Criteria:* Users can generate AI drafts, edit, submit for human approval, schedule posts, and publish to permitted channels (Telegram/Discord/Manual Export) with atomic credit deduction and strict tenant isolation (403 on cross-tenant access).
3. **Phase 3 — Web3 Research Engine (Permitted Sources)**
   - *Dependencies:* `src/zoe/agents/research_agent.py`, `scanner.py`, `crypto_news.py`.
   - *Acceptance Criteria:* Ecosystem, DeFi/NFT/RWA, and official-announcement research reports generated with explicit source attribution and watchlists/alerts.
4. **Phase 4 — Social & Growth Intelligence**
   - *Dependencies:* Phase 3, `src/zoe/scanner/narratives.py`, `mindshare.py`.
   - *Acceptance Criteria:* Topic/narrative discovery and campaign/growth opportunity reports scoped strictly to tenant `organization_id`; internal Market Acquisition Engine strictly gated by `require_super_admin`.
5. **Phase 5 — Authorized Social Platform Integrations & E2E Verification**
   - *Dependencies:* Valid X Developer clearance / OAuth2 credentials.
   - *Acceptance Criteria:* OAuth2 PKCE token storage encrypted via `integration_security.py`, zero secret exposure to frontend, full tenant-isolation & billing E2E test suite passing.
