"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import {
  Radar,
  Search,
  Loader2,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  TrendingUp,
  Lock,
  Unlock,
  Users,
  Info,
  Clock,
  Eye,
  RefreshCw,
  FileSearch,
  Code2,
  Globe,
  User,
  Share2,
  Download,
  Bot,
  Bookmark,
  BookmarkCheck,
  Crown
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
import { api, InvestigationReport, SavedInvestigation } from "@/lib/api"

export default function InvestigatePage() {
  const [caInput, setCaInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<InvestigationReport | null>(null)
  const [copied, setCopied] = useState(false)
  const [copiedCreator, setCopiedCreator] = useState(false)
  const [copiedHistoryId, setCopiedHistoryId] = useState<string | null>(null)

  // Investigation History state
  const [history, setHistory] = useState<SavedInvestigation[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  // Watchlist state (Mega-Module 5)
  const [addingToWatchlist, setAddingToWatchlist] = useState(false)
  const [inWatchlist, setInWatchlist] = useState(false)
  const [watchlistSuccessMsg, setWatchlistSuccessMsg] = useState<string | null>(null)

  // Subscription entitlement state (Mega-Module 6)
  const [isProUser, setIsProUser] = useState(false)

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const data = await api.getInvestigations()
      setHistory(data || [])
    } catch (err) {
      console.warn("Notice: Failed to load investigation history:", err)
    } finally {
      setHistoryLoading(false)
    }
  }

  const loadEntitlement = async () => {
    try {
      const ent = await api.getEntitlement()
      setIsProUser(ent.is_pro)
    } catch {
      setIsProUser(false)
    }
  }

  const handleAddToWatchlist = async () => {
    if (!report || !report.ca) return
    setAddingToWatchlist(true)
    setWatchlistSuccessMsg(null)
    try {
      await api.addToWatchlist(report.ca, report.name || "Unknown Token")
      setInWatchlist(true)
      setWatchlistSuccessMsg("Added to Watchlist")
      setTimeout(() => setWatchlistSuccessMsg(null), 3000)
    } catch (err: any) {
      setWatchlistSuccessMsg(err.message || "Failed to add to watchlist")
      setTimeout(() => setWatchlistSuccessMsg(null), 3000)
    } finally {
      setAddingToWatchlist(false)
    }
  }

  const copyCreatorToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCreator(true)
    setTimeout(() => setCopiedCreator(false), 2000)
  }

  useEffect(() => {
    loadHistory()
    loadEntitlement()

    // Auto-detect and scan CA passed via query parameter (e.g. from Watchlist page)
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search)
      const caParam = urlParams.get("ca")
      if (caParam && caParam.trim()) {
        const cleanCa = caParam.trim()
        setCaInput(cleanCa)
        handleScan(cleanCa)
      }
    }
  }, [])

  const handleScan = async (targetCa?: string) => {
    const addressToScan = (targetCa || caInput).trim()
    if (!addressToScan) {
      setError("Please enter a Solana contract address.")
      return
    }

    setLoading(true)
    setError(null)
    setReport(null)
    setInWatchlist(false)
    setWatchlistSuccessMsg(null)

    try {
      const data = await api.investigate(addressToScan)
      if (!data.valid) {
        setError(data.error || "Invalid Solana contract address.")
      } else {
        setReport(data)
        // Auto-refresh history so newest scan appears at the top
        loadHistory()
      }
    } catch (err: any) {
      setError(err.message || "Failed to complete investigation scan.")
    } finally {
      setLoading(false)
    }
  }

  const handleViewSavedReport = (item: SavedInvestigation) => {
    setError(null)
    setReport(item.report_json)
    setCaInput(item.contract_address)
    setInWatchlist(false)
    setWatchlistSuccessMsg(null)
    // Smooth scroll to report view
    setTimeout(() => {
      const el = document.getElementById("investigation-report")
      if (el) {
        el.scrollIntoView({ behavior: "smooth" })
      }
    }, 100)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const copyHistoryCa = (ca: string, id: string) => {
    navigator.clipboard.writeText(ca)
    setCopiedHistoryId(id)
    setTimeout(() => setCopiedHistoryId(null), 2000)
  }

  const formatNumber = (num?: number | null, decimals = 2) => {
    if (num === undefined || num === null) return "N/A"
    if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(decimals)}B`
    if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(decimals)}M`
    if (num >= 1_000) return `$${(num / 1_000).toFixed(decimals)}K`
    if (num < 0.000001) return `$${num.toFixed(8)}`
    if (num < 0.01) return `$${num.toFixed(6)}`
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: decimals })}`
  }

  const formatPrice = (price?: number | null) => {
    if (price === undefined || price === null) return "N/A"
    if (price === 0) return "$0.00"
    if (price < 0.000001) return `$${price.toFixed(8)}`
    if (price < 0.001) return `$${price.toFixed(6)}`
    if (price < 1.0) return `$${price.toFixed(4)}`
    return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "Just now"
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    } catch {
      return dateStr
    }
  }

  // Sample tokens for instant 1-click testing
  const sampleTokens = [
    { name: "BONK", ca: "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" },
    { name: "USDC (Solana)", ca: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" },
    { name: "Wrapped SOL", ca: "So11111111111111111111111111111111111111112" },
  ]

  const riskLevel = report?.risk?.level || "UNKNOWN"
  const getRiskColor = (level?: string | null) => {
    switch (level) {
      case "CRITICAL":
        return {
          pill: "bg-rose-500/10 border-rose-500/40 text-rose-400",
          card: "border-rose-500/30",
          icon: ShieldAlert,
        }
      case "HIGH":
        return {
          pill: "bg-amber-500/10 border-amber-500/40 text-amber-400",
          card: "border-amber-500/30",
          icon: AlertTriangle,
        }
      case "MEDIUM":
        return {
          pill: "bg-yellow-500/10 border-yellow-500/40 text-yellow-400",
          card: "border-yellow-500/30",
          icon: AlertTriangle,
        }
      case "LOW":
        return {
          pill: "bg-[#00ff66]/10 border-[#00ff66]/40 text-[#00ff66]",
          card: "border-[#00ff66]/30",
          icon: ShieldCheck,
        }
      default:
        return {
          pill: "bg-neutral-800 border-neutral-700 text-neutral-400",
          card: "border-neutral-800",
          icon: Info,
        }
    }
  }

  const riskMeta = getRiskColor(riskLevel)
  const RiskIcon = riskMeta.icon

  const score = report?.safety_score ?? (riskLevel === "LOW" ? 85 : riskLevel === "MEDIUM" ? 55 : riskLevel === "HIGH" ? 30 : 15)
  const getScoreColor = (s: number) => {
    if (s >= 70) {
      return {
        text: "text-[#00ff66]",
        border: "border-[#00ff66]/40",
        bg: "bg-[#00ff66]/10",
        stroke: "#00ff66",
        badge: "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30",
        label: "High Safety",
      }
    }
    if (s >= 40) {
      return {
        text: "text-amber-400",
        border: "border-amber-500/40",
        bg: "bg-amber-500/10",
        stroke: "#fbbf24",
        badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
        label: "Moderate Risk",
      }
    }
    return {
      text: "text-rose-400",
      border: "border-rose-500/40",
      bg: "bg-rose-500/10",
      stroke: "#f43f5e",
      badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
      label: "Critical Caution",
    }
  }
  const scoreMeta = getScoreColor(score)

  return (
    <div className="space-y-8 pb-16">
      {/* Clean PDF Print Styles */}
      <style jsx global>{`
        @media print {
          body {
            background-color: #0a0a0a !important;
            color: #ffffff !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          .no-print, header, aside, nav, button, input {
            display: none !important;
          }
          .print-report-container {
            display: block !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
          }
        }
      `}</style>

      {/* Page Header */}
      <div className="space-y-2 no-print">
        <div className="inline-flex items-center gap-2 bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full text-xs font-bold text-[#00ff66]">
          <Radar className="h-3.5 w-3.5 animate-pulse" />
          Zoe Intelligence Terminal · Milestone 3
        </div>
        <h1 className="text-3xl font-black tracking-tight text-white">
          Intelligence Scanner
        </h1>
        <p className="text-xs text-neutral-400 max-w-2xl">
          Deep on-chain security audit, liquidity validation, holder concentration, and honeypot risk assessment for Solana tokens.
        </p>
      </div>

      {/* Hero Search Section */}
      <div className="bg-[#121212] border border-neutral-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-4 no-print">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleScan()
          }}
          className="flex flex-col sm:flex-row items-center gap-3"
        >
          <div className="relative w-full flex-1">
            <Search className="absolute left-4 top-3.5 h-4 w-4 text-neutral-500" />
            <Input
              type="text"
              placeholder="Paste Solana token contract address (e.g. DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263)..."
              value={caInput}
              onChange={(e) => setCaInput(e.target.value)}
              className="h-12 pl-11 pr-4 bg-neutral-900 border-neutral-700 rounded-full text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66]"
            />
          </div>
          <Button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto h-12 px-7 bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Scanning On-Chain...</span>
              </>
            ) : (
              <>
                <Radar className="h-4 w-4" />
                <span>Scan Token</span>
              </>
            )}
          </Button>
        </form>

        {/* Quick Sample Suggestions */}
        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-neutral-400">
          <span className="text-[11px] font-semibold text-neutral-500">Quick Samples:</span>
          {sampleTokens.map((t) => (
            <button
              key={t.name}
              type="button"
              onClick={() => {
                setCaInput(t.ca)
                handleScan(t.ca)
              }}
              className="px-3 py-1 rounded-full bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 hover:border-neutral-700 text-neutral-300 hover:text-white transition-all text-[11px] cursor-pointer"
            >
              {t.name}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-3 no-print">
          <ShieldAlert className="h-5 w-5 shrink-0 text-rose-400" />
          <div>
            <p className="font-bold">Investigation Scan Error</p>
            <p className="text-[11px] text-rose-300/90">{error}</p>
          </div>
        </div>
      )}

      {/* Section 2: Recent Investigations Table (Under Search Bar) */}
      <div className="space-y-4 no-print">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-[#00ff66]" />
            <h2 className="text-lg font-bold text-white tracking-tight">Recent Investigations</h2>
            <span className="text-xs bg-neutral-900 text-neutral-400 px-2.5 py-0.5 rounded-full border border-neutral-800 font-mono">
              {history.length} Saved
            </span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadHistory}
            disabled={historyLoading}
            className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-8 px-3 rounded-full cursor-pointer"
          >
            <RefreshCw className={`h-3 w-3 mr-1.5 ${historyLoading ? "animate-spin text-[#00ff66]" : ""}`} />
            Refresh
          </Button>
        </div>

        <div className="rounded-3xl border border-neutral-800 bg-[#121212] overflow-hidden shadow-2xl">
          <Table>
            <TableHeader>
              <TableRow className="border-b border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Token Name
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Contract Address
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Risk Level
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Date
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider text-right">
                  Action
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {historyLoading && history.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-28 text-center text-neutral-500">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin text-[#00ff66]" />
                      <span className="text-xs">Loading investigation history...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : history.length > 0 ? (
                history.map((item) => {
                  const itemRiskMeta = getRiskColor(item.risk_level)
                  const ItemRiskIcon = itemRiskMeta.icon
                  const shortCa = `${item.contract_address.slice(0, 4)}...${item.contract_address.slice(-4)}`

                  return (
                    <TableRow
                      key={item.id}
                      className="border-b border-neutral-800/60 hover:bg-neutral-900/60 transition-colors"
                    >
                      {/* Token Name */}
                      <TableCell className="py-3.5 px-5 text-xs">
                        <div className="flex items-center gap-2">
                          <div className="h-7 w-7 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66] font-bold text-xs">
                            {item.token_name ? item.token_name[0] : "T"}
                          </div>
                          <div>
                            <span className="font-bold text-white block">
                              {item.token_name || "Unknown Token"}
                            </span>
                            <span className="text-[10px] text-neutral-500 uppercase">Solana</span>
                          </div>
                        </div>
                      </TableCell>

                      {/* Contract Address */}
                      <TableCell className="py-3.5 px-5 text-xs font-mono">
                        <div className="inline-flex items-center gap-1.5 bg-neutral-900 border border-neutral-800 px-2.5 py-1 rounded-full text-neutral-300">
                          <span>{shortCa}</span>
                          <button
                            type="button"
                            onClick={() => copyHistoryCa(item.contract_address, item.id)}
                            className="text-neutral-500 hover:text-[#00ff66] transition-colors cursor-pointer"
                          >
                            {copiedHistoryId === item.id ? (
                              <Check className="h-3 w-3 text-[#00ff66]" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </button>
                        </div>
                      </TableCell>

                      {/* Risk Level Badge */}
                      <TableCell className="py-3.5 px-5 text-xs">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${itemRiskMeta.pill}`}
                        >
                          <ItemRiskIcon className="h-3 w-3" />
                          {item.risk_level || "UNKNOWN"}
                        </span>
                      </TableCell>

                      {/* Date */}
                      <TableCell className="py-3.5 px-5 text-xs text-neutral-400">
                        {formatDate(item.created_at)}
                      </TableCell>

                      {/* Open Report Action */}
                      <TableCell className="py-3.5 px-5 text-xs text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewSavedReport(item)}
                          className="h-8 px-3 rounded-full border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black hover:border-[#00ff66] text-white text-xs font-semibold cursor-pointer transition-all"
                        >
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          Open Report
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-neutral-500 text-xs">
                    <div className="space-y-1">
                      <p className="font-semibold text-neutral-400">No saved investigations yet</p>
                      <p className="text-[11px] text-neutral-600">
                        Scanned tokens will automatically appear in this history log.
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Loading Skeleton Indicator */}
      {loading && (
        <div className="p-12 rounded-3xl bg-[#121212] border border-neutral-800 flex flex-col items-center justify-center text-center space-y-4 no-print">
          <div className="h-14 w-14 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66]">
            <Loader2 className="h-7 w-7 animate-spin" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">Aggregating Evidence...</h3>
            <p className="text-xs text-neutral-400">
              Querying DexScreener pair liquidity and GoPlus Solana security registers.
            </p>
          </div>
        </div>
      )}

      {/* Scan Results Report */}
      {report && (
        <div id="investigation-report" className="space-y-6 print-report-container">
          {/* Mega-Module 4: Safety Score Gauge & AI Analyst Layer */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Safety Score Radial Gauge Card */}
            <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden flex flex-col justify-between p-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider">
                  Safety Score
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${scoreMeta.badge}`}>
                  {scoreMeta.label}
                </span>
              </div>

              {/* Circular Radial Gauge */}
              <div className="relative flex items-center justify-center py-3">
                <svg className="w-36 h-36 -rotate-90 transform" viewBox="0 0 120 120">
                  <circle
                    cx="60"
                    cy="60"
                    r="48"
                    className="stroke-neutral-900"
                    strokeWidth="10"
                    fill="transparent"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="48"
                    stroke={scoreMeta.stroke}
                    strokeWidth="10"
                    strokeDasharray={2 * Math.PI * 48}
                    strokeDashoffset={2 * Math.PI * 48 * (1 - score / 100)}
                    strokeLinecap="round"
                    fill="transparent"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className={`text-4xl font-black ${scoreMeta.text} tracking-tight`}>
                    {score}
                  </span>
                  <span className="text-[10px] font-bold uppercase text-neutral-500 tracking-wider">
                    / 100
                  </span>
                </div>
              </div>

              <div className="text-center text-xs text-neutral-400 border-t border-neutral-800/80 pt-3">
                {score >= 70
                  ? "Verified contract hygiene & healthy tokenomics"
                  : score >= 40
                    ? "Moderate risk factors detected on-chain"
                    : "Extreme caution advised — high vulnerability signals"}
              </div>
            </Card>

            {/* AI Analyst Glassmorphism Card (Pro Gated) */}
            {(() => {
              const isPro = report.is_pro ?? isProUser
              return (
                <Card className="md:col-span-2 bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden p-6 flex flex-col justify-between relative">
                  <CardHeader className="p-0 pb-3 border-b border-neutral-800/80 flex flex-row items-center justify-between">
                    <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                      <Bot className="h-5 w-5 text-[#00ff66]" />
                      <span>AI Analyst Intelligence</span>
                    </CardTitle>
                    <span className="text-[10px] font-semibold bg-[#00ff66]/10 text-[#00ff66] px-2.5 py-0.5 rounded-full border border-[#00ff66]/30">
                      Groq LLM Verified
                    </span>
                  </CardHeader>

                  <div className="relative flex-1 flex flex-col justify-center min-h-[140px]">
                    <CardContent className={`p-0 pt-4 flex-1 flex flex-col justify-center space-y-3 transition-all ${
                      !isPro ? "filter blur-sm select-none pointer-events-none opacity-25" : ""
                    }`}>
                      <div className="p-4 rounded-2xl bg-[#1a1a1a] border border-neutral-800">
                        <p className="text-sm text-neutral-200 leading-relaxed font-medium">
                          "{report.ai_summary || "Automated analysis indicates that token risk factors are actively monitored across on-chain security registries. Exercise due diligence before allocating capital."}"
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-neutral-500">
                        <Info className="h-3.5 w-3.5 text-[#00ff66] shrink-0" />
                        <span>Objective 2-sentence executive summary synthesized from raw DEX, contract & OSINT evidence.</span>
                      </div>
                    </CardContent>

                    {!isPro && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/75 backdrop-blur-[2px] rounded-2xl p-4 text-center space-y-2.5 z-10 border border-neutral-800">
                        <div className="h-9 w-9 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66]">
                          <Crown className="h-4 w-4" />
                        </div>
                        <div className="space-y-0.5 max-w-sm">
                          <h4 className="text-xs font-bold text-white">🔒 Upgrade to Pro to unlock this intelligence</h4>
                          <p className="text-[10px] text-neutral-400">
                            AI executive health summaries are reserved for Pro subscribers ($20 USDT/mo).
                          </p>
                        </div>
                        <Link href="/billing">
                          <Button size="sm" className="h-8 px-4 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-[11px] cursor-pointer shadow-lg shadow-[#00ff66]/20">
                            Upgrade to Pro
                          </Button>
                        </Link>
                      </div>
                    )}
                  </div>
                </Card>
              )
            })()}
          </div>

          {/* Top Risk Assessment Banner */}
          <div className={`p-6 sm:p-8 rounded-3xl bg-[#121212] border ${riskMeta.card} shadow-2xl space-y-5`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                    Token Investigation Report
                  </span>
                  <span className="text-[10px] bg-neutral-800 text-neutral-300 px-2 py-0.5 rounded-full border border-neutral-700">
                    {report.chain || "Solana"}
                  </span>
                </div>
                <h2 className="text-2xl font-black text-white tracking-tight mt-1">
                  {report.name || "Unknown Token"} <span className="text-neutral-500 font-mono text-base font-semibold">({report.symbol || "TOKEN"})</span>
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-mono text-neutral-400">
                    {report.ca}
                  </span>
                  <button
                    onClick={() => copyToClipboard(report.ca || "")}
                    className="text-neutral-500 hover:text-[#00ff66] transition-colors cursor-pointer"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-[#00ff66]" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>

              {/* Large Risk Badge, Watchlist, Trade & PDF Download */}
              <div className="flex flex-wrap items-center gap-3">
                <div className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl border text-sm font-black tracking-wider ${riskMeta.pill}`}>
                  <RiskIcon className="h-5 w-5" />
                  <span>RISK LEVEL: {riskLevel}</span>
                </div>

                <Link href={`/trading?ca=${encodeURIComponent(report.ca || "")}`}>
                  <Button
                    type="button"
                    className="h-11 px-4 rounded-2xl bg-[#00ff66] hover:bg-[#00e65c] text-black text-xs font-bold cursor-pointer transition-all flex items-center gap-2 no-print shadow-lg shadow-[#00ff66]/20"
                  >
                    <TrendingUp className="h-4 w-4 stroke-[2.5]" />
                    <span>Trade this Token</span>
                  </Button>
                </Link>

                <Button
                  type="button"
                  variant="outline"
                  onClick={handleAddToWatchlist}
                  disabled={addingToWatchlist || inWatchlist}
                  className="h-11 px-4 rounded-2xl border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black hover:border-[#00ff66] text-white text-xs font-bold cursor-pointer transition-all flex items-center gap-2 no-print shadow-lg"
                >
                  {addingToWatchlist ? (
                    <Loader2 className="h-4 w-4 animate-spin text-[#00ff66]" />
                  ) : inWatchlist ? (
                    <BookmarkCheck className="h-4 w-4 text-[#00ff66]" />
                  ) : (
                    <Bookmark className="h-4 w-4" />
                  )}
                  <span>{inWatchlist ? "Watching" : watchlistSuccessMsg || "Add to Watchlist"}</span>
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => window.print()}
                  className="h-11 px-4 rounded-2xl border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black hover:border-[#00ff66] text-white text-xs font-bold cursor-pointer transition-all flex items-center gap-2 no-print shadow-lg"
                >
                  <Download className="h-4 w-4" />
                  <span>Download PDF</span>
                </Button>
              </div>
            </div>

            {/* Risk Reasons Bullet List */}
            <div className="pt-4 border-t border-neutral-800 space-y-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider block">
                🚨 Evidence-Based Risk Flags:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                {report.risk?.reasons && report.risk.reasons.length > 0 ? (
                  report.risk.reasons.map((reason, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 flex items-start gap-2.5 text-xs text-neutral-300"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66] mt-1.5 shrink-0" />
                      <span>{reason}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-neutral-400 italic">No critical risk flags detected.</div>
                )}
              </div>
            </div>
          </div>

          {/* Mega-Module 1: Advanced Contract, Holder & LP Intelligence */}
          {(() => {
            const top10 = report.holder_intelligence?.top_10_percent ?? report.security?.top_10_holders_percent ?? null
            const holders = report.holder_intelligence?.holder_count ?? report.security?.holder_count ?? null
            const holderStatus = report.holder_intelligence?.status || (top10 !== null ? (top10 > 80 ? "Critical Danger" : top10 > 40 ? "Concentrated" : "Healthy") : "Unknown")

            const lpLocked = report.lp_intelligence?.is_locked ?? (report.security?.lp_locked ?? false)
            const lpPct = report.lp_intelligence?.lock_percent ?? report.security?.lp_lock_percent ?? (lpLocked ? 100 : 0)

            const devPct = report.dev_wallet_intelligence?.holds_percent ?? report.security?.dev_wallet_percent ?? 0
            const devStatus = report.dev_wallet_intelligence?.status || (devPct > 10 ? "High risk" : devPct > 5 ? "Moderate risk" : "Low risk")
            const creatorAddr = report.dev_wallet_intelligence?.creator_address || report.security?.creator_address
            const creatorAddrShort = report.dev_wallet_intelligence?.creator_address_short || (creatorAddr ? `${creatorAddr.slice(0, 4)}...${creatorAddr.slice(-4)}` : null)

            return (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 1. Holder Concentration Card */}
                <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden flex flex-col justify-between">
                  <CardHeader className="p-6 border-b border-neutral-800">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                        <Users className="h-4 w-4 text-[#00ff66]" />
                        <span>Holder Concentration</span>
                      </CardTitle>
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${top10 !== null && top10 > 80
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                        : top10 !== null && top10 > 40
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          : "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                        }`}>
                        {holderStatus}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6 space-y-4">
                    <div>
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Top 10 Holders Control
                      </span>
                      <div className="text-3xl font-black text-white mt-1">
                        {top10 !== null ? `${top10.toFixed(1)}%` : "N/A"}
                      </div>
                    </div>
                    <div className="w-full bg-neutral-900 rounded-full h-2 overflow-hidden border border-neutral-800">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${top10 !== null && top10 > 80
                          ? "bg-rose-500"
                          : top10 !== null && top10 > 40
                            ? "bg-amber-400"
                            : "bg-[#00ff66]"
                          }`}
                        style={{ width: `${Math.min(top10 || 0, 100)}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
                      <span>Total Unique Holders</span>
                      <span className="text-white font-mono font-bold">
                        {holders ? holders.toLocaleString() : "N/A"}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                {/* 2. Liquidity Pool Lock Card */}
                <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden flex flex-col justify-between">
                  <CardHeader className="p-6 border-b border-neutral-800">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                        <Lock className="h-4 w-4 text-[#00ff66]" />
                        <span>Liquidity Pool (LP)</span>
                      </CardTitle>
                      {lpLocked ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                          <Check className="h-3 w-3" /> Locked (Safe)
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                          <AlertTriangle className="h-3 w-3" /> Unlocked (Risky)
                        </span>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="p-6 space-y-4">
                    <div>
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        LP Burn / Lock Ratio
                      </span>
                      <div className={`text-3xl font-black mt-1 ${lpLocked ? "text-[#00ff66]" : "text-rose-400"}`}>
                        {lpPct !== null && lpPct !== undefined ? `${lpPct.toFixed(1)}%` : (lpLocked ? "100.0%" : "0.0%")}
                      </div>
                    </div>
                    <div className="w-full bg-neutral-900 rounded-full h-2 overflow-hidden border border-neutral-800">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${lpLocked ? "bg-[#00ff66]" : "bg-rose-500"}`}
                        style={{ width: `${Math.min(lpPct || (lpLocked ? 100 : 0), 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-neutral-400 leading-relaxed">
                      {lpLocked
                        ? "DEX liquidity pair tokens are burned or secured in a lock contract."
                        : "Liquidity is NOT locked. Deployer could pull liquidity pool at any time."}
                    </p>
                  </CardContent>
                </Card>

                {/* 3. Developer Wallet Card */}
                <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden flex flex-col justify-between">
                  <CardHeader className="p-6 border-b border-neutral-800">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                        <Code2 className="h-4 w-4 text-[#00ff66]" />
                        <span>Dev Wallet</span>
                      </CardTitle>
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${devPct > 10
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                        : devPct > 5
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          : "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                        }`}>
                        {devStatus}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6 space-y-4">
                    <div>
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Developer Holding
                      </span>
                      <div className={`text-3xl font-black mt-1 ${devPct > 10 ? "text-rose-400" : devPct > 5 ? "text-amber-400" : "text-[#00ff66]"}`}>
                        {devPct !== null && devPct !== undefined ? `${devPct.toFixed(1)}%` : "0.0%"}
                      </div>
                    </div>
                    <div className="w-full bg-neutral-900 rounded-full h-2 overflow-hidden border border-neutral-800">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${devPct > 10 ? "bg-rose-500" : devPct > 5 ? "bg-amber-400" : "bg-[#00ff66]"
                          }`}
                        style={{ width: `${Math.min(devPct || 0, 100)}%` }}
                      />
                    </div>
                    {creatorAddr ? (
                      <div className="p-2.5 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-between text-xs">
                        <span className="font-mono text-neutral-300 truncate max-w-[170px]" title={creatorAddr}>
                          {creatorAddrShort || creatorAddr}
                        </span>
                        <button
                          onClick={() => copyCreatorToClipboard(creatorAddr)}
                          className="text-neutral-400 hover:text-[#00ff66] transition-colors cursor-pointer p-1"
                          title="Copy Deployer Address"
                        >
                          {copiedCreator ? <Check className="h-3.5 w-3.5 text-[#00ff66]" /> : <Copy className="h-3.5 w-3.5" />}
                        </button>
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 italic">Deployer address not detected or creator identity revoked.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            )
          })()}

          {/* Mega-Module 7: Deep Wallet Intelligence & Capital Trace Card */}
          {(() => {
            const trace = report.wallet_trace
            const creator = report.dev_wallet_intelligence?.creator_address || report.security?.creator_address || trace?.wallet_address
            const creatorShort = creator && creator !== "Unknown" ? `${creator.slice(0, 4)}...${creator.slice(-4)}` : "Unknown"
            const funder = trace?.funding_source || "Unknown"
            const funderShort = funder && funder !== "Unknown" ? `${funder.slice(0, 4)}...${funder.slice(-4)}` : "Unknown"
            const fundingEntity = trace?.funding_entity || "Unknown"
            const isCex = trace?.is_cex_funded || false
            const isFresh = trace?.is_fresh_funding_wallet || false
            const outflowRisk = trace?.outflow_risk || "LOW"
            const outflowDetails = trace?.outflow_details || "No suspicious capital drain detected."

            return (
              <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden">
                <CardHeader className="p-6 border-b border-neutral-800 flex flex-row items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
                      <Search className="h-4 w-4" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                        <span>Wallet Intelligence &amp; Capital Trace</span>
                        <span className="text-[10px] bg-[#00ff66]/10 text-[#00ff66] px-2 py-0.5 rounded-full border border-[#00ff66]/30 font-mono">
                          Solana On-Chain
                        </span>
                      </CardTitle>
                    </div>
                  </div>

                  <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${
                    outflowRisk === "HIGH" || isFresh
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                      : isCex
                        ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                        : "bg-neutral-800 text-neutral-300 border-neutral-700"
                  }`}>
                    {isCex ? "CEX Verified" : isFresh ? "Sybil / Fresh Risk" : "Standard Wallet"}
                  </span>
                </CardHeader>

                <CardContent className="p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* 1. Developer Address */}
                    <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-2">
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Developer Address
                      </span>
                      {creator && creator !== "Unknown" ? (
                        <div className="flex items-center justify-between gap-2">
                          <a
                            href={`https://solscan.io/account/${creator}`}
                            target="_blank"
                            rel="noreferrer"
                            className="font-mono text-xs font-bold text-[#00ff66] hover:underline truncate inline-flex items-center gap-1"
                          >
                            <span>{creatorShort}</span>
                            <ExternalLink className="h-3 w-3 shrink-0" />
                          </a>
                          <button
                            type="button"
                            onClick={() => copyCreatorToClipboard(creator)}
                            className="text-neutral-500 hover:text-white transition-colors cursor-pointer p-1"
                            title="Copy Dev Address"
                          >
                            {copiedCreator ? <Check className="h-3 w-3 text-[#00ff66]" /> : <Copy className="h-3 w-3" />}
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-neutral-500 italic">Not detected</span>
                      )}
                    </div>

                    {/* 2. Funding Source */}
                    <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-2">
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Initial Funding Source
                      </span>
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <span className={`text-xs font-bold block ${
                            isCex ? "text-[#00ff66]" : isFresh ? "text-rose-400" : "text-white"
                          }`}>
                            {fundingEntity}
                          </span>
                          {funder && funder !== "Unknown" && (
                            <a
                              href={`https://solscan.io/account/${funder}`}
                              target="_blank"
                              rel="noreferrer"
                              className="font-mono text-[10px] text-neutral-500 hover:text-neutral-300 inline-flex items-center gap-1 mt-0.5"
                            >
                              <span>{funderShort}</span>
                              <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          )}
                        </div>
                        {trace?.initial_funding_sol ? (
                          <span className="text-[11px] font-mono font-bold text-neutral-300 bg-neutral-800 px-2 py-0.5 rounded-md">
                            +{trace.initial_funding_sol} SOL
                          </span>
                        ) : null}
                      </div>
                    </div>

                    {/* 3. Outflow & Capital Extraction Risk */}
                    <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-2">
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Outflow Risk Assessment
                      </span>
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                          outflowRisk === "HIGH"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                        }`}>
                          {outflowRisk} DUMP RISK
                        </span>
                      </div>
                      <p className="text-[11px] text-neutral-400 leading-tight">
                        {outflowDetails}
                      </p>
                    </div>
                  </div>

                  {/* Trace Analysis Banner */}
                  <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 flex items-start gap-3 text-xs">
                    <Info className="h-4 w-4 text-[#00ff66] shrink-0 mt-0.5" />
                    <div className="space-y-0.5">
                      <span className="font-bold text-white">Detective Intelligence Summary:</span>
                      <p className="text-neutral-400 text-[11px] leading-relaxed">
                        {trace?.risk_reason || "Wallet ancestry traced via genesis transaction on Solana RPC. Provides transparency against Sybil deployments and sudden developer capital extraction."}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })()}

          {/* Grid Cards: Market Data & Security Checks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Market Data Card */}
            <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden">
              <CardHeader className="p-6 border-b border-neutral-800">
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-[#00ff66]" />
                  <span>Market & Liquidity Metrics</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-1">
                    <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                      Price (USD)
                    </span>
                    <div className="text-xl font-bold text-white">
                      {formatPrice(report.market?.price_usd)}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-1">
                    <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                      Market Cap / FDV
                    </span>
                    <div className="text-xl font-bold text-white">
                      {formatNumber(report.market?.market_cap)}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-1">
                    <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                      DEX Liquidity
                    </span>
                    <div className="text-xl font-bold text-[#00ff66]">
                      {formatNumber(report.market?.liquidity_usd)}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-1">
                    <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                      24h Volume
                    </span>
                    <div className="text-xl font-bold text-white">
                      {formatNumber(report.market?.volume_24h)}
                    </div>
                  </div>
                </div>

                {report.market?.pair_url && (
                  <div className="pt-2">
                    <a
                      href={report.market.pair_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#00ff66] hover:underline"
                    >
                      <span>View Live Trading Pair on DexScreener</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 2. Security Checks Card */}
            <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden">
              <CardHeader className="p-6 border-b border-neutral-800">
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-[#00ff66]" />
                  <span>On-Chain Security Checks</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                <div className="divide-y divide-neutral-800">
                  {/* Mint Authority */}
                  <div className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Lock className="h-4 w-4 text-neutral-400" />
                      <div>
                        <span className="font-semibold text-white block">Mint Authority</span>
                        <span className="text-[11px] text-neutral-500">Fixed vs expandable supply</span>
                      </div>
                    </div>
                    {report.security?.mint_revoked === true ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                        <Check className="h-3 w-3" /> Revoked
                      </span>
                    ) : report.security?.mint_revoked === false ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                        <AlertTriangle className="h-3 w-3" /> Active (Inflation Risk)
                      </span>
                    ) : (
                      <span className="text-neutral-500 font-medium">Unknown</span>
                    )}
                  </div>

                  {/* Freeze Authority */}
                  <div className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Unlock className="h-4 w-4 text-neutral-400" />
                      <div>
                        <span className="font-semibold text-white block">Freeze Authority</span>
                        <span className="text-[11px] text-neutral-500">Ability to freeze holder tokens</span>
                      </div>
                    </div>
                    {report.security?.freeze_revoked === true ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                        <Check className="h-3 w-3" /> Revoked
                      </span>
                    ) : report.security?.freeze_revoked === false ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        <AlertTriangle className="h-3 w-3" /> Active (Can Freeze)
                      </span>
                    ) : (
                      <span className="text-neutral-500 font-medium">Unknown</span>
                    )}
                  </div>

                  {/* Top 10 Holder Concentration */}
                  <div className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-neutral-400" />
                      <div>
                        <span className="font-semibold text-white block">Top 10 Holders Share</span>
                        <span className="text-[11px] text-neutral-500">Supply centralization ratio</span>
                      </div>
                    </div>
                    <span className="text-sm font-bold font-mono text-white">
                      {report.security?.top_10_holders_percent !== null && report.security?.top_10_holders_percent !== undefined
                        ? `${report.security.top_10_holders_percent.toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </div>

                  {/* Total Holders */}
                  {report.security?.holder_count && (
                    <div className="py-3 flex items-center justify-between text-xs">
                      <span className="text-neutral-400">Total Unique Holders</span>
                      <span className="font-bold text-white font-mono">
                        {report.security.holder_count.toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>

                {/* External Explorer Button */}
                <div className="pt-2 flex items-center gap-3">
                  <a
                    href={`https://solscan.io/token/${report.ca}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-neutral-400 hover:text-white transition-colors"
                  >
                    <span>Inspect on Solscan</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Mega-Module 2: Project OSINT & Founder Research Card (Pro Gated) */}
          {(() => {
            const isPro = report.is_pro ?? isProUser
            const osintData = report.osint || report.project_osint
            const hasWebsite = Boolean(osintData?.website && osintData.website !== "Unknown" && osintData.has_official_website !== false)
            const hasTwitter = Boolean(osintData?.twitter && osintData.twitter !== "Unknown")
            const founderName = osintData?.founder && osintData.founder !== "Unknown" ? osintData.founder : "Unverified"
            const isAnon = Boolean(osintData?.is_anonymous_founder || founderName === "Unverified" || founderName.includes("Anonymous"))

            return (
              <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden relative">
                <CardHeader className="p-6 border-b border-neutral-800">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                      <Globe className="h-4 w-4 text-[#00ff66]" />
                      <span>Project OSINT</span>
                    </CardTitle>
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${hasWebsite
                      ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                      : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                      }`}>
                      {hasWebsite ? "Web Presence Verified" : "Unverified Web Presence"}
                    </span>
                  </div>
                </CardHeader>
                <div className="relative min-h-[180px]">
                  <CardContent className={`p-6 space-y-6 transition-all ${
                    !isPro ? "filter blur-sm select-none pointer-events-none opacity-25" : ""
                  }`}>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* 1. Official Website */}
                    <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-2">
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Website
                      </span>
                      {hasWebsite && osintData?.website ? (
                        <a
                          href={osintData.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-sm font-bold text-[#00ff66] hover:underline truncate max-w-full"
                        >
                          <Globe className="h-4 w-4 shrink-0" />
                          <span className="truncate">{osintData.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}</span>
                          <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                        </a>
                      ) : (
                        <div className="text-xs text-neutral-400 italic flex items-center gap-1.5">
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                          <span>No official website found</span>
                        </div>
                      )}
                    </div>

                    {/* 2. Official Twitter / X */}
                    <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-2">
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Twitter / X
                      </span>
                      {hasTwitter && osintData?.twitter ? (
                        <a
                          href={osintData.twitter}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-sm font-bold text-white hover:text-[#00ff66] transition-colors truncate max-w-full"
                        >
                          <Share2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                          <span className="truncate">{osintData.twitter.replace(/^https?:\/\/(?:www\.)?(?:twitter\.com|x\.com)\//, "@")}</span>
                          <ExternalLink className="h-3.5 w-3.5 shrink-0 text-neutral-500" />
                        </a>
                      ) : (
                        <div className="text-xs text-neutral-400 italic">No official Twitter/X detected</div>
                      )}
                    </div>

                    {/* 3. Founder / CEO Identification */}
                    <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 space-y-2">
                      <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                        Founder / Executive
                      </span>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-[#00ff66] shrink-0" />
                        <span className="text-sm font-bold text-white">
                          {founderName}
                        </span>
                        {isAnon && (
                          <span className="text-[10px] bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full border border-neutral-700">
                            Anon Team
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Additional Social Links & OSINT Evidence Sources */}
                  <div className="pt-2 border-t border-neutral-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    {/* Social Chips */}
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-neutral-500 font-semibold">Community:</span>
                      {osintData?.telegram && (
                        <a
                          href={osintData.telegram}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-800 text-[11px] font-medium transition-colors"
                        >
                          Telegram <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                      {osintData?.discord && (
                        <a
                          href={osintData.discord}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-800 text-[11px] font-medium transition-colors"
                        >
                          Discord <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                      {osintData?.github && (
                        <a
                          href={osintData.github}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-800 text-[11px] font-medium transition-colors"
                        >
                          GitHub <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                      {!osintData?.telegram && !osintData?.discord && !osintData?.github && (
                        <span className="text-neutral-500 italic">No secondary socials discovered</span>
                      )}
                    </div>

                    {/* Evidence Sources */}
                    {osintData?.evidence_sources && osintData.evidence_sources.length > 0 && (
                      <div className="flex items-center gap-1.5 text-neutral-400 text-[11px]">
                        <span className="text-neutral-500">Sources:</span>
                        <span>{osintData.evidence_sources.slice(0, 3).join(", ")}</span>
                      </div>
                    )}
                  </div>
                </CardContent>

                {!isPro && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/75 backdrop-blur-[2px] rounded-b-3xl p-6 text-center space-y-3 z-10 border-t border-neutral-800">
                    <div className="h-10 w-10 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66]">
                      <Crown className="h-5 w-5" />
                    </div>
                    <div className="space-y-1 max-w-md">
                      <h4 className="text-sm font-bold text-white">🔒 Upgrade to Pro to unlock this intelligence</h4>
                      <p className="text-xs text-neutral-400">
                        Automated website scraping, social media verification, and founder identity OSINT are reserved for Pro subscribers ($20 USDT/mo).
                      </p>
                    </div>
                    <Link href="/billing">
                      <Button size="sm" className="h-9 px-5 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20">
                        Upgrade to Pro
                      </Button>
                    </Link>
                  </div>
                )}
                </div>
              </Card>
            )
          })()}

          {/* Evidence Footer */}
          <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-neutral-400">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#00ff66]" />
              <span>Evidence Sources: <strong>DexScreener API</strong>, <strong>GoPlus Security</strong>, <strong>DuckDuckGo OSINT</strong></span>
            </div>
            <div className="text-[11px] text-neutral-500">
              Timestamp: {report.timestamp_utc} · Preliminary automated scan, not financial advice.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
