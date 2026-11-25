"use client"

import React, { useState, useEffect } from "react"
import {
  Flame,
  Search,
  Radar,
  ArrowUpRight,
  TrendingUp,
  Sparkles,
  ExternalLink,
  Loader2,
  RefreshCw,
  Shield,
  MessageSquare,
  Users,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api, TrendingProject } from "@/lib/api"

interface TrendingDiscoveryProps {
  onScanToken?: (symbolOrCa: string) => void
}

export function TrendingDiscovery({ onScanToken }: TrendingDiscoveryProps) {
  const [projects, setProjects] = useState<TrendingProject[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterQuery, setFilterQuery] = useState("")

  const loadProjects = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getTrendingProjects()
      setProjects(data || [])
    } catch (err: any) {
      setError(err.message || "Failed to load trending projects.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
      p.symbol.toLowerCase().includes(filterQuery.toLowerCase()) ||
      p.narrative.toLowerCase().includes(filterQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-emerald-400" />
            Trending Project Discovery Radar
          </h2>
          <p className="text-xs text-neutral-400">
            Multi-signal discovery detecting unusual attention surges across news, social discussions, and on-chain liquidity.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative w-48 sm:w-64">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-neutral-500" />
            <input
              type="text"
              placeholder="Filter by name, symbol, or narrative..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="h-9 w-full pl-9 pr-3 rounded-full bg-neutral-900 border border-neutral-800 text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66] focus:outline-none"
            />
          </div>
          <Button
            onClick={loadProjects}
            disabled={loading}
            variant="outline"
            size="sm"
            className="border-neutral-800 text-xs text-neutral-300 hover:text-white bg-neutral-900 cursor-pointer"
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Discovery Table */}
      <div className="rounded-3xl border border-neutral-800 bg-[#121212] shadow-2xl overflow-hidden">
        <Table className="min-w-[800px] sm:min-w-full">
          <TableHeader>
            <TableRow className="border-b border-neutral-800 hover:bg-transparent">
              <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                Project &amp; Narrative
              </TableHead>
              <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                Discovery Reason
              </TableHead>
              <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                Momentum &amp; Volume
              </TableHead>
              <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                Sentiment
              </TableHead>
              <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider text-right">
                Action
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && projects.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-32 text-center text-neutral-500 text-xs">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin text-[#00ff66]" />
                    <span>Scanning multi-signal attention metrics across Web3...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-28 text-center text-neutral-500 text-xs">
                  No projects match your filter.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((proj, idx) => {
                const isPositive = proj.sentiment_label === "positive"
                const isNegative = proj.sentiment_label === "negative"

                return (
                  <TableRow
                    key={idx}
                    className="border-b border-neutral-800/60 hover:bg-neutral-900/40 transition-colors"
                  >
                    {/* Project & Narrative */}
                    <TableCell className="py-4 px-5">
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-2xl bg-neutral-900 border border-neutral-700/60 flex items-center justify-center font-bold text-white text-xs">
                          {proj.symbol.slice(0, 3)}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-extrabold text-white text-xs">{proj.name}</span>
                            <span className="text-[10px] font-mono text-neutral-400 bg-neutral-900 px-1.5 py-0.2 rounded border border-neutral-800">
                              ${proj.symbol}
                            </span>
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-400">
                              {proj.chain}
                            </span>
                          </div>
                          <div className="text-[11px] text-[#00ff66] font-medium mt-0.5">
                            {proj.narrative}
                          </div>
                        </div>
                      </div>
                    </TableCell>

                    {/* Discovery Reason */}
                    <TableCell className="py-4 px-5 max-w-sm">
                      <p className="text-xs text-neutral-300 leading-snug line-clamp-2">
                        {proj.discovery_reason}
                      </p>
                      {proj.flags && proj.flags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {proj.flags.map((flag, fIdx) => (
                            <span
                              key={fIdx}
                              className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            >
                              {flag}
                            </span>
                          ))}
                        </div>
                      )}
                    </TableCell>

                    {/* Momentum & Volume */}
                    <TableCell className="py-4 px-5">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-xs font-bold inline-flex items-center gap-0.5 ${
                            proj.momentum_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          <ArrowUpRight className="h-3 w-3" />
                          {proj.momentum_pct >= 0 ? `+${proj.momentum_pct}%` : `${proj.momentum_pct}%`}
                        </span>
                        <span className="text-[10px] text-neutral-500">24h Surge</span>
                      </div>
                      <div className="text-[11px] text-neutral-400 flex items-center gap-3 mt-1 font-mono">
                        <span className="inline-flex items-center gap-1">
                          <MessageSquare className="h-3 w-3 text-neutral-500" />
                          {proj.social_volume} posts
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Users className="h-3 w-3 text-neutral-500" />
                          {proj.unique_authors} authors
                        </span>
                      </div>
                    </TableCell>

                    {/* Sentiment */}
                    <TableCell className="py-4 px-5">
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                          isPositive
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : isNegative
                            ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                            : "bg-neutral-800 text-neutral-300 border border-neutral-700"
                        }`}
                      >
                        {proj.sentiment_label} ({proj.sentiment_score >= 0 ? `+${proj.sentiment_score}` : proj.sentiment_score})
                      </span>
                    </TableCell>

                    {/* Action */}
                    <TableCell className="py-4 px-5 text-right">
                      <Button
                        size="sm"
                        onClick={() => onScanToken?.(proj.contract_address || proj.symbol)}
                        className="h-8 px-3.5 bg-neutral-900 hover:bg-[#00ff66] text-neutral-300 hover:text-black border border-neutral-700 hover:border-[#00ff66] text-xs font-bold rounded-full transition-all cursor-pointer inline-flex items-center gap-1.5"
                      >
                        <Radar className="h-3 w-3" />
                        <span>Audit Security</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
