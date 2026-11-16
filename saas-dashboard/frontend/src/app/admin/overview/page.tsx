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
  Activity,
  ArrowUp,
  Sparkles,
  TrendingUp,
  Radio,
  FileCode
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
    { name: "One Love Community Bot", event: "FAISS Ingestion", type: "Knowledge", amount: "+2 Chunks", time: "10m ago" },
    { name: "Hummingbird AI", event: "Capability Isolated", type: "Security", amount: "Refused Ext CA", time: "25m ago" },
    { name: "Zero-Railway Bridge", event: "Health Ping", type: "Engine", amount: "200 OK", time: "42m ago" },
    { name: "Supabase Keepalive", event: "Cron Trigger", type: "Database", amount: "Alive", time: "1h ago" },
    { name: "Zoe Core Engine", event: "Polling Loop Cycle", type: "Runtime", amount: "1.0s Rate", time: "2h ago" },
  ]

  return (
    <div className="space-y-8 pb-12">
      {/* WealthWave 4 Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Vibrant Hero Card (WealthWave Green) */}
        <div className="bg-[#00ff66] text-black rounded-3xl p-6 shadow-xl shadow-[#00ff66]/20 flex flex-col justify-between transition-all hover:scale-[1.01]">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-black flex items-center justify-center text-[#00ff66]">
              <Bot className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-black/10 text-black px-2.5 py-1 rounded-full border border-black/10">
              <ArrowUp className="h-3 w-3" /> 100%
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-semibold text-black/70 uppercase tracking-wider block">
              Active Fleet Bots
            </span>
            <div className="text-3xl font-black text-black tracking-tight mt-1">
              {projects.length > 0 ? projects.length : "2"} Live
            </div>
          </div>
        </div>

        {/* Card 2: Dark Stat Card */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between transition-all hover:border-[#00ff66]/40">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <Activity className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#1a212b] text-[#00ff66] px-2.5 py-1 rounded-full border border-[#212833]">
              <ArrowUp className="h-3 w-3" /> 99.9%
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-medium text-[#818c99] uppercase tracking-wider block">
              Fleet Health
            </span>
            <div className="text-3xl font-bold text-white tracking-tight mt-1">
              Optimal
            </div>
          </div>
        </div>

        {/* Card 3: Dark Stat Card */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between transition-all hover:border-amber-400/40">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Layers className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#1a212b] text-amber-400 px-2.5 py-1 rounded-full border border-[#212833]">
              <ArrowUp className="h-3 w-3" /> FAISS
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-medium text-[#818c99] uppercase tracking-wider block">
              Vector Brain Memory
            </span>
            <div className="text-3xl font-bold text-white tracking-tight mt-1">
              7 Chunks
            </div>
          </div>
        </div>

        {/* Card 4: Dark Stat Card */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between transition-all hover:border-cyan-400/40">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#1a212b] text-cyan-400 px-2.5 py-1 rounded-full border border-[#212833]">
              <ArrowUp className="h-3 w-3" /> AES-256
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-medium text-[#818c99] uppercase tracking-wider block">
              Security Cipher
            </span>
            <div className="text-3xl font-bold text-white tracking-tight mt-1">
              Encrypted
            </div>
          </div>
        </div>
      </div>

      {/* WealthWave Visual Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Donut Distribution Card */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between pb-4 border-b border-[#212833]">
            <div>
              <h3 className="font-bold text-white text-sm">Agent Allocation</h3>
              <p className="text-[11px] text-[#818c99] mt-0.5">Fleet distribution ratio</p>
            </div>
            <span className="h-2.5 w-2.5 rounded-full bg-[#00ff66] animate-pulse" />
          </div>

          {/* Donut Chart Visual */}
          <div className="py-6 flex items-center justify-center">
            <div className="relative flex items-center justify-center">
              <svg className="w-40 h-40 transform -rotate-90">
                <circle
                  cx="80"
                  cy="80"
                  r="62"
                  stroke="#1c242d"
                  strokeWidth="16"
                  fill="transparent"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="62"
                  stroke="#00ff66"
                  strokeWidth="16"
                  strokeDasharray="390"
                  strokeDashoffset="120"
                  strokeLinecap="round"
                  fill="transparent"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="62"
                  stroke="#f59e0b"
                  strokeWidth="16"
                  strokeDasharray="390"
                  strokeDashoffset="310"
                  strokeLinecap="round"
                  fill="transparent"
                />
              </svg>
              <div className="absolute text-center">
                <span className="text-2xl font-black text-white block tracking-tight">100%</span>
                <span className="text-[10px] text-[#818c99] uppercase font-bold tracking-wider">Fleet Active</span>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="pt-4 border-t border-[#212833] space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-[#00ff66]" />
                <span className="text-white font-medium">One Love AI</span>
              </div>
              <span className="text-[#818c99] font-mono">71%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                <span className="text-white font-medium">Hummingbird AI</span>
              </div>
              <span className="text-[#818c99] font-mono">29%</span>
            </div>
          </div>
        </div>

        {/* Right: Inference Traffic Wavy Curve Chart */}
        <div className="lg:col-span-2 bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between pb-4 border-b border-[#212833]">
            <div>
              <h3 className="font-bold text-white text-sm">Engine Traffic & Polling Activity</h3>
              <p className="text-[11px] text-[#818c99] mt-0.5">Real-time Telegram webhook & polling loop</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 text-xs text-[#00ff66] font-medium">
                <span className="h-2 w-2 rounded-full bg-[#00ff66]" />
                Inference
              </span>
              <span className="inline-flex items-center gap-1.5 text-xs text-amber-400 font-medium">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                Polling
              </span>
            </div>
          </div>

          {/* Wavy Graph SVG Visual */}
          <div className="py-6 relative">
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-[#1b222b] border border-[#00ff66]/40 text-[#00ff66] px-3 py-1 rounded-full text-xs font-bold shadow-xl shadow-[#00ff66]/10 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-[#00ff66] animate-pulse" />
              1.0s Loop Cycle
            </div>

            <svg viewBox="0 0 600 200" className="w-full h-44 overflow-visible">
              <defs>
                <linearGradient id="neonGlow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00ff66" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#00ff66" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="0" y1="50" x2="600" y2="50" stroke="#1f2530" strokeDasharray="4 4" />
              <line x1="0" y1="100" x2="600" y2="100" stroke="#1f2530" strokeDasharray="4 4" />
              <line x1="0" y1="150" x2="600" y2="150" stroke="#1f2530" strokeDasharray="4 4" />

              {/* Area fill */}
              <path
                d="M0,160 Q100,140 200,90 T400,60 T600,110 L600,200 L0,200 Z"
                fill="url(#neonGlow)"
              />

              {/* Amber Curve */}
              <path
                d="M0,170 Q100,160 200,140 T400,120 T600,150"
                fill="none"
                stroke="#f59e0b"
                strokeWidth="3"
                strokeLinecap="round"
              />

              {/* Green Curve */}
              <path
                d="M0,160 Q100,140 200,90 T400,60 T600,110"
                fill="none"
                stroke="#00ff66"
                strokeWidth="3.5"
                strokeLinecap="round"
              />

              {/* Target dot marker */}
              <circle cx="360" cy="62" r="6" fill="#00ff66" />
              <circle cx="360" cy="62" r="12" fill="#00ff66" opacity="0.3" />
            </svg>
          </div>

          <div className="pt-3 border-t border-[#212833] flex items-center justify-between text-xs text-[#818c99]">
            <span>Latency: <strong className="text-white">142ms avg</strong></span>
            <span>Uptime: <strong className="text-[#00ff66]">100%</strong></span>
            <span>Engine: <strong className="text-white">FastAPI + AsyncIO</strong></span>
          </div>
        </div>
      </div>

      {/* WealthWave Recent Activities Table & Deployed Bots */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2 cols): Recent Activities Table */}
        <div className="lg:col-span-2 bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#212833]">
            <h3 className="font-bold text-white text-base">Recent Activities</h3>
            <Link href="/admin/projects" className="text-xs text-[#00ff66] hover:underline font-bold flex items-center gap-1">
              See more <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-[#212833]">
            {recentActivity.map((act, i) => (
              <div key={i} className="py-3.5 flex items-center justify-between text-xs hover:bg-[#181d24]/50 rounded-xl px-2 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-[#181d24] border border-[#212833] flex items-center justify-center text-[#00ff66]">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="font-semibold text-white block">{act.name}</span>
                    <span className="text-[11px] text-[#818c99]">{act.event}</span>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <span className="bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 px-3 py-0.5 rounded-full text-[11px] font-bold">
                    {act.type}
                  </span>
                  <span className="font-mono text-white text-xs">{act.amount}</span>
                  <span className="text-[#818c99] text-[11px] w-16 text-right">{act.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right (1 col): Deployed Bots Card */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#212833]">
              <h3 className="font-bold text-white text-base">Deployed Agents</h3>
              <span className="text-xs text-[#00ff66] font-bold">2 Active</span>
            </div>

            <div className="space-y-4 pt-3">
              {defaultProjects.map((bot) => (
                <div key={bot.id} className="p-4 rounded-2xl bg-[#161b22] border border-[#212833] space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="h-8 w-8 rounded-full bg-[#00ff66] text-black flex items-center justify-center font-bold text-xs">
                        {bot.name[0]}
                      </div>
                      <div>
                        <span className="font-bold text-white text-xs block">{bot.name}</span>
                        <span className="text-[10px] text-[#818c99]">{bot.botUsername}</span>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-[#00ff66] font-bold">
                      {bot.tokenSymbol}
                    </span>
                  </div>

                  {/* Contract snippet */}
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#0e1116] border border-[#212833] text-[11px] font-mono text-[#818c99]">
                    <span className="truncate max-w-[170px]">{bot.ca}</span>
                    <button
                      onClick={() => copyToClipboard(bot.ca)}
                      className="text-[#818c99] hover:text-[#00ff66] transition-colors cursor-pointer"
                    >
                      {copiedCA === bot.ca ? <Check className="h-3 w-3 text-[#00ff66]" /> : <Copy className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Link href="/admin/projects" className="w-full">
            <Button className="w-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer">
              <Plus className="h-3.5 w-3.5 mr-1.5 stroke-[3]" />
              Deploy New Agent
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
