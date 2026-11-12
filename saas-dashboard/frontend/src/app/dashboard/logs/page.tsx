"use client"

import { useState } from "react"
import { 
  MessageSquareCode, 
  ShieldCheck, 
  Search, 
  Filter, 
  Activity, 
  Terminal, 
  Play, 
  Pause, 
  RefreshCw,
  CheckCircle2,
  Clock,
  Zap,
  Radio,
  FileText
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface LogItem {
  id: string
  timestamp: string
  project: string
  intent: string
  category: "rag" | "price" | "safety" | "system"
  message: string
  latency: string
  status: "success" | "guard" | "verified" | "neutral"
}

export default function DashboardLogsPage() {
  const [filter, setFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [isStreaming, setIsStreaming] = useState<boolean>(true)

  const logs: LogItem[] = [
    {
      id: "log-1",
      timestamp: "2026-11-12 11:46:54",
      project: "onelove",
      intent: "command_links",
      category: "rag",
      message: "Incoming /links command: generated inline buttons for Twitter, Telegram, TikTok & Website.",
      latency: "14ms",
      status: "verified"
    },
    {
      id: "log-2",
      timestamp: "2026-11-12 11:46:53",
      project: "onelove",
      intent: "knowledge",
      category: "rag",
      message: "Query: 'Who is the founder of One Love?' -> FAISS vector recall hit: 'Captain Robert Olson (Robbie Olson)'.",
      latency: "182ms",
      status: "success"
    },
    {
      id: "log-3",
      timestamp: "2026-11-12 11:46:52",
      project: "onelove",
      intent: "auto_ingest",
      category: "system",
      message: "Auto-Ingestion complete: Rebuilt FAISS index at data/indexes/onelove/index.faiss (5 chunks indexed).",
      latency: "840ms",
      status: "success"
    },
    {
      id: "log-4",
      timestamp: "2026-11-12 11:46:50",
      project: "live_test",
      intent: "auto_ingest",
      category: "system",
      message: "Auto-Ingestion complete: data/knowledge/hummingbird_info.txt indexed (2 chunks).",
      latency: "410ms",
      status: "success"
    },
    {
      id: "log-5",
      timestamp: "2026-11-12 11:46:46",
      project: "system",
      intent: "bootstrap",
      category: "system",
      message: "SQLite database bootstrap: operational.db, official_knowledge.db, and community_memory.db schemas verified.",
      latency: "25ms",
      status: "success"
    },
    {
      id: "log-6",
      timestamp: "2026-11-12 11:46:40",
      project: "onelove",
      intent: "command_price",
      category: "price",
      message: "CA scanner query for F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon -> DexScreener Raydium pool synced.",
      latency: "195ms",
      status: "verified"
    },
    {
      id: "log-7",
      timestamp: "2026-11-12 11:46:35",
      project: "onelove",
      intent: "safety_check",
      category: "safety",
      message: "Safety filter evaluated: Whitelisted domains verified (onelovesailingcoin.com, tiktok.com, x.com, t.me). Zero prompt injections detected.",
      latency: "8ms",
      status: "verified"
    },
    {
      id: "log-8",
      timestamp: "2026-11-12 11:46:20",
      project: "onelove",
      intent: "accuracy_guard",
      category: "rag",
      message: "Forced Web Search OFF for Project Facts: Unindexed query intercepted by Fail-Closed Accuracy Guard.",
      latency: "15ms",
      status: "guard"
    }
  ]

  const filteredLogs = logs.filter((item) => {
    if (filter !== "all" && item.category !== filter) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return (
        item.message.toLowerCase().includes(q) ||
        item.project.toLowerCase().includes(q) ||
        item.intent.toLowerCase().includes(q)
      )
    }
    return true
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
              <Terminal className="h-7 w-7 text-cyan-400" />
              Live Telemetry & Conversation Logs
            </h1>
            <Badge className="bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 text-[10px] font-mono">
              Real-Time WebSocket
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time audit stream of Telegram updates, FAISS vector retrievals, CA scans, and fail-closed safety validations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsStreaming(!isStreaming)}
            className="border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-slate-300 text-xs gap-1.5 cursor-pointer"
          >
            {isStreaming ? (
              <>
                <Pause className="h-3.5 w-3.5 text-amber-400" />
                <span>Pause Stream</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 text-emerald-400" />
                <span>Resume Stream</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#090d16] p-4 rounded-2xl border border-slate-800/80">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: "all", label: "All Logs" },
            { id: "rag", label: "Knowledge / RAG" },
            { id: "price", label: "CA Scanners" },
            { id: "safety", label: "Safety Shield" },
            { id: "system", label: "Orchestrator Core" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setFilter(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap cursor-pointer ${
                filter === cat.id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search log output..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
      </div>

      {/* Terminal View Card */}
      <div className="glass-card rounded-2xl border border-slate-800/90 shadow-2xl overflow-hidden">
        {/* Terminal Header Bar */}
        <div className="h-10 bg-slate-950/90 px-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
            <span className="text-[11px] font-mono text-slate-500 ml-2">telemetry@zoe-orchestrator:~# live-tail</span>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1">
              <Radio className="h-3 w-3 text-emerald-400 animate-pulse" />
              Connected
            </span>
            <span className="text-slate-600">|</span>
            <span>{filteredLogs.length} events logged</span>
          </div>
        </div>

        {/* Log Entries Stream */}
        <div className="p-4 divide-y divide-slate-850/50 max-h-[600px] overflow-y-auto font-mono text-xs">
          {filteredLogs.map((log) => (
            <div key={log.id} className="py-3 px-2 hover:bg-slate-900/40 transition-colors rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex items-start md:items-center gap-3 flex-1 min-w-0">
                <span className="text-[10px] text-slate-500 whitespace-nowrap">
                  {log.timestamp}
                </span>

                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                  log.category === "rag" ? "bg-cyan-950/60 text-cyan-300 border-cyan-800/60" :
                  log.category === "price" ? "bg-indigo-950/60 text-indigo-300 border-indigo-800/60" :
                  log.category === "safety" ? "bg-purple-950/60 text-purple-300 border-purple-800/60" :
                  "bg-slate-900 text-slate-400 border-slate-800"
                }`}>
                  {log.project}
                </span>

                <span className="text-slate-300 text-xs font-sans truncate">
                  {log.message}
                </span>
              </div>

              <div className="flex items-center gap-3 self-end md:self-auto flex-shrink-0">
                <span className="text-[10px] text-slate-500">
                  {log.latency}
                </span>

                <Badge className={`text-[9px] uppercase font-mono px-1.5 py-0 ${
                  log.status === "verified" ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60" :
                  log.status === "guard" ? "bg-amber-950/80 text-amber-300 border border-amber-800/60" :
                  log.status === "success" ? "bg-cyan-950/80 text-cyan-300 border border-cyan-800/60" :
                  "bg-slate-900 text-slate-400 border border-slate-800"
                }`}>
                  {log.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
