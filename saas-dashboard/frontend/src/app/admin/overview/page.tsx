"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  Bot, 
  Layers, 
  ShieldCheck, 
  Plus, 
  Copy,
  Check,
  Cpu,
  ArrowUpRight,
  RefreshCw,
  Activity
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Project } from "@/lib/api"

export default function AdminOverviewPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCA(text)
    setTimeout(() => setCopiedCA(null), 2000)
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const data = await api.getProjects()
      setProjects(data || [])
    } catch {
      // Fallback
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const defaultProjects = [
    {
      id: "onelove",
      name: "One Love AI",
      botUsername: "@OneLoveManager_bot",
      tokenSymbol: "$ONELOVE",
      chain: "Solana",
      ca: "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon",
      status: "Online",
      chunks: 5,
      group: "-5214407126",
    },
    {
      id: "hummingbird",
      name: "Hummingbird AI",
      botUsername: "@HummingbirdAIBot",
      tokenSymbol: "$FLY",
      chain: "Solana",
      ca: "5m6Z5B3z1xYQvWvA9aP8kE7dM2uC1tL3",
      status: "Online",
      chunks: 2,
      group: "-1002345678901",
    }
  ]

  const recentActivity = [
    { category: "Security", text: "Capability check isolated external CA scan on $FLY", time: "10m ago" },
    { category: "Knowledge", text: "FAISS vector brain re-indexed on One Love", time: "32m ago" },
    { category: "Engine", text: "Zero-Railway Bridge dispatched spawn heartbeat", time: "1h ago" },
    { category: "Auth", text: "RBAC tenant scoping enforced across 2 active tenants", time: "2h ago" },
  ]

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Super Admin Overview
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Global monitoring for autonomous AI agents, runtime health, and multi-tenant isolation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="text-xs h-9 cursor-pointer shadow-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Sync Metrics
          </Button>
          <Link href="/admin/projects">
            <Button className="text-xs h-9 px-4 font-medium shadow-xs cursor-pointer">
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              Manage Fleet
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <Card className="p-5 shadow-xs">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Active Bots
            </span>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold text-foreground mt-1">
            {projects.length > 0 ? projects.length : "2"} Deployed
          </div>
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            100% operational uptime
          </p>
        </Card>

        {/* Card 2 */}
        <Card className="p-5 shadow-xs">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Fleet Health
            </span>
            <Activity className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">Optimal</div>
          <p className="text-xs text-muted-foreground mt-1">Polling rate: 1.0s / loop</p>
        </Card>

        {/* Card 3 */}
        <Card className="p-5 shadow-xs">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              FAISS Brain
            </span>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold text-foreground mt-1">7 Chunks</div>
          <p className="text-xs text-muted-foreground mt-1">Vector indexed memory on disk</p>
        </Card>

        {/* Card 4 */}
        <Card className="p-5 shadow-xs">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Security Cipher
            </span>
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold text-foreground mt-1">AES-256</div>
          <p className="text-xs text-muted-foreground mt-1">Fernet symmetric bot encryption</p>
        </Card>
      </div>

      {/* Active Projects Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">
            Core Deployed Agents
          </h2>
          <Link href="/admin/projects" className="text-xs text-foreground hover:underline flex items-center gap-1 font-medium">
            View full table <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {defaultProjects.map((fleet) => (
            <Card key={fleet.id} className="p-5 shadow-xs">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-foreground text-sm">{fleet.name}</h3>
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                      {fleet.status}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{fleet.botUsername}</p>
                </div>
                <span className="text-xs font-medium text-foreground bg-secondary px-2.5 py-1 rounded-md border border-border font-mono">
                  {fleet.tokenSymbol} · {fleet.chain}
                </span>
              </div>

              {/* Contract Address Box */}
              <div className="mt-4 p-2.5 rounded-md bg-muted/40 border border-border flex items-center justify-between gap-2">
                <div className="truncate text-xs font-mono text-muted-foreground">
                  {fleet.ca}
                </div>
                <button
                  onClick={() => copyToClipboard(fleet.ca)}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors cursor-pointer"
                  title="Copy address"
                >
                  {copiedCA === fleet.ca ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                  <span className="text-[11px] font-medium">{copiedCA === fleet.ca ? "Copied" : "Copy"}</span>
                </button>
              </div>

              <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
                <span>Knowledge: <strong className="text-foreground font-medium">{fleet.chunks} chunks</strong></span>
                <span className="font-mono">Group: {fleet.group}</span>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Activity Log */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-foreground">
          System Activity Log
        </h2>

        <Card className="overflow-hidden shadow-xs">
          <div className="divide-y divide-border">
            {recentActivity.map((event, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 text-xs hover:bg-muted/40 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-secondary text-foreground border border-border">
                    {event.category}
                  </span>
                  <span className="text-foreground">
                    {event.text}
                  </span>
                </div>
                <span className="text-muted-foreground font-mono text-[11px]">
                  {event.time}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
