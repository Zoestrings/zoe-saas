"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { PerformanceAlertsPanel } from "@/components/scanner/performance-alerts-panel"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { api, Project, ProjectAnalytics, EntitlementResponse } from "@/lib/api"

export default function OwnerDashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null)
  const [entitlement, setEntitlement] = useState<EntitlementResponse | null>(null)
  const [docCount, setDocCount] = useState<number>(0)
  const [researchReport, setResearchReport] = useState<{ id: string; report_text: string; created_at: string } | null>(null)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [reportError, setReportError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  // Deploy New Bot Modal State (Self-Serve Owner Deployment)
  const [deployOpen, setDeployOpen] = useState(false)
  const [deployName, setDeployName] = useState("")
  const [deployToken, setDeployToken] = useState("")
  const [deployGroupId, setDeployGroupId] = useState("")
  const [deployCA, setDeployCA] = useState("")
  const [deploying, setDeploying] = useState(false)
  const [deployError, setDeployError] = useState<string | null>(null)

  const handleDeployBot = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!deployName.trim() || !deployToken.trim()) {
      setDeployError("Project name and Telegram Bot Token are required.")
      return
    }
    setDeploying(true)
    setDeployError(null)
    try {
      await api.createProject({
        name: deployName.trim(),
        platform: "telegram",
        telegram_bot_token: deployToken.trim(),
        telegram_group_id: deployGroupId.trim() || undefined,
        token_address: deployCA.trim() || undefined,
      })
      setDeployOpen(false)
      setDeployName("")
      setDeployToken("")
      setDeployGroupId("")
      setDeployCA("")
      await loadDashboardData()
    } catch (err: any) {
      setDeployError(err?.message || "Failed to deploy bot.")
    } finally {
      setDeploying(false)
    }
  }

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

        try {
          const reports = await api.getProjectResearchReports(primaryProject.id, 1)
          if (Array.isArray(reports) && reports.length > 0) {
            setResearchReport(reports[0])
          }
        } catch (err) {
          console.warn("Could not load automated research reports:", err)
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

  const handleGenerateReport = async (projectId: string) => {
    setGeneratingReport(true)
    setReportError(null)
    try {
      const report = await api.generateProjectResearchReport(projectId)
      setResearchReport(report)
      // Refresh entitlement balance after 20-credit deduction
      try {
        const updatedEnt = await api.getEntitlement()
        setEntitlement(updatedEnt)
      } catch {
        // Ignore non-critical refresh error
      }
    } catch (err: any) {
      setReportError(err?.message || "Failed to generate research report. Please check your credit balance.")
    } finally {
      setGeneratingReport(false)
    }
  }

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-neutral-400 gap-3">
        <RefreshCw className="h-7 w-7 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Syncing project workspace...</p>
      </div>
    )
  }

  const isPro = Boolean(entitlement?.is_pro || entitlement?.plan === "pro")
  const creditBalance = entitlement?.credits ?? 0
  const primaryProject = projects.length > 0 ? projects[0] : null

  const deployBotModal = (
    <Dialog open={deployOpen} onOpenChange={setDeployOpen}>
      <DialogContent className="w-[92vw] sm:max-w-[460px] bg-[#121212] border border-neutral-800 text-white rounded-3xl p-6">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
            <Bot className="h-5 w-5 text-[#00ff66]" />
            Deploy New Bot
          </DialogTitle>
          <DialogDescription className="text-xs text-neutral-400">
            Connect your Telegram Bot Token to launch your autonomous Zoe community agent.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleDeployBot} className="space-y-4 pt-2">
          {deployError && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs">
              {deployError}
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="owner-bot-name" className="text-xs font-semibold text-white">
              Project Name *
            </Label>
            <Input
              id="owner-bot-name"
              placeholder="e.g. One Love AI"
              value={deployName}
              onChange={(e) => setDeployName(e.target.value)}
              required
              className="bg-neutral-950 border-neutral-800 text-white text-xs h-10 rounded-xl focus:border-[#00ff66]"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="owner-bot-token" className="text-xs font-semibold text-white">
              Telegram Bot Token *
            </Label>
            <Input
              id="owner-bot-token"
              type="password"
              placeholder="1234567890:ABCdef..."
              value={deployToken}
              onChange={(e) => setDeployToken(e.target.value)}
              required
              className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="owner-group-id" className="text-xs font-semibold text-white">
              Telegram Group ID (Optional)
            </Label>
            <Input
              id="owner-group-id"
              placeholder="-1001234567890"
              value={deployGroupId}
              onChange={(e) => setDeployGroupId(e.target.value)}
              className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="owner-ca" className="text-xs font-semibold text-white">
              Token Contract Address (Optional)
            </Label>
            <Input
              id="owner-ca"
              placeholder="Solana Mint or 0x..."
              value={deployCA}
              onChange={(e) => setDeployCA(e.target.value)}
              className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
            />
          </div>
          <DialogFooter className="pt-3 border-t border-neutral-800">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setDeployOpen(false)}
              className="text-xs text-neutral-400 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={deploying}
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-5 rounded-xl cursor-pointer"
            >
              {deploying ? "Deploying..." : "Deploy Bot"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )

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
            <span className="text-[#00ff66]">• 💳 {creditBalance.toLocaleString()} Credits</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            No Assigned Bot
          </h1>
          <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed max-w-md mx-auto">
            Your client profile is verified. Deploy your own Telegram community bot now or view subscription plans.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            onClick={() => setDeployOpen(true)}
            className="w-full sm:w-auto bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-6 rounded-full cursor-pointer shadow-lg shadow-[#00ff66]/20"
          >
            <Bot className="h-3.5 w-3.5 mr-2" />
            Deploy New Bot
          </Button>
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
              variant="outline"
              className="w-full sm:w-auto border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white font-bold text-xs h-10 px-6 rounded-full cursor-pointer"
            >
              View Plans
            </Button>
          </Link>
        </div>
        {deployBotModal}
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

        <div className="flex flex-wrap items-center gap-2">
          <Link href="/billing">
            <div className="px-3.5 py-1.5 rounded-full bg-neutral-900 border border-[#00ff66]/40 text-xs font-mono text-white flex items-center gap-1.5 cursor-pointer hover:border-[#00ff66]">
              <span>💳 {creditBalance.toLocaleString()} Credits</span>
            </div>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={loadDashboardData}
            className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 px-4 rounded-full cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setDeployOpen(true)}
            className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-9 px-4 rounded-full cursor-pointer shadow-md shadow-[#00ff66]/20"
          >
            <Bot className="h-3.5 w-3.5 mr-1.5" />
            Deploy New Bot
          </Button>
          <Link href="/owner/project">
            <Button
              variant="outline"
              size="sm"
              className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white font-bold text-xs h-9 px-4 rounded-full cursor-pointer"
            >
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
            <div className={`h-11 w-11 rounded-2xl border flex items-center justify-center shrink-0 ${isPro ? "bg-[#00ff66]/10 border-[#00ff66]/20 text-[#00ff66]" : "bg-amber-500/10 border-amber-500/20 text-amber-400"
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

      {/* Automated Research Reports (Pillar 3: Autonomous Agent) */}
      <Card className="bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl overflow-hidden">
        <CardHeader className="pb-4 border-b border-neutral-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                <span>Automated Research Reports</span>
                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/20">
                  Daily Brief
                </span>
              </CardTitle>
              <CardDescription className="text-xs text-neutral-400">
                Proactive Morning Brief combining DexScreener liquidity, live Web3 news, and X sentiment.
              </CardDescription>
            </div>
          </div>

          <Button
            onClick={() => handleGenerateReport(primaryProject.id)}
            disabled={generatingReport}
            size="sm"
            className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-9 px-4 rounded-full cursor-pointer shadow-lg shadow-[#00ff66]/10 shrink-0"
          >
            {generatingReport ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                <span>Generating Brief...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                <span>Generate Report Now (20 Credits)</span>
              </>
            )}
          </Button>
        </CardHeader>

        <CardContent className="p-6">
          {reportError && (
            <div className="mb-4 p-3 rounded-2xl bg-red-500/10 border border-red-500/30 text-xs text-red-400">
              {reportError}
            </div>
          )}

          <div className="rounded-2xl bg-neutral-950/60 backdrop-blur-xl border border-neutral-800/80 p-5 space-y-3">
            {researchReport ? (
              <>
                <div className="flex items-center justify-between text-[11px] text-neutral-400 font-mono pb-2 border-b border-neutral-800/70">
                  <span className="flex items-center gap-1.5 text-[#00ff66]">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Latest Autonomous Intelligence Brief</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{new Date(researchReport.created_at).toLocaleString()}</span>
                  </span>
                </div>
                <div className="text-xs sm:text-sm text-neutral-200 leading-relaxed whitespace-pre-line">
                  {researchReport.report_text}
                </div>
              </>
            ) : (
              <div className="py-6 text-center space-y-2">
                <p className="text-xs text-neutral-300 font-medium">
                  No automated Morning Brief has been generated for {primaryProject.name} yet.
                </p>
                <p className="text-[11px] text-neutral-500">
                  Zoe automatically generates a fresh report every 24 hours, or click &quot;Generate Report Now&quot; to run one immediately.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

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
      <div className="pt-2">
        <PerformanceAlertsPanel />
      </div>
      {deployBotModal}
    </div>
  )
}
