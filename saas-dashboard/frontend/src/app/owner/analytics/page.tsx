"use client"

import React, { useEffect, useState } from "react"
import { BarChart3, Download, RefreshCw } from "lucide-react"
import { api } from "@/lib/api"

export default function OwnerAnalyticsPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.getOwnerAnalytics()
      setData(res)
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const exportJson = () => {
    if (!data) return
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `zoe-owner-analytics-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const ov = data?.overview || {}

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-[#00ff66]" />
          <div>
            <h1 className="text-2xl font-bold text-white">Analytics &amp; Reports</h1>
            <p className="text-xs text-neutral-400">
              Tenant-scoped operational metrics · Source: {data?.source || "zoe_operational_database"} · Period:{" "}
              {data?.reporting_period || "all_time_tenant_scoped"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={load} disabled={loading} className="inline-flex items-center gap-1.5 rounded-lg border border-neutral-700 px-3 py-1.5 text-xs text-neutral-200 hover:bg-neutral-800">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          <button onClick={exportJson} disabled={!data} className="inline-flex items-center gap-1.5 rounded-lg bg-[#00ff66] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50">
            <Download className="w-3.5 h-3.5" /> Export JSON
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-neutral-400">Loading organization analytics...</p>
      ) : !data ? (
        <p className="text-sm text-neutral-400">No analytics data available yet.</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Projects (Active / Total)</div>
            <div className="text-xl font-bold text-white mt-1">
              {ov.projects?.active ?? 0} / {ov.projects?.total ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Connected Bots (TG / Discord)</div>
            <div className="text-xl font-bold text-[#00ff66] mt-1">
              {ov.integrations?.telegram_connected ?? 0} / {ov.integrations?.discord_connected ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Monitored Tokens / Research</div>
            <div className="text-xl font-bold text-cyan-400 mt-1">
              {ov.intelligence?.monitored_tokens ?? 0} / {ov.intelligence?.research_reports ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Credits Balance / Spent</div>
            <div className="text-xl font-bold text-amber-400 mt-1">
              {ov.billing?.credits ?? 0} / {data.credits_consumed ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Milestone Alerts (+ / -)</div>
            <div className="text-xl font-bold text-white mt-1">
              {data.performance_alerts?.positive ?? 0} / {data.performance_alerts?.negative ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Social Posts (Published / Queue)</div>
            <div className="text-xl font-bold text-white mt-1">
              {data.social_publishing?.published ?? 0} / {data.social_publishing?.in_pipeline ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Growth Campaigns / NFT</div>
            <div className="text-xl font-bold text-white mt-1">
              {ov.growth?.campaigns ?? 0} / {ov.growth?.nft_collections ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="text-neutral-400">Investor Pipeline / Team</div>
            <div className="text-xl font-bold text-white mt-1">
              {ov.growth?.investor_entries ?? 0} / {ov.team_members ?? 0}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
