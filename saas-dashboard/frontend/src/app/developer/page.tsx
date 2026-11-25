"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  Code2,
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  AlertTriangle,
  BookOpen,
  Activity,
  Loader2,
  Sparkles,
} from "lucide-react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

interface ApiKeyItem {
  id: string
  key_name: string
  key_prefix: string
  is_active: boolean
  created_at: string
}

export default function DeveloperPortalPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([])
  const [loading, setLoading] = useState(true)
  const [newKeyName, setNewKeyName] = useState("")
  const [creating, setCreating] = useState(false)
  const [revealedKey, setRevealedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [usage, setUsage] = useState<{
    total_requests: number
    total_credits_used: number
    daily: { date: string; requests: number; credits: number }[]
  }>({ total_requests: 0, total_credits_used: 0, daily: [] })

  const loadPortalData = async () => {
    setLoading(true)
    try {
      const [keysRes, usageRes] = await Promise.allSettled([
        api.getDeveloperApiKeys(),
        api.getDeveloperApiUsage(),
      ])
      if (keysRes.status === "fulfilled" && Array.isArray(keysRes.value)) {
        setKeys(keysRes.value)
      }
      if (usageRes.status === "fulfilled" && usageRes.value) {
        setUsage(usageRes.value)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPortalData()
  }, [])

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    setCreating(true)
    try {
      const res = await api.createDeveloperApiKey(newKeyName.trim())
      setRevealedKey(res.api_key)
      setNewKeyName("")
      await loadPortalData()
    } catch (err: any) {
      alert(err?.message || "Failed to generate API key.")
    } finally {
      setCreating(false)
    }
  }

  const handleRevokeKey = async (id: string) => {
    try {
      await api.revokeDeveloperApiKey(id)
      await loadPortalData()
    } catch (err: any) {
      alert(err?.message || "Failed to revoke API key.")
    }
  }

  const handleCopyKey = () => {
    if (!revealedKey) return
    navigator.clipboard.writeText(revealedKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-8 pb-16 max-w-6xl mx-auto">
      {/* Header */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#121212] border border-[#00ff66]/30 shadow-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="h-12 w-12 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shrink-0">
            <Code2 className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
                Zoe Developer API Portal
              </h1>
              <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#00ff66]/15 text-[#00ff66] border border-[#00ff66]/30">
                v1 REST API
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-0.5">
              Build Web3 applications powered by Zoe Intelligence (/api/v1/chat, /scan, /audit).
            </p>
          </div>
        </div>

        <Link href="/developer/docs">
          <Button
            variant="outline"
            size="sm"
            className="border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 px-4 rounded-full cursor-pointer"
          >
            <BookOpen className="h-3.5 w-3.5 mr-1.5 text-[#00ff66]" />
            API Documentation
          </Button>
        </Link>
      </div>

      {/* One-Time Plaintext Key Reveal Alert */}
      {revealedKey && (
        <div className="p-5 rounded-3xl bg-[#00ff66]/10 border border-[#00ff66]/40 space-y-3 shadow-xl">
          <div className="flex items-center gap-2 text-amber-300 text-xs font-bold">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>Copy this key now. You won&apos;t see it again.</span>
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 p-3 rounded-xl bg-black/70 border border-neutral-800 text-[#00ff66] font-mono text-xs break-all">
              {revealedKey}
            </code>
            <Button
              type="button"
              onClick={handleCopyKey}
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-4 rounded-xl cursor-pointer shrink-0"
            >
              {copied ? <Check className="h-4 w-4 mr-1" /> : <Copy className="h-4 w-4 mr-1" />}
              {copied ? "Copied" : "Copy Key"}
            </Button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Key Management */}
        <Card className="lg:col-span-6 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <Key className="h-4 w-4 text-[#00ff66]" />
              <span>API Keys</span>
            </CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Authenticate requests with <code className="text-neutral-200">Authorization: Bearer zoe_sk_...</code>
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <form onSubmit={handleCreateKey} className="flex gap-2">
              <Input
                placeholder="Key name (e.g. Trading Bot Prod)"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="bg-neutral-950 border-neutral-800 focus:border-[#00ff66] text-white text-xs h-10 rounded-xl"
              />
              <Button
                type="submit"
                disabled={creating || !newKeyName.trim()}
                className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-4 rounded-xl cursor-pointer shrink-0"
              >
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4 mr-1" />}
                Generate Key
              </Button>
            </form>

            {loading ? (
              <div className="py-8 flex items-center justify-center text-neutral-400 text-xs gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-[#00ff66]" />
                <span>Loading API keys...</span>
              </div>
            ) : keys.length === 0 ? (
              <div className="p-6 rounded-2xl border border-dashed border-neutral-800 text-center text-xs text-neutral-500">
                No active API keys yet. Create one above to start calling Zoe v1 endpoints.
              </div>
            ) : (
              <div className="space-y-2.5">
                {keys.map((k) => (
                  <div
                    key={k.id}
                    className="p-3.5 rounded-2xl bg-neutral-950/70 border border-neutral-800 flex items-center justify-between gap-3"
                  >
                    <div>
                      <p className="text-xs font-bold text-white">{k.key_name}</p>
                      <p className="text-[11px] font-mono text-neutral-400 mt-0.5">
                        {k.key_prefix} · Created {k.created_at.slice(0, 10)}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevokeKey(k.id)}
                      className="border-rose-900/50 bg-rose-950/20 hover:bg-rose-950/50 text-rose-400 text-xs h-8 px-3 rounded-xl cursor-pointer"
                    >
                      <Trash2 className="h-3.5 w-3.5 mr-1" />
                      Revoke
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: Recharts Usage Dashboard */}
        <Card className="lg:col-span-6 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#00ff66]" />
              <span>API Usage Telemetry</span>
            </CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Daily API requests and credit consumption across your developer keys.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-2xl bg-neutral-950/70 border border-neutral-800">
                <span className="text-[11px] text-neutral-400 block">Total API Requests</span>
                <span className="text-lg font-extrabold text-white font-mono mt-0.5 block">
                  {usage.total_requests.toLocaleString()}
                </span>
              </div>
              <div className="p-3.5 rounded-2xl bg-neutral-950/70 border border-neutral-800">
                <span className="text-[11px] text-neutral-400 block">Credits Consumed</span>
                <span className="text-lg font-extrabold text-[#00ff66] font-mono mt-0.5 block">
                  {usage.total_credits_used.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="h-56 w-full rounded-2xl bg-neutral-950/60 border border-neutral-800 p-3">
              {usage.daily.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={usage.daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                    <XAxis dataKey="date" stroke="#737373" fontSize={11} />
                    <YAxis stroke="#737373" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#121212",
                        borderColor: "#262626",
                        borderRadius: "12px",
                        fontSize: "12px",
                        color: "#ffffff",
                      }}
                    />
                    <Bar dataKey="requests" name="Requests" fill="#00ff66" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center text-xs text-neutral-500 gap-2">
                  <Sparkles className="h-5 w-5 text-neutral-600" />
                  <span>Make a request to /api/v1/chat, /scan, or /audit to populate daily usage charts.</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
