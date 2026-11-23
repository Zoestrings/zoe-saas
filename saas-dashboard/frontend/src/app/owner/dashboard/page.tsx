"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  Bot,
  BrainCircuit,
  FileCode,
  Radar,
  MessageSquare,
  Sparkles,
  Inbox,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Check,
  Crown,
  Layers,
  TrendingUp,
  ExternalLink,
  Flame,
  Clock
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Project, ProjectAnalytics, EntitlementResponse } from "@/lib/api"

export default function OwnerDashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null)
  const [entitlement, setEntitlement] = useState<EntitlementResponse | null>(null)
  const [docCount, setDocCount] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCA(text)
    setTimeout(() => setCopiedCA(null), 2000)
  }

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const [projRes, entRes] = await Promise.allSettled([
        api.getProjects(),
        api.getEntitlement(),
      ])

      let primaryProject: Project | null = null
      if (projRes.status === "fulfilled") {
        const list = projRes.value || []
        setProjects(list)
        if (list.length > 0) {
          primaryProject = list[0]
        }
      }

      if (entRes.status === "fulfilled" && entRes.value) {
        setEntitlement(entRes.value)
      }

      // If project exists, fetch its live telemetry and knowledge docs
      if (primaryProject) {
        try {
          const stats = await api.getProjectAnalytics(primaryProject.id)
          setAnalytics(stats)
        } catch (err) {
          console.warn("Could not load analytics for project:", err)
        }

        try {
          const docs = await api.getProjectDocuments(primaryProject.id)
          setDocCount(Array.isArray(docs) ? docs.length : 0)
        } catch (err) {
          console.warn("Could not load docs for project:", err)
        }
      }
    } catch (err) {
      console.warn("Failed to load owner dashboard data:", err)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-neutral-400 gap-3">
        <RefreshCw className="h-7 w-7 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Syncing project workspace...</p>
      </div>
    )
  }

  const isPro = Boolean(entitlement?.is_pro || entitlement?.plan === "pro")
  const primaryProject = projects.length > 0 ? projects[0] : null

  // Empty State: Intentional, centered, elegant card
  if (!primaryProject) {
    return (
      <div className="py-16 sm:py-24 max-w-xl mx-auto text-center space-y-6 px-4">
        <div className="h-20 w-20 mx-auto rounded-3xl bg-neutral-900/90 border border-neutral-800 flex items-center justify-center text-neutral-400 shadow-2xl shadow-black/50">
          <Bot className="h-10 w-10 text-[#00ff66]" />
        </div>

        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-xs font-mono text-neutral-400 mb-2">
            <span>Status: Account Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            No Assigned Bot
          </h1>
          <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed max-w-md mx-auto">
            Your client profile is verified, but no autonomous community bot has been assigned to your workspace yet. 
            Please contact the Zoe platform administrator to provision and link your bot.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            variant="outline"
            onClick={loadDashboardData}
            className="w-full sm:w-auto border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-10 px-6 rounded-full cursor-pointer shadow-lg"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-2" />
            Check Again
          </Button>
          <Link href="/billing" className="w-full sm:w-auto">
            <Button
              className="w-full sm:w-auto bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-6 rounded-full cursor-pointer shadow-lg shadow-[#00ff66]/20"
            >
              View Subscription Plans
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  const shortCA = primaryProject.token_address
    ? `${primaryProject.token_address.slice(0, 6)}...${primaryProject.token_address.slice(-6)}`
    : null

  return (
    <div className="space-y-8">
      {/* Welcoming Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-neutral-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Welcome back to {primaryProject.name}
            </h1>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 font-bold">
              <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66] animate-pulse" />
              Online
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Real-time analytics, intelligence controls, and autonomous community orchestration.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadDashboardData}
            className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 px-4 rounded-full cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
          <Link href="/owner/project">
            <Button
              size="sm"
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-9 px-4 rounded-full cursor-pointer shadow-md shadow-[#00ff66]/20"
            >
              <Bot className="h-3.5 w-3.5 mr-1.5" />
              Bot Config
            </Button>
          </Link>
        </div>
      </div>

      {/* Free Plan Upgrade Banner */}
      {!isPro && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-neutral-900 to-amber-500/5 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-sm">Your bot is on the Free tier</span>
                <span className="text-[10px] font-mono uppercase bg-amber-500/20 text-amber-400 border border-amber-500/40 px-2 py-0.5 rounded-full font-bold">
                  Free Plan
                </span>
              </div>
              <p className="text-xs text-neutral-300 mt-0.5">
                Upgrade to Pro for $20/month to unlock autonomous background liquidity surveillance and deep wallet audits.
              </p>
            </div>
          </div>
          <Link href="/billing">
            <Button className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-extrabold text-xs h-9 px-5 rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer shrink-0">
              Upgrade to Pro ($20)
            </Button>
          </Link>
        </div>
      )}

      {/* Responsive Metric Cards (1 col mobile, 2 cols md, 4 cols xl) */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Messages Handled */}
        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Messages Handled</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {(analytics?.total_messages ?? 0).toLocaleString()}
              </h3>
              <p className="text-[11px] text-[#00ff66] mt-0.5">
                Episodic memory logged
              </p>
            </div>
            <div className="h-11 w-11 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66] shrink-0">
              <MessageSquare className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        {/* Tokens Scanned */}
        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Tokens Scanned</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {(analytics?.ca_scans ?? 0).toLocaleString()}
              </h3>
              <p className="text-[11px] text-cyan-400 mt-0.5">
                On-chain security sweeps
              </p>
            </div>
            <div className="h-11 w-11 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <Radar className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        {/* Documents Indexed */}
        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Documents Indexed</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {docCount}
              </h3>
              <p className="text-[11px] text-purple-400 mt-0.5">
                FAISS vector memory
              </p>
            </div>
            <div className="h-11 w-11 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
              <BrainCircuit className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        {/* Active Plan */}
        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Active Plan</p>
              <h3 className="text-2xl font-bold text-white mt-1 uppercase flex items-center gap-1.5">
                {isPro ? (
                  <span className="text-[#00ff66]">Pro</span>
                ) : (
                  <span className="text-amber-400">Free</span>
                )}
              </h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">
                {isPro ? "Unlimited intelligence" : "Standard quota"}
              </p>
            </div>
            <div className={`h-11 w-11 rounded-2xl border flex items-center justify-center shrink-0 ${
              isPro ? "bg-[#00ff66]/10 border-[#00ff66]/20 text-[#00ff66]" : "bg-amber-500/10 border-amber-500/20 text-amber-400"
            }`}>
              <Crown className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions (3 Large Prominent Cards) */}
      <div className="space-y-3">
        <h2 className="text-base font-bold text-white tracking-tight">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Action 1: Knowledge Base */}
          <Link href="/owner/dashboard/knowledge" className="block group">
            <Card className="bg-[#121212] border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900/60 transition-all duration-300 h-full cursor-pointer">
              <CardContent className="p-6 space-y-3">
                <div className="h-12 w-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                  <BrainCircuit className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base group-hover:text-[#00ff66] transition-colors">
                    Update Knowledge Base
                  </h3>
                  <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                    Upload project whitepapers, FAQs, or scrape website URLs directly into your bot&apos;s vector memory.
                  </p>
                </div>
                <div className="pt-2 flex items-center text-xs font-bold text-[#00ff66] gap-1 group-hover:gap-2 transition-all">
                  <span>Manage Knowledge</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Action 2: Token Scanner */}
          <Link href="/investigate" className="block group">
            <Card className="bg-[#121212] border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900/60 transition-all duration-300 h-full cursor-pointer">
              <CardContent className="p-6 space-y-3">
                <div className="h-12 w-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
                  <Radar className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base group-hover:text-[#00ff66] transition-colors">
                    Scan a Token
                  </h3>
                  <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                    Audit contract security, honeypot mechanics, mint authority, and liquidity depth on Solana.
                  </p>
                </div>
                <div className="pt-2 flex items-center text-xs font-bold text-[#00ff66] gap-1 group-hover:gap-2 transition-all">
                  <span>Open Scanner</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Action 3: Conversation Logs */}
          <Link href="/owner/logs" className="block group">
            <Card className="bg-[#121212] border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900/60 transition-all duration-300 h-full cursor-pointer">
              <CardContent className="p-6 space-y-3">
                <div className="h-12 w-12 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66] group-hover:scale-110 transition-transform">
                  <MessageSquare className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base group-hover:text-[#00ff66] transition-colors">
                    View Conversation Logs
                  </h3>
                  <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                    Inspect episodic community transcripts, user queries, intent tags, and AI response accuracy.
                  </p>
                </div>
                <div className="pt-2 flex items-center text-xs font-bold text-[#00ff66] gap-1 group-hover:gap-2 transition-all">
                  <span>Inspect Logs</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>

      {/* Active Bot Workspace Summary */}
      <div className="bg-[#121212] border border-neutral-800 rounded-3xl p-6 sm:p-7 shadow-2xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-800/80">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66] font-bold">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{primaryProject.name}</h3>
              <p className="text-xs text-neutral-400">Primary Autonomous Agent</p>
            </div>
          </div>
          <Link href="/owner/project">
            <Button
              variant="outline"
              size="sm"
              className="border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-8 px-3 rounded-full cursor-pointer"
            >
              <span>Full Details</span>
              <ExternalLink className="h-3 w-3 ml-1.5" />
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800">
            <span className="text-neutral-400 text-[11px] block">Platform Gateway</span>
            <span className="font-bold text-white capitalize mt-1 block">
              {primaryProject.platform || "Telegram"}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800">
            <span className="text-neutral-400 text-[11px] block">Connected Group ID</span>
            <span className="font-mono text-neutral-200 mt-1 block truncate">
              {primaryProject.telegram_group_id || "Global Listen Mode"}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800">
            <span className="text-neutral-400 text-[11px] block">Token Address</span>
            {primaryProject.token_address ? (
              <div className="flex items-center gap-1.5 mt-1">
                <span className="font-mono text-neutral-200 truncate">{shortCA}</span>
                <button
                  type="button"
                  onClick={() => copyToClipboard(primaryProject.token_address!)}
                  className="text-neutral-500 hover:text-[#00ff66] cursor-pointer"
                  title="Copy Address"
                >
                  {copiedCA === primaryProject.token_address ? (
                    <Check className="h-3 w-3 text-[#00ff66]" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </button>
              </div>
            ) : (
              <span className="text-neutral-500 mt-1 block">None assigned</span>
            )}
          </div>

          <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800">
            <span className="text-neutral-400 text-[11px] block">Created Date</span>
            <span className="text-neutral-300 mt-1 block font-mono">
              {primaryProject.created_at ? primaryProject.created_at.slice(0, 10) : "Active"}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
