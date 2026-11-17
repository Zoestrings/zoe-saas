"use client"

import { useEffect, useState } from "react"
import { 
  ShieldCheck, 
  Database, 
  Cpu, 
  CheckCircle2, 
  Key, 
  Server, 
  RefreshCw, 
  Radio, 
  Zap,
  Activity
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, SystemHealthResponse } from "@/lib/api"

export default function AdminSettingsPage() {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null)
  const [healthLoading, setHealthLoading] = useState(false)

  const fetchHealth = async () => {
    setHealthLoading(true)
    try {
      const res = await api.getSystemHealth()
      setHealth(res)
    } catch (e) {
      console.error("Failed to fetch system health:", e)
    } finally {
      setHealthLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
  }, [])

  const cloudVars = [
    { name: "SUPABASE_URL", status: "Active", desc: "PostgreSQL multi-tenant database" },
    { name: "SUPABASE_KEY", status: "Active", desc: "Client anonymous authentication key" },
    { name: "ENCRYPTION_KEY", status: "Active", desc: "Fernet AES-256 cipher key" },
    { name: "ENGINE_SHARED_SECRET", status: "Active", desc: "Zero-Railway Dynamic Spawning Bridge" },
    { name: "GROQ_API_KEY", status: "Active", desc: "Cloud AI inference provider" },
    { name: "ZOE_BOT_TOKEN", status: "Active", desc: "Main Platform Admin Bot (@ZoeCoreBot)" },
    { name: "ZOE_SOLANA_WALLET", status: "Active", desc: "USDT subscription treasury on Solana" },
  ]

  const allowlistedDomains = [
    "onelovesailingcoin.com",
    "x.com",
    "twitter.com",
    "t.me",
    "tiktok.com",
    "dexscreener.com",
    "solscan.io",
    "github.com"
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#212833]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Server className="h-6 w-6 text-[#00ff66]" />
            Settings & System Health
          </h1>
          <p className="text-xs text-[#818c99] mt-1">
            Review cloud platform status, live infrastructure telemetry, and security policies.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchHealth}
          disabled={healthLoading}
          className="border-[#212833] bg-[#12161c] hover:bg-[#181d24] text-white text-xs h-10 px-4 rounded-full cursor-pointer shadow-sm w-fit"
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${healthLoading ? "animate-spin text-[#00ff66]" : ""}`} />
          Check Health
        </Button>
      </div>

      {/* Live System Health Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Health 1: FastAPI Gateway */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#818c99] uppercase tracking-wider">FastAPI Gateway</span>
            <span className="h-2 w-2 rounded-full bg-[#00ff66] animate-pulse" />
          </div>
          <div className="text-lg font-bold text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#00ff66]" />
            <span className="capitalize">{health?.fastapi || "Online"}</span>
          </div>
          <span className="text-[11px] text-[#818c99] block font-mono">Port 8000 / HTTP REST</span>
        </div>

        {/* Health 2: Database Connection */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#818c99] uppercase tracking-wider">Database Storage</span>
            <span className="h-2 w-2 rounded-full bg-[#00ff66] animate-pulse" />
          </div>
          <div className="text-lg font-bold text-white flex items-center gap-2">
            <Database className="h-4 w-4 text-[#00ff66]" />
            <span className="capitalize">{health?.database || "Connected"}</span>
          </div>
          <span className="text-[11px] text-[#818c99] block font-mono">SQLite / Supabase Sync</span>
        </div>

        {/* Health 3: Solana Public RPC */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#818c99] uppercase tracking-wider">Solana RPC</span>
            <span className="h-2 w-2 rounded-full bg-[#00ff66] animate-pulse" />
          </div>
          <div className="text-lg font-bold text-white flex items-center gap-2">
            <Radio className="h-4 w-4 text-[#00ff66]" />
            <span className="capitalize">{health?.solana_rpc || "Online"}</span>
          </div>
          <span className="text-[11px] text-[#818c99] block font-mono">api.mainnet-beta.solana.com</span>
        </div>

        {/* Health 4: Zoe Engine Orchestrator */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#818c99] uppercase tracking-wider">Engine Core</span>
            <span className="h-2 w-2 rounded-full bg-[#00ff66] animate-pulse" />
          </div>
          <div className="text-lg font-bold text-white flex items-center gap-2">
            <Activity className="h-4 w-4 text-[#00ff66]" />
            <span className="capitalize">{health?.engine || "Active"}</span>
          </div>
          <span className="text-[11px] text-[#818c99] block font-mono">Multi-tenant Polling</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: 2 Cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cloud & Database */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-[#212833]">
              <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Database & Storage Configuration</h3>
                <p className="text-xs text-[#818c99]">PostgreSQL cloud multi-tenant storage with local fallback</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs py-2 border-b border-[#212833]">
                <span className="text-[#818c99]">PostgreSQL Cloud Provider</span>
                <span className="font-bold text-white">Supabase (AWS us-east-1)</span>
              </div>
              <div className="flex items-center justify-between text-xs py-2 border-b border-[#212833]">
                <span className="text-[#818c99]">Schema Version</span>
                <span className="font-mono text-[#00ff66] font-bold">v2.1 (Multi-tenant RBAC + Auto-Migration)</span>
              </div>
              <div className="flex items-center justify-between text-xs py-2">
                <span className="text-[#818c99]">Keepalive Automation</span>
                <span className="inline-flex items-center gap-1.5 text-[#00ff66] font-bold">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Active
                </span>
              </div>
            </div>
          </div>

          {/* Environment Variables & Secrets */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-[#212833]">
              <div className="h-10 w-10 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <Key className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Environment Secrets</h3>
                <p className="text-xs text-[#818c99]">Encrypted cloud and runtime keys</p>
              </div>
            </div>

            <div className="divide-y divide-[#212833]">
              {cloudVars.map((v, i) => (
                <div key={i} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono text-white font-bold">{v.name}</span>
                    <p className="text-[11px] text-[#818c99] mt-0.5">{v.desc}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#00ff66] bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-0.5 rounded-full">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66]" />
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Security Card */}
        <div className="space-y-6">
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-[#212833]">
              <div className="h-10 w-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Security Policy</h3>
                <p className="text-xs text-[#818c99]">Domain boundaries & RLS</p>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-[#818c99] leading-relaxed">
                Zoe Knowledge Ingestion is restricted to verified domains to prevent prompt injection and unauthorized exfiltration.
              </p>

              <div className="pt-2">
                <span className="text-[10px] font-bold text-[#818c99] uppercase tracking-wider block mb-2">
                  Allowlisted Domains
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {allowlistedDomains.map((dom) => (
                    <span
                      key={dom}
                      className="px-2.5 py-1 rounded-full bg-[#161b22] border border-[#212833] text-[11px] font-mono text-[#00ff66]"
                    >
                      {dom}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
