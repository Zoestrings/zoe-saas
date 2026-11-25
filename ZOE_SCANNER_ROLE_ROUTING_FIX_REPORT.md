# Zoe Intelligence — Scanner Role Routing Fix Report

## 1. Root Cause

The scanner page (`saas-dashboard/frontend/src/app/investigate/page.tsx`) and its companion routes (`/watchlist`, `/community`) were rendered inside standalone Next.js layouts (`investigate/layout.tsx`, `watchlist/layout.tsx`, `community/layout.tsx`) that **unconditionally** rendered `<AdminSidebar />` and `<AdminHeader />` for every authenticated user.

Because `OwnerLayout` (`saas-dashboard/frontend/src/app/owner/layout.tsx`) linked to `/investigate` and `/watchlist`, any Project Owner who opened the Web3 Scanner (or navigated to `/investigate`, `/watchlist`, or `/community`) was immediately placed inside the Super Admin navigation shell—making it appear as though performing a scan redirected them to the Super Admin Dashboard.

Additionally, `GET /api/investigations` (`saas-dashboard/backend/main.py`) always filtered strictly by `user_id = current_user.get("id")` without an explicit Super Admin global-history flag (`all_tenants`), whereas Super Admins need to inspect global scan records while Project Owners must remain strictly isolated to their own records.

---

## 2. Files Changed

### Frontend
- **Created** `saas-dashboard/frontend/src/components/layout/role-aware-shell.tsx`
  - Checks `getToken()`; redirects unauthenticated users to `/login`.
  - Checks `isSuperAdmin()`; renders `<AdminSidebar />` + `<AdminHeader />` for `super_admin` and wraps content in `<OwnerLayout>` for Project Owners.
- **Created** `saas-dashboard/frontend/src/app/owner/investigate/page.tsx`
  - Renders the shared `<InvestigatePage />` inside `/owner/*` so Project Owners stay on `/owner/investigate` within `OwnerLayout`.
- **Updated** `saas-dashboard/frontend/src/app/investigate/layout.tsx`
- **Updated** `saas-dashboard/frontend/src/app/watchlist/layout.tsx`
- **Updated** `saas-dashboard/frontend/src/app/community/layout.tsx`
  - Replaced unconditional `<AdminSidebar />` + `<AdminHeader />` with `<RoleAwareShell>`.
- **Updated** `saas-dashboard/frontend/src/app/owner/layout.tsx`
  - Updated `Web3 Scanner` sidebar link from `/investigate` to `/owner/investigate`.
- **Updated** `saas-dashboard/frontend/src/app/owner/dashboard/page.tsx`
  - Updated quick-action `Token Scanner` link from `/investigate` to `/owner/investigate`.
- **Updated** `saas-dashboard/frontend/src/app/owner/billing/page.tsx`
  - Updated `Open Scanner` link from `/investigate` to `/owner/investigate`.
- **Updated** `saas-dashboard/frontend/src/components/scanner/performance-alerts-panel.tsx`
  - Updated `Token Investigator` link to route to `/admin/investigate` for Super Admins and `/owner/investigate` for Project Owners via `isSuperAdmin()`.
- **Updated** `saas-dashboard/frontend/src/lib/api.ts`
  - Added `allTenants = false` parameter to `api.getInvestigations(allTenants)` appending `?all_tenants=true` when requested.
- **Updated** `saas-dashboard/frontend/src/app/investigate/page.tsx`
  - Updated `loadHistory()` to pass `isSuperAdmin()` to `api.getInvestigations(isSuperAdmin())`.

### Backend
- **Updated** `saas-dashboard/backend/main.py` (`GET /api/investigations`)
  - Added `all_tenants: bool = False` query parameter.
  - Enforces `403 Forbidden` if a non-`super_admin` passes `all_tenants=true`.
  - Returns global records (up to 50) when `all_tenants=True` and `current_user.get("role") == "super_admin"`; otherwise strictly scopes to `user_id = current_user.get("id")` (up to 10).

### Tests
- **Created** `tests/test_scanner_role_routing.py`
  - Verifies `401 Unauthorized` for unauthenticated `GET /api/investigations` and `POST /api/investigate`.
  - Verifies Project Owner tenant isolation on `GET /api/investigations` and `POST /api/investigate`.
  - Verifies `403 Forbidden` when a Project Owner requests `?all_tenants=true`.
  - Verifies Super Admin global history access with `?all_tenants=true`.
  - Verifies frontend layouts (`investigate`, `watchlist`, `community`) use `RoleAwareShell` without unconditional `AdminSidebar`/`AdminHeader`, and `/owner/investigate` is wired.

---

## 3. Routes Corrected

| Route | Before | After |
|---|---|---|
| `/owner/investigate` | Did not exist | Dedicated Project Owner scanner route inside `OwnerLayout` |
| `/investigate` | Always rendered `AdminSidebar` + `AdminHeader` | Uses `RoleAwareShell` (`OwnerLayout` for Project Owners, `AdminSidebar` + `AdminHeader` for Super Admins, `/login` if unauthenticated) |
| `/watchlist` | Always rendered `AdminSidebar` + `AdminHeader` | Uses `RoleAwareShell` |
| `/community` | Always rendered `AdminSidebar` + `AdminHeader` | Uses `RoleAwareShell` |
| `/admin/investigate` | Super Admin scanner route | Preserved inside `AdminLayout` + Super Admin flow |

---

## 4. Security Implications

- **No Super Admin UI leakage:** Project Owners can no longer see `AdminSidebar` or `AdminHeader` on `/investigate`, `/watchlist`, `/community`, or `/owner/investigate`.
- **Backend-enforced tenant isolation:** `POST /api/investigate` and `GET /api/investigations` derive `user_id` and `role` exclusively from the verified JWT session (`get_current_user`).
- **Privilege escalation blocked:** Passing `?all_tenants=true` as a Project Owner returns `403 Forbidden`.

---

## 5. Tests Executed and Results

1. **Frontend TypeScript Check & Production Build (`saas-dashboard/frontend`):**
   - `npx tsc --noEmit` & `npm run build`: **Passed** (`48/48` routes compiled and generated cleanly, including `/owner/investigate`, `/investigate`, `/admin/investigate`, `/watchlist`, `/community`).
2. **Backend & Routing Unit Tests:**
   - `tests/test_scanner_role_routing.py` (4 tests) + `tests/test_project_owner_dashboard.py` (1 test): **5 passed**.
   - Offline scanner unit tests (`tests/test_scanner.py -k "not live"`): executed alongside the routing suite (live OSINT network test `test_live_scan_solana_token` excluded in offline run).

---

## 6. Remaining Issues

- **Git / Deployment:** Per instructions, changes have **not** been committed, pushed, or deployed.
- **Watchlist & Community `/owner/*` aliases:** `/watchlist` and `/community` now safely render inside `OwnerLayout` for Project Owners via `RoleAwareShell`; dedicated `/owner/watchlist` and `/owner/community` route aliases can be added later if desired, though the current routes already preserve role context.
