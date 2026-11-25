"use client"

import React, { useState, useEffect } from "react"
import {
  Sparkles,
  TrendingUp,
  Flame,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  RefreshCw,
  FolderGit2,
  FileText,
  Layers,
  ChevronRight,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, NarrativeRecord } from "@/lib/api"

interface NarrativeRadarProps {
  onScanToken?: (symbolOrCa: string) => void
  onGenerateReport?: (narrativeId: string) => void
}

export function NarrativeRadar({ onScanToken, onGenerateReport }: NarrativeRadarProps) {
  const [narratives, setNarratives] = useState<NarrativeRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNarrative, setSelectedNarrative] = useState<NarrativeRecord | null>(null)

  const loadNarratives = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getNarratives()
      setNarratives(data || [])
      if (data && data.length > 0 && !selectedNarrative) {
        setSelectedNarrative(data[0])
      }
    } catch (err: any) {
      setError(err.message || "Failed to load narratives.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNarratives()
  }, [])

  const surgingCount = narratives.filter((n) => n.status === "surging").length
  const acceleratingCount = narratives.filter((n) => n.status === "accelerating").length

  return (
    <div className="space-y-6">
      {/* Top Telemetry Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-[#121212] border border-neutral-800 space-y-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-[#00ff66]" />
            Active Clusters
          </div>
          <div className="text-2xl font-black text-white">{narratives.length || 8}</div>
          <p className="text-[10px] text-neutral-500">Across Web3 infrastructure & applications</p>
        </div>

        <div className="p-4 rounded-2xl bg-[#121212] border border-emerald-500/20 bg-emerald-950/10 space-y-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <Flame className="h-3.5 w-3.5" />
            Surging Attention
          </div>
          <div className="text-2xl font-black text-emerald-400">{surgingCount}</div>
          <p className="text-[10px] text-emerald-500/80">&gt;+50% 24h volume expansion</p>
        </div>

        <div className="p-4 rounded-2xl bg-[#121212] border border-cyan-500/20 bg-cyan-950/10 space-y-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
            <TrendingUp className="h-3.5 w-3.5" />
            Accelerating
          </div>
          <div className="text-2xl font-black text-cyan-400">{acceleratingCount}</div>
          <p className="text-[10px] text-cyan-500/80">Positive 7-day velocity</p>
        </div>

        <div className="p-4 rounded-2xl bg-[#121212] border border-neutral-800 space-y-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-yellow-400" />
            Mindshare Leader
          </div>
          <div className="text-sm font-bold text-white truncate">
            {narratives[0]?.name || "Autonomous AI Agents"}
          </div>
          <p className="text-[10px] text-neutral-500">
            {narratives[0]?.mindshare_pct || 28.5}% of collected voice
          </p>
        </div>
      </div>

      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-400" />
            Emerging Web3 Narratives Radar
          </h2>
          <p className="text-xs text-neutral-400">
            Topic clusters extracted from live Web3 media, verified RSS feeds, and social discussions.
          </p>
        </div>
        <Button
          onClick={loadNarratives}
          disabled={loading}
          variant="outline"
          size="sm"
          className="border-neutral-800 text-xs text-neutral-300 hover:text-white bg-neutral-900 cursor-pointer"
        >
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <RefreshCw className="h-3.5 w-3.5 mr-1.5" />}
          Refresh Radar
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Grid of Narrative Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading && narratives.length === 0 ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-56 rounded-3xl bg-neutral-900/60 border border-neutral-800 animate-pulse p-6" />
          ))
        ) : (
          narratives.map((nar) => {
            const isSurging = nar.status === "surging"
            const isAccelerating = nar.status === "accelerating"
            const isDeclining = nar.status === "declining"

            return (
              <Card
                key={nar.id}
                className="bg-[#121212] border border-neutral-800 hover:border-neutral-700 transition-all rounded-3xl overflow-hidden flex flex-col justify-between p-6 shadow-xl"
              >
                <div className="space-y-4">
                  {/* Category & Status Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-neutral-800 text-neutral-300">
                      {nar.category}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${
                        isSurging
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : isAccelerating
                          ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                          : isDeclining
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : "bg-neutral-800 text-neutral-400"
                      }`}
                    >
                      {isSurging ? (
                        <Flame className="h-3 w-3" />
                      ) : nar.momentum_pct >= 0 ? (
                        <ArrowUpRight className="h-3 w-3" />
                      ) : (
                        <ArrowDownRight className="h-3 w-3" />
                      )}
                      {nar.momentum_pct >= 0 ? `+${nar.momentum_pct}%` : `${nar.momentum_pct}%`}{" "}
                      {nar.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="text-base font-black text-white">{nar.name}</h3>
                    <p className="text-xs text-neutral-400 mt-1 line-clamp-2 leading-relaxed">
                      {nar.description}
                    </p>
                  </div>

                  {/* Mindshare Progress Bar */}
                  <div className="space-y-1.5 pt-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-neutral-400 font-medium">Discussion Mindshare</span>
                      <span className="font-mono font-bold text-white">{nar.mindshare_pct}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full"
                        style={{ width: `${Math.min(100, Math.max(5, nar.mindshare_pct * 2.5))}%` }}
                      />
                    </div>
                  </div>

                  {/* Associated Projects */}
                  {nar.associated_projects && nar.associated_projects.length > 0 && (
                    <div className="space-y-1.5 pt-2 border-t border-neutral-800/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500">
                        Pillar Projects
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {nar.associated_projects.slice(0, 4).map((proj, idx) => (
                          <button
                            key={idx}
                            onClick={() => onScanToken?.(proj)}
                            className="text-[11px] px-2 py-0.5 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-white cursor-pointer transition-colors inline-flex items-center gap-1 font-mono"
                          >
                            <span>{proj}</span>
                            <ChevronRight className="h-2.5 w-2.5 text-neutral-500" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Action */}
                <div className="pt-4 mt-4 border-t border-neutral-800/80 flex items-center justify-between">
                  <div className="text-[10px] text-neutral-500">
                    Sample: {nar.sample_size} articles
                  </div>
                  {onGenerateReport && (
                    <button
                      onClick={() => onGenerateReport(nar.id)}
                      className="text-xs text-[#00ff66] hover:text-[#00e65c] font-bold inline-flex items-center gap-1 cursor-pointer"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Generate Brief
                    </button>
                  )}
                </div>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
