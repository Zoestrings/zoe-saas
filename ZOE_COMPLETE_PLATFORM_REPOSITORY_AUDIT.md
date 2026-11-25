# Zoe Intelligence — Master Repository Audit & Platform Implementation Readiness

**Audit Type:** Strictly Read-Only Technical Audit, Dashboard Audit & Implementation Roadmap  
**Date:** 2026-11-25  
**Git Working Tree Inspected:** `main` branch (`35d8799` / `1d829f8` + local uncommitted Social/Growth engine changes in `src/zoe/social/`, `routes/social_growth.py`, `owner/social/`, `admin/growth/`, `tests/test_social_growth_engine.py`).

---

## 1. Executive Summary
Zoe Intelligence has evolved from a Telegram/Discord AI community bot into a multi-tenant Web3 SaaS platform built on **Next.js 16.4.5** (`React 19.3.0`), **FastAPI**, **Supabase PostgreSQL** (with SQLite `saas_dev.db` operational fallback), **Groq/Gemini LLM routing**, **DexScreener/GoPlus Web3 scanning**, **AES-256-GCM encrypted bot integrations**, and an **atomic credit/subscription engine (`EntitlementEngine` / `CreditManager`)**.

However, auditing against the complete product vision reveals clear gaps:
1. **Super Admin Dashboard** has solid core metrics, project suspension/activation, billing plan/credit adjustment, performance monitoring, and an initial internal Market Acquisition page, but lacks dedicated UI/endpoints for **global Telegram/Discord integration monitoring**, **global AI provider/fallback configuration**, **user/role suspension**, and a **unified Audit Log explorer**.
2. **Project Owner Dashboard** has strong Telegram/Discord onboarding, knowledge base management, AI instructions, billing usage, token performance monitoring, and an initial Social & Growth workspace, but lacks **Team Members & Granular Org Permissions**, **NFT Growth & Sales** (currently only AI image generation in `src/zoe/tools/nft_studio.py`), **Customer-Facing Investor Intelligence**, and **Referral/Invoice Management**.
3. **Route & Component Duplication:** Legacy `/dashboard/*` and top-level routes (`/projects`, `/logs`, `/settings`, `/billing`, `/community`) coexist alongside `/owner/*` and `/admin/*`, creating navigation ambiguity.

**Readiness Verdict:** **Ready for phased hardening and feature completion**, provided Phase 1 resolves legacy route duplication, team-member RBAC, scheduler multi-worker locking, and remaining legacy test drift before expanding NFT Growth & Sales and Investor Intelligence.

---

## 2. Existing Technology Stack
- **Frontend:** Next.js `16.4.5` (Turbopack), React `19.3.0`, TypeScript `^5`, Tailwind CSS `^4`, Radix UI primitives, `@tanstack/react-table` `^8.21.3`, `recharts` `^3.11.1`, `lucide-react` `^1.70.0` (`saas-dashboard/frontend/package.json`).
- **Backend:** FastAPI (`saas-dashboard/backend/main.py` + `routes/api_v1.py`, `routes/integrations.py`, `routes/performance_alerts.py`, `routes/social_growth.py`), Pydantic, Uvicorn.
- **Database:** Supabase (PostgreSQL + Auth + RLS) + SQLite (`saas_dev.db`) fallback via `get_dev_db()`.
- **AI / LLM:** `src/zoe/llm/router.py` (`groq_provider.py`, `gemini_provider.py`, `rate_limiter.py`, `mock.py`).
- **Web3 / Market Data:** DexScreener (`src/zoe/tools/dexscreener.py`, `scanner.py`), GoPlus Security (`scanner.py`), Solana RPC (`monitor.py`), Pollinations.ai (`nft_studio.py`), Crypto News (`crypto_news.py`), DuckDuckGo OSINT (`web_search.py`).
- **Security:** `cryptography` (`AESGCM` 256-bit in `saas-dashboard/backend/security/integration_security.py`), JWT verification in `main.py`.
- **Deployment:** Railway (`zoe-dashboard` frontend, `zoe-saas` backend, `zoe-worker` background bots) with custom domains configured for `pixelnesttrade.com` / `api.pixelnesttrade.com`.

---

## 3. Repository Architecture
- `src/zoe/`: Core intelligence engine — `agents/`, `billing/`, `conversation/`, `discord/`, `telegram/`, `knowledge/`, `llm/`, `memory/`, `outbox/`, `participation/`, `safety/`, `scanner/`, `social/`, `tools/`, `twitter/`, `worker/`, and `monitor.py`.
- `saas-dashboard/backend/`: FastAPI application (`main.py`, `init_db.py`, `routes/*`, `security/*`).
- `saas-dashboard/frontend/`: Next.js App Router (`src/app/*`, `src/components/*`, `src/lib/api.ts`).
- `scripts/`: 12 SQL schema scripts (`scripts/setup_*.sql`) and bot runner (`scripts/run_all_bots.py`).
- `tests/`: Automated unit, integration, adversarial, and E2E suites.

---

## 4. Frontend Architecture
- **Total App Routes:** `39` `page.tsx` routes (`42` static/dynamic Next.js build targets).
- **Layouts & Navigation:** `saas-dashboard/frontend/src/components/layout/admin-sidebar.tsx` and owner/dashboard layouts; Tailwind v4 dark UI.
- **API Layer:** Centralized `apiRequest` in `saas-dashboard/frontend/src/lib/api.ts` injecting `Authorization: Bearer <token>` against `NEXT_PUBLIC_API_URL`.
- **Real-Time UI:** `PerformanceAlertsPanel` (`src/components/scanner/performance-alerts-panel.tsx`) uses `EventSource` SSE (`/api/scanner/performance-alerts/stream`) with 15s polling fallback and non-blocking popups.
- **Duplication Identified:** Overlapping routes exist between `/owner/*`, `/dashboard/*` (`/dashboard/community`, `/dashboard/investigate`, `/dashboard/logs`, `/dashboard/projects`, `/dashboard/settings`), and root (`/community`, `/investigate`, `/logs`, `/projects`, `/settings`, `/billing`).

---

## 5. Backend Architecture
- **Core Entry:** `saas-dashboard/backend/main.py` (95 route decorators) + modular routers:
  - `routes/api_v1.py` (Developer API v1 + API Key auth)
  - `routes/integrations.py` (Telegram `getMe` + Discord OAuth2 + AES-256)
  - `routes/performance_alerts.py` (Token performance monitoring + SSE stream + Super Admin defaults)
  - `routes/social_growth.py` (Social publishing, Web3 research, growth opportunities, Super Admin Market Acquisition)
- **Background Workers:** `main.py` launches `run_monitoring_loop(interval_seconds=900)` and `run_buy_monitoring_loop(interval_seconds=30)` at `@app.on_event("startup")`, alongside `scripts/run_all_bots.py` on `zoe-worker`.
- **Queue / Pipeline:** `src/zoe/worker/claim.py`, `pipeline.py`, `outbox/service.py`, `finalizer/sweep.py`.

---

## 6. Database Architecture
- **Production DDL:** `saas-dashboard/backend/init_db.py` + 12 `scripts/setup_*.sql` files (`setup_all_supabase_tables.sql`, `setup_billing_tables.sql`, `setup_unified_billing_tables.sql`, `setup_integrations_tables.sql`, `setup_developer_api_tables.sql`, `setup_investigations_table.sql`, `setup_watchlist_table.sql`, `setup_caller_reputation_tables.sql`, `setup_buy_monitors_table.sql`, `setup_paper_trading_tables.sql`, `setup_price_alerts_and_wallet_follows.sql`, `setup_research_reports_table.sql`).
- **Operational SQLite Fallback (`saas_dev.db`):** `users`, `projects`, `investigations`, `watchlists`, `monitored_tokens`, `token_performance_alerts`, `performance_monitor_settings`, `platform_integrations`, `api_keys`, `api_usage_logs`, `dev_entitlements`, `dev_credit_transactions`, `agent_ledger`, `social_campaigns`, `social_posts`, `social_accounts`, `web3_research_reports`, `research_watchlists`, `growth_opportunities`, `market_acquisition_leads`.
- **Gaps:** No `organizations`, `organization_members`, `team_invitations`, `audit_logs`, `invoices`, `nft_collections`, `nft_campaigns`, or `investor_pipelines` tables exist yet.

---

## 7. Existing Feature Inventory & Classification

| Module | Classification | Evidence |
| --- | --- | --- |
| **Web3 Scanner & Token Performance Alerts** | **1. Fully implemented & verified** | `src/zoe/tools/scanner.py`, `performance_monitor.py`, `routes/performance_alerts.py`, `investigate/page.tsx`, `tests/test_token_performance_monitoring.py` |
| **Wallet Intelligence & Trading Research** | **1. Fully implemented & verified** | `src/zoe/tools/wallet_intel.py`, `trading_intel.py`, `trading/page.tsx` |
| **Telegram & Discord Integrations** | **1. Fully implemented & verified** | `routes/integrations.py`, `integration_security.py`, `owner/integrations/*`, `tests/test_integrations_e2e.py` |
| **Billing, Subscriptions & Atomic Credits** | **1. Fully implemented & verified** | `src/zoe/billing/credit_manager.py`, `main.py` (`/api/billing/*`), `tests/test_unified_billing.py`, `tests/test_credit_integrity.py` |
| **Developer API v1 & Key Hashing** | **1. Fully implemented & verified** | `routes/api_v1.py`, `developer/page.tsx`, `tests/test_developer_api.py` |
| **AI Provider Router & Agents** | **1. Fully implemented & verified** | `src/zoe/llm/router.py`, `src/zoe/agents/*`, `dashboard/agents/page.tsx` |
| **Social Publishing, Web3 Research & Growth** | **2. Partially implemented** | `src/zoe/social/*`, `routes/social_growth.py`, `owner/social/page.tsx`, `admin/growth/page.tsx` (uncommitted local module; Telegram/Discord/Export live, X gated off) |
| **Knowledge Base & RAG** | **2. Partially implemented** | `src/zoe/knowledge/*`, `owner/dashboard/knowledge/page.tsx` (embedding tests hang without cached model weights) |
| **Community Analytics** | **2. Partially implemented** | `community/page.tsx`, `dashboard/community/page.tsx`, `src/zoe/agents/analytics.py` |
| **NFT Growth & Sales** | **2. Partially implemented (Art Studio only)** | `src/zoe/tools/nft_studio.py` + `nft-studio/page.tsx` only generate AI images via Pollinations.ai; no mint campaigns, collection tracking, or sales attribution |
| **Internal Market Acquisition Engine** | **2. Partially implemented** | `admin/growth/page.tsx` + `/api/admin/market-acquisition` provides lead CRUD, but lacks automated prospect discovery, pitch generation, and pilot tracking |
| **Investor Intelligence (Customer-Facing)** | **6. Planned, not implemented** | No customer VC discovery, investor matching, or private fundraising pipeline exists |
| **Team Members & Org Permissions** | **6. Planned, not implemented** | Single `owner_id` / `user_id` ownership model; no multi-user org invites or granular member roles |

---

## 8. Super Admin Dashboard Audit
- **Implemented:** `/admin/overview` (metrics, charts, recent activity, system health, `AdminPerformanceCard`), `/admin/projects` (project list, suspend/activate, assign owner), `/admin/revenue` & `/admin/billing` (plans, revenue, failed payments, manual credit adjustment), `/admin/investigate`, `/admin/settings`, `/admin/growth` (Market Acquisition leads).
- **Missing:** Global customer/user account suspension & role editor UI; global Telegram/Discord integration health & activity monitor (without credential exposure); AI provider/model/fallback management UI; unified platform Audit Log viewer; invoice management.

---

## 9. Project Owner Dashboard Audit
- **Implemented:** `/owner/dashboard` (primary project stats, `PerformanceAlertsPanel`), `/owner/project`, `/owner/dashboard/instructions`, `/owner/dashboard/knowledge`, `/owner/integrations/telegram`, `/owner/integrations/discord`, `/owner/logs`, `/owner/billing`, `/owner/social` (campaigns, AI drafts, approval queue, Web3 research, growth opportunities).
- **Missing:** Team member invitations & role permissions; NFT Growth & Sales (collection monitoring, mint campaigns, referral/sales attribution); customer-facing Investor Intelligence; downloadable invoices & payment method management.

---

## 10. Authentication & Authorization Audit & 11. Multi-Tenant Security Audit
- **Auth & RBAC:** `get_current_user` (JWT) and `require_super_admin` (`role == "super_admin"` or `SUPER_ADMIN_EMAILS`) in `main.py`.
- **Isolation:** `routes/integrations.py`, `routes/performance_alerts.py`, and `routes/social_growth.py` enforce `user_id`/`owner_id` scoping and return `403 Forbidden` on cross-tenant mutations.
- **Security Risks:**
  1. Legacy `/dashboard/*` vs `/owner/*` route duplication increases maintenance surface.
  2. Lack of organization-level `organization_members` table prevents safe delegated team access.
  3. No centralized `audit_logs` table recording all Super Admin mutations (plan edits, credit adjustments, suspensions, global monitor settings).
  4. FastAPI `@app.on_event("startup")` background loops would run duplicate jobs if scaled to >1 web worker.

---

## 12. Telegram & 13. Discord Integration Audit
- **Telegram:** Verified via `getMe`, supports multi-bot & multi-community, tokens encrypted with AES-256-GCM (`integration_security.py`), SHA-256 hashed for duplicate detection, and stripped by `sanitize_integration_record()`.
- **Discord:** Uses official OAuth2 flow (`routes/integrations.py`), encrypted tokens, never asks users to paste raw bot tokens.
- **Gap:** Super Admin has no dedicated global integration health dashboard view across all tenants.

---

## 14. Knowledge Base & RAG Audit
- `src/zoe/knowledge/ingestion.py`, `retriever.py`, `screening.py` separate official project knowledge from community memory (`data/official_knowledge` vs `data/community_memory`).
- `tests/integration/knowledge/test_knowledge.py` and `tests/integration/test_citations.py` hang when local embedding weights are not pre-cached.

---

## 15. AI Provider & Agent Audit
- `src/zoe/llm/router.py` supports Groq + Gemini fallback and rate limiting.
- `src/zoe/agents/` (`BaseAgent`, `AgentRegistry`, `AgentOrchestrator`, `AgentLedger`) is operational with specialized agents in `src/zoe/agents/specialized/`.

---

## 16. Web3 Scanner & Intelligence Audit
- `src/zoe/tools/scanner.py` (Solana + 10 EVM chains via DexScreener & GoPlus) and `src/zoe/scanner/performance_monitor.py` (baseline tracking, 2x/4x/5x/10x & decline alerts, SSE delivery, stale/provider failure safety) are verified and passing (`22/22` tests in `test_token_performance_monitoring.py` + `test_scanner.py`).

---

## 17. Social Intelligence, 18. Growth Engine, 19. NFT Growth & Sales, 20. Investor Intelligence, 21. Market Acquisition Readiness
- **Social Intelligence & Publishing:** Ready at core (`src/zoe/social/*`), with X API/auto-reply/scraping strictly disabled by default (`src/zoe/social/compliance.py`).
- **Growth Engine:** Basic opportunity tracker and analytics live in `growth_intel.py`; lacks referral tracking and campaign attribution.
- **NFT Growth & Sales:** Only `nft_studio.py` artwork generation exists; requires collection/mint/sales data models and on-chain verification.
- **Investor Intelligence (Customer):** Not built; requires private tenant-isolated `investor_pipelines` and VC research service.
- **Market Acquisition (Internal):** Basic Super Admin lead CRUD exists at `/admin/growth`; requires automated prospect discovery and pitch/pilot tracking, kept strictly isolated from customer Investor Intelligence.

---

## 22. Billing & Credit Audit & 23. Notifications & 24. Testing Infrastructure
- **Billing:** Centralized `CreditManager` (`src/zoe/billing/credit_manager.py`) with atomic conditional decrements and idempotency keys (`test_credit_integrity.py`, `test_unified_billing.py`, `test_billing.py` all passing). Missing: invoice PDF/records and automated recurring renewal webhooks.
- **Notifications:** Authenticated SSE stream (`/api/scanner/performance-alerts/stream`) + 15s polling + persistent Notification Centre (`performance-alerts-panel.tsx`).
- **Testing:** Recent SaaS suites pass cleanly; 46 older unit/adversarial tests fail due to `MockLLMClient` fixture drift and outdated prompt assertions, and 2 embedding tests hang without cached model weights.

---

## 25. Missing Capabilities, 26. Critical Security Risks & 27. Duplication
- **Missing:** Team RBAC (`organization_members`), global `audit_logs`, Super Admin Integration Health & AI Infra UI, NFT Growth & Sales subsystem, Customer Investor Intelligence, Invoices/Renewals.
- **Risks:** Multi-worker scheduler duplication; un-audited admin mutations without a persistent `audit_logs` table; legacy test suite drift.
- **Duplication:** Coexisting `/dashboard/*`, root `/projects|/logs|/settings`, and `/owner/*` pages.

---

## 28. External Services & Dependencies Required
- **Active:** Supabase, Railway, Groq, Gemini, DexScreener, GoPlus, Telegram Bot API, Discord OAuth2, Solana RPC, Pollinations.ai.
- **Optional Future:** Official X API v2 OAuth2 (only after account clearance), NFT indexing provider (Helius/Alchemy/Reservoir), Stripe/Coinbase/Solana Pay webhooks for recurring billing.

---

## 29. Recommended Target Architecture & 30. Prioritized Implementation Roadmap

1. **PHASE 1 — Critical Architecture & Security Fixes:** Persistent `audit_logs` table, distributed/SQLite scheduler lock for `zoe-worker`, consolidate duplicate `/dashboard/*` routes into `/owner/*`, fix legacy `MockLLMClient` test fixtures.
2. **PHASE 2 — Super Admin Dashboard Completion:** User/account suspension UI, Global Integration Health monitor (read-only metadata), AI Provider/Model config UI, Audit Log viewer.
3. **PHASE 3 — Project Owner Dashboard Completion:** Organization & Team Member RBAC (`organization_members`, invites, role permissions), unified Owner sidebar.
4. **PHASE 4 — Telegram & Discord Integration Hardening:** Global health telemetry & escalation logs surfaced to Super Admin without credential exposure.
5. **PHASE 5 — Billing, Subscriptions, Credits & Invoices:** Invoice generation, recurring renewal webhooks, org-level usage attribution.
6. **PHASE 6 — Web3 Intelligence & Scanner Enhancements:** Batch DexScreener polling & custom alert policies.
7. **PHASE 7 — Web3 Research & Social Intelligence:** Scheduled watchlist digests and notification centre integration.
8. **PHASE 8 — Social Publishing Agent:** Full calendar UI, recurring schedules, and verified X OAuth2 activation only after X Developer clearance.
9. **PHASE 9 — Growth Engine & NFT Growth & Sales:** Referral tracking, NFT collection monitoring, mint campaigns, verified sales attribution.
10. **PHASE 10 — Investor Intelligence & Market Acquisition:** Private customer fundraising/VC pipeline + Super Admin automated prospect discovery & pitch workflows.
11. **PHASE 11 — AI Agents & Workflow Automation:** Owner-configurable safe workflow triggers with strict tool allowlists.
12. **PHASE 12 — Full Security, Integration & Production-Readiness Testing:** Automated execution of the 18-item security & tenant-isolation test plan below.

---

## 31. Required Security & Functionality Test Plan (18 Mandatory Checks)
1. Super Admin global access (`200` on `/api/admin/*`).
2. Project Owner isolation (`user_id`/`organization_id` scoped queries).
3. Cross-tenant API request rejection (`403` on Owner A vs Owner B).
4. Unauthorized Super Admin endpoint access (`403` for Project Owners).
5. Team permission enforcement (read-only member cannot mutate billing/integrations).
6. Telegram integration ownership & secret stripping.
7. Discord integration OAuth2 ownership & secret stripping.
8. Knowledge-base isolation across projects/orgs.
9. Scanner & performance alert isolation.
10. Billing & credit isolation.
11. Customer Investor Intelligence isolation.
12. Internal Market Acquisition Engine Super-Admin-only isolation (`403` for customers).
13. AES-256-GCM credential encryption at rest.
14. Subscription entitlement enforcement (`403`/`402`).
15. Atomic credit transactions under concurrency.
16. Notification & SSE stream ownership.
17. Immutable administrative audit logging.
18. Background worker tenant context & idempotency.

---

## 32. Estimated Implementation Complexity
- **Overall:** **High** for full 12-phase completion (especially Team RBAC, NFT Growth/Sales indexing, and Investor Intelligence), with Phases 1–4 being **Medium** because core auth, billing, AES-256 vault, SSE notifications, and scanner infrastructure are already verified.
