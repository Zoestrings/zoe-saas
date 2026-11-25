"use client"

import React, { useEffect, useState } from "react"
import { Activity, AlertTriangle, RefreshCw, ShieldCheck, TrendingDown, TrendingUp } from "lucide-react"
import { api } from "@/lib/api"

export function AdminPerformanceCard() {
  const [data, setData] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [maxFree, setMaxFree] = useState<number>(5)
  const [maxPro, setMaxPro] = useState<number>(50)
  const [pollSec, setPollSec] = useState<number>(300)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  const loadOverview = async () => {
    setLoading(true)
    try {
      const res = await api.getAdminPerformanceOverview()
      setData(res)
      if (res?.settings) {
        setMaxFree(res.settings.max_monitored_free ?? 5)
        setMaxPro(res.settings.max_monitored_pro ?? 50)
        setPollSec(res.settings.polling_interval_seconds ?? 300)
      }
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOverview()
  }, [])

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setSaveMsg(null)
    try {
      await api.updateAdminPerformanceSettings({
        max_monitored_free: Number(maxFree),
        max_monitored_pro: Number(maxPro),
        polling_interval_seconds: Number(pollSec),
      })
      setSaveMsg("Platform monitoring defaults saved.")
      await loadOverview()
    } catch (err: any) {
      setSaveMsg(err?.message || "Failed to update settings")
    } finally {
      setSaving(false)
    }
  }

  const summary = data?.summary || {}
  const recentAlerts = data?.recent_alerts || []

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/75 p-5 space-y-4 mt-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-base font-semibold text-white">Global Token Performance Monitoring</h3>
            <p className="text-xs text-slate-400">
              Cross-tenant monitoring health, milestone activity &amp; platform defaults (Super Admin audited)
            </p>
          </div>
        </div>
        <button
          onClick={loadOverview}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-800"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
          <div className="text-slate-400">Total Monitored</div>
          <div className="text-lg font-bold text-white mt-1">{summary.total_monitored_tokens ?? 0}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
          <div className="text-slate-400">Active Monitors</div>
          <div className="text-lg font-bold text-emerald-400 mt-1">{summary.active_monitored_tokens ?? 0}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
          <div className="text-slate-400 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Positive Alerts
          </div>
          <div className="text-lg font-bold text-emerald-400 mt-1">{summary.total_positive_alerts ?? 0}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
          <div className="text-slate-400 flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" /> Negative Alerts
          </div>
          <div className="text-lg font-bold text-rose-400 mt-1">{summary.total_negative_alerts ?? 0}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
          <div className="text-slate-400 flex items-center gap-1">
            {summary.provider_health === "healthy" ? (
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            )}
            Provider Health
          </div>
          <div className="text-sm font-semibold uppercase text-white mt-1.5">
            {summary.provider_health || "healthy"}
          </div>
        </div>
      </div>

      {/* Platform Defaults Form */}
      <form onSubmit={handleSaveSettings} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end pt-2 border-t border-slate-800">
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Max Monitored (Free)</label>
          <input
            type="number"
            min={1}
            max={500}
            value={maxFree}
            onChange={(e) => setMaxFree(Number(e.target.value))}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white"
          />
        </div>
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Max Monitored (Pro)</label>
          <input
            type="number"
            min={1}
            max={2000}
            value={maxPro}
            onChange={(e) => setMaxPro(Number(e.target.value))}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white"
          />
        </div>
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Polling Interval (sec)</label>
          <input
            type="number"
            min={60}
            max={3600}
            value={pollSec}
            onChange={(e) => setPollSec(Number(e.target.value))}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white"
          />
        </div>
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-cyan-400 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Platform Defaults"}
        </button>
      </form>
      {saveMsg && <p className="text-xs text-cyan-300">{saveMsg}</p>}

      {recentAlerts.length > 0 && (
        <div className="pt-2 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-300 mb-2">Recent Global Performance Alerts</h4>
          <div className="space-y-1.5 max-h-48 overflow-y-auto text-xs">
            {recentAlerts.slice(0, 8).map((a: any) => (
              <div key={a.alert_id} className="flex items-center justify-between rounded bg-slate-950/60 px-3 py-1.5">
                <span className="text-slate-200">
                  <strong>{a.token_symbol}</strong> ({a.blockchain}) — {a.message}
                </span>
                <span className="text-[11px] text-slate-500 font-mono">tenant:{String(a.user_id).slice(0, 8)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
