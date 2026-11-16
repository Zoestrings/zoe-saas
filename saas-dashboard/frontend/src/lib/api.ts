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
  }
  security?: {
    success: boolean
    mint_revoked?: boolean | null
    freeze_revoked?: boolean | null
    top_10_holders_percent?: number | null
    holder_count?: number | null
    is_honeypot?: boolean
    source?: string
  }
  risk?: {
    level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    reasons: string[]
    risk_score?: number
  }
  timestamp_utc?: string
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
}
