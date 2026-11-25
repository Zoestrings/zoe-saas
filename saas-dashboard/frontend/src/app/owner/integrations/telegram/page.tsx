"use client"

import { useEffect, useState } from "react"
import {
  Send,
  Plus,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  PowerOff,
  Bot,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api, Project } from "@/lib/api"

export default function TelegramIntegrationPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [integrations, setIntegrations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Multi-step Wizard State: 1 = Token, 2 = Community, 3 = Permissions
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [selectedProjectId, setSelectedProjectId] = useState("")
  const [botToken, setBotToken] = useState("")
  const [chatId, setChatId] = useState("")
  const [chatTitle, setChatTitle] = useState("")
  const [permAiQa, setPermAiQa] = useState(true)
  const [permScamAlerts, setPermScamAlerts] = useState(true)
  const [permModeration, setPermModeration] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [projList, intList] = await Promise.allSettled([
        api.getProjects(),
        api.listTelegramIntegrations(),
      ])
      if (projList.status === "fulfilled" && Array.isArray(projList.value)) {
        setProjects(projList.value)
        if (!selectedProjectId && projList.value.length > 0) {
          setSelectedProjectId(projList.value[0].id)
        }
      }
      if (intList.status === "fulfilled" && Array.isArray(intList.value)) {
        setIntegrations(intList.value)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleConnect = async () => {
    if (!selectedProjectId || !botToken.trim()) {
      setError("Please select a project and enter a valid BotFather token.")
      return
    }
    setSubmitting(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await api.addTelegramIntegration({
        project_id: selectedProjectId,
        bot_token: botToken.trim(),
        chat_id: chatId.trim() || undefined,
        chat_title: chatTitle.trim() || undefined,
        permissions: {
          ai_qa: permAiQa,
          scam_alerts: permScamAlerts,
          moderation: permModeration,
        },
      })
      setSuccessMsg(`Connected @${res.bot_username} successfully! Token encrypted at rest.`)
      setBotToken("")
      setChatId("")
      setChatTitle("")
      setStep(1)
      await loadData()
    } catch (err: any) {
      setError(err?.message || "Failed to validate and connect Telegram bot.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDisconnect = async (id: string) => {
    try {
      await api.disconnectTelegramIntegration(id)
      await loadData()
    } catch (err: any) {
      alert(err?.message || "Failed to disconnect integration.")
    }
  }

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      <div className="p-5 sm:p-6 rounded-3xl bg-[#121212] border border-[#00ff66]/30 shadow-2xl flex items-center gap-3.5">
        <div className="h-12 w-12 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shrink-0">
          <Send className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
            Telegram Integration Management
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Connect multiple Telegram bots verified live via Telegram getMe. Tokens are encrypted with AES-256-GCM and never exposed.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Multi-Step Add Bot Wizard */}
        <Card className="lg:col-span-6 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Plus className="h-4 w-4 text-[#00ff66]" />
                Add Telegram Bot Wizard
              </span>
              <span className="text-[11px] font-mono text-[#00ff66]">Step {step} of 3</span>
            </CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              {step === 1 && "Step 1: Select project & enter BotFather token for live verification."}
              {step === 2 && "Step 2: Link your Telegram group or supergroup ID."}
              {step === 3 && "Step 3: Configure autonomous agent permissions."}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className="p-3 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            {step === 1 && (
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-white">Target Project</Label>
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="w-full h-10 rounded-xl bg-neutral-950 border border-neutral-800 text-white text-xs px-3"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-white">Telegram Bot Token (from @BotFather)</Label>
                  <Input
                    type="password"
                    placeholder="7123456789:AAH..."
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl"
                  />
                </div>
                <Button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={!botToken.trim() || !selectedProjectId}
                  className="w-full h-10 rounded-xl bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer"
                >
                  Next: Community Connection
                </Button>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-white">Telegram Group / Supergroup ID (Optional)</Label>
                  <Input
                    placeholder="-1001234567890"
                    value={chatId}
                    onChange={(e) => setChatId(e.target.value)}
                    className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-white">Community Display Title (Optional)</Label>
                  <Input
                    placeholder="e.g. One Love Official Group"
                    value={chatTitle}
                    onChange={(e) => setChatTitle(e.target.value)}
                    className="bg-neutral-950 border-neutral-800 text-white text-xs h-10 rounded-xl"
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => setStep(1)} className="flex-1 h-10 rounded-xl border-neutral-800 text-xs">
                    Back
                  </Button>
                  <Button type="button" onClick={() => setStep(3)} className="flex-1 h-10 rounded-xl bg-[#00ff66] text-black font-bold text-xs">
                    Next: Permissions
                  </Button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-3">
                <label className="flex items-center gap-2.5 text-xs text-neutral-200 cursor-pointer">
                  <input type="checkbox" checked={permAiQa} onChange={(e) => setPermAiQa(e.target.checked)} />
                  <span>Enable AI Community Q&amp;A (RAG Grounded)</span>
                </label>
                <label className="flex items-center gap-2.5 text-xs text-neutral-200 cursor-pointer">
                  <input type="checkbox" checked={permScamAlerts} onChange={(e) => setPermScamAlerts(e.target.checked)} />
                  <span>Enable Real-Time Token &amp; Scam Scanning</span>
                </label>
                <label className="flex items-center gap-2.5 text-xs text-neutral-200 cursor-pointer">
                  <input type="checkbox" checked={permModeration} onChange={(e) => setPermModeration(e.target.checked)} />
                  <span>Enable Autonomous Spam &amp; Phishing Moderation</span>
                </label>
                <div className="flex gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => setStep(2)} className="flex-1 h-10 rounded-xl border-neutral-800 text-xs">
                    Back
                  </Button>
                  <Button
                    type="button"
                    onClick={handleConnect}
                    disabled={submitting}
                    className="flex-1 h-10 rounded-xl bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer"
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <ShieldCheck className="h-4 w-4 mr-1" />}
                    Verify &amp; Connect Bot
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Connected Bots Overview */}
        <Card className="lg:col-span-6 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white">Connected Telegram Bots</CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Active and disconnected integrations for your authorized projects.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <div className="py-8 flex items-center justify-center text-xs text-neutral-400 gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-[#00ff66]" />
                Loading integrations...
              </div>
            ) : integrations.length === 0 ? (
              <div className="p-6 rounded-2xl border border-dashed border-neutral-800 text-center text-xs text-neutral-500">
                No Telegram bots connected yet. Use the wizard to connect your first bot.
              </div>
            ) : (
              integrations.map((item) => (
                <div key={item.id} className="p-4 rounded-2xl bg-neutral-950/70 border border-neutral-800 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66]">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-white">@{item.bot_username}</p>
                      <p className="text-[11px] text-neutral-400">
                        {item.chat_title || item.chat_id || "Global Listen Mode"} ·{" "}
                        <span className={item.status === "connected" ? "text-[#00ff66]" : "text-neutral-500"}>
                          {item.status}
                        </span>
                      </p>
                    </div>
                  </div>
                  {item.status === "connected" && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnect(item.id)}
                      className="border-rose-900/50 bg-rose-950/20 hover:bg-rose-950/50 text-rose-400 text-xs h-8 px-3 rounded-xl cursor-pointer"
                    >
                      <PowerOff className="h-3.5 w-3.5 mr-1" />
                      Disconnect
                    </Button>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
