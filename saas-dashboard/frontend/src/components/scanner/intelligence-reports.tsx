"use client"

import React, { useState, useEffect } from "react"
import {
  FileText,
  Sparkles,
  Loader2,
  ExternalLink,
  Plus,
  ShieldCheck,
  AlertCircle,
  Clock,
  Layers,
  ChevronRight,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api, IntelligenceReport } from "@/lib/api"

export function IntelligenceReports() {
  const [reports, setReports] = useState<IntelligenceReport[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [topicInput, setTopicInput] = useState("")
  const [selectedReport, setSelectedReport] = useState<IntelligenceReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadReports = async () => {
    setLoading(true)
    try {
      const data = await api.getIntelligenceReports()
      setReports(data || [])
      if (data && data.length > 0 && !selectedReport) {
        setSelectedReport(data[0])
      }
    } catch (err: any) {
      console.warn("Notice: Failed to load intelligence reports:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  const handleGenerate = async () => {
    if (!topicInput.trim()) return
    setGenerating(true)
    setError(null)
    try {
      const newReport = await api.generateIntelligenceReport(topicInput.trim())
      setReports((prev) => [newReport, ...prev])
      setSelectedReport(newReport)
      setTopicInput("")
    } catch (err: any) {
      setError(err.message || "Failed to generate report.")
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Creation Bar */}
      <div className="p-6 rounded-3xl bg-[#121212] border border-neutral-800 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <FileText className="h-4 w-4 text-[#00ff66]" />
              Automated Intelligence Research Briefs
            </h2>
            <p className="text-xs text-neutral-400">
              Generate structured, evidence-grounded due diligence briefs separating verified facts from analytical interpretations.
            </p>
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleGenerate()
          }}
          className="flex flex-col sm:flex-row items-center gap-3"
        >
          <input
            type="text"
            placeholder="Enter a project or narrative topic (e.g. 'Virtuals Protocol', 'AI Agents', 'BONK')..."
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            className="h-11 flex-1 w-full px-4 rounded-full bg-neutral-900 border border-neutral-700 text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66] focus:outline-none"
          />
          <Button
            type="submit"
            disabled={generating || !topicInput.trim()}
            className="w-full sm:w-auto h-11 px-6 bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer transition-all flex items-center justify-center gap-2"
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Synthesizing Evidence...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Generate Intelligence Brief</span>
              </>
            )}
          </Button>
        </form>

        {error && (
          <div className="p-3 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-xs text-rose-300">
            {error}
          </div>
        )}
      </div>

      {/* Main Content Area: Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Reports List */}
        <div className="space-y-3">
          <div className="text-xs font-bold uppercase tracking-wider text-neutral-400 px-2">
            Saved Research Briefs ({reports.length})
          </div>

          {loading && reports.length === 0 ? (
            <div className="p-8 text-center text-neutral-500 text-xs">
              <Loader2 className="h-4 w-4 animate-spin mx-auto mb-2 text-[#00ff66]" />
              Loading research briefs...
            </div>
          ) : reports.length === 0 ? (
            <div className="p-8 text-center rounded-3xl bg-[#121212] border border-neutral-800 text-neutral-500 text-xs">
              No briefs generated yet. Enter a topic above to create your first research brief.
            </div>
          ) : (
            reports.map((rep) => {
              const isSelected = selectedReport?.report_id === rep.report_id
              return (
                <div
                  key={rep.report_id}
                  onClick={() => setSelectedReport(rep)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-1 ${
                    isSelected
                      ? "bg-neutral-900 border-[#00ff66] shadow-lg shadow-[#00ff66]/10"
                      : "bg-[#121212] border-neutral-800 hover:border-neutral-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white truncate max-w-[200px]">
                      {rep.title}
                    </span>
                    <span className="text-[10px] font-mono text-neutral-500">
                      {rep.created_at_utc?.slice(0, 10)}
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-400 line-clamp-1">
                    {rep.executive_summary}
                  </p>
                </div>
              )
            })
          )}
        </div>

        {/* Right: Selected Report View */}
        <div className="lg:col-span-2">
          {selectedReport ? (
            <div className="p-6 sm:p-8 rounded-3xl bg-[#121212] border border-neutral-800 shadow-2xl space-y-6">
              {/* Header */}
              <div className="border-b border-neutral-800 pb-4 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#00ff66] bg-[#00ff66]/10 px-2.5 py-0.5 rounded-full border border-[#00ff66]/20">
                    Audit-Ready Brief
                  </span>
                  <span className="text-xs font-mono text-neutral-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {selectedReport.created_at_utc}
                  </span>
                </div>
                <h3 className="text-xl font-black text-white pt-1">{selectedReport.title}</h3>
              </div>

              {/* Executive Summary */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                  1. Executive Summary
                </h4>
                <div className="p-4 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-xs text-neutral-200 leading-relaxed">
                  {selectedReport.executive_summary}
                </div>
              </div>

              {/* Narrative & Market Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5" />
                    Narrative Thesis
                  </h4>
                  <div className="text-xs text-neutral-300 whitespace-pre-line leading-relaxed">
                    {selectedReport.narrative_overview}
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Market &amp; Mindshare
                  </h4>
                  <div className="text-xs text-neutral-300 whitespace-pre-line leading-relaxed font-mono">
                    {selectedReport.market_and_mindshare}
                  </div>
                </div>
              </div>

              {/* Sentiment Analysis */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                  2. Sentiment Intelligence
                </h4>
                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 text-xs text-neutral-300 whitespace-pre-line leading-relaxed">
                  {selectedReport.sentiment_analysis}
                </div>
              </div>

              {/* Verified Sources */}
              {selectedReport.important_sources && selectedReport.important_sources.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                    3. Supporting Sources &amp; Citations
                  </h4>
                  <div className="space-y-2">
                    {selectedReport.important_sources.map((src, sIdx) => (
                      <a
                        key={sIdx}
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-3 rounded-2xl bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 transition-colors flex items-center justify-between text-xs text-neutral-300 hover:text-white"
                      >
                        <span className="font-semibold truncate max-w-md">{src.title}</span>
                        <div className="flex items-center gap-2 text-neutral-500 font-mono text-[11px] shrink-0">
                          <span>{src.domain || "Web3"}</span>
                          <ExternalLink className="h-3 w-3" />
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations & Confidence Disclaimer */}
              <div className="p-4 rounded-2xl bg-neutral-900/90 border border-neutral-800 text-[11px] text-neutral-400 space-y-1">
                <div className="font-bold text-neutral-300 flex items-center gap-1.5">
                  <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
                  Limitations &amp; Analytical Confidence
                </div>
                <p className="leading-relaxed">
                  {selectedReport.limitations_and_confidence}
                </p>
              </div>
            </div>
          ) : (
            <div className="h-96 rounded-3xl bg-[#121212] border border-neutral-800 flex flex-col items-center justify-center text-neutral-500 text-xs gap-2">
              <FileText className="h-8 w-8 text-neutral-700" />
              <span>Select a brief on the left or generate a new one above.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
