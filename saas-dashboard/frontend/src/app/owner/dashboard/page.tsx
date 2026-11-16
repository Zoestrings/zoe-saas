"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  Bot,
  BrainCircuit,
  FileCode,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
  Layers,
  ShieldCheck,
  Sparkles,
  Inbox,
  MessageSquare,
  Cpu,
  DollarSign
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Project, ProjectAnalytics } from "@/lib/api"

export default function OwnerDashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCA(text)
    setTimeout(() => setCopiedCA(null), 2000)
  }

  const loadProjects = async () => {
    setLoading(true)
    try {
      const data = await api.getProjects()
      setProjects(data || [])
      if (data && data.length > 0) {
        try {
          const stats = await api.getProjectAnalytics(data[0].id)
          setAnalytics(stats)
        } catch (statsErr) {
          console.warn("Could not load project analytics:", statsErr)
        }
      }
    } catch (err) {
      console.warn("Notice: Backend service unavailable or not logged in yet:", err)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-neutral-400 gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Loading your bot profile...</p>
      </div>
    )
  }

  // Zero-state condition
  if (projects.length === 0) {
    return (
      <div className="py-20 max-w-xl mx-auto text-center space-y-5">
        <div className="h-16 w-16 mx-auto rounded-3xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-500 shadow-xl">
          <Inbox className="h-8 w-8 text-[#00ff66]" />
        </div>
        <div className="space-y-2">
          <h2 className="text-lg font-bold text-white">No Assigned Bot</h2>
          <p className="text-xs text-neutral-400 leading-relaxed">
            You don&apos;t have any projects assigned yet. Please contact the Zoe platform admin to deploy your bot.
          </p>
        </div>
        <div className="pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadProjects}
            className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 rounded-full cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Check Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-neutral-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Bot className="h-6 w-6 text-[#00ff66]" />
            My Deployed Agents
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Manage your autonomous Telegram community assistant, custom facts, and response persona.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadProjects}
          className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 rounded-full cursor-pointer w-fit"
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Refresh Status
        </Button>
      </div>

      {/* Analytics Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Messages Handled */}
        <Card className="bg-[#121212] border border-neutral-800 hover:border-[#00ff66]/30 transition-all rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Messages Handled</span>
            <div className="h-8 w-8 rounded-lg bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <MessageSquare className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-[#00ff66] tracking-tight">
            {analytics ? analytics.total_messages.toLocaleString() : "..."}
          </div>
          <p className="text-[11px] text-neutral-500 mt-1">Community inquiries & automated replies</p>
        </Card>

        {/* Token Usage */}
        <Card className="bg-[#121212] border border-neutral-800 hover:border-[#00ff66]/30 transition-all rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Token Usage</span>
            <div className="h-8 w-8 rounded-lg bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <Cpu className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-[#00ff66] tracking-tight">
            {analytics
              ? analytics.total_tokens >= 1_000_000
                ? `${(analytics.total_tokens / 1_000_000).toFixed(1)}M`
                : analytics.total_tokens >= 1_000
                ? `${(analytics.total_tokens / 1_000).toFixed(1)}k`
                : analytics.total_tokens.toLocaleString()
              : "..."}
          </div>
          <p className="text-[11px] text-neutral-500 mt-1">Prompt & context generation tokens</p>
        </Card>

        {/* Est. API Cost */}
        <Card className="bg-[#121212] border border-neutral-800 hover:border-[#00ff66]/30 transition-all rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Est. API Cost</span>
            <div className="h-8 w-8 rounded-lg bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <DollarSign className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-[#00ff66] tracking-tight">
            ${analytics ? analytics.estimated_cost_usd.toFixed(2) : "0.00"}
          </div>
          <p className="text-[11px] text-neutral-500 mt-1">Estimated model cost ($0.001 / 1k tokens)</p>
        </Card>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {projects.map((proj) => {
          const isHealthy = !proj.status || proj.status === "active" || proj.status === "online"
          const isDeploying = proj.status === "deploying"
          const isError = proj.status === "error"

          return (
            <Card
              key={proj.id}
              className="bg-[#121212] border border-neutral-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col justify-between"
            >
              <CardHeader className="p-6 border-b border-neutral-800 pb-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-base font-bold text-white tracking-tight">
                        {proj.name}
                      </CardTitle>
                      {isHealthy && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#00ff66] bg-[#00ff66]/10 border border-[#00ff66]/30 px-2.5 py-0.5 rounded-full">
                          <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66] animate-pulse" />
                          Online
                        </span>
                      )}
                      {isDeploying && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-amber-400 bg-amber-950/60 border border-amber-800/60 px-2.5 py-0.5 rounded-full">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                          Deploying
                        </span>
                      )}
                      {isError && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-rose-400 bg-rose-950/60 border border-rose-800/60 px-2.5 py-0.5 rounded-full">
                          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                          Error
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-neutral-400 mt-1 font-mono">
                      ID: {proj.id}
                    </p>
                  </div>

                  <div className="h-9 w-9 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
                    <Sparkles className="h-4 w-4" />
                  </div>
                </div>
              </CardHeader>

              <CardContent className="p-6 space-y-5 flex-1 flex flex-col justify-between">
                <div className="space-y-4">
                  {/* Token Address Row */}
                  {proj.token_address ? (
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 block mb-1.5">
                        Token Contract Address
                      </span>
                      <div className="flex items-center justify-between p-2.5 rounded-2xl bg-neutral-900 border border-neutral-800">
                        <span className="font-mono text-xs text-white truncate max-w-[260px]">
                          {proj.token_address}
                        </span>
                        <button
                          onClick={() => copyToClipboard(proj.token_address!)}
                          className="flex items-center gap-1 text-[11px] text-neutral-300 hover:text-[#00ff66] px-2.5 py-1 rounded-full bg-neutral-800 hover:bg-neutral-700 transition-colors cursor-pointer"
                        >
                          {copiedCA === proj.token_address ? (
                            <Check className="h-3 w-3 text-[#00ff66]" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          <span>{copiedCA === proj.token_address ? "Copied" : "Copy"}</span>
                        </button>
                      </div>
                    </div>
                  ) : null}

                  {/* Telegram Group */}
                  {proj.telegram_group_id && (
                    <div className="flex items-center justify-between text-xs py-1.5 border-b border-neutral-800">
                      <span className="text-neutral-400">Telegram Group ID</span>
                      <span className="font-mono text-white">{proj.telegram_group_id}</span>
                    </div>
                  )}

                  {/* Custom Instructions Snippet */}
                  {proj.custom_instructions && (
                    <div className="text-xs space-y-1">
                      <span className="text-neutral-400 font-medium">Custom Persona</span>
                      <p className="text-neutral-300 bg-neutral-900/60 p-3 rounded-2xl border border-neutral-800 text-[11px] line-clamp-2 italic">
                        &quot;{proj.custom_instructions}&quot;
                      </p>
                    </div>
                  )}
                </div>

                {/* Quick Actions */}
                <div className="pt-4 border-t border-neutral-800 grid grid-cols-2 gap-3">
                  <Link href="/owner/dashboard/knowledge" className="w-full">
                    <Button
                      variant="outline"
                      className="w-full justify-center border-neutral-800 bg-neutral-900 hover:bg-neutral-800 hover:text-[#00ff66] text-white text-xs h-10 rounded-full cursor-pointer"
                    >
                      <BrainCircuit className="h-3.5 w-3.5 mr-1.5 text-[#00ff66]" />
                      Knowledge Base
                    </Button>
                  </Link>
                  <Link href="/owner/dashboard/instructions" className="w-full">
                    <Button
                      variant="outline"
                      className="w-full justify-center border-neutral-800 bg-neutral-900 hover:bg-neutral-800 hover:text-[#00ff66] text-white text-xs h-10 rounded-full cursor-pointer"
                    >
                      <FileCode className="h-3.5 w-3.5 mr-1.5 text-[#00ff66]" />
                      Instructions
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

