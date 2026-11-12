"use client"

import { useState } from "react"
import { 
  Search, 
  RefreshCw,
  Clock,
  CheckCircle2,
  Filter
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface LogItem {
  id: string
  timestamp: string
  project: string
  category: "Knowledge" | "Price" | "Safety" | "System"
  message: string
  latency: string
  status: "Success" | "Active" | "Verified"
}

export default function DashboardLogsPage() {
  const [filter, setFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")

  const logs: LogItem[] = [
    {
      id: "log-1",
      timestamp: "11:46:54",
      project: "One Love",
      category: "Knowledge",
      message: "Resolved /links command: generated official inline links for Twitter, Telegram, TikTok & Website.",
      latency: "14ms",
      status: "Verified"
    },
    {
      id: "log-2",
      timestamp: "11:46:53",
      project: "One Love",
      category: "Knowledge",
      message: "Query: 'Who is the founder of One Love?' -> Retrieved answer: 'Captain Robbie Olson' via FAISS index.",
      latency: "182ms",
      status: "Success"
    },
    {
      id: "log-3",
      timestamp: "11:46:21",
      project: "One Love",
      category: "Price",
      message: "Market inquiry on $ONELOVE -> DexScreener live price scan generated inline chart buttons.",
      latency: "340ms",
      status: "Success"
    },
    {
      id: "log-4",
      timestamp: "11:45:10",
      project: "System",
      category: "Safety",
      message: "Outbound message passed URL allowlist filter (onelovesailingcoin.com & tiktok.com).",
      latency: "2ms",
      status: "Verified"
    },
    {
      id: "log-5",
      timestamp: "11:44:02",
      project: "System",
      category: "System",
      message: "Multi-tenant polling update: processed update offset receipt in operational.db.",
      latency: "8ms",
      status: "Active"
    },
    {
      id: "log-6",
      timestamp: "11:43:18",
      project: "Hummingbird",
      category: "System",
      message: "Cross-chat awareness check completed for active Telegram discussion topic.",
      latency: "24ms",
      status: "Success"
    }
  ]

  const filteredLogs = logs.filter((log) => {
    const matchesFilter = filter === "all" || log.category.toLowerCase() === filter.toLowerCase()
    const matchesSearch = 
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.project.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Activity Logs
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time audit stream of agent queries, knowledge retrievals, and safety checks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {}}
            className="border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs h-9"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Filter logs by keyword or project..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto">
          {["all", "Knowledge", "Price", "Safety", "System"].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                filter === cat
                  ? "bg-slate-900 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {cat === "all" ? "All Logs" : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Clean Log Table */}
      <Card className="enterprise-card border border-slate-200 shadow-sm bg-white overflow-hidden">
        <div className="divide-y divide-slate-100">
          {filteredLogs.map((log) => (
            <div key={log.id} className="p-4 hover:bg-slate-50/70 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-start sm:items-center gap-3">
                <span className="font-mono text-slate-400 shrink-0 text-[11px] pt-0.5 sm:pt-0">
                  {log.timestamp}
                </span>

                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
                  {log.project}
                </span>

                <span className={`px-2 py-0.5 rounded text-[11px] font-medium shrink-0 ${
                  log.category === "Knowledge" 
                    ? "bg-blue-50 text-blue-700 border border-blue-200" 
                    : log.category === "Safety"
                    ? "bg-purple-50 text-purple-700 border border-purple-200"
                    : log.category === "Price"
                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                    : "bg-slate-100 text-slate-600 border border-slate-200"
                }`}>
                  {log.category}
                </span>

                <p className="text-slate-700 font-normal">
                  {log.message}
                </p>
              </div>

              <div className="flex items-center gap-3 shrink-0 pl-12 sm:pl-0">
                <span className="font-mono text-slate-400 text-[11px]">{log.latency}</span>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {log.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
