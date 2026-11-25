"use client"

import React, { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCheck,
  Pause,
  Play,
  RefreshCw,
  Trash2,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react"
import { api, isSuperAdmin } from "@/lib/api"

interface PerformanceAlertsPanelProps {
  refreshTrigger?: number
}

function formatPrice(val: number | null | undefined): string {
  if (val === null || val === undefined || Number.isNaN(val)) return "—"
  if (val === 0) return "$0"
  if (val < 0.0001) return `$${val.toExponential(4)}`
  if (val < 1) return `$${val.toFixed(6)}`
  return `$${val.toLocaleString(undefined, { maximumFractionDigits: 4 })}`
}

export function PerformanceAlertsPanel({ refreshTrigger = 0 }: PerformanceAlertsPanelProps) {
  const [monitoredTokens, setMonitoredTokens] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [popupAlerts, setPopupAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [checkingNow, setCheckingNow] = useState<boolean>(false)
  const [chainFilter, setChainFilter] = useState<string>("")
  const [typeFilter, setTypeFilter] = useState<string>("")
  const [tokenFilter, setTokenFilter] = useState<string>("")
  const seenAlertIdsRef = useRef<Set<string>>(new Set())
  const initializedRef = useRef<boolean>(false)

  const loadData = useCallback(async () => {
    try {
      const [monRes, alertRes] = await Promise.all([
        api.getMonitoredTokens(),
        api.getPerformanceAlerts({
          blockchain: chainFilter || undefined,
          alert_type: typeFilter || undefined,
          token: tokenFilter || undefined,
          limit: 100,
        }),
      ])
      setMonitoredTokens(monRes.items || [])
      const fetchedAlerts = alertRes.alerts || []
      setAlerts(fetchedAlerts)
      setUnreadCount(alertRes.unread_count || 0)

      if (!initializedRef.current) {
        fetchedAlerts.forEach((a: any) => seenAlertIdsRef.current.add(a.alert_id))
        initializedRef.current = true
      } else {
        const newlyArrived = fetchedAlerts.filter(
          (a: any) => !a.read_status && !seenAlertIdsRef.current.has(a.alert_id)
        )
        if (newlyArrived.length > 0) {
          newlyArrived.forEach((a: any) => seenAlertIdsRef.current.add(a.alert_id))
          setPopupAlerts((prev) => [...newlyArrived, ...prev].slice(0, 4))
        }
      }
    } catch {
      // Fail gracefully if user is unauthenticated or endpoint temporarily unavailable
    } finally {
      setLoading(false)
    }
  }, [chainFilter, typeFilter, tokenFilter])

  useEffect(() => {
    loadData()
  }, [loadData, refreshTrigger])

  // Real-time SSE stream + authenticated polling fallback (15s)
  useEffect(() => {
    let es: EventSource | null = null
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    try {
      es = new EventSource(`${baseUrl}/api/scanner/performance-alerts/stream`, {
        withCredentials: true,
      })
      es.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          if (parsed?.type === "performance_alerts" && Array.isArray(parsed.alerts)) {
            const fresh = parsed.alerts.filter((a: any) => !seenAlertIdsRef.current.has(a.alert_id))
            if (fresh.length > 0) {
              fresh.forEach((a: any) => seenAlertIdsRef.current.add(a.alert_id))
              setPopupAlerts((prev) => [...fresh, ...prev].slice(0, 4))
              loadData()
            }
          }
        } catch {
          // ignore keepalive parse errors
        }
      }
      es.onerror = () => {
        es?.close()
      }
    } catch {
      // Fallback to polling
    }

    const interval = setInterval(() => {
      loadData()
    }, 15000)

    return () => {
      es?.close()
      clearInterval(interval)
    }
  }, [loadData])

  const handleCheckNow = async () => {
    setCheckingNow(true)
    try {
      await api.checkMonitoredTokensNow()
      await loadData()
    } finally {
      setCheckingNow(false)
    }
  }

  const handleToggleStatus = async (item: any) => {
    const nextStatus = item.monitoring_status === "active" ? "paused" : "active"
    await api.updateMonitoredToken(item.monitoring_id, { monitoring_status: nextStatus })
    await loadData()
  }

  const handleDelete = async (monitoringId: string) => {
    await api.deleteMonitoredToken(monitoringId)
    await loadData()
  }

  const handleMarkRead = async (alertId: string) => {
    await api.markPerformanceAlertRead(alertId)
    setPopupAlerts((prev) => prev.filter((p) => p.alert_id !== alertId))
    await loadData()
  }

  const handleMarkAllRead = async () => {
    await api.markAllPerformanceAlertsRead()
    setPopupAlerts([])
    await loadData()
  }

  return (
    <div className="space-y-6">
      {/* Non-blocking Floating Milestone Popup Notifications */}
      {popupAlerts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
          {popupAlerts.map((alert) => {
            const isPositive = alert.alert_type === "positive_milestone"
            return (
              <div
                key={alert.alert_id}
                className={`pointer-events-auto rounded-xl border p-4 shadow-2xl backdrop-blur-md transition-all ${
                  isPositive
                    ? "bg-emerald-950/95 border-emerald-500/40 text-emerald-50"
                    : "bg-rose-950/95 border-rose-500/40 text-rose-50"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {isPositive ? (
                      <TrendingUp className="w-5 h-5 text-emerald-400 shrink-0" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-rose-400 shrink-0" />
                    )}
                    <div>
                      <p className="text-sm font-semibold">
                        {alert.token_symbol} ({alert.blockchain})
                      </p>
                      <p className="text-xs opacity-90 mt-0.5">{alert.message}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setPopupAlerts((prev) => prev.filter((p) => p.alert_id !== alert.alert_id))}
                    className="text-slate-400 hover:text-white"
                    aria-label="Dismiss notification"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px] opacity-80">
                  <span>
                    {formatPrice(alert.observed_price)} ({alert.observed_multiple.toFixed(2)}x /{" "}
                    {alert.observed_percentage_change >= 0 ? "+" : ""}
                    {alert.observed_percentage_change.toFixed(1)}%)
                  </span>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/investigate?ca=${encodeURIComponent(alert.contract_address)}`}
                      className="underline hover:text-white"
                    >
                      View Details
                    </Link>
                    <button onClick={() => handleMarkRead(alert.alert_id)} className="underline hover:text-white">
                      Mark Read
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Disclaimer Banner */}
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-200 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong>Unrealized Price Performance:</strong> Multiples and percentage changes are calculated against each
          token&apos;s validated market price at scan/monitoring activation, not realized trading profit.
        </span>
      </div>

      {/* Monitored Tokens Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-semibold text-white">Monitored Tokens ({monitoredTokens.length})</h3>
          </div>
          <button
            onClick={handleCheckNow}
            disabled={checkingNow}
            className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-3 py-1.5 text-xs font-medium text-cyan-300 hover:bg-cyan-500/20 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checkingNow ? "animate-spin" : ""}`} />
            {checkingNow ? "Refreshing..." : "Refresh Live Prices"}
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-slate-400">Loading monitored tokens...</p>
        ) : monitoredTokens.length === 0 ? (
          <p className="text-sm text-slate-400">
            No tokens are currently monitored. Scan a token in{" "}
            <Link href={isSuperAdmin() ? "/admin/investigate" : "/owner/investigate"} className="text-cyan-400 underline">
              Token Investigator
            </Link>{" "}
            and click <strong>Monitor Token</strong> to track 2x, 4x, 5x, 10x milestones and downside alerts.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 text-slate-400 uppercase">
                <tr>
                  <th className="py-2 pr-3">Token</th>
                  <th className="py-2 pr-3">Chain</th>
                  <th className="py-2 pr-3">Baseline Price</th>
                  <th className="py-2 pr-3">Current Price</th>
                  <th className="py-2 pr-3">Performance</th>
                  <th className="py-2 pr-3">High / Drawdown</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {monitoredTokens.map((item) => {
                  const pct = Number(item.percentage_change || 0)
                  const mult = Number(item.current_multiple || 1)
                  const dd = Number(item.drawdown_from_high_pct || 0)
                  return (
                    <tr key={item.monitoring_id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 pr-3">
                        <div className="font-medium text-white">
                          {item.token_symbol} <span className="text-slate-400 font-normal">({item.token_name})</span>
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono truncate max-w-[160px]">
                          {item.contract_address}
                        </div>
                      </td>
                      <td className="py-2.5 pr-3 uppercase text-[11px] text-slate-300">{item.blockchain}</td>
                      <td className="py-2.5 pr-3">
                        <div>{formatPrice(item.baseline_price)}</div>
                        <div className="text-[10px] text-slate-500">
                          {new Date(item.baseline_timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="py-2.5 pr-3">
                        <div>{formatPrice(item.current_price)}</div>
                        <div className="text-[10px] text-slate-500">
                          {item.data_freshness !== "live" ? (
                            <span className="text-amber-400">Delayed ({item.data_freshness})</span>
                          ) : (
                            <span>{item.data_source}</span>
                          )}
                        </div>
                      </td>
                      <td className="py-2.5 pr-3">
                        <span className={pct >= 0 ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                          {mult.toFixed(2)}x ({pct >= 0 ? "+" : ""}
                          {pct.toFixed(1)}%)
                        </span>
                      </td>
                      <td className="py-2.5 pr-3">
                        <div>{formatPrice(item.highest_observed_price)}</div>
                        <div className="text-[10px] text-slate-400">Drawdown: -{dd.toFixed(1)}%</div>
                      </td>
                      <td className="py-2.5 pr-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${
                            item.monitoring_status === "active"
                              ? "bg-emerald-500/20 text-emerald-300"
                              : "bg-slate-700 text-slate-300"
                          }`}
                        >
                          {item.monitoring_status}
                        </span>
                      </td>
                      <td className="py-2.5 text-right space-x-2">
                        <button
                          onClick={() => handleToggleStatus(item)}
                          className="inline-flex items-center rounded border border-slate-700 px-2 py-1 text-[11px] hover:bg-slate-800"
                          title={item.monitoring_status === "active" ? "Pause" : "Resume"}
                        >
                          {item.monitoring_status === "active" ? (
                            <Pause className="w-3 h-3" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(item.monitoring_id)}
                          className="inline-flex items-center rounded border border-rose-500/30 px-2 py-1 text-[11px] text-rose-400 hover:bg-rose-500/10"
                          title="Stop & Remove"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Persistent Notification Centre */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-violet-400" />
            <h3 className="text-base font-semibold text-white">
              Performance Notification Centre
              {unreadCount > 0 && (
                <span className="ml-2 rounded-full bg-violet-600 px-2 py-0.5 text-xs text-white">
                  {unreadCount} unread
                </span>
              )}
            </h3>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
            >
              <CheckCheck className="w-3.5 h-3.5" /> Mark All Read
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
          <input
            type="text"
            placeholder="Filter by token symbol or CA..."
            value={tokenFilter}
            onChange={(e) => setTokenFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white placeholder-slate-500"
          />
          <select
            value={chainFilter}
            onChange={(e) => setChainFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white"
          >
            <option value="">All Blockchains</option>
            <option value="solana">Solana</option>
            <option value="ethereum">Ethereum</option>
            <option value="base">Base</option>
            <option value="bsc">BSC</option>
            <option value="arbitrum">Arbitrum</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white"
          >
            <option value="">All Alert Types</option>
            <option value="positive_milestone">Positive Milestones (2x, 4x, 5x...)</option>
            <option value="negative_decline">Negative Declines (-20%, -50%...)</option>
            <option value="drawdown_alert">High-Water-Mark Drawdown</option>
          </select>
        </div>

        {alerts.length === 0 ? (
          <p className="text-sm text-slate-400">No performance alerts recorded yet.</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {alerts.map((alert) => {
              const isPositive = alert.alert_type === "positive_milestone"
              return (
                <div
                  key={alert.alert_id}
                  className={`rounded-lg border p-3 text-xs flex flex-wrap items-center justify-between gap-2 ${
                    alert.read_status
                      ? "border-slate-800 bg-slate-950/50 text-slate-400"
                      : "border-violet-500/40 bg-violet-950/20 text-slate-100"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {isPositive ? (
                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-rose-400" />
                      )}
                      <span className="font-semibold text-white">{alert.message}</span>
                      <span className="uppercase text-[10px] rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">
                        {alert.blockchain}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Baseline: {formatPrice(alert.baseline_price)} → Observed: {formatPrice(alert.observed_price)} (
                      {alert.observed_multiple.toFixed(2)}x / {alert.observed_percentage_change >= 0 ? "+" : ""}
                      {alert.observed_percentage_change.toFixed(1)}%) • Source: {alert.provider} •{" "}
                      {new Date(alert.event_timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/investigate?ca=${encodeURIComponent(alert.contract_address)}`}
                      className="rounded border border-slate-700 px-2 py-1 text-[11px] text-cyan-300 hover:bg-slate-800"
                    >
                      Inspect
                    </Link>
                    {!alert.read_status && (
                      <button
                        onClick={() => handleMarkRead(alert.alert_id)}
                        className="rounded border border-violet-500/40 px-2 py-1 text-[11px] text-violet-300 hover:bg-violet-500/20"
                      >
                        Mark Read
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
