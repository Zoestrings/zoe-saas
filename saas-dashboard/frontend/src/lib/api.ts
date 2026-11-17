/**
 * API client and auth token management for Zoe SaaS Dashboard.
 * Talks to FastAPI backend at http://localhost:8000
 */

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "https://zoe-saas-production.up.railway.app"
).replace(/\/$/, "")

const TOKEN_KEY = "zoe_auth_token"
const USER_KEY = "zoe_auth_user"

export interface User {
  id: string
  email: string
  role?: "super_admin" | "project_owner" | string
}

export function isSuperAdmin(user?: User | null): boolean {
  const u = user || getUser()
  return u?.role === "super_admin"
}

export interface AuthResponse {
  access_token: string
  token_type?: string
  user: User
}

export interface Project {
  id: string
  owner_id: string
  name: string
  telegram_group_id?: string | null
  token_address?: string | null
  custom_instructions?: string | null
  status?: string | null
  status_error?: string | null
  created_at?: string | null
}

export interface ConversationLogItem {
  id: number
  project_id: string
  user_message: string
  bot_response?: string | null
  intent?: string | null
  category?: string | null
  timestamp: string
  pseudonymous_user_id?: string | null
}

export interface ProjectAnalytics {
  project_id: string
  total_messages: number
  total_tokens: number
  estimated_cost_usd: number
  ca_scans: number
}

export interface CreateProjectPayload {
  name: string
  telegram_bot_token: string
  token_address: string
  telegram_group_id?: string | null
  token_symbol?: string | null
  knowledge_base?: string | null
  custom_instructions?: string | null
}

export interface InvestigationReport {
  valid: boolean
  error?: string
  ca?: string
  ca_short?: string
  name?: string
  symbol?: string
  chain?: string
  market?: {
    found: boolean
    name?: string | null
    symbol?: string | null
    price_usd?: number | null
    market_cap?: number | null
    liquidity_usd?: number | null
    volume_24h?: number | null
    pair_url?: string | null
    pair_created_at?: number | null
    chain_id?: string | null
    chain_name?: string | null
  }
  security?: {
    success: boolean
    mint_revoked?: boolean | null
    freeze_revoked?: boolean | null
    top_10_holders_percent?: number | null
    holder_count?: number | null
    is_honeypot?: boolean
    is_open_source?: boolean | null
    buy_tax?: number | null
    sell_tax?: number | null
    is_mintable?: boolean | null
    lp_locked?: boolean
    lp_lock_percent?: number
    creator_address?: string | null
    dev_wallet_percent?: number
    source?: string
  }
  holder_intelligence?: {
    top_10_percent?: number | null
    holder_count?: number | null
    status?: string
  }
  lp_intelligence?: {
    is_locked: boolean
    lock_percent?: number
    status?: string
  }
  dev_wallet_intelligence?: {
    creator_address?: string | null
    creator_address_short?: string
    holds_percent?: number
    status?: string
  }
  osint?: {
    has_official_website?: boolean
    website?: string | null
    twitter?: string | null
    telegram?: string | null
    discord?: string | null
    github?: string | null
    linkedin?: string | null
    founder?: string | null
    is_anonymous_founder?: boolean
    socials?: Record<string, string>
    evidence_sources?: string[]
  }
  project_osint?: {
    has_official_website?: boolean
    website?: string | null
    twitter?: string | null
    telegram?: string | null
    discord?: string | null
    github?: string | null
    linkedin?: string | null
    founder?: string | null
    is_anonymous_founder?: boolean
    socials?: Record<string, string>
    evidence_sources?: string[]
  }
  risk?: {
    level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    reasons: string[]
    risk_score?: number
  }
  safety_score?: number
  ai_summary?: string
  is_pro?: boolean
  pro_locked?: boolean
  wallet_trace?: WalletTrace
  timestamp_utc?: string
}

export interface WalletTrace {
  traced: boolean
  wallet_address: string
  funding_source: string
  funding_source_short?: string
  funding_entity: string
  is_cex_funded: boolean
  is_fresh_funding_wallet: boolean
  initial_funding_sol: number
  first_tx_hash?: string | null
  outflow_risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNKNOWN"
  outflow_details: string
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN"
  risk_reason: string
  total_tx_count: number
}

export interface Invoice {
  id: string
  user_id: string
  amount_usdt: number
  status: "pending" | "paid" | "expired"
  tx_hash?: string | null
  created_at: string
}

export interface CreateInvoiceResponse {
  invoice_id: string
  amount_usdt: number
  receiving_wallet: string
  status: string
  created_at: string
}

export interface VerifyPaymentResponse {
  success: boolean
  message: string
  plan: string
  expires_at?: string | null
}

export interface EntitlementResponse {
  plan: "free" | "pro"
  is_pro: boolean
  expires_at?: string | null
  receiving_wallet: string
}

export interface AdminRevenueInvoice {
  id: string
  user_id: string
  email: string
  amount_usdt: number
  status: "paid" | "pending" | "expired"
  tx_hash?: string | null
  created_at: string
}

export interface AdminRevenueSummary {
  total_revenue: number
  paid_invoices_count: number
  pending_invoices_count: number
  active_pro_subscribers: number
  monthly_run_rate: number
}

export interface AdminRevenueResponse {
  summary: AdminRevenueSummary
  invoices: AdminRevenueInvoice[]
}

export interface RecentSignup {
  id: string
  email: string
  role: string
  created_at: string
  plan: string
}

export interface RevenueChartPoint {
  date: string
  revenue: number
}

export interface AdminOverviewResponse {
  summary: {
    total_revenue: number
    total_users: number
    total_projects: number
    active_bots: number
    pro_subscribers: number
  }
  recent_signups: RecentSignup[]
  revenue_chart: RevenueChartPoint[]
}

export interface AdminProjectItem {
  id: string
  name: string
  owner_id: string
  owner_email: string
  status: string
  plan: string
  telegram_group_id?: string | null
  token_address?: string | null
  created_at: string
}

export interface SystemHealthResponse {
  status: string
  fastapi: string
  database: string
  solana_rpc: string
  engine: string
  timestamp: string
}

export interface SavedInvestigation {
  id: string
  user_id: string
  contract_address: string
  token_name?: string | null
  risk_level?: string | null
  report_json: InvestigationReport
  created_at: string
}

export interface WatchlistItem {
  id: string
  user_id: string
  contract_address: string
  token_name?: string | null
  initial_liquidity?: number | null
  initial_price?: number | null
  current_liquidity?: number | null
  current_price?: number | null
  last_checked_at?: string | null
  created_at: string
}

export interface SecurityAlert {
  id: string
  user_id?: string
  contract_address: string
  token_name?: string | null
  alert_type: string
  message: string
  old_value?: number | null
  new_value?: number | null
  created_at: string
}

export interface PaperPosition {
  token_address: string
  token_name: string
  token_symbol?: string | null
  token_amount: number
  avg_buy_price: number
  current_price: number
  current_value_usdt: number
  unrealized_pnl_usdt: number
  unrealized_pnl_percent: number
}

export interface PaperTradeItem {
  id: string
  token_address: string
  token_name?: string | null
  trade_type: "buy" | "sell"
  amount_usdt: number
  token_amount: number
  price_at_trade: number
  created_at: string
}

export interface PaperWalletResponse {
  balance_usdt: number
  total_portfolio_value_usdt: number
  total_pnl_usdt: number
  total_pnl_percent: number
  positions: PaperPosition[]
  recent_trades: PaperTradeItem[]
}

export interface ExecutePaperTradeResponse {
  status: string
  message: string
  trade: PaperTradeItem
  balance_usdt: number
}

// --- Local Storage Helpers ---

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch (err) {
    console.error("Failed to save auth token to localStorage", err)
  }
}

export function removeToken(): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch (err) {
    console.error("Failed to remove auth token from localStorage", err)
  }
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setUser(user: User): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch (err) {
    console.error("Failed to save user to localStorage", err)
  }
}

export function removeUser(): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(USER_KEY)
  } catch (err) {
    console.error("Failed to remove user from localStorage", err)
  }
}

export function logout(): void {
  removeToken()
  removeUser()
  if (typeof window !== "undefined") {
    window.location.href = "/login"
  }
}

// --- API Request Client ---

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers || {})

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers,
    })
  } catch (err) {
    // If local backend is not running, automatically failover to live Railway backend
    if (url.includes("localhost:8000")) {
      const fallbackUrl = url.replace("http://localhost:8000", "https://zoe-saas-production.up.railway.app")
      try {
        response = await fetch(fallbackUrl, {
          ...options,
          headers,
        })
      } catch {
        throw new Error("Unable to connect to backend service. Please check your network or start the local server.")
      }
    } else {
      throw new Error("Unable to connect to backend service. Please check your network connection.")
    }
  }

  // Try parsing JSON response
  let data: any = null
  const text = await response.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { message: text }
    }
  }

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      logout()
    }
    const errorMessage = data?.detail || data?.message || `Request failed with status ${response.status}`
    throw new Error(errorMessage)
  }

  return data as T
}

// --- High-Level API Methods ---

export const api = {
  // Authentication
  async register(email: string, password: string): Promise<AuthResponse> {
    const res = await apiRequest<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    if (res.access_token) {
      setToken(res.access_token)
    }
    if (res.user) {
      setUser(res.user)
    }
    return res
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await apiRequest<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    if (res.access_token) {
      setToken(res.access_token)
    }
    if (res.user) {
      setUser(res.user)
    }
    return res
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    return apiRequest<Project[]>("/api/projects", {
      method: "GET",
    })
  },

  async getProject(id: string): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${id}`, {
      method: "GET",
    })
  },

  async createProject(payload: CreateProjectPayload): Promise<Project> {
    return apiRequest<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async patchProject(id: string, payload: { telegram_group_id?: string; token_address?: string }): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },

  async deleteProject(id: string): Promise<{ project_id: string; status: string; message: string }> {
    return apiRequest<{ project_id: string; status: string; message: string }>(`/api/projects/${id}`, {
      method: "DELETE",
    })
  },

  async getProjectStatus(id: string): Promise<any> {
    return apiRequest<any>(`/api/projects/${id}/status`, {
      method: "GET",
    })
  },

  async getProjectLogs(projectId: string, search?: string, limit?: number): Promise<ConversationLogItem[]> {
    const params = new URLSearchParams()
    if (search) params.set("search", search)
    if (limit) params.set("limit", String(limit))
    const query = params.toString() ? `?${params.toString()}` : ""
    return apiRequest<ConversationLogItem[]>(`/api/projects/${projectId}/logs${query}`, {
      method: "GET",
    })
  },

  async getProjectAnalytics(projectId: string): Promise<ProjectAnalytics> {
    return apiRequest<ProjectAnalytics>(`/api/projects/${projectId}/analytics`, {
      method: "GET",
    })
  },

  async investigate(contractAddress: string): Promise<InvestigationReport> {
    return apiRequest<InvestigationReport>("/api/investigate", {
      method: "POST",
      body: JSON.stringify({ contract_address: contractAddress }),
    })
  },

  async getInvestigations(): Promise<SavedInvestigation[]> {
    return apiRequest<SavedInvestigation[]>("/api/investigations", {
      method: "GET",
    })
  },

  // Watchlist & Monitoring (Mega-Module 5)
  async getWatchlist(): Promise<WatchlistItem[]> {
    return apiRequest<WatchlistItem[]>("/api/watchlist", {
      method: "GET",
    })
  },

  async addToWatchlist(contractAddress: string, tokenName?: string): Promise<WatchlistItem> {
    return apiRequest<WatchlistItem>("/api/watchlist", {
      method: "POST",
      body: JSON.stringify({ contract_address: contractAddress, token_name: tokenName }),
    })
  },

  async removeFromWatchlist(id: string): Promise<{ status: string; id: string }> {
    return apiRequest<{ status: string; id: string }>(`/api/watchlist/${id}`, {
      method: "DELETE",
    })
  },

  async getAlerts(): Promise<SecurityAlert[]> {
    return apiRequest<SecurityAlert[]>("/api/alerts", {
      method: "GET",
    })
  },

  async triggerWatchlistCheck(): Promise<{ status: string; message: string; alerts_count: number; alerts: SecurityAlert[] }> {
    return apiRequest<{ status: string; message: string; alerts_count: number; alerts: SecurityAlert[] }>("/api/watchlist/check-now", {
      method: "POST",
    })
  },

  // Billing & Entitlements (Mega-Module 6)
  async getEntitlement(): Promise<EntitlementResponse> {
    return apiRequest<EntitlementResponse>("/api/billing/entitlement", {
      method: "GET",
    })
  },

  async createInvoice(): Promise<CreateInvoiceResponse> {
    return apiRequest<CreateInvoiceResponse>("/api/billing/create-invoice", {
      method: "POST",
    })
  },

  async verifyPayment(invoiceId: string, txHash: string): Promise<VerifyPaymentResponse> {
    return apiRequest<VerifyPaymentResponse>("/api/billing/verify-payment", {
      method: "POST",
      body: JSON.stringify({ invoice_id: invoiceId, tx_hash: txHash }),
    })
  },

  async getInvoices(): Promise<Invoice[]> {
    return apiRequest<Invoice[]>("/api/billing/invoices", {
      method: "GET",
    })
  },

  async getAdminRevenue(): Promise<AdminRevenueResponse> {
    return apiRequest<AdminRevenueResponse>("/api/admin/revenue", {
      method: "GET",
    })
  },

  // Admin Master Control (Mega-Module 10)
  async getAdminOverview(): Promise<AdminOverviewResponse> {
    return apiRequest<AdminOverviewResponse>("/api/admin/overview", {
      method: "GET",
    })
  },

  async getAdminAllProjects(): Promise<AdminProjectItem[]> {
    return apiRequest<AdminProjectItem[]>("/api/admin/projects", {
      method: "GET",
    })
  },

  async suspendProject(projectId: string): Promise<{ status: string; project_id: string; message: string }> {
    return apiRequest<{ status: string; project_id: string; message: string }>(`/api/admin/projects/${projectId}/suspend`, {
      method: "POST",
    })
  },

  async activateProject(projectId: string): Promise<{ status: string; project_id: string; message: string }> {
    return apiRequest<{ status: string; project_id: string; message: string }>(`/api/admin/projects/${projectId}/activate`, {
      method: "POST",
    })
  },

  async getSystemHealth(): Promise<SystemHealthResponse> {
    return apiRequest<SystemHealthResponse>("/api/admin/health", {
      method: "GET",
    })
  },

  // Paper Trading Engine (Mega-Module 11)
  async getPaperWallet(): Promise<PaperWalletResponse> {
    return apiRequest<PaperWalletResponse>("/api/trading/wallet", {
      method: "GET",
    })
  },

  async executePaperTrade(payload: {
    token_address: string
    trade_type: "buy" | "sell"
    amount_usdt: number
    token_name?: string
  }): Promise<ExecutePaperTradeResponse> {
    return apiRequest<ExecutePaperTradeResponse>("/api/trading/execute", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async resetPaperWallet(): Promise<{ status: string; balance_usdt: number; message: string }> {
    return apiRequest<{ status: string; balance_usdt: number; message: string }>("/api/trading/reset", {
      method: "POST",
    })
  },
}
