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
  Send,
  MessageSquare,
  Sparkles,
  Inbox,
  ShieldCheck,
  Radar,
  ArrowRight
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Project } from "@/lib/api"

export default function OwnerProjectPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [instructions, setInstructions] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)
  const [copiedGroup, setCopiedGroup] = useState<string | null>(null)

  const copyToClipboard = (text: string, type: "ca" | "group") => {
    navigator.clipboard.writeText(text)
    if (type === "ca") {
      setCopiedCA(text)
      setTimeout(() => setCopiedCA(null), 2000)
    } else {
      setCopiedGroup(text)
      setTimeout(() => setCopiedGroup(null), 2000)
    }
  }

  const loadProjectDetails = async () => {
    setLoading(true)
    try {
      const data = await api.getProjects()
      const list = data || []
      setProjects(list)

      if (list.length > 0) {
        try {
          const settings = await api.getProjectSettings(list[0].id)
          if (settings && settings.custom_instructions) {
            setInstructions(settings.custom_instructions)
          }
        } catch (settingsErr) {
          console.warn("Could not load project settings:", settingsErr)
        }
      }
    } catch (err) {
      console.warn("Failed to load projects:", err)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjectDetails()
  }, [])

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-neutral-400 gap-3">
        <RefreshCw className="h-7 w-7 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Loading project specifications...</p>
      </div>
    )
  }

  const project = projects.length > 0 ? projects[0] : null

  if (!project) {
    return (
      <div className="py-20 max-w-xl mx-auto text-center space-y-6">
        <div className="h-16 w-16 mx-auto rounded-3xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-400">
          <Bot className="h-8 w-8 text-[#00ff66]" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-white">No Assigned Project</h2>
          <p className="text-xs text-neutral-400 leading-relaxed max-w-sm mx-auto">
            You do not have a deployed bot assigned to your owner account yet. Please contact the Zoe platform administrator.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={loadProjectDetails}
          className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 rounded-full cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Check Again
        </Button>
      </div>
    )
  }

  const platformName = (project.platform || "telegram").toLowerCase()

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-neutral-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              {project.name}
            </h1>
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
              {project.status || "Live"}
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Bot configuration, gateway credentials, token parameters, and persona instructions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadProjectDetails}
            className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 px-4 rounded-full cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
          <Link href="/owner/dashboard/instructions">
            <Button
              size="sm"
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-9 px-4 rounded-full cursor-pointer shadow-md shadow-[#00ff66]/20"
            >
              <FileCode className="h-3.5 w-3.5 mr-1.5" />
              Edit Persona
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid: Bot Configuration Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Core Identity Card */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-[#121212] border-neutral-800 rounded-3xl overflow-hidden shadow-2xl">
            <CardHeader className="border-b border-neutral-800/80 pb-4">
              <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                <Bot className="h-5 w-5 text-[#00ff66]" />
                Agent Identity &amp; Gateway
              </CardTitle>
              <CardDescription className="text-xs text-neutral-400">
                Connection parameters powering your autonomous community presence.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-5">
              {/* Parameter Rows */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-1">
                  <span className="text-[11px] text-neutral-400 font-medium">Platform</span>
                  <div className="flex items-center gap-2 text-white font-bold text-sm capitalize">
                    {platformName === "discord" ? (
                      <MessageSquare className="h-4 w-4 text-[#5865F2]" />
                    ) : (
                      <Send className="h-4 w-4 text-[#2AABEE]" />
                    )}
                    <span>{project.platform || "Telegram"}</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-1">
                  <span className="text-[11px] text-neutral-400 font-medium">Internal Project ID</span>
                  <div className="font-mono text-xs text-neutral-300 font-bold truncate">
                    {project.id}
                  </div>
                </div>
              </div>

              {/* Telegram Group ID */}
              <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-1">
                <span className="text-[11px] text-neutral-400 font-medium">Linked Group / Channel ID</span>
                <div className="flex items-center justify-between gap-2 mt-1">
                  <span className="font-mono text-xs text-white">
                    {project.telegram_group_id || "Unrestricted (Global Multi-Group Mode)"}
                  </span>
                  {project.telegram_group_id && (
                    <button
                      type="button"
                      onClick={() => copyToClipboard(project.telegram_group_id!, "group")}
                      className="text-neutral-500 hover:text-[#00ff66] cursor-pointer"
                      title="Copy Group ID"
                    >
                      {copiedGroup === project.telegram_group_id ? (
                        <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Token Contract Address */}
              <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-2">
                <span className="text-[11px] text-neutral-400 font-medium">Token Contract Address (Solana / EVM)</span>
                {project.token_address ? (
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1">
                    <span className="font-mono text-xs text-white break-all bg-black/40 px-3 py-2 rounded-xl border border-neutral-800">
                      {project.token_address}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(project.token_address!, "ca")}
                        className="h-8 px-3 rounded-full border-neutral-700 bg-neutral-800 hover:bg-neutral-700 text-white text-xs cursor-pointer flex items-center gap-1.5"
                      >
                        {copiedCA === project.token_address ? (
                          <>
                            <Check className="h-3 w-3 text-[#00ff66]" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span>Copy</span>
                          </>
                        )}
                      </Button>
                      <Link href={`/investigate?ca=${encodeURIComponent(project.token_address)}`}>
                        <Button
                          size="sm"
                          className="h-8 px-3 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer flex items-center gap-1"
                        >
                          <Radar className="h-3 w-3" />
                          <span>Audit CA</span>
                        </Button>
                      </Link>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-neutral-500 italic">
                    No token contract assigned. The bot can still manage conversations without token surveillance.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Persona / Instructions Summary */}
          <Card className="bg-[#121212] border-neutral-800 rounded-3xl overflow-hidden shadow-2xl">
            <CardHeader className="border-b border-neutral-800/80 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <FileCode className="h-5 w-5 text-[#00ff66]" />
                  Active Persona &amp; System Prompt
                </CardTitle>
                <CardDescription className="text-xs text-neutral-400">
                  Custom guidance governing response tone, banned phrases, and domain expertise.
                </CardDescription>
              </div>
              <Link href="/owner/dashboard/instructions">
                <Button
                  size="sm"
                  variant="outline"
                  className="border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-8 px-3 rounded-full"
                >
                  Edit
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-6">
              {instructions ? (
                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 text-xs font-mono text-neutral-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {instructions}
                </div>
              ) : (
                <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800/80 text-center space-y-2">
                  <Sparkles className="h-6 w-6 text-[#00ff66] mx-auto opacity-80" />
                  <p className="text-xs text-neutral-300 font-semibold">Standard Web3 Community Persona</p>
                  <p className="text-[11px] text-neutral-500 max-w-sm mx-auto">
                    Operating on default Zoe intelligence prompts (JARVIS persona, concise crypto phrasing, zero markdown asterisks).
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Quick Navigation & Intelligence Links */}
        <div className="space-y-6">
          <Card className="bg-[#121212] border-neutral-800 rounded-3xl overflow-hidden shadow-2xl">
            <CardHeader className="border-b border-neutral-800/80 pb-4">
              <CardTitle className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Management Shortcuts
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-3">
              <Link href="/owner/dashboard/knowledge" className="block">
                <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900 transition-all flex items-center justify-between cursor-pointer">
                  <div className="flex items-center gap-2.5">
                    <BrainCircuit className="h-4 w-4 text-purple-400" />
                    <div>
                      <span className="text-xs font-bold text-white block">Knowledge Base</span>
                      <span className="text-[11px] text-neutral-400">FAISS document store</span>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-500" />
                </div>
              </Link>

              <Link href="/owner/dashboard/instructions" className="block">
                <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900 transition-all flex items-center justify-between cursor-pointer">
                  <div className="flex items-center gap-2.5">
                    <FileCode className="h-4 w-4 text-amber-400" />
                    <div>
                      <span className="text-xs font-bold text-white block">Custom Instructions</span>
                      <span className="text-[11px] text-neutral-400">Persona &amp; guardrails</span>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-500" />
                </div>
              </Link>

              <Link href="/owner/logs" className="block">
                <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900 transition-all flex items-center justify-between cursor-pointer">
                  <div className="flex items-center gap-2.5">
                    <MessageSquare className="h-4 w-4 text-[#00ff66]" />
                    <div>
                      <span className="text-xs font-bold text-white block">Conversation Logs</span>
                      <span className="text-[11px] text-neutral-400">Live chat surveillance</span>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-500" />
                </div>
              </Link>

              <Link href="/watchlist" className="block">
                <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800 hover:border-[#00ff66]/50 hover:bg-neutral-900 transition-all flex items-center justify-between cursor-pointer">
                  <div className="flex items-center gap-2.5">
                    <Radar className="h-4 w-4 text-cyan-400" />
                    <div>
                      <span className="text-xs font-bold text-white block">Token Surveillance</span>
                      <span className="text-[11px] text-neutral-400">15-min liquidity sweep</span>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-500" />
                </div>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
