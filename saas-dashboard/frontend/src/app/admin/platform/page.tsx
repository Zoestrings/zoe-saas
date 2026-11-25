"use client"

import React, { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { Activity, Bot, Cpu, FileText, ShieldCheck, Users } from "lucide-react"
import { api } from "@/lib/api"

export default function AdminPlatformControlPage() {
  const [tab, setTab] = useState<"integrations" | "ai" | "users" | "audit">("integrations")
  const [integrations, setIntegrations] = useState<any[]>([])
  const [intSummary, setIntSummary] = useState<any>({})
  const [users, setUsers] = useState<any[]>([])
  const [auditLogs, setAuditLogs] = useState<any[]>([])
  const [primaryProvider, setPrimaryProvider] = useState("groq")
  const [fallbackProvider, setFallbackProvider] = useState("gemini")
  const [defaultModel, setDefaultModel] = useState("llama-3.3-70b-versatile")
  const [maxTokens, setMaxTokens] = useState(1024)
  const [msg, setMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    try {
      const [intRes, aiRes, usrRes, audRes] = await Promise.all([
        api.getAdminIntegrationsOverview(),
        api.getAdminAIConfig(),
        api.getAdminUsers(),
        api.getAdminAuditLogs(100),
      ])
      setIntegrations(intRes.integrations || [])
      setIntSummary(intRes.summary || {})
      setUsers(usrRes.users || [])
      setAuditLogs(audRes.logs || [])
      if (aiRes) {
        setPrimaryProvider(aiRes.primary_provider || "groq")
        setFallbackProvider(aiRes.fallback_provider || "gemini")
        setDefaultModel(aiRes.default_model || "llama-3.3-70b-versatile")
        setMaxTokens(aiRes.max_tokens || 1024)
      }
    } catch (err: any) {
      setError(err?.message || "Super Admin access required")
    }
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const handleSaveAI = async (e: React.FormEvent) => {
    e.preventDefault()
    setMsg(null)
    await api.updateAdminAIConfig({
      primary_provider: primaryProvider,
      fallback_provider: fallbackProvider,
      default_model: defaultModel,
      max_tokens: Number(maxTokens),
    })
    setMsg("Global AI provider configuration updated and audited.")
    await loadAll()
  }

  const handleRoleChange = async (userId: string, role: "project_owner" | "super_admin" | "suspended") => {
    await api.updateAdminUserRole(userId, role)
    setMsg(`Updated role for ${userId} to ${role} (audited).`)
    await loadAll()
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Super Admin Platform Control Centre</h1>
            <p className="text-xs text-slate-400">
              Global Integration Health (sanitized), AI Infrastructure, Account RBAC &amp; Immutable Audit Logs
            </p>
          </div>
        </div>
        <Link href="/admin/overview" className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs hover:bg-slate-800">
          Back to Admin Overview
        </Link>
      </div>

      {error && <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-200">{error}</div>}
      {msg && <div className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 p-3 text-xs text-cyan-200">{msg}</div>}

      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        <button onClick={() => setTab("integrations")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "integrations" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <Bot className="w-3.5 h-3.5" /> Global Integrations ({intSummary.total_integrations ?? 0})
        </button>
        <button onClick={() => setTab("ai")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "ai" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <Cpu className="w-3.5 h-3.5" /> AI Infrastructure
        </button>
        <button onClick={() => setTab("users")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "users" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <Users className="w-3.5 h-3.5" /> Accounts &amp; Roles ({users.length})
        </button>
        <button onClick={() => setTab("audit")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "audit" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <FileText className="w-3.5 h-3.5" /> Audit Logs ({auditLogs.length})
        </button>
      </div>

      {tab === "integrations" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="text-slate-400">Total Connected</div>
              <div className="text-lg font-bold mt-1">{intSummary.total_integrations ?? 0}</div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="text-slate-400">Telegram Bots</div>
              <div className="text-lg font-bold text-cyan-400 mt-1">{intSummary.telegram_count ?? 0}</div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="text-slate-400">Discord Apps</div>
              <div className="text-lg font-bold text-violet-400 mt-1">{intSummary.discord_count ?? 0}</div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="text-slate-400">Unhealthy</div>
              <div className="text-lg font-bold text-rose-400 mt-1">{intSummary.unhealthy_count ?? 0}</div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 text-slate-400 uppercase">
                <tr>
                  <th className="py-2 pr-3">Platform</th>
                  <th className="py-2 pr-3">Handle / Bot</th>
                  <th className="py-2 pr-3">Owner ID</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2">Last Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {integrations.map((item) => (
                  <tr key={item.id}>
                    <td className="py-2 pr-3 uppercase">{item.platform}</td>
                    <td className="py-2 pr-3 text-white">{item.bot_username || "—"}</td>
                    <td className="py-2 pr-3 font-mono text-[11px]">{item.owner_id}</td>
                    <td className="py-2 pr-3">{item.status}</td>
                    <td className="py-2 text-rose-300">{item.last_error || "None"}</td>
                  </tr>
                ))}
                {integrations.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-slate-400">No integrations recorded yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "ai" && (
        <form onSubmit={handleSaveAI} className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 max-w-xl text-xs">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Activity className="w-4 h-4 text-cyan-400" /> Global AI Provider &amp; Fallback Policy
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1">Primary Provider</label>
              <input value={primaryProvider} onChange={(e) => setPrimaryProvider(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Fallback Provider</label>
              <input value={fallbackProvider} onChange={(e) => setFallbackProvider(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Default Model</label>
              <input value={defaultModel} onChange={(e) => setDefaultModel(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Max Tokens</label>
              <input type="number" min={128} max={8192} value={maxTokens} onChange={(e) => setMaxTokens(Number(e.target.value))} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </div>
          </div>
          <button type="submit" className="rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-black hover:bg-cyan-400">
            Save AI Configuration
          </button>
        </form>
      )}

      {tab === "users" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 text-slate-400 uppercase">
              <tr>
                <th className="py-2 pr-3">Email</th>
                <th className="py-2 pr-3">Role</th>
                <th className="py-2 pr-3">Plan / Credits</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="py-2 pr-3 text-white">{u.email}</td>
                  <td className="py-2 pr-3">{u.role}</td>
                  <td className="py-2 pr-3">{u.plan} ({u.credits} credits)</td>
                  <td className="py-2 text-right space-x-2">
                    <button onClick={() => handleRoleChange(u.id, "project_owner")} className="rounded border border-slate-700 px-2 py-1 hover:bg-slate-800">
                      Set Owner
                    </button>
                    <button onClick={() => handleRoleChange(u.id, "suspended")} className="rounded border border-rose-500/40 px-2 py-1 text-rose-300 hover:bg-rose-500/10">
                      Suspend
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-4 text-slate-400">No local dev users recorded.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "audit" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-2 max-h-96 overflow-y-auto text-xs">
          {auditLogs.map((l) => (
            <div key={l.id} className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 flex flex-wrap justify-between gap-2">
              <div>
                <span className="font-semibold text-cyan-300">{l.action}</span> on{" "}
                <span className="text-white">{l.target_type}</span> ({l.target_id}) by {l.actor_email || l.actor_id}
              </div>
              <div className="text-slate-400">{new Date(l.created_at).toLocaleString()}</div>
            </div>
          ))}
          {auditLogs.length === 0 && <p className="text-slate-400">No audit events logged yet.</p>}
        </div>
      )}
    </div>
  )
}
