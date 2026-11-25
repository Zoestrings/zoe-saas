# Zoe Intelligence — Token Performance Monitoring & Real-Time Dashboard Alerts Implementation Report

## 1. Existing Functionality Reused
- **Token Identification & Chain Detection:** Reused `detect_chain` from `src/zoe/tools/scanner.py` (supports Solana and EVM contract addresses).
- **Market Data Provider:** Reused `fetch_dexscreener_market_data` from `src/zoe/tools/scanner.py` (no duplicate scanner or market-data client was created).
- **Background Worker Loop:** Integrated `run_performance_monitoring_cycle()` into the existing `run_monitoring_loop()` in `src/zoe/monitor.py` started at FastAPI boot (`saas-dashboard/backend/main.py`).
- **Authentication, RBAC & Entitlements:** Reused `get_current_user`, `require_super_admin`, `get_dev_db`, and `dev_entitlements` in `saas-dashboard/backend/main.py`.

## 2. Database Changes
Implemented in `ensure_performance_schema(conn)` inside `src/zoe/scanner/performance_monitor.py`:
- `monitored_tokens`: Stores tenant ownership (`user_id`, `organization_id`, `project_id`), `scan_id`, `blockchain`, `contract_address`, `token_name`, `token_symbol`, validated `baseline_price`, `baseline_timestamp`, `current_price`, `highest_observed_price`, `current_multiple`, `percentage_change`, `drawdown_from_high_pct`, `market_cap`, `liquidity_usd`, `data_source`, `data_freshness`, `monitoring_status`, `positive_thresholds_json`, `negative_thresholds_json`, `drawdown_threshold_pct`, `realert_cooldown_seconds`, `last_checked_at`, `last_successful_at`, with `UNIQUE(user_id, blockchain, contract_address)`.
- `token_performance_alerts`: Stores persistent alert events (`id`, `monitoring_id`, `organization_id`, `project_id`, `user_id`, `blockchain`, `contract_address`, `token_name`, `token_symbol`, `alert_type`, `threshold_value`, `baseline_price`, `observed_price`, `observed_multiple`, `observed_percentage_change`, `market_cap`, `provider`, `message`, `idempotency_key UNIQUE`, `notification_status`, `read_status`, `event_timestamp`, `created_at`).
- `performance_monitor_settings`: Stores platform-wide Super Admin defaults (`default_positive_thresholds_json`, `default_negative_thresholds_json`, `max_monitored_free`, `max_monitored_pro`, `polling_interval_seconds`).

## 3. Monitoring Architecture & Price Calculation Methodology
- **Shared Engine (`src/zoe/scanner/performance_monitor.py`):**
  - `register_token_monitoring(...)`: Validates contract address via `detect_chain`, rejects failed snapshots (`found=False`) or non-positive prices (`<= 0`), enforces per-plan monitoring limits (`PermissionError` when exceeded), and captures the validated baseline price & timestamp.
  - `evaluate_price_update(...)`: Uses full floating-point precision prior to threshold evaluation:
    - `current_multiple = observed_price / baseline_price`
    - `percentage_change = ((observed_price - baseline_price) / baseline_price) * 100`
    - Tracks `highest_observed_price` and separate `drawdown_from_high_pct` without conflating drawdown with baseline performance.
  - **Market-Data Reliability:** Missing (`None`), non-positive (`<= 0`), or `is_stale=True` prices never trigger alerts and update `data_freshness` (`stale` or `provider_error`) while preserving the last valid `current_price`.
  - **Deduplication & Anti-Spam:** Thread mutex (`_MONITOR_MUTEX`) + `UNIQUE(idempotency_key)` ensures each crossed threshold alerts once per monitoring record (including multi-milestone jumps in a single update, e.g., `1.5x -> 4.5x` triggers `2x`, `3x`, `4x` without duplicating on subsequent oscillations).

## 4. Threshold Configuration
- **Default Positive Milestones:** `2x, 3x, 4x, 5x, 10x, 20x, 50x, 100x` (configurable per token and globally by Super Admin).
- **Default Negative Declines:** `-10%, -20%, -30%, -50%, -70%, -90%` (plus optional high-water-mark `drawdown_threshold_pct`).

## 5. API Endpoints, Notification Delivery & Tenant Isolation
Implemented in `saas-dashboard/backend/routes/performance_alerts.py` and mounted in `saas-dashboard/backend/main.py`:
- `POST /api/scanner/monitor` — Validates CA & fetches live DexScreener market snapshot server-side (never trusts client-submitted baseline price).
- `GET /api/scanner/monitored` — Scoped to `current_user["id"]`; `all_tenants=true` requires `role == "super_admin"` (403 otherwise).
- `PATCH /api/scanner/monitored/{monitoring_id}` & `DELETE /api/scanner/monitored/{monitoring_id}` — Enforces record ownership (403 on cross-tenant access).
- `POST /api/scanner/monitored/check-now` — Runs `run_performance_monitoring_cycle(user_id_filter=user_id)`.
- `GET /api/scanner/performance-alerts`, `POST /api/scanner/performance-alerts/{alert_id}/read`, `POST /api/scanner/performance-alerts/read-all` — Persistent notification centre with blockchain, alert type, token, and unread filters so offline users receive missed alerts upon return.
- `GET /api/scanner/performance-alerts/stream` — Authenticated Server-Sent Events (SSE) stream with 15-second authenticated polling fallback in `PerformanceAlertsPanel`.
- `GET /api/admin/performance-monitoring` & `POST /api/admin/performance-monitoring/settings` — Protected by `Depends(require_super_admin)`.

## 6. Frontend Integration
- `saas-dashboard/frontend/src/lib/api.ts`: Added TypeScript client methods for registration, monitoring management, alerts, and admin overview/settings.
- `saas-dashboard/frontend/src/components/scanner/performance-alerts-panel.tsx`: Non-blocking floating milestone popup notifications, Unrealized Price Performance disclaimer banner, Monitored Tokens table (pause/resume/delete/refresh), and persistent Notification Centre with filters.
- `saas-dashboard/frontend/src/app/investigate/page.tsx`: Added **[Monitor Token]** action button on scan results and mounted `PerformanceAlertsPanel`.
- `saas-dashboard/frontend/src/app/owner/dashboard/page.tsx`: Mounted `PerformanceAlertsPanel`.
- `saas-dashboard/frontend/src/components/scanner/admin-performance-card.tsx` & `saas-dashboard/frontend/src/app/admin/overview/page.tsx`: Added Global Token Performance Monitoring summary card and platform defaults form.

## 7. Automated Test & Build Results
- **Backend Pytest Suite:**
  - Command: `$env:PYTHONPATH='src;saas-dashboard/backend'; .venv\Scripts\python.exe -m pytest tests/test_token_performance_monitoring.py tests/test_scanner.py -v`
  - Result: **22 passed, 0 failed** (8 new tests covering scan registration, invalid token rejection, baseline capture, 2x/4x/multi-milestone jumps, -20%/-50% drops, deduplication/anti-spam, stale/provider failure safety, plan limits, concurrent jobs, cross-tenant 403 isolation, Super Admin global access, and offline missed alerts + 14 existing `tests/test_scanner.py` tests including live Solana DexScreener scan).
- **Frontend Production Build:**
  - Command: `cd saas-dashboard\frontend; npm run build`
  - Result: **Passed** (`40/40` Next.js static/dynamic routes compiled cleanly with 0 TypeScript errors).

## 8. Known Limitations & Deployment Requirements
- **Live Market Data:** `test_scanner.py::test_live_scan_solana_token` exercises live DexScreener API calls; `test_token_performance_monitoring.py` uses controlled price fixtures for deterministic threshold/failure assertions.
- **Polling Interval:** `run_monitoring_loop` runs on FastAPI startup in `saas-dashboard/backend/main.py`; production deployments behind multiple worker processes should run a single dedicated scheduler instance or external worker to avoid redundant DexScreener requests.
