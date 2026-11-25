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
  display_name?: string | null
}

export function isSuperAdmin(user?: User | null): boolean {
  const u = user || getUser()
  const email = (u?.email || "").toLowerCase().trim()
  if (email === "akpodomagoodluck7@gmail.com" || email === "admin@zoe.com" || email === "founder@zoe.com" || email === "defimaverick7@gmail.com") {
    return true
  }
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
  platform?: string | null
  discord_token?: string | null
  twitter_api_key?: string | null
  twitter_api_secret?: string | null
  twitter_access_token?: string | null
  twitter_access_secret?: string | null
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
  telegram_bot_token?: string | null
  token_address?: string | null
  telegram_group_id?: string | null
  token_symbol?: string | null
  knowledge_base?: string | null
  custom_instructions?: string | null
  api_key?: string | null
  owner_id?: string | null
  platform?: string | null
  discord_token?: string | null
  twitter_api_key?: string | null
  twitter_api_secret?: string | null
  twitter_access_token?: string | null
  twitter_access_secret?: string | null
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
  x_sentiment?: {
    sentiment: "Bullish" | "Bearish" | "Neutral" | "Mixed" | "Unknown" | string
    summary: string
    top_narratives: string[]
    bullish_factors?: string[]
    bearish_factors?: string[]
    tweet_count?: number
    disclaimer?: string
  }
  upcoming_catalysts?: Array<{
    date: string
    event: string
    source?: string
  }>
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
  credit_amount?: number
  receiving_wallet: string
  status: string
  created_at: string
}

export interface VerifyPaymentResponse {
  success: boolean
  message: string
  plan: string
  credits?: number
  expires_at?: string | null
}

export interface EntitlementResponse {
  plan: "free" | "pro"
  is_pro: boolean
  credits?: number
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

export interface ServiceHealthItem {
  name: string
  status: "healthy" | "degraded" | "warning" | "offline"
  latency_ms?: number
  model?: string
  detail?: string
}

export interface AdminSystemHealthResponse {
  status: "healthy" | "degraded" | "offline"
  timestamp: string
  services: {
    supabase: ServiceHealthItem
    engine: ServiceHealthItem
    ai: ServiceHealthItem
  }
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
  platform?: string | null
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
  is_read?: boolean
}

export interface NarrativeRecord {
  id: string
  name: string
  category: string
  description: string
  keywords: string[]
  status: string
  current_frequency: number
  historical_frequency: number
  momentum_pct: number
  mindshare_pct: number
  sentiment_score: number
  sentiment_label: string
  associated_projects: string[]
  sample_size: number
  updated_at: string
}

export interface TrendingProject {
  name: string
  symbol: string
  contract_address?: string | null
  chain: string
  narrative: string
  news_count: number
  social_volume: number
  unique_authors: number
  mindshare_pct: number
  momentum_pct: number
  sentiment_label: string
  sentiment_score: number
  price_usd?: number | null
  liquidity_usd?: number | null
  volume_24h_usd?: number | null
  discovery_reason: string
  flags: string[]
}

export interface MindshareResult {
  category: string
  timeframe: string
  total_mentions_in_category: number
  total_unique_authors: number
  projects: Array<{
    name: string
    symbol: string
    posts_count: number
    unique_authors: number
    mindshare_pct: number
    previous_mindshare_pct: number
    change_pct: number
    author_diversity_ratio: number
  }>
  methodology: string
}

export interface ScannerAlertRule {
  rule_id: string
  user_id: string
  project_id?: string | null
  rule_type: string
  target_entity: string
  threshold: number
  cooldown_minutes: number
  enabled: boolean
  created_at: string
}

export interface ScannerAlertEvent {
  event_id: string
  rule_id?: string | null
  severity: "low" | "medium" | "high" | "critical"
  title: string
  message: string
  trigger_explanation: string
  supporting_sources: Array<{ title: string; url: string; domain?: string }>
  is_read: boolean
  timestamp_utc: string
}

export interface IntelligenceReport {
  report_id: string
  title: string
  topic: string
  entity_type: string
  executive_summary: string
  narrative_overview: string
  market_and_mindshare: string
  sentiment_analysis: string
  social_and_news_evidence: string
  important_sources: Array<{ title: string; url: string; domain?: string }>
  missing_information: string
  limitations_and_confidence: string
  created_at_utc: string
}

export interface AgentConfig {
  agent_id: string
  name: string
  description: string
  category: string
  capabilities: string[]
  approved_tools: string[]
  security_level: string
  system_prompt?: string
  max_steps: number
  timeout_seconds: number
  is_custom?: boolean
  is_active: boolean
  credit_cost_per_call: number
}

export interface OrchestrationResult {
  workflow_id: string
  execution_id: string
  status: string
  step_results: Record<string, any>
  final_output: Record<string, any>
  final_synthesis?: string
  total_time_ms: number
  total_execution_time_ms?: number
  agents_involved: string[]
  audit_trail: Array<{
    step: string
    agent: string
    status: string
    latency_ms: number
    tools?: string[]
  }>
}

export interface AgentTaskRecord {
  task_id: string
  correlation_id: string
  agent_id: string
  action: string
  status: string
  payload: Record<string, any>
  result_data: any
  latency_ms: number
  tools_called: string[]
  created_at: string
}

export interface WorkflowTemplate {
  workflow_id: string
  name: string
  description: string
  trigger_type?: string
  schedule_cron?: string
  steps: Array<{
    step_id: string
    name: string
    agent_id: string
    action: string
    depends_on?: string[]
  }>
  is_active?: boolean
  created_at?: string
}

export interface BillingHistoryItem {
  id: string
  user_id?: string
  date: string
  created_at: string
  amount: number
  amount_usdt: number
  status: "pending" | "paid" | "expired" | string
  tx_hash?: string | null
  currency?: string
  network?: string
  plan?: string
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

  async getProjectDocuments(projectId: string): Promise<any[]> {
    return apiRequest<any[]>(`/api/projects/${projectId}/documents`, {
      method: "GET",
    })
  },

  async getProjectResearchReports(projectId: string, limit: number = 5): Promise<{ id: string; project_id: string; report_text: string; created_at: string }[]> {
    return apiRequest<{ id: string; project_id: string; report_text: string; created_at: string }[]>(
      `/api/projects/${projectId}/research-reports?limit=${limit}`,
      { method: "GET" }
    )
  },

  async generateProjectResearchReport(projectId: string): Promise<{ id: string; project_id: string; report_text: string; created_at: string }> {
    return apiRequest<{ id: string; project_id: string; report_text: string; created_at: string }>(
      `/api/projects/${projectId}/research-reports/generate`,
      { method: "POST" }
    )
  },

  async getProjectSettings(projectId: string): Promise<{ custom_instructions?: string; model?: string }> {
    return apiRequest<{ custom_instructions?: string; model?: string }>(`/api/projects/${projectId}/settings`, {
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

  async markAlertsRead(): Promise<{ success: boolean; message: string }> {
    return apiRequest<{ success: boolean; message: string }>("/api/alerts/read", {
      method: "POST",
    })
  },

  async triggerWatchlistCheck(): Promise<{ status: string; message: string; alerts_count: number; alerts: SecurityAlert[] }> {
    return apiRequest<{ status: string; message: string; alerts_count: number; alerts: SecurityAlert[] }>("/api/watchlist/check-now", {
      method: "POST",
    })
  },

  // User Profile & Security Settings (Mega-Module 12)
  async updateProfile(displayName: string): Promise<{ success: boolean; message: string; display_name: string; user?: User }> {
    const res = await apiRequest<{ success: boolean; message: string; display_name: string; user?: User }>("/api/user/profile", {
      method: "POST",
      body: JSON.stringify({ display_name: displayName }),
    })
    const cur = getUser()
    if (cur) {
      setUser({ ...cur, display_name: displayName })
    }
    return res
  },

  async updatePassword(password: string): Promise<{ success: boolean; message: string }> {
    return apiRequest<{ success: boolean; message: string }>("/api/user/password", {
      method: "POST",
      body: JSON.stringify({ password }),
    })
  },

  // Billing & Entitlements (Mega-Module 6 & 12)
  async getBillingHistory(): Promise<BillingHistoryItem[]> {
    return apiRequest<BillingHistoryItem[]>("/api/billing/history", {
      method: "GET",
    })
  },
  async getEntitlement(): Promise<EntitlementResponse> {
    return apiRequest<EntitlementResponse>("/api/billing/entitlement", {
      method: "GET",
    })
  },

  async createInvoice(params?: { credit_amount?: number; price_usdt?: number }): Promise<CreateInvoiceResponse> {
    return apiRequest<CreateInvoiceResponse>("/api/billing/create-invoice", {
      method: "POST",
      body: JSON.stringify(params || {}),
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

  async assignProjectOwner(projectId: string, email: string): Promise<{ status: string; message: string; project_id: string; owner_id: string; owner_email: string }> {
    return apiRequest<{ status: string; message: string; project_id: string; owner_id: string; owner_email: string }>(`/api/admin/projects/${projectId}/assign-owner`, {
      method: "POST",
      body: JSON.stringify({ email }),
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

  // Community Intelligence (Coral Parity)
  async getCommunityLeaderboard(projectId?: string, timeframe: string = "7d"): Promise<any[]> {
    const q = new URLSearchParams()
    if (projectId) q.append("project_id", projectId)
    q.append("timeframe", timeframe)
    return apiRequest<any[]>(`/api/community/leaderboard?${q.toString()}`, {
      method: "GET",
    })
  },

  async getCommunityPredictions(projectId?: string): Promise<any[]> {
    const q = new URLSearchParams()
    if (projectId) q.append("project_id", projectId)
    return apiRequest<any[]>(`/api/community/predictions?${q.toString()}`, {
      method: "GET",
    })
  },

  async createPredictionMarket(payload: {
    project_id: string
    question: string
    target_token?: string
    target_metric?: string
    target_value?: number
    duration_hours?: number
  }): Promise<any> {
    return apiRequest<any>("/api/community/predictions", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async votePredictionMarket(predictionId: string, choice: "yes" | "no"): Promise<any> {
    return apiRequest<any>(`/api/community/predictions/${predictionId}/vote`, {
      method: "POST",
      body: JSON.stringify({ choice }),
    })
  },

  async getWalletIntelligence(address: string): Promise<any> {
    return apiRequest<any>(`/api/community/wallet/${encodeURIComponent(address)}`, {
      method: "GET",
    })
  },

  async getXAccountIntelligence(username: string): Promise<any> {
    return apiRequest<any>(`/api/community/x/${encodeURIComponent(username)}`, {
      method: "GET",
    })
  },

  async getAdminMetrics(): Promise<{
    total_projects: number
    total_conversations: number
    total_investigations: number
    system_uptime: string
    rag_chunks: number
  }> {
    return apiRequest<{
      total_projects: number
      total_conversations: number
      total_investigations: number
      system_uptime: string
      rag_chunks: number
    }>("/api/admin/metrics", { method: "GET" })
  },

  async getAdminChartData(): Promise<{
    days: Array<{ date: string; value: number }>
  }> {
    return apiRequest<{
      days: Array<{ date: string; value: number }>
    }>("/api/admin/chart-data", { method: "GET" })
  },

  async getAdminRecentActivity(): Promise<{
    activities: Array<{ type: string; title: string; text: string; time: string }>
  }> {
    return apiRequest<{
      activities: Array<{ type: string; title: string; text: string; time: string }>
    }>("/api/admin/recent-activity", { method: "GET" })
  },

  async getAdminSystemHealth(): Promise<AdminSystemHealthResponse> {
    return apiRequest<AdminSystemHealthResponse>("/api/admin/system-health", {
      method: "GET",
    })
  },

  // --- Phase 3: Advanced Scanner, Narrative Detection & Social Intelligence ---
  async getNarratives(): Promise<NarrativeRecord[]> {
    return apiRequest<NarrativeRecord[]>("/api/scanner/narratives", { method: "GET" })
  },

  async getNarrativeDetail(id: string): Promise<any> {
    return apiRequest<any>(`/api/scanner/narratives/${id}`, { method: "GET" })
  },

  async getTrendingProjects(): Promise<TrendingProject[]> {
    return apiRequest<TrendingProject[]>("/api/scanner/trending-projects", { method: "GET" })
  },

  async getMindshare(category?: string, timeframe?: string): Promise<MindshareResult> {
    const q = new URLSearchParams()
    if (category) q.append("category", category)
    if (timeframe) q.append("timeframe", timeframe)
    return apiRequest<MindshareResult>(`/api/scanner/mindshare?${q.toString()}`, { method: "GET" })
  },

  async getScannerSentiment(query: string): Promise<any> {
    return apiRequest<any>(`/api/scanner/sentiment?query=${encodeURIComponent(query)}`, { method: "GET" })
  },

  async getSocialIntel(query: string): Promise<any> {
    return apiRequest<any>(`/api/scanner/social?query=${encodeURIComponent(query)}`, { method: "GET" })
  },

  async getIntelligenceReports(): Promise<IntelligenceReport[]> {
    return apiRequest<IntelligenceReport[]>("/api/scanner/reports", { method: "GET" })
  },

  async generateIntelligenceReport(topic: string, entityType: string = "narrative"): Promise<IntelligenceReport> {
    return apiRequest<IntelligenceReport>("/api/scanner/reports/generate", {
      method: "POST",
      body: JSON.stringify({ topic, entity_type: entityType }),
    })
  },

  async getScannerAlertRules(): Promise<ScannerAlertRule[]> {
    return apiRequest<ScannerAlertRule[]>("/api/scanner/alerts/rules", { method: "GET" })
  },

  async createScannerAlertRule(payload: {
    rule_type: string
    target_entity: string
    threshold: number
    cooldown_minutes?: number
  }): Promise<any> {
    return apiRequest<any>("/api/scanner/alerts/rules", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async deleteScannerAlertRule(ruleId: string): Promise<any> {
    return apiRequest<any>(`/api/scanner/alerts/rules/${ruleId}`, { method: "DELETE" })
  },

  async getScannerAlertEvents(): Promise<ScannerAlertEvent[]> {
    return apiRequest<ScannerAlertEvent[]>("/api/scanner/alerts/events", { method: "GET" })
  },

  async markScannerAlertRead(eventId: string): Promise<any> {
    return apiRequest<any>(`/api/scanner/alerts/events/${eventId}/read`, { method: "POST" })
  },

  // --- Phase 4: Autonomous Agents & Multi-Agent Orchestration ---
  async getAgents(category?: string): Promise<AgentConfig[]> {
    const q = category ? `?category=${encodeURIComponent(category)}` : ""
    return apiRequest<AgentConfig[]>(`/api/agents${q}`, { method: "GET" })
  },

  async createAgent(payload: {
    name: string
    description: string
    category?: string
    capabilities?: string[]
    approved_tools?: string[]
    security_level?: string
    system_prompt?: string
    credit_cost_per_call?: number
  }): Promise<any> {
    return apiRequest<any>("/api/agents", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async orchestrateGoal(goal: string, target_entity?: string): Promise<OrchestrationResult> {
    return apiRequest<OrchestrationResult>("/api/agents/orchestrate", {
      method: "POST",
      body: JSON.stringify({ goal, target_entity: target_entity || goal }),
    })
  },

  async getAgentTasks(limit: number = 25): Promise<AgentTaskRecord[]> {
    return apiRequest<AgentTaskRecord[]>(`/api/agents/tasks?limit=${limit}`, { method: "GET" })
  },

  async getAgentMarketplace(category?: string): Promise<any> {
    const q = category ? `?category=${encodeURIComponent(category)}` : ""
    return apiRequest<any>(`/api/agents/marketplace${q}`, { method: "GET" })
  },

  async getWorkflows(): Promise<WorkflowTemplate[]> {
    return apiRequest<WorkflowTemplate[]>("/api/agents/workflows", { method: "GET" })
  },

  async createWorkflow(payload: {
    name: string
    description: string
    trigger_type?: string
    schedule_cron?: string
    steps: any[]
  }): Promise<any> {
    return apiRequest<any>("/api/agents/workflows", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async runWorkflow(workflowId: string, target_entity: string = "Ethereum"): Promise<any> {
    return apiRequest<any>(`/api/agents/workflows/${workflowId}/run?target_entity=${encodeURIComponent(target_entity)}`, {
      method: "POST",
    })
  },

  async getAgentAnalytics(): Promise<any> {
    return apiRequest<any>("/api/agents/analytics", { method: "GET" })
  },

  async runTradingResearch(contractAddress: string): Promise<{
    contract_address: string
    token_name?: string
    token_symbol?: string
    price_usd?: number | null
    liquidity_usd?: number | null
    top_10_holders_percent?: number | null
    sentiment?: string
    bullets: string[]
    brief_text: string
    disclaimer: string
    credits_remaining?: number | null
    credits_charged?: number
  }> {
    return apiRequest("/api/trading/research", {
      method: "POST",
      body: JSON.stringify({ contract_address: contractAddress }),
    })
  },

  async generateNftArtwork(prompt: string): Promise<{
    prompt: string
    image_url: string
    credits_remaining?: number | null
    credits_charged?: number
  }> {
    return apiRequest("/api/nft/generate", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    })
  },

  async getAgentPersonas(): Promise<{
    id: string
    name: string
    description: string
    system_prompt: string
    welcome_message?: string
  }[]> {
    return apiRequest("/api/agents/personas", { method: "GET" })
  },

  async createAgentPersona(payload: {
    id: string
    name: string
    description: string
    system_prompt: string
  }): Promise<{
    id: string
    name: string
    description: string
    system_prompt: string
    welcome_message?: string
  }> {
    return apiRequest("/api/agents/personas", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async getAdminAgentLedger(limit: number = 25): Promise<{
    id: string
    project_id: string
    user_id: string
    agent_name: string
    tool_name: string
    credit_cost: number
    status: string
    message: string
    created_at: string
  }[]> {
    return apiRequest(`/api/admin/agent-ledger?limit=${limit}`, { method: "GET" })
  },

  async getDeveloperApiKeys(): Promise<{
    id: string
    key_name: string
    key_prefix: string
    is_active: boolean
    created_at: string
  }[]> {
    return apiRequest("/api/developer/keys", { method: "GET" })
  },

  async createDeveloperApiKey(keyName: string): Promise<{
    id: string
    key_name: string
    key_prefix: string
    api_key: string
    is_active: boolean
    created_at: string
  }> {
    return apiRequest("/api/developer/keys", {
      method: "POST",
      body: JSON.stringify({ key_name: keyName }),
    })
  },

  async revokeDeveloperApiKey(id: string): Promise<{ status: string; id: string }> {
    return apiRequest(`/api/developer/keys/${id}`, { method: "DELETE" })
  },

  async getDeveloperApiUsage(): Promise<{
    total_requests: number
    total_credits_used: number
    daily: { date: string; requests: number; credits: number }[]
  }> {
    return apiRequest("/api/developer/usage", { method: "GET" })
  },

  // Platform Integrations (Telegram & Discord)
  async addTelegramIntegration(payload: {
    project_id: string
    bot_token: string
    chat_id?: string
    chat_title?: string
    permissions?: Record<string, boolean>
  }): Promise<any> {
    return apiRequest("/api/integrations/telegram/add", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async listTelegramIntegrations(projectId?: string): Promise<any[]> {
    const q = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""
    return apiRequest(`/api/integrations/telegram/list${q}`, { method: "GET" })
  },

  async disconnectTelegramIntegration(integrationId: string): Promise<{ status: string; id: string }> {
    return apiRequest(`/api/integrations/telegram/${integrationId}/disconnect`, { method: "POST" })
  },

  async startDiscordOAuth(projectId: string): Promise<{ oauth_url: string; state: string }> {
    return apiRequest(`/api/integrations/discord/oauth/start?project_id=${encodeURIComponent(projectId)}`, {
      method: "GET",
    })
  },

  async completeDiscordOAuth(code: string, state: string): Promise<any> {
    return apiRequest(
      `/api/integrations/discord/oauth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
      { method: "GET" }
    )
  },

  async listDiscordIntegrations(projectId?: string): Promise<any[]> {
    const q = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""
    return apiRequest(`/api/integrations/discord/list${q}`, { method: "GET" })
  },

  async disconnectDiscordIntegration(integrationId: string): Promise<{ status: string; id: string }> {
    return apiRequest(`/api/integrations/discord/${integrationId}/disconnect`, { method: "POST" })
  },

  // Unified Billing & Admin Controls
  async getBillingUsage(limit: number = 30): Promise<any[]> {
    return apiRequest(`/api/billing/usage?limit=${limit}`, { method: "GET" })
  },

  async getAdminBillingOverview(): Promise<{
    total_revenue_usdt: number
    active_subscriptions: number
    failed_payments: any[]
    recent_credit_transactions: any[]
  }> {
    return apiRequest("/api/admin/billing/overview", { method: "GET" })
  },

  async adminAdjustCredits(targetUserId: string, amount: number, reason: string): Promise<any> {
    return apiRequest("/api/admin/billing/adjust-credits", {
      method: "POST",
      body: JSON.stringify({ target_user_id: targetUserId, amount, reason }),
    })
  },

  async getSubscriptionPlans(): Promise<any[]> {
    return apiRequest("/api/admin/billing/plans", { method: "GET" })
  },

  // Token Performance Monitoring & Real-Time Dashboard Alerts
  async registerTokenMonitoring(payload: {
    contract_address: string
    project_id?: string
    scan_id?: string
    positive_thresholds?: number[]
    negative_thresholds?: number[]
    drawdown_threshold_pct?: number
  }): Promise<{ status: string; monitored_token: any }> {
    return apiRequest("/api/scanner/monitor", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },

  async getMonitoredTokens(params?: { all_tenants?: boolean; status_filter?: string }): Promise<{ items: any[]; count: number }> {
    const qs = new URLSearchParams()
    if (params?.all_tenants) qs.set("all_tenants", "true")
    if (params?.status_filter) qs.set("status_filter", params.status_filter)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return apiRequest(`/api/scanner/monitored${suffix}`, { method: "GET" })
  },

  async updateMonitoredToken(
    monitoringId: string,
    payload: {
      monitoring_status?: "active" | "paused" | "stopped"
      positive_thresholds?: number[]
      negative_thresholds?: number[]
      drawdown_threshold_pct?: number
    }
  ): Promise<{ status: string; monitored_token: any }> {
    return apiRequest(`/api/scanner/monitored/${monitoringId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },

  async deleteMonitoredToken(monitoringId: string): Promise<{ status: string; monitoring_id: string }> {
    return apiRequest(`/api/scanner/monitored/${monitoringId}`, { method: "DELETE" })
  },

  async checkMonitoredTokensNow(): Promise<{ status: string; new_alerts_count: number; new_alerts: any[] }> {
    return apiRequest("/api/scanner/monitored/check-now", { method: "POST" })
  },

  async getPerformanceAlerts(params?: {
    unread_only?: boolean
    blockchain?: string
    alert_type?: string
    token?: string
    all_tenants?: boolean
    limit?: number
  }): Promise<{ alerts: any[]; unread_count: number }> {
    const qs = new URLSearchParams()
    if (params?.unread_only) qs.set("unread_only", "true")
    if (params?.blockchain) qs.set("blockchain", params.blockchain)
    if (params?.alert_type) qs.set("alert_type", params.alert_type)
    if (params?.token) qs.set("token", params.token)
    if (params?.all_tenants) qs.set("all_tenants", "true")
    if (params?.limit) qs.set("limit", String(params.limit))
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return apiRequest(`/api/scanner/performance-alerts${suffix}`, { method: "GET" })
  },

  async markPerformanceAlertRead(alertId: string): Promise<{ status: string; alert_id: string }> {
    return apiRequest(`/api/scanner/performance-alerts/${alertId}/read`, { method: "POST" })
  },

  async markAllPerformanceAlertsRead(): Promise<{ status: string }> {
    return apiRequest("/api/scanner/performance-alerts/read-all", { method: "POST" })
  },

  async getAdminPerformanceOverview(): Promise<{
    summary: any
    top_milestones: any[]
    recent_alerts: any[]
    monitored_tokens: any[]
    settings: any
    audited_by?: string
  }> {
    return apiRequest("/api/admin/performance-monitoring", { method: "GET" })
  },

  async updateAdminPerformanceSettings(payload: {
    default_positive_thresholds?: number[]
    default_negative_thresholds?: number[]
    max_monitored_free?: number
    max_monitored_pro?: number
    polling_interval_seconds?: number
  }): Promise<{ status: string; settings: any }> {
    return apiRequest("/api/admin/performance-monitoring/settings", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
}
