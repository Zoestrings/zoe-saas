# ZOE INTELLIGENCE — BILLING ARCHITECTURE AUDIT (PHASE A)

**Audit Date:** November 25, 2026  
**Scope:** Existing Credit System, Solana USDT Payments, Subscription Plans, Usage Metering, Tenant Isolation, and Super Admin Controls.

---

## 1. Current Credit System
- **Storage:** Credits are stored in `public.entitlements` (Supabase) and `dev_entitlements` (`saas_dev.db` SQLite) with `plan`, `credits` (default `50`), `expires_at`, `updated_at`.
- **Deduction & Ledger:** [credit_manager.py](file:///c:/Users/GOODLUCK/Desktop/zoe/src/zoe/billing/credit_manager.py) provides `CreditManager.deduct_credits`, `refund_credits`, and `admin_adjust_credits` using SQLite `BEGIN IMMEDIATE` transactions, conditional `UPDATE ... WHERE credits >= ?`, idempotency keys, and `dev_credit_transactions`.
- **Gap:** Lacks two-phase `reserve_credits` / `settle_credits` reservations (`credit_reservations`), dedicated `credit_wallets`, `subscription_plans`, `subscriptions`, `payment_transactions`, and `usage_records` tables.

## 2. Payment Integration
- **Verification:** `POST /api/billing/create-invoice` and `POST /api/billing/verify-payment` in [main.py](file:///c:/Users/GOODLUCK/Desktop/zoe/saas-dashboard/backend/main.py#L3766-L3960) verify on-chain Solana SPL USDT transfers to `ZOE_SOLANA_WALLET` via `verify_solana_usdt_payment(tx_hash, required_amount_usdt)`.
- **Gap:** Lacks explicit duplicate `tx_hash` replay protection across invoices (`payment_transactions` unique `tx_hash` constraint) and a signed webhook endpoint for automated payment settlement.

## 3. Existing Plans
- **Pricing:** Hardcoded in `main.py` (`$20 USDT` for Pro 30-day subscription; `$5 = 500`, `$15 = 1,600`, `$40 = 4,500` credit bundles).
- **Gap:** Plans are not stored in a configurable `subscription_plans` database table manageable by the Super Admin.

## 4. API Usage Metering
- **Current Metering:** `DEFAULT_ACTION_COSTS` in `credit_manager.py` and `CREDIT_COSTS` in `pipeline.py` map actions (`token_scan: 15`, `contract_audit: 50`, `nft_generate: 20`, `trading_research: 10`, `api_v1_chat: 2`).
- **Gap:** No centralized `usage_records` table or `EntitlementEngine` checking subscription status + plan feature flags + wallet balance before execution.

## 5. Tenant Isolation
- **Current State:** `/api/billing/*` endpoints filter by `current_user["id"]`.
- **Gap:** Needs explicit RLS policies on all new billing tables (`credit_wallets`, `subscriptions`, `payment_transactions`, `usage_records`) and cross-tenant automated tests.

## 6. Super Admin Controls
- **Current State:** `GET /api/admin/revenue` returns invoices and Pro subscriber counts (restricted to `super_admin`).
- **Gap:** `/admin/billing` lacks configurable plan management, failed-payment visibility, and an interactive Super Admin credit-adjustment UI with audit trail.
