"use client"

import React, { useState, useEffect } from "react"
import {
  Bell,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Flame,
  TrendingDown,
  ShieldAlert,
  Loader2,
  ExternalLink,
  Clock,
  Radio,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api, ScannerAlertEvent, ScannerAlertRule } from "@/lib/api"

export function SmartAlertsHub() {
  const [rules, setRules] = useState<ScannerAlertRule[]>([])
  const [events, setEvents] = useState<ScannerAlertEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Form State
  const [ruleType, setRuleType] = useState("narrative_spike")
  const [targetEntity, setTargetEntity] = useState("Autonomous AI Agents")
  const [threshold, setThreshold] = useState("50")
  const [cooldown, setCooldown] = useState("60")

  const loadData = async () => {
    setLoading(true)
    try {
      const [rulesData, eventsData] = await Promise.all([
        api.getScannerAlertRules().catch(() => []),
        api.getScannerAlertEvents().catch(() => []),
      ])
      setRules(rulesData || [])
      setEvents(eventsData || [])
    } catch (err: any) {
      console.warn("Failed to load alerts:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!targetEntity.trim()) return
    setCreating(true)
    setError(null)
    setSuccessMsg(null)
    try {
      await api.createScannerAlertRule({
        rule_type: ruleType,
        target_entity: targetEntity.trim(),
        threshold: parseFloat(threshold) || 50,
        cooldown_minutes: parseInt(cooldown, 10) || 60,
      })
      setSuccessMsg("Alert rule created successfully.")
      setTimeout(() => setSuccessMsg(null), 3000)
      await loadData()
    } catch (err: any) {
      setError(err.message || "Failed to create rule.")
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await api.deleteScannerAlertRule(ruleId)
      setRules((prev) => prev.filter((r) => r.rule_id !== ruleId))
    } catch (err: any) {
      setError(err.message || "Failed to delete rule.")
    }
  }

  const handleMarkRead = async (eventId: string) => {
    try {
      await api.markScannerAlertRead(eventId)
      setEvents((prev) =>
        prev.map((ev) => (ev.event_id === eventId ? { ...ev, is_read: true } : ev))
      )
    } catch (err) {
      console.warn("Notice: Failed to mark alert read:", err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Bell className="h-4 w-4 text-rose-400" />
          Smart Surveillance &amp; Intelligence Alerts
        </h2>
        <p className="text-xs text-neutral-400">
          Set custom quantitative thresholds for emerging narrative spikes, unusual sentiment drops, and on-chain liquidity drain.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-800/60 text-xs text-emerald-300">
          {successMsg}
        </div>
      )}

      {/* Grid: Create Rule + Active Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Rule Form */}
        <div className="p-6 rounded-3xl bg-[#121212] border border-neutral-800 shadow-xl space-y-4">
          <div className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <Plus className="h-3.5 w-3.5 text-[#00ff66]" />
            Configure New Rule
          </div>

          <form onSubmit={handleCreateRule} className="space-y-4 text-xs">
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-neutral-400">Alert Trigger Condition</label>
              <select
                value={ruleType}
                onChange={(e) => setRuleType(e.target.value)}
                className="w-full h-10 px-3 bg-neutral-900 border border-neutral-800 rounded-2xl text-xs text-white focus:outline-none focus:border-[#00ff66]"
              >
                <option value="narrative_spike">Narrative Attention Surge (&gt; % growth)</option>
                <option value="sentiment_shift">Negative Sentiment Drop (&lt; score)</option>
                <option value="volume_surge">Social Discussion Volume Spike (&gt; %)</option>
                <option value="watchlist_drain">Watchlist Liquidity Drain (&gt; 20% drop)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-neutral-400">Target Entity or Category</label>
              <Input
                type="text"
                placeholder="e.g. 'Autonomous AI Agents', 'BONK', or 'all'"
                value={targetEntity}
                onChange={(e) => setTargetEntity(e.target.value)}
                className="h-10 bg-neutral-900 border-neutral-800 rounded-2xl text-xs text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-neutral-400">Threshold Value</label>
                <Input
                  type="number"
                  placeholder="50"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="h-10 bg-neutral-900 border-neutral-800 rounded-2xl text-xs text-white font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-neutral-400">Cooldown (mins)</label>
                <Input
                  type="number"
                  placeholder="60"
                  value={cooldown}
                  onChange={(e) => setCooldown(e.target.value)}
                  className="h-10 bg-neutral-900 border-neutral-800 rounded-2xl text-xs text-white font-mono"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={creating || !targetEntity.trim()}
              className="w-full h-10 bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer transition-all"
            >
              {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : null}
              Add Surveillance Rule
            </Button>
          </form>
        </div>

        {/* Active Rules List */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-[#121212] border border-neutral-800 shadow-xl space-y-4">
          <div className="text-xs font-bold uppercase tracking-wider text-white flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Radio className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
              Active Surveillance Rules ({rules.length})
            </span>
          </div>

          {loading && rules.length === 0 ? (
            <div className="h-32 flex items-center justify-center text-neutral-500 text-xs">
              <Loader2 className="h-4 w-4 animate-spin mr-2 text-[#00ff66]" />
              Loading configured alert rules...
            </div>
          ) : rules.length === 0 ? (
            <div className="p-6 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 text-center text-neutral-500 text-xs">
              No custom alert rules configured yet. Create one on the left to start automated surveillance.
            </div>
          ) : (
            <div className="space-y-2.5">
              {rules.map((r) => (
                <div
                  key={r.rule_id}
                  className="p-3.5 rounded-2xl bg-neutral-900/80 border border-neutral-800 flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">{r.target_entity}</span>
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-300">
                        {r.rule_type.replace("_", " ")}
                      </span>
                    </div>
                    <div className="text-[11px] text-neutral-400 font-mono mt-0.5">
                      Threshold: &ge; {r.threshold}% · Cooldown: {r.cooldown_minutes}m
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteRule(r.rule_id)}
                    className="p-2 rounded-xl text-neutral-500 hover:text-rose-400 hover:bg-neutral-800 transition-colors cursor-pointer"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Triggered Alert Events Feed */}
      <div className="p-6 rounded-3xl bg-[#121212] border border-neutral-800 shadow-xl space-y-4">
        <div className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-rose-400" />
          Recent Alert Surveillance Feed ({events.length})
        </div>

        {events.length === 0 ? (
          <div className="p-6 text-center rounded-2xl bg-neutral-900/60 text-neutral-500 text-xs">
            No triggered alert events recorded. All tracked entities within normal ranges.
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((ev) => {
              const isCrit = ev.severity === "critical"
              const isHigh = ev.severity === "high"

              return (
                <div
                  key={ev.event_id}
                  className={`p-4 rounded-2xl border transition-all space-y-2 ${
                    isCrit
                      ? "bg-rose-950/20 border-rose-800/80"
                      : isHigh
                      ? "bg-orange-950/20 border-orange-800/80"
                      : "bg-neutral-900/60 border-neutral-800"
                  } ${ev.is_read ? "opacity-60" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded-full ${
                          isCrit
                            ? "bg-rose-500 text-white"
                            : isHigh
                            ? "bg-orange-500 text-black"
                            : "bg-neutral-800 text-neutral-300"
                        }`}
                      >
                        {ev.severity}
                      </span>
                      <span className="text-xs font-bold text-white">{ev.title}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-mono text-neutral-500">
                        {ev.timestamp_utc}
                      </span>
                      {!ev.is_read && (
                        <button
                          onClick={() => handleMarkRead(ev.event_id)}
                          className="text-[11px] text-[#00ff66] hover:underline font-medium cursor-pointer"
                        >
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-neutral-300 leading-relaxed">{ev.message}</p>
                  <div className="text-[11px] text-neutral-400 font-mono">
                    Trigger Explanation: {ev.trigger_explanation}
                  </div>

                  {ev.supporting_sources && ev.supporting_sources.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1 border-t border-neutral-800/60">
                      {ev.supporting_sources.map((src, sIdx) => (
                        <a
                          key={sIdx}
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-neutral-400 hover:text-white inline-flex items-center gap-1 font-mono"
                        >
                          <span>{src.title}</span>
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
