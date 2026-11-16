"use client"

import { useEffect, useState, useMemo } from "react"
import {
  MessageSquare,
  Search,
  RefreshCw,
  Clock,
  ShieldAlert,
  Bot,
  User as UserIcon,
  Filter,
  Sparkles,
  Inbox,
  ArrowRight,
  HelpCircle,
  Radar
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api, Project, ConversationLogItem } from "@/lib/api"

export default function OwnerLogsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string>("")
  const [logs, setLogs] = useState<ConversationLogItem[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [loadingLogs, setLoadingLogs] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [intentFilter, setIntentFilter] = useState<string>("all")

  // Load projects owned by user
  useEffect(() => {
    async function init() {
      try {
        const projs = await api.getProjects()
        setProjects(projs || [])
        if (projs && projs.length > 0) {
          setSelectedProjectId(projs[0].id)
        }
      } catch (err) {
        console.warn("Failed to load projects:", err)
      } finally {
        setLoadingProjects(false)
      }
    }
    init()
  }, [])

  // Load logs whenever selected project changes
  const fetchLogs = async (projectId: string, search?: string) => {
    if (!projectId) return
    setLoadingLogs(true)
    try {
      const data = await api.getProjectLogs(projectId, search, 50)
      setLogs(data || [])
    } catch (err) {
      console.warn("Failed to fetch logs:", err)
      setLogs([])
    } finally {
      setLoadingLogs(false)
    }
  }

  useEffect(() => {
    if (selectedProjectId) {
      fetchLogs(selectedProjectId, searchQuery)
    }
  }, [selectedProjectId])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedProjectId) {
      fetchLogs(selectedProjectId, searchQuery)
    }
  }

  // Filter logs by category/intent locally if selected
  const filteredLogs = useMemo(() => {
    if (intentFilter === "all") return logs
    return logs.filter((log) => {
      const combined = `${log.intent || ""} ${log.category || ""}`.toLowerCase()
      if (intentFilter === "scanner") return combined.includes("ca") || combined.includes("price") || combined.includes("crypto")
      if (intentFilter === "moderation") return combined.includes("scam") || combined.includes("spammer") || combined.includes("moderation")
      if (intentFilter === "faq") return combined.includes("direct_question") || combined.includes("project")
      return true
    })
  }, [logs, intentFilter])

  const getIntentBadge = (log: ConversationLogItem) => {
    const raw = `${log.intent || ""} ${log.category || ""}`.toLowerCase()
    if (raw.includes("scam") || raw.includes("moderation") || raw.includes("spammer")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/30">
          <ShieldAlert className="h-2.5 w-2.5" />
          Moderated Scam
        </span>
      )
    }
    if (raw.includes("ca") || raw.includes("price") || raw.includes("crypto") || raw.includes("scan")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
          <Radar className="h-2.5 w-2.5" />
          Scanned Token
        </span>
      )
    }
    if (raw.includes("direct_question") || raw.includes("faq")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/30">
          <HelpCircle className="h-2.5 w-2.5" />
          Answered FAQ
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-neutral-800 text-neutral-300 border border-neutral-700">
        <Sparkles className="h-2.5 w-2.5" />
        Community Chat
      </span>
    )
  }

  const formatTimestamp = (tsStr: string) => {
    if (!tsStr) return ""
    try {
      const d = new Date(tsStr)
      if (isNaN(d.getTime())) return tsStr
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " • " + d.toLocaleDateString([], { month: "short", day: "numeric" })
    } catch {
      return tsStr
    }
  }

  if (loadingProjects) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-neutral-400 gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Loading conversation console...</p>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="py-20 max-w-xl mx-auto text-center space-y-5">
        <div className="h-16 w-16 mx-auto rounded-3xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-500 shadow-xl">
          <Inbox className="h-8 w-8 text-[#00ff66]" />
        </div>
        <div className="space-y-2">
          <h2 className="text-lg font-bold text-white">No Assigned Bot</h2>
          <p className="text-xs text-neutral-400 leading-relaxed">
            You don&apos;t have any projects deployed yet. Contact platform administration to provision your bot.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-neutral-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <MessageSquare className="h-6 w-6 text-[#00ff66]" />
            Live Conversation Logs
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Real-time feed of community messages, automated answers, and safety moderation events.
          </p>
        </div>

        {/* Controls: Project Switcher & Refresh */}
        <div className="flex items-center gap-3">
          {projects.length > 1 && (
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-neutral-900 border border-neutral-800 text-xs text-white rounded-full px-3 py-1.5 focus:outline-none focus:border-[#00ff66]"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchLogs(selectedProjectId, searchQuery)}
            disabled={loadingLogs}
            className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 rounded-full cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loadingLogs ? "animate-spin text-[#00ff66]" : ""}`} />
            Refresh Feed
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-[#121212] p-3 rounded-2xl border border-neutral-800 shadow-md">
        {/* Search Input */}
        <form onSubmit={handleSearch} className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search keywords in messages or replies..."
            className="pl-10 h-10 bg-neutral-950 border-neutral-800 text-xs text-white placeholder:text-neutral-500 rounded-xl focus-visible:ring-[#00ff66]"
          />
        </form>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIntentFilter("all")}
            className={`text-xs h-8 px-3 rounded-xl cursor-pointer ${
              intentFilter === "all" ? "bg-neutral-800 text-[#00ff66] font-bold" : "text-neutral-400 hover:text-white"
            }`}
          >
            All Logs ({logs.length})
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIntentFilter("faq")}
            className={`text-xs h-8 px-3 rounded-xl cursor-pointer ${
              intentFilter === "faq" ? "bg-neutral-800 text-blue-400 font-bold" : "text-neutral-400 hover:text-white"
            }`}
          >
            FAQs
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIntentFilter("scanner")}
            className={`text-xs h-8 px-3 rounded-xl cursor-pointer ${
              intentFilter === "scanner" ? "bg-neutral-800 text-[#00ff66] font-bold" : "text-neutral-400 hover:text-white"
            }`}
          >
            CA Scans
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIntentFilter("moderation")}
            className={`text-xs h-8 px-3 rounded-xl cursor-pointer ${
              intentFilter === "moderation" ? "bg-neutral-800 text-red-400 font-bold" : "text-neutral-400 hover:text-white"
            }`}
          >
            Moderation
          </Button>
        </div>
      </div>

      {/* Chat Log Stream */}
      <div className="space-y-4">
        {loadingLogs ? (
          <div className="py-20 flex flex-col items-center justify-center text-neutral-400 gap-3">
            <RefreshCw className="h-6 w-6 animate-spin text-[#00ff66]" />
            <p className="text-xs font-semibold text-white tracking-wide">Syncing message history...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <Card className="bg-[#121212] border border-neutral-800 p-12 text-center rounded-3xl shadow-xl">
            <div className="h-12 w-12 mx-auto rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-500 mb-3">
              <MessageSquare className="h-6 w-6 text-neutral-400" />
            </div>
            <h3 className="text-sm font-bold text-white mb-1">No Messages Found</h3>
            <p className="text-xs text-neutral-500 max-w-sm mx-auto">
              {searchQuery
                ? `No conversation matched "${searchQuery}". Try clearing your search term.`
                : "No conversations have been logged for this bot yet. Interactions from your Telegram group will stream here automatically."}
            </p>
          </Card>
        ) : (
          filteredLogs.map((log) => (
            <Card
              key={log.id}
              className="bg-[#121212] border border-neutral-800/80 hover:border-neutral-700/80 transition-all rounded-3xl p-5 shadow-xl space-y-4"
            >
              {/* Event Metadata Bar */}
              <div className="flex items-center justify-between pb-3 border-b border-neutral-800/60 text-xs">
                <div className="flex items-center gap-2">
                  {getIntentBadge(log)}
                  <span className="text-[11px] text-neutral-500 hidden sm:inline">
                    Log #{log.id}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-neutral-400 text-[11px]">
                  <Clock className="h-3 w-3 text-neutral-500" />
                  {formatTimestamp(log.timestamp)}
                </div>
              </div>

              {/* Chat Bubbles Container */}
              <div className="space-y-3 pt-1">
                {/* 1. Community Member Message (Left Aligned - Gray Bubble) */}
                <div className="flex items-start gap-3 max-w-[85%] sm:max-w-[75%]">
                  <div className="h-8 w-8 rounded-full bg-neutral-800 border border-neutral-700/80 flex items-center justify-center shrink-0 text-neutral-300 shadow-sm mt-0.5">
                    <UserIcon className="h-4 w-4" />
                  </div>
                  <div className="bg-neutral-800/90 text-white rounded-2xl rounded-tl-sm px-4 py-3 border border-neutral-700/60 shadow-sm">
                    <p className="text-xs font-medium leading-relaxed whitespace-pre-wrap select-text">
                      {log.user_message}
                    </p>
                    <span className="block text-[10px] text-neutral-400 mt-1 font-mono">
                      User: {log.pseudonymous_user_id ? `${log.pseudonymous_user_id.slice(0, 8)}...` : "Community Member"}
                    </span>
                  </div>
                </div>

                {/* 2. Zoe AI Bot Response (Right Aligned - Neon Green Bubble) */}
                {log.bot_response ? (
                  <div className="flex items-start justify-end gap-3 max-w-[85%] sm:max-w-[75%] ml-auto">
                    <div className="bg-[#00ff66]/10 text-neutral-100 rounded-2xl rounded-tr-sm px-4 py-3 border border-[#00ff66]/30 shadow-[0_0_15px_rgba(0,255,102,0.06)]">
                      <p className="text-xs leading-relaxed whitespace-pre-wrap select-text">
                        {log.bot_response}
                      </p>
                      <div className="flex items-center justify-end gap-1.5 mt-1.5">
                        <span className="text-[10px] font-bold text-[#00ff66] flex items-center gap-1">
                          <Bot className="h-3 w-3" />
                          Zoe Community Agent
                        </span>
                      </div>
                    </div>
                    <div className="h-8 w-8 rounded-full bg-[#00ff66] text-black flex items-center justify-center shrink-0 font-bold shadow-md shadow-[#00ff66]/20 mt-0.5">
                      <Bot className="h-4 w-4 fill-black text-black" />
                    </div>
                  </div>
                ) : (
                  <div className="text-right text-[11px] text-neutral-500 italic pr-2">
                    (No bot reply required — silent participation)
                  </div>
                )}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
