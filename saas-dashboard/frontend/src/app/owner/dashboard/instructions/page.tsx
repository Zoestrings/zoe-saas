"use client"

import { useState, useEffect } from "react"
import { 
  FileCode, 
  Save, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Sparkles, 
  Inbox,
  HelpCircle
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { api, Project, getToken } from "@/lib/api"

export default function OwnerInstructionsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string>("")
  const [loadingProjects, setLoadingProjects] = useState(true)

  const [instructions, setInstructions] = useState("")
  const [loadingSettings, setLoadingSettings] = useState(false)
  const [saving, setSaving] = useState(false)

  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" } | null>(null)

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const showNotification = (message: string, type: "success" | "error" = "success") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  const getAuthHeaders = (extra: Record<string, string> = {}) => {
    const token = getToken()
    const headers: Record<string, string> = { ...extra }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    return headers
  }

  // Load projects
  useEffect(() => {
    const load = async () => {
      setLoadingProjects(true)
      try {
        const list = await api.getProjects()
        setProjects(list || [])
        if (list && list.length > 0) {
          setSelectedProjectId(list[0].id)
        }
      } catch (err) {
        console.error("Failed to load projects:", err)
      } finally {
        setLoadingProjects(false)
      }
    }
    load()
  }, [])

  // Fetch settings when project changes
  const fetchSettings = async () => {
    if (!selectedProjectId) return
    setLoadingSettings(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${selectedProjectId}/settings`, {
        headers: getAuthHeaders(),
      })
      if (res.ok) {
        const data = await res.json()
        setInstructions(data.custom_instructions || "")
      } else {
        showNotification("Failed to fetch custom instructions.", "error")
      }
    } catch {
      showNotification("Could not reach backend service.", "error")
    } finally {
      setLoadingSettings(false)
    }
  }

  useEffect(() => {
    if (selectedProjectId) {
      fetchSettings()
    }
  }, [selectedProjectId])

  // Save settings
  const handleSave = async () => {
    if (!selectedProjectId) return
    setSaving(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${selectedProjectId}/settings`, {
        method: "POST",
        headers: getAuthHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ custom_instructions: instructions }),
      })
      const data = await res.json()
      if (res.ok) {
        showNotification(data.message || "Custom instructions saved successfully!")
      } else {
        showNotification(data.detail || "Failed to update instructions.", "error")
      }
    } catch {
      showNotification("Network error while updating instructions.", "error")
    } finally {
      setSaving(false)
    }
  }

  if (loadingProjects) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-cyan-400" />
        <p className="text-xs font-medium">Loading instructions...</p>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="py-20 max-w-xl mx-auto text-center space-y-5">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center text-slate-500 shadow-xl">
          <Inbox className="h-8 w-8 text-slate-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-white">No Assigned Bot</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            You don&apos;t have any projects assigned yet. Please contact the Zoe platform admin to deploy your bot.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <FileCode className="h-6 w-6 text-indigo-400" />
            Persona & System Instructions
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Define tone of voice, greeting messages, personality traits, and strict behavioral boundaries.
          </p>
        </div>

        {projects.length > 1 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Select Bot:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-white text-xs rounded-md px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Notifications */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center gap-3 text-xs backdrop-blur-md shadow-lg ${
            notification.type === "success"
              ? "bg-emerald-950/60 border-emerald-800/80 text-emerald-300"
              : "bg-rose-950/60 border-rose-800/80 text-rose-300"
          }`}
        >
          {notification.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Instructions Card */}
      <Card className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden backdrop-blur-sm shadow-xl">
        <CardHeader className="p-6 border-b border-slate-800/60 flex flex-row items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 mb-1">
              <Sparkles className="h-4 w-4" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Custom Prompting</span>
            </div>
            <CardTitle className="text-base font-bold text-white">System Prompt Directives</CardTitle>
            <CardDescription className="text-xs text-slate-400 mt-0.5">
              These guidelines are prepended to every incoming community member inquiry.
            </CardDescription>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={fetchSettings}
            disabled={loadingSettings}
            className="border-slate-800 bg-slate-950/60 hover:bg-slate-800 text-slate-300 text-xs h-8 cursor-pointer"
          >
            <RefreshCw className={`h-3 w-3 mr-1.5 ${loadingSettings ? "animate-spin" : ""}`} />
            Reload
          </Button>
        </CardHeader>

        <CardContent className="p-6 space-y-5">
          <div className="space-y-2">
            <Textarea
              placeholder={`e.g.\nYou are Zoe, the official AI representative for One Love.
1. Be welcoming, warm, and encourage positive community vibes.
2. If asked about the roadmap, highlight the upcoming Q1 2026 decentralized exchange launch.
3. Never give financial advice. Always remind users to DYOR.`}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              disabled={loadingSettings || saving}
              rows={12}
              className="bg-slate-950/80 border-slate-800 text-white font-mono text-xs focus:border-indigo-500 leading-relaxed min-h-[260px]"
            />
          </div>

          {/* Quick tips */}
          <div className="p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs text-slate-400 flex items-start gap-2.5">
            <HelpCircle className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="text-slate-300 font-medium">Prompt Engineering Tip:</span>
              <p className="text-[11px] text-slate-400">
                Keep rules explicit and bulleted. Use negative constraints (e.g. &ldquo;Never discuss competitor tokens&rdquo;) to enforce strict brand safety.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end pt-2">
            <Button
              onClick={handleSave}
              disabled={saving || loadingSettings}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs h-9 px-5 font-medium cursor-pointer"
            >
              {saving ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                  Saving Directives...
                </>
              ) : (
                <>
                  <Save className="h-3.5 w-3.5 mr-1.5" />
                  Save Instructions
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

