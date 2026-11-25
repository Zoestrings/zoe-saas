"use client"

import React, { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import {
  Calendar,
  CheckCircle2,
  Compass,
  Send,
  ShieldAlert,
  Sparkles,
  Trash2,
  TrendingUp,
  XCircle,
} from "lucide-react"
import { api } from "@/lib/api"

export default function OwnerSocialGrowthPage() {
  const [tab, setTab] = useState<"publishing" | "research" | "growth">("publishing")
  const [compliance, setCompliance] = useState<any>(null)
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [posts, setPosts] = useState<any[]>([])
  const [reports, setReports] = useState<any[]>([])
  const [watchlists, setWatchlists] = useState<any[]>([])
  const [trends, setTrends] = useState<any>(null)
  const [opportunities, setOpportunities] = useState<any[]>([])
  const [analytics, setAnalytics] = useState<any>(null)

  const [topic, setTopic] = useState("")
  const [platform, setPlatform] = useState("telegram_channel")
  const [campName, setCampName] = useState("")
  const [researchQuery, setResearchQuery] = useState("")
  const [researchCat, setResearchCat] = useState("ecosystem")
  const [oppTitle, setOppTitle] = useState("")
  const [oppCat, setOppCat] = useState("campaign_opportunity")
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const loadAll = useCallback(async () => {
    try {
      const [comp, campRes, postRes, repRes, wlRes, trRes, oppRes, anRes] = await Promise.all([
        api.getSocialComplianceStatus(),
        api.listSocialCampaigns(),
        api.listSocialPosts(),
        api.listWeb3Research(),
        api.listResearchWatchlists(),
        api.getSocialTrends(),
        api.listGrowthOpportunities(),
        api.getGrowthAnalytics(),
      ])
      setCompliance(comp)
      setCampaigns(campRes.campaigns || [])
      setPosts(postRes.posts || [])
      setReports(repRes.reports || [])
      setWatchlists(wlRes.watchlists || [])
      setTrends(trRes)
      setOpportunities(oppRes.opportunities || [])
      setAnalytics(anRes)
    } catch (err: any) {
      setMsg(err?.message || "Failed to load Social & Growth workspace")
    }
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const handleGenerateDraft = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return
    setBusy(true)
    setMsg(null)
    try {
      const res = await api.generateSocialPostDraft({ topic, platform })
      setTopic("")
      setMsg(res.ai_disclosure || "AI draft created for human review.")
      await loadAll()
    } catch (err: any) {
      setMsg(err?.message || "Failed to generate draft")
    } finally {
      setBusy(false)
    }
  }

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!campName.trim()) return
    await api.createSocialCampaign({ name: campName })
    setCampName("")
    await loadAll()
  }

  const handleRunResearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!researchQuery.trim()) return
    setBusy(true)
    setMsg(null)
    try {
      await api.runWeb3Research({ query: researchQuery, category: researchCat })
      setResearchQuery("")
      await loadAll()
    } catch (err: any) {
      setMsg(err?.message || "Research failed")
    } finally {
      setBusy(false)
    }
  }

  const handleAddOpportunity = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!oppTitle.trim()) return
    await api.createGrowthOpportunity({ title: oppTitle, category: oppCat, priority: "medium" })
    setOppTitle("")
    await loadAll()
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Social Intelligence, Publishing &amp; Growth Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            AI-assisted content calendar with human approval, permitted Web3 research &amp; tenant-isolated growth analytics
          </p>
        </div>
        <Link href="/owner/dashboard" className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs hover:bg-slate-800">
          Back to Owner Dashboard
        </Link>
      </div>

      {compliance && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Compliance Gate:</strong> {compliance.policy_notice} (X API:{" "}
            {compliance.x_api_enabled ? "Enabled" : "Disabled"}, Auto-Reply:{" "}
            {compliance.x_auto_reply_enabled ? "Enabled" : "Disabled"})
          </span>
        </div>
      )}

      {msg && <div className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs text-cyan-200">{msg}</div>}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setTab("publishing")}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "publishing" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}
        >
          Social Publishing Agent ({posts.length})
        </button>
        <button
          onClick={() => setTab("research")}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "research" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}
        >
          Web3 &amp; Social Research ({reports.length})
        </button>
        <button
          onClick={() => setTab("growth")}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "growth" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}
        >
          Growth Intelligence ({opportunities.length})
        </button>
      </div>

      {tab === "publishing" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <form onSubmit={handleGenerateDraft} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Sparkles className="w-4 h-4 text-cyan-400" /> AI Content Draft Generator (Human Approval Required)
              </div>
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Topic or announcement (e.g. Q4 Solana Liquidity Milestone)..."
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
              />
              <div className="flex gap-2">
                <select
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
                >
                  <option value="telegram_channel">Telegram Channel</option>
                  <option value="discord_webhook">Discord Announcement</option>
                  <option value="manual_export">Manual Export</option>
                </select>
                <button
                  type="submit"
                  disabled={busy}
                  className="rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-black hover:bg-cyan-400 disabled:opacity-50"
                >
                  {busy ? "Generating..." : "Generate AI Draft"}
                </button>
              </div>
            </form>

            <form onSubmit={handleCreateCampaign} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Calendar className="w-4 h-4 text-violet-400" /> Campaigns ({campaigns.length})
              </div>
              <div className="flex gap-2">
                <input
                  value={campName}
                  onChange={(e) => setCampName(e.target.value)}
                  placeholder="New campaign name..."
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
                />
                <button type="submit" className="rounded-lg border border-violet-500/40 bg-violet-500/20 px-3 py-2 text-xs text-violet-200">
                  Create
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {campaigns.map((c) => (
                  <span key={c.id} className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] text-slate-300">
                    {c.name}
                  </span>
                ))}
              </div>
            </form>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
            <h3 className="text-sm font-semibold">Content Calendar &amp; Approval Queue</h3>
            {posts.length === 0 ? (
              <p className="text-xs text-slate-400">No drafts yet. Generate an AI draft above.</p>
            ) : (
              <div className="space-y-2">
                {posts.map((p) => (
                  <div key={p.id} className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-xs space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-semibold text-white">
                        {p.title || "Untitled"} <span className="text-slate-400 font-normal">({p.platform})</span>
                      </div>
                      <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase text-cyan-300">
                        {p.status}
                      </span>
                    </div>
                    <p className="text-slate-300">{p.content}</p>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {p.status === "draft" && (
                        <button
                          onClick={() => api.submitSocialPost(p.id).then(loadAll)}
                          className="rounded border border-slate-700 px-2.5 py-1 hover:bg-slate-800"
                        >
                          Submit for Approval
                        </button>
                      )}
                      {p.status === "pending_approval" && (
                        <>
                          <button
                            onClick={() => api.approveSocialPost(p.id).then(loadAll)}
                            className="inline-flex items-center gap-1 rounded border border-emerald-500/40 px-2.5 py-1 text-emerald-300 hover:bg-emerald-500/10"
                          >
                            <CheckCircle2 className="w-3 h-3" /> Approve
                          </button>
                          <button
                            onClick={() => api.rejectSocialPost(p.id, "Needs revision").then(loadAll)}
                            className="inline-flex items-center gap-1 rounded border border-rose-500/40 px-2.5 py-1 text-rose-300 hover:bg-rose-500/10"
                          >
                            <XCircle className="w-3 h-3" /> Reject
                          </button>
                        </>
                      )}
                      {p.status === "approved" && (
                        <button
                          onClick={() => api.publishSocialPostNow(p.id).then(loadAll).catch((e) => setMsg(e.message))}
                          className="inline-flex items-center gap-1 rounded bg-emerald-500 px-2.5 py-1 font-semibold text-black hover:bg-emerald-400"
                        >
                          <Send className="w-3 h-3" /> Publish Now
                        </button>
                      )}
                      <button
                        onClick={() => api.deleteSocialPost(p.id).then(loadAll)}
                        className="inline-flex items-center gap-1 rounded border border-rose-500/30 px-2 py-1 text-rose-400 hover:bg-rose-500/10"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "research" && (
        <div className="space-y-4">
          <form onSubmit={handleRunResearch} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 flex flex-wrap gap-2">
            <input
              value={researchQuery}
              onChange={(e) => setResearchQuery(e.target.value)}
              placeholder="Token CA, project name, DeFi/RWA narrative..."
              className="flex-1 min-w-[220px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
            />
            <select
              value={researchCat}
              onChange={(e) => setResearchCat(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
            >
              <option value="ecosystem">Ecosystem</option>
              <option value="project_discovery">Project Discovery</option>
              <option value="defi_nft">DeFi &amp; NFT</option>
              <option value="rwa_tokenization">RWA &amp; Tokenization</option>
              <option value="narrative">Narrative</option>
              <option value="announcement">Official Announcements</option>
            </select>
            <button
              type="submit"
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-black"
            >
              <Compass className="w-3.5 h-3.5" /> {busy ? "Researching..." : "Run Permitted Research"}
            </button>
          </form>

          {trends?.narratives && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
              <h3 className="text-xs font-semibold uppercase text-slate-400 mb-2">Tracked Ecosystem Narratives</h3>
              <div className="flex flex-wrap gap-2">
                {trends.narratives.map((n: any, idx: number) => (
                  <span key={idx} className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-slate-200">
                    {n.narrative || n.name || JSON.stringify(n)}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            {reports.map((r) => (
              <div key={r.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-xs space-y-1.5">
                <div className="font-semibold text-white">{r.title}</div>
                <p className="text-slate-300">{r.summary}</p>
                <div className="text-[11px] text-slate-400">
                  Sources: {(r.sources || []).map((s: any) => s.provider).join(", ")} • {new Date(r.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-xs">
            <h3 className="font-semibold text-white mb-2">Research Watchlists ({watchlists.length})</h3>
            <div className="flex flex-wrap gap-2">
              {watchlists.map((w) => (
                <span key={w.id} className="inline-flex items-center gap-2 rounded-full bg-slate-800 px-3 py-1">
                  {w.topic_or_project}
                  <button onClick={() => api.deleteResearchWatchlist(w.id).then(loadAll)} className="text-rose-400">
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "growth" && (
        <div className="space-y-4">
          {analytics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
                <div className="text-slate-400">Published Posts</div>
                <div className="text-lg font-bold text-emerald-400 mt-1">{analytics.total_published ?? 0}</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
                <div className="text-slate-400">Research Reports</div>
                <div className="text-lg font-bold text-cyan-400 mt-1">{analytics.research_reports_count ?? 0}</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
                <div className="text-slate-400">Open Opportunities</div>
                <div className="text-lg font-bold text-violet-400 mt-1">{analytics.opportunities_by_status?.open ?? 0}</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
                <div className="text-slate-400">Watchlists</div>
                <div className="text-lg font-bold text-white mt-1">{analytics.research_watchlists_count ?? 0}</div>
              </div>
            </div>
          )}

          <form onSubmit={handleAddOpportunity} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 flex flex-wrap gap-2">
            <input
              value={oppTitle}
              onChange={(e) => setOppTitle(e.target.value)}
              placeholder="New growth opportunity or campaign lead..."
              className="flex-1 min-w-[220px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
            />
            <select
              value={oppCat}
              onChange={(e) => setOppCat(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
            >
              <option value="campaign_opportunity">Campaign Opportunity</option>
              <option value="audience_insight">Audience Insight</option>
              <option value="partnership_lead">Partnership Lead</option>
              <option value="content_performance">Content Performance</option>
            </select>
            <button type="submit" className="inline-flex items-center gap-1 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-black">
              <TrendingUp className="w-3.5 h-3.5" /> Add Opportunity
            </button>
          </form>

          <div className="space-y-2">
            {opportunities.map((o) => (
              <div key={o.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-3 text-xs flex items-center justify-between">
                <div>
                  <div className="font-semibold text-white">{o.title}</div>
                  <div className="text-slate-400">
                    {o.category} • priority: {o.priority} • status: {o.status}
                  </div>
                </div>
                {o.status !== "completed" && (
                  <button
                    onClick={() => api.updateGrowthOpportunity(o.id, { status: "completed" }).then(loadAll)}
                    className="rounded border border-emerald-500/40 px-2.5 py-1 text-emerald-300 hover:bg-emerald-500/10"
                  >
                    Mark Completed
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
