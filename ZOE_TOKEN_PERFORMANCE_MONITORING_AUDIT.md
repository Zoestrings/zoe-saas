# ZOE INTELLIGENCE — TOKEN PERFORMANCE MONITORING AUDIT (PHASE A)

**Audit Date:** November 25, 2026  
**Scope:** Existing Token Scanner, Market-Data Providers, Watchlist/Alerts, Notifications, Authorization, and Background Jobs.

---

## 1. Existing Token Scanner & Supported Networks
- **Location:** [scanner.py](file:///c:/Users/GOODLUCK/Desktop/zoe/src/zoe/tools/scanner.py)
- **Supported Networks:** Solana (validated via `is_valid_solana_ca`) and 10 EVM chains (`ethereum`, `bsc`, `base`, `arbitrum`, `polygon`, `avalanche`, `linea`, `optimism`, `zksync`, `blast` via `detect_chain()`).
- **Historical Scan Persistence:** `POST /api/investigate` in [main.py](file:///c:/Users/GOODLUCK/Desktop/zoe/saas-dashboard/backend/main.py#L3344) persists scan summaries into `dev_investigations` (SQLite) and `investigations` (Supabase).

## 2. Market-Data Providers & Retrieval
- **Primary Market Provider:** DexScreener (`fetch_dexscreener_market_data` in `scanner.py` and `get_token_price` in `dexscreener.py`) returns `price_usd`, `liquidity_usd`, `market_cap` (FDV), `volume_24h`, `name`, `symbol`, and `chain_id`.
- **Security Providers:** RugCheck (Solana) and GoPlus Security API (EVM).

## 3. Existing Watchlists, Alerts & Background Monitoring
- **Background Worker:** [monitor.py](file:///c:/Users/GOODLUCK/Desktop/zoe/src/zoe/monitor.py) runs `run_monitoring_loop(interval_seconds=900)` on FastAPI startup (`main.py:6190`).
- **Existing Tables:** `dev_watchlists` (tracks `initial_liquidity`, `initial_price`, `last_checked_at`) and `dev_alerts` (stores liquidity drop alerts > 20%).
- **Gap Identified:** `monitor.py` only checks liquidity drops (> 20%) and does **not** track token price multiples (`2x`, `3x`, `4x`, `5x`, `10x`), percentage declines (`-10%` to `-90%`), high-water-mark drawdown, idempotency keys per milestone, multi-milestone jumps, or per-tenant/Super Admin performance dashboards.

## 4. Notification & Delivery Infrastructure
- **Current Delivery:** `admin-header.tsx` polls `GET /api/alerts` for the notification bell. No SSE/WebSocket stream exists for real-time milestone popups.
- **Authorization & Entitlements:** `get_current_user`, `require_super_admin`, and `EntitlementEngine` (`src/zoe/billing/credit_manager.py`) are operational and ready for plan-based monitoring limits.

## 5. Implementation Approach
Reuse `detect_chain`, `fetch_dexscreener_market_data`, `run_monitoring_loop` (`monitor.py`), and `EntitlementEngine` to add a shared Token Performance Monitoring engine (`src/zoe/scanner/performance_monitor.py`), SSE + polling endpoints, and tenant-isolated Owner & Super Admin UI panels.
