"use client"

import * as React from "react"
import { useState, useEffect } from "react"
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
  FileSearch
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
  const [copiedHistoryId, setCopiedHistoryId] = useState<string | null>(null)

  // Investigation History state
  const [history, setHistory] = useState<SavedInvestigation[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const data = await api.getInvestigations()
      setHistory(data || [])
    } catch (err) {
      console.error("Failed to load investigation history:", err)
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
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
    // Smooth scroll to report view
    window.scrollTo({ top: 0, behavior: "smooth" })
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

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div className="space-y-2">
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
      <div className="bg-[#121212] border border-neutral-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-4">
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
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 shrink-0 text-rose-400" />
          <div>
            <p className="font-bold">Investigation Scan Error</p>
            <p className="text-[11px] text-rose-300/90">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton Indicator */}
      {loading && (
        <div className="p-12 rounded-3xl bg-[#121212] border border-neutral-800 flex flex-col items-center justify-center text-center space-y-4">
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
        <div className="space-y-6">
          {/* Top Risk Assessment Banner */}
          <div className={`p-6 sm:p-8 rounded-3xl bg-[#121212] border ${riskMeta.card} shadow-2xl space-y-5`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                    Token Investigation Report
                  </span>
                  <span className="text-[10px] bg-neutral-800 text-neutral-300 px-2 py-0.5 rounded-full border border-neutral-700">
                    Solana
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

              {/* Large Risk Badge */}
              <div className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl border text-sm font-black tracking-wider ${riskMeta.pill}`}>
                <RiskIcon className="h-5 w-5" />
                <span>RISK LEVEL: {riskLevel}</span>
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

          {/* Evidence Footer */}
          <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-neutral-400">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#00ff66]" />
              <span>Evidence Sources: <strong>DexScreener API</strong>, <strong>GoPlus Solana Security</strong></span>
            </div>
            <div className="text-[11px] text-neutral-500">
              Timestamp: {report.timestamp_utc} · Preliminary automated scan, not financial advice.
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Recent Investigations Table */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-[#00ff66]" />
            <h2 className="text-lg font-bold text-white tracking-tight">Recent Investigations</h2>
            <span className="text-xs bg-neutral-900 text-neutral-400 px-2 py-0.5 rounded-full border border-neutral-800">
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
            Refresh History
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
                  Scanned At
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider text-right">
                  Action
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {historyLoading && history.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-neutral-500">
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

                      {/* View Report Action */}
                      <TableCell className="py-3.5 px-5 text-xs text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewSavedReport(item)}
                          className="h-8 px-3 rounded-full border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black hover:border-[#00ff66] text-white text-xs font-semibold cursor-pointer transition-all"
                        >
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          View Report
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-28 text-center text-neutral-500 text-xs">
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
    </div>
  )
}
