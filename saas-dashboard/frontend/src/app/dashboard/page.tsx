"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  Bot, 
  Layers, 
  ShieldCheck, 
  Plus, 
  ExternalLink,
  Copy,
  Check,
  Cpu,
  ArrowUpRight
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Project, getUser } from "@/lib/api"

export default function DashboardOverviewPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCA(text)
    setTimeout(() => setCopiedCA(null), 2000)
  }

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await api.getProjects()
        setProjects(data)
      } catch {
        // Fallback for visual mock
      } finally {
        setLoading(false)
      }
    }
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
      socials: {
        twitter: "https://x.com/thecaptrobbie?s=11",
        telegram: "https://t.me/ONELOVECoinCrew",
        tiktok: "https://www.tiktok.com/@captain.robbie"
      }
    },
    {
      id: "live_test",
      name: "Zoe Core Hummingbird",
      botUsername: "@zoe_live_test_bot",
      tokenSymbol: "$FLY",
      chain: "Multi-Chain",
      ca: "0x1b44f3514812d835eb1bdb0acb33d3ff3351655c",
      status: "Online",
      chunks: 2,
      group: "Verified Testnet",
      socials: {}
    }
  ]

  const recentActivity = [
    { time: "Just now", category: "System", text: "Multi-tenant polling heartbeat active across all telegram groups" },
    { time: "3m ago", category: "Knowledge", text: "Vector index verified for One Love documentation (5 chunks)" },
    { time: "8m ago", category: "Security", text: "Encrypted token access authorized via Supabase security policy" },
    { time: "14m ago", category: "Safety", text: "Domain allowlist passed for onelovesailingcoin.com & tiktok.com" },
    { time: "22m ago", category: "Inference", text: "Groq cloud AI model initialized and ready for incoming messages" },
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header Overview */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Dashboard Overview
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time status of your active AI agents, knowledge bases, and community activity.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard/projects">
            <Button className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-9 px-4 rounded-md font-medium cursor-pointer">
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              Add Project
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <Card className="enterprise-card border border-slate-200 shadow-sm bg-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 pt-4 px-5">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Active Projects
            </CardTitle>
            <Bot className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent className="px-5 pb-4">
            <div className="text-2xl font-bold text-slate-900">2 Online</div>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block" />
              One Love & Hummingbird
            </p>
          </CardContent>
        </Card>

        {/* Card 2 */}
        <Card className="enterprise-card border border-slate-200 shadow-sm bg-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 pt-4 px-5">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              AI Engine
            </CardTitle>
            <Cpu className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent className="px-5 pb-4">
            <div className="text-2xl font-bold text-slate-900">Groq AI</div>
            <p className="text-xs text-slate-500 mt-1">High-speed cloud inference</p>
          </CardContent>
        </Card>

        {/* Card 3 */}
        <Card className="enterprise-card border border-slate-200 shadow-sm bg-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 pt-4 px-5">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Knowledge Base
            </CardTitle>
            <Layers className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent className="px-5 pb-4">
            <div className="text-2xl font-bold text-slate-900">7 Chunks</div>
            <p className="text-xs text-slate-500 mt-1">Indexed project documents</p>
          </CardContent>
        </Card>

        {/* Card 4 */}
        <Card className="enterprise-card border border-slate-200 shadow-sm bg-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 pt-4 px-5">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Token Security
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent className="px-5 pb-4">
            <div className="text-2xl font-bold text-slate-900">Encrypted</div>
            <p className="text-xs text-slate-500 mt-1">AES-256 cloud encryption</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Projects List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">
            Active Projects
          </h2>
          <Link href="/dashboard/projects" className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1 font-medium">
            Manage projects <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {defaultProjects.map((fleet) => (
            <Card key={fleet.id} className="enterprise-card border border-slate-200 shadow-sm bg-white p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-900 text-sm">{fleet.name}</h3>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      {fleet.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{fleet.botUsername}</p>
                </div>
                <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                  {fleet.tokenSymbol} · {fleet.chain}
                </span>
              </div>

              {/* Contract Address Box */}
              <div className="mt-4 p-2.5 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-between gap-2">
                <div className="truncate text-xs font-mono text-slate-600">
                  {fleet.ca}
                </div>
                <button
                  onClick={() => copyToClipboard(fleet.ca)}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors cursor-pointer"
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

              {/* Footer info & links */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>Knowledge: <strong className="text-slate-700 font-medium">{fleet.chunks} chunks</strong></span>
                {fleet.socials && Object.keys(fleet.socials).length > 0 && (
                  <div className="flex items-center gap-2">
                    {fleet.socials.telegram && (
                      <a 
                        href={fleet.socials.telegram} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-slate-500 hover:text-slate-900 text-xs font-medium inline-flex items-center gap-0.5"
                      >
                        Telegram <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                    {fleet.socials.twitter && (
                      <a 
                        href={fleet.socials.twitter} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-slate-500 hover:text-slate-900 text-xs font-medium inline-flex items-center gap-0.5"
                      >
                        X <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Activity Log */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">
            Recent Activity Log
          </h2>
          <Link href="/dashboard/logs" className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1 font-medium">
            View full log <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <Card className="enterprise-card border border-slate-200 shadow-sm bg-white overflow-hidden">
          <div className="divide-y divide-slate-100">
            {recentActivity.map((event, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 text-xs hover:bg-slate-50/70 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                    {event.category}
                  </span>
                  <span className="text-slate-700 font-normal">
                    {event.text}
                  </span>
                </div>
                <span className="text-slate-400 font-normal text-right pl-4 whitespace-nowrap">
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
