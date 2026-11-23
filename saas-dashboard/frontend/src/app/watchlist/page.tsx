"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import {
  Bookmark,
  Trash2,
  Radar,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Plus,
  Loader2,
  RefreshCw,
  Copy,
  Check,
  Bell,
  TrendingDown,
  ShieldCheck,
  Search,
  ExternalLink
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
import { api, WatchlistItem, SecurityAlert } from "@/lib/api"

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([])
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Quick Add State
  const [newCa, setNewCa] = useState("")
  const [newTokenName, setNewTokenName] = useState("")
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)

  // Immediate Sweep State
  const [checkingNow, setCheckingNow] = useState(false)
  const [checkStatusMsg, setCheckStatusMsg] = useState<string | null>(null)

  // Copy helper
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [watchlistData, alertsData] = await Promise.all([
        api.getWatchlist().catch((err) => {
          console.warn("Failed to load watchlist:", err)
          return []
        }),
        api.getAlerts().catch((err) => {
          console.warn("Failed to load alerts:", err)
          return []
        })
      ])
      setItems(watchlistData || [])
      setAlerts(alertsData || [])
    } catch (err: any) {
      setError(err.message || "Failed to load watchlist monitoring data.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    const ca = newCa.trim()
    if (!ca) {
      setAddError("Please enter a Solana contract address.")
      return
    }

    setAdding(true)
    setAddError(null)

    try {
      await api.addToWatchlist(ca, newTokenName.trim() || undefined)
      setNewCa("")
      setNewTokenName("")
      await loadData()
    } catch (err: any) {
      setAddError(err.message || "Failed to add token to watchlist.")
    } finally {
      setAdding(false)
    }
  }

  const handleRemove = async (id: string) => {
    try {
      await api.removeFromWatchlist(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
    } catch (err: any) {
      alert("Failed to remove token: " + (err.message || "Unknown error"))
    }
  }

  const handleCheckNow = async () => {
    setCheckingNow(true)
    setCheckStatusMsg(null)
    try {
      const res = await api.triggerWatchlistCheck()
      setCheckStatusMsg(
        res.alerts_count > 0
          ? `⚠️ Sweep complete: ${res.alerts_count} new alert(s) triggered!`
          : `✅ Sweep complete: All ${items.length} token(s) healthy. No critical liquidity drops.`
      )
      await loadData()
      setTimeout(() => setCheckStatusMsg(null), 6000)
    } catch (err: any) {
      setCheckStatusMsg("Failed to run manual check: " + (err.message || "Unknown error"))
    } finally {
      setCheckingNow(false)
    }
  }

  const formatCurrency = (val?: number | null) => {
    if (val === null || val === undefined) return "--"
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: val < 0.01 ? 8 : 2
    }).format(val)
  }

  const formatDate = (isoStr?: string | null) => {
    if (!isoStr) return "--"
    try {
      const d = new Date(isoStr)
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      })
    } catch {
      return isoStr
    }
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full text-xs font-bold text-[#00ff66]">
            <Bookmark className="h-3.5 w-3.5" />
            Zoe Continuous Surveillance · 15-Minute Daemon
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white">
            Security Watchlist & Alerts
          </h1>
          <p className="text-xs text-neutral-400 max-w-2xl">
            Autonomous background intelligence. Tokens added here are monitored every 15 minutes for liquidity rug-pulls, LP drainage (&gt;20%), and price crashes.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={handleCheckNow}
            disabled={checkingNow || items.length === 0}
            className="h-11 px-5 rounded-full border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black hover:border-[#00ff66] text-white text-xs font-bold cursor-pointer transition-all flex items-center gap-2 shadow-lg"
          >
            {checkingNow ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-[#00ff66]" />
                <span>Sweeping Blockchain...</span>
              </>
            ) : (
              <>
                <Radar className="h-4 w-4 text-[#00ff66]" />
                <span>Check Watchlist Now</span>
              </>
            )}
          </Button>

          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={loadData}
            disabled={loading}
            className="h-11 w-11 rounded-full border-neutral-800 bg-[#121212] hover:bg-neutral-800 text-white cursor-pointer"
            title="Refresh Watchlist"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#00ff66]" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Immediate Check Status Notification */}
      {checkStatusMsg && (
        <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800 text-xs text-white flex items-center justify-between shadow-xl">
          <span className="font-semibold">{checkStatusMsg}</span>
          <button
            onClick={() => setCheckStatusMsg(null)}
            className="text-neutral-500 hover:text-white text-xs underline cursor-pointer ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Critical Alerts Banner Feed */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-rose-400">
            <Bell className="h-4 w-4 animate-bounce" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-rose-400">
              Active Security Alerts ({alerts.length})
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {alerts.slice(0, 4).map((alert) => (
              <div
                key={alert.id}
                className="p-5 rounded-3xl bg-rose-950/30 border border-rose-800/60 shadow-xl space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-xl bg-rose-900/50 border border-rose-700/60 flex items-center justify-center text-rose-400 shrink-0">
                      <TrendingDown className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-sm">
                        {alert.token_name || "Watched Token"}
                      </h3>
                      <p className="font-mono text-[11px] text-neutral-400">
                        {alert.contract_address.slice(0, 4)}...{alert.contract_address.slice(-4)}
                      </p>
                    </div>
                  </div>

                  <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full bg-rose-900/60 text-rose-300 border border-rose-700/50">
                    {alert.alert_type}
                  </span>
                </div>

                <p className="text-xs text-rose-200/90 leading-relaxed font-medium">
                  {alert.message}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-rose-900/40 text-[11px] text-neutral-400">
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3 w-3 text-neutral-500" />
                    <span>{formatDate(alert.created_at)}</span>
                  </div>

                  <Link
                    href={`/investigate?ca=${encodeURIComponent(alert.contract_address)}`}
                    className="inline-flex items-center gap-1 text-[#00ff66] hover:underline font-bold text-xs"
                  >
                    <span>Investigate</span>
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Token To Watchlist Form */}
      <div className="bg-[#121212] border border-neutral-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="flex items-center gap-2 text-white">
          <Plus className="h-4 w-4 text-[#00ff66]" />
          <h2 className="text-base font-bold tracking-tight">Add Token to Continuous Surveillance</h2>
        </div>

        <form onSubmit={handleAdd} className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div className="relative md:col-span-7">
            <Search className="absolute left-4 top-3.5 h-4 w-4 text-neutral-500" />
            <Input
              type="text"
              placeholder="Paste Solana contract address (e.g. DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263)..."
              value={newCa}
              onChange={(e) => setNewCa(e.target.value)}
              className="h-12 pl-11 pr-4 bg-neutral-900 border-neutral-700 rounded-full text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66]"
            />
          </div>

          <div className="md:col-span-3">
            <Input
              type="text"
              placeholder="Token Name (optional)..."
              value={newTokenName}
              onChange={(e) => setNewTokenName(e.target.value)}
              className="h-12 px-5 bg-neutral-900 border-neutral-700 rounded-full text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66]"
            />
          </div>

          <div className="md:col-span-2">
            <Button
              type="submit"
              disabled={adding}
              className="w-full h-12 bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer transition-all flex items-center justify-center gap-2"
            >
              {adding ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <Bookmark className="h-4 w-4" />
                  <span>Add to Watchlist</span>
                </>
              )}
            </Button>
          </div>
        </form>

        {addError && (
          <p className="text-xs text-rose-400 font-medium pl-2">{addError}</p>
        )}
      </div>

      {/* Watchlist Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bookmark className="h-4 w-4 text-[#00ff66]" />
            <h2 className="text-lg font-bold text-white tracking-tight">Watched Tokens</h2>
            <span className="text-xs bg-neutral-900 text-neutral-400 px-2.5 py-0.5 rounded-full border border-neutral-800 font-mono">
              {items.length} Active
            </span>
          </div>
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
                  Initial Liquidity
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Initial Price
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Alerts &amp; Status
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Added Date
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider text-right">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {loading && items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center text-neutral-500">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin text-[#00ff66]" />
                      <span className="text-xs">Loading surveillance watchlist...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : items.length > 0 ? (
                items.map((item) => {
                  const shortCa = `${item.contract_address.slice(0, 4)}...${item.contract_address.slice(-4)}`
                  const matchingAlert = alerts.find(
                    (a) => a.contract_address.toLowerCase() === item.contract_address.toLowerCase()
                  )

                  return (
                    <TableRow
                      key={item.id}
                      className="border-b border-neutral-800/60 hover:bg-neutral-900/60 transition-colors"
                    >
                      {/* Token Name */}
                      <TableCell className="py-4 px-5 text-xs">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66] font-bold text-xs">
                            {item.token_name ? item.token_name[0] : "T"}
                          </div>
                          <div>
                            <span className="font-bold text-white block">
                              {item.token_name || "Unknown Token"}
                            </span>
                            <span className="text-[10px] text-neutral-500 uppercase tracking-wider">
                              Solana
                            </span>
                          </div>
                        </div>
                      </TableCell>

                      {/* Contract Address */}
                      <TableCell className="py-4 px-5 text-xs font-mono">
                        <div className="inline-flex items-center gap-1.5 bg-neutral-900 border border-neutral-800 px-2.5 py-1 rounded-full text-neutral-300">
                          <span>{shortCa}</span>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(item.contract_address, item.id)}
                            className="text-neutral-500 hover:text-[#00ff66] transition-colors cursor-pointer"
                            title="Copy Contract Address"
                          >
                            {copiedId === item.id ? (
                              <Check className="h-3 w-3 text-[#00ff66]" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </button>
                        </div>
                      </TableCell>

                      {/* Initial Liquidity */}
                      <TableCell className="py-4 px-5 text-xs font-mono text-white">
                        {formatCurrency(item.initial_liquidity)}
                      </TableCell>

                      {/* Initial Price */}
                      <TableCell className="py-4 px-5 text-xs font-mono text-neutral-300">
                        {formatCurrency(item.initial_price)}
                      </TableCell>

                      {/* Alerts & Risk Status Column */}
                      <TableCell className="py-4 px-5 text-xs">
                        {matchingAlert ? (
                          <div 
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse cursor-help"
                            title={matchingAlert.message}
                          >
                            <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-rose-400" />
                            <span className="truncate max-w-[110px]">
                              {matchingAlert.alert_type === "liquidity_drop" ? "Liquidity Drop" : "Risk Alert"}
                            </span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                            <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-[#00ff66]" />
                            <span>Healthy</span>
                          </div>
                        )}
                      </TableCell>

                      {/* Added Date */}
                      <TableCell className="py-4 px-5 text-xs text-neutral-400">
                        {formatDate(item.created_at)}
                      </TableCell>

                      {/* Actions */}
                      <TableCell className="py-4 px-5 text-xs text-right">
                        <div className="inline-flex items-center gap-2">
                          <Link
                            href={`/investigate?ca=${encodeURIComponent(item.contract_address)}`}
                          >
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              className="h-8 px-3 rounded-full border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black hover:border-[#00ff66] text-white text-[11px] font-bold cursor-pointer transition-all flex items-center gap-1.5"
                            >
                              <Radar className="h-3.5 w-3.5" />
                              <span>Scan</span>
                            </Button>
                          </Link>

                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={() => handleRemove(item.id)}
                            className="h-8 w-8 p-0 rounded-full text-neutral-500 hover:text-rose-400 hover:bg-rose-950/30 cursor-pointer transition-colors"
                            title="Remove from Watchlist"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center text-neutral-500 text-xs">
                    <div className="space-y-2">
                      <Bookmark className="h-6 w-6 text-neutral-600 mx-auto" />
                      <p className="font-semibold text-neutral-400">No tokens in your surveillance watchlist</p>
                      <p className="text-[11px] text-neutral-600 max-w-sm mx-auto">
                        Add a token contract above or click &ldquo;Add to Watchlist&rdquo; directly on any Intelligence Scanner report.
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

