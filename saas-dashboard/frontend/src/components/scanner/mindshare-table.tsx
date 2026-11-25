"use client"

import React, { useState, useEffect } from "react"
import {
  BarChart3,
  Users,
  MessageSquare,
  TrendingUp,
  Loader2,
  RefreshCw,
  Info,
  Layers,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, MindshareResult } from "@/lib/api"

export function MindshareTable() {
  const [data, setData] = useState<MindshareResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [selectedTimeframe, setSelectedTimeframe] = useState("24h")

  const categories = [
    { id: "all", name: "All Categories" },
    { id: "AI Agents", name: "AI Agents" },
    { id: "DePIN", name: "DePIN" },
    { id: "RWA", name: "RWA" },
    { id: "DeFi", name: "DeFi" },
    { id: "Memecoins", name: "Memecoins" },
  ]

  const timeframes = ["24h", "7d", "30d"]

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await api.getMindshare(selectedCategory, selectedTimeframe)
      setData(res)
    } catch (err) {
      console.warn("Failed to load mindshare:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [selectedCategory, selectedTimeframe])

  return (
    <div className="space-y-6">
      {/* Controls & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-cyan-400" />
            Project Attention Mindshare Engine
          </h2>
          <p className="text-xs text-neutral-400">
            Share of voice calculations weighted by author diversity to eliminate spam astroturfing.
          </p>
        </div>

        {/* Category & Timeframe Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Categories */}
          <div className="flex items-center bg-neutral-900 border border-neutral-800 rounded-full p-1">
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCategory(c.id)}
                className={`text-xs px-3 py-1 rounded-full font-medium transition-all cursor-pointer ${
                  selectedCategory === c.id
                    ? "bg-[#00ff66] text-black font-bold shadow-md shadow-[#00ff66]/20"
                    : "text-neutral-400 hover:text-white"
                }`}
              >
                {c.name}
              </button>
            ))}
          </div>

          {/* Timeframes */}
          <div className="flex items-center bg-neutral-900 border border-neutral-800 rounded-full p-1">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setSelectedTimeframe(tf)}
                className={`text-xs px-2.5 py-1 rounded-full font-mono transition-all cursor-pointer ${
                  selectedTimeframe === tf
                    ? "bg-neutral-800 text-white font-bold"
                    : "text-neutral-400 hover:text-white"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Mindshare Card */}
      <div className="p-6 rounded-3xl bg-[#121212] border border-neutral-800 shadow-2xl space-y-6">
        {loading && !data ? (
          <div className="h-64 flex flex-col items-center justify-center gap-2 text-neutral-500 text-xs">
            <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
            <span>Computing mathematical attention mindshare...</span>
          </div>
        ) : !data || data.projects.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-neutral-500 text-xs">
            No project mindshare data recorded for this selection.
          </div>
        ) : (
          <div className="space-y-4">
            {data.projects.map((proj, idx) => {
              const share = proj.mindshare_pct
              const change = proj.change_pct

              return (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 hover:border-neutral-700 transition-all space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-bold text-neutral-500 w-5">
                        #{idx + 1}
                      </span>
                      <span className="text-sm font-extrabold text-white">{proj.name}</span>
                      <span className="text-xs font-mono text-neutral-400 bg-neutral-900 px-1.5 py-0.2 rounded border border-neutral-800">
                        ${proj.symbol}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span
                        className={`text-xs font-mono font-bold ${
                          change >= 0 ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {change >= 0 ? `+${change}%` : `${change}%`}
                      </span>
                      <span className="text-base font-black font-mono text-white">
                        {share}%
                      </span>
                    </div>
                  </div>

                  {/* Visual Bar */}
                  <div className="h-2 w-full bg-neutral-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-400 to-[#00ff66] rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(3, share * 3))}%` }}
                    />
                  </div>

                  {/* Telemetry Sub-row */}
                  <div className="flex items-center justify-between text-[11px] text-neutral-500 font-mono pt-1">
                    <span className="flex items-center gap-1.5">
                      <MessageSquare className="h-3 w-3" />
                      {proj.posts_count} mentions
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Users className="h-3 w-3" />
                      {proj.unique_authors} unique authors
                    </span>
                    <span className="text-neutral-400">
                      Diversity: {Math.round(proj.author_diversity_ratio * 100)}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Methodology Footnote */}
        <div className="p-4 rounded-2xl bg-neutral-900 border border-neutral-800/80 flex items-start gap-2.5 text-xs text-neutral-400">
          <Info className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-white">Mathematical Calculation Methodology:</span>
            <p className="text-[11px] text-neutral-400 leading-relaxed">
              {data?.methodology ||
                "Calculated as (project_weighted_mentions / total_category_mentions) * 100, where unique author diversity discounts duplicate posting frequency."}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
