"use client"

import { Suspense, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import {
  Layers,
  ExternalLink,
  Loader2,
  PowerOff,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Project } from "@/lib/api"

function DiscordIntegrationContent() {
  const searchParams = useSearchParams()
  const oauthCode = searchParams.get("code")
  const oauthState = searchParams.get("state")

  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState("")
  const [servers, setServers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [projRes, srvRes] = await Promise.allSettled([
        api.getProjects(),
        api.listDiscordIntegrations(),
      ])
      if (projRes.status === "fulfilled" && Array.isArray(projRes.value)) {
        setProjects(projRes.value)
        if (!selectedProjectId && projRes.value.length > 0) {
          setSelectedProjectId(projRes.value[0].id)
        }
      }
      if (srvRes.status === "fulfilled" && Array.isArray(srvRes.value)) {
        setServers(srvRes.value)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (oauthCode && oauthState) {
      setConnecting(true)
      api
        .completeDiscordOAuth(oauthCode, oauthState)
        .then((res) => {
          setStatusMsg(`Connected Discord server: ${res.guild_name || res.bot_username}`)
          loadData()
        })
        .catch((err: any) => {
          setErrorMsg(err?.message || "Discord OAuth2 callback failed.")
        })
        .finally(() => setConnecting(false))
    }
  }, [oauthCode, oauthState])

  const handleStartOAuth = async () => {
    if (!selectedProjectId) {
      setErrorMsg("Please select a project first.")
      return
    }
    setConnecting(true)
    setErrorMsg(null)
    try {
      const { oauth_url } = await api.startDiscordOAuth(selectedProjectId)
      window.location.href = oauth_url
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to initiate Discord OAuth2 flow.")
      setConnecting(false)
    }
  }

  const handleDisconnect = async (id: string) => {
    try {
      await api.disconnectDiscordIntegration(id)
      await loadData()
    } catch (err: any) {
      alert(err?.message || "Failed to disconnect Discord server.")
    }
  }

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      <div className="p-5 sm:p-6 rounded-3xl bg-[#121212] border border-[#5865F2]/40 shadow-2xl flex items-center gap-3.5">
        <div className="h-12 w-12 rounded-2xl bg-[#5865F2]/15 border border-[#5865F2]/30 flex items-center justify-center text-[#5865F2] shrink-0">
          <Layers className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
            Discord OAuth2 Integration
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Authorize Zoe via official Discord OAuth2 to monitor channels, answer community questions, and run security scans.
          </p>
        </div>
      </div>

      {statusMsg && (
        <div className="p-4 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="lg:col-span-5 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white">Connect Discord Server</CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Select your target Zoe project and launch official Discord OAuth2 authorization.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
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
            <Button
              type="button"
              onClick={handleStartOAuth}
              disabled={connecting || !selectedProjectId}
              className="w-full h-11 rounded-2xl bg-[#5865F2] hover:bg-[#4752C4] text-white font-bold text-xs cursor-pointer"
            >
              {connecting ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <ExternalLink className="h-4 w-4 mr-1.5" />}
              Install Zoe via Discord OAuth2
            </Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-7 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white">Connected Discord Servers</CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Guilds linked to your tenant workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <div className="py-8 flex items-center justify-center text-xs text-neutral-400 gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-[#00ff66]" />
                Loading servers...
              </div>
            ) : servers.length === 0 ? (
              <div className="p-6 rounded-2xl border border-dashed border-neutral-800 text-center text-xs text-neutral-500">
                No Discord servers connected yet.
              </div>
            ) : (
              servers.map((srv) => (
                <div key={srv.id} className="p-4 rounded-2xl bg-neutral-950/70 border border-neutral-800 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-bold text-white">{srv.guild_name || srv.bot_username}</p>
                    <p className="text-[11px] font-mono text-neutral-400">
                      Guild ID: {srv.guild_id || "—"} ·{" "}
                      <span className={srv.status === "connected" ? "text-[#00ff66]" : "text-neutral-500"}>
                        {srv.status}
                      </span>
                    </p>
                  </div>
                  {srv.status === "connected" && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnect(srv.id)}
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

export default function DiscordIntegrationPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-xs text-neutral-400">Loading Discord Integration...</div>}>
      <DiscordIntegrationContent />
    </Suspense>
  )
}
