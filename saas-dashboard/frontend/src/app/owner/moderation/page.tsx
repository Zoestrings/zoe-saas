"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { Lock, ShieldAlert, ShieldCheck } from "lucide-react"
import { api } from "@/lib/api"

export default function OwnerModerationPage() {
  const [projects, setProjects] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [settings, setSettings] = useState<any>({})
  const [msg, setMsg] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getProjects()
      .then((list) => {
        setProjects(list || [])
        if (list && list.length > 0) setSelectedId(list[0].id)
      })
      .catch(() => setProjects([]))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    api.getProjectSettings(selectedId)
      .then((s) => setSettings(s || {}))
      .catch(() => setSettings({}))
  }, [selectedId])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedId) return
    setSaving(true)
    setMsg(null)
    try {
      await api.updateProjectSettings(selectedId, settings)
      setMsg("Moderation & participation settings saved.")
    } catch (err: any) {
      setMsg(err?.message || "Failed to save moderation settings")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-[#00ff66]" />
          <div>
            <h1 className="text-2xl font-bold text-white">Community Moderation &amp; Security</h1>
            <p className="text-xs text-neutral-400">
              Configure spam/link filters &amp; escalation behavior. Core anti-scam &amp; key-safety rules are always enforced.
            </p>
          </div>
        </div>
        <Link href="/owner/logs" className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs hover:bg-neutral-800">
          View Activity &amp; Escalations
        </Link>
      </div>

      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200 flex items-center gap-2">
        <Lock className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong>Immutable Safety Guardrails:</strong> Private key/seed-phrase phishing protection, financial fraud blocks,
          and credential-leak redaction are enforced at platform level and cannot be disabled.
        </span>
      </div>

      {msg && <div className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 p-3 text-xs text-cyan-200">{msg}</div>}

      {projects.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-6 text-xs text-neutral-400">
          No projects found. Create a project in <Link href="/owner/project" className="text-[#00ff66] underline">My Projects</Link> first.
        </div>
      ) : (
        <form onSubmit={handleSave} className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-5 space-y-4 text-xs">
          <div>
            <label className="block text-neutral-400 mb-1">Select Project</label>
            <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-white">
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="flex items-center gap-2 rounded-lg border border-neutral-800 bg-neutral-950 p-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.anti_spam_enabled ?? true}
                onChange={(e) => setSettings({ ...settings, anti_spam_enabled: e.target.checked })}
              />
              <span>Enable Automated Anti-Spam &amp; Scam Link Screening</span>
            </label>
            <label className="flex items-center gap-2 rounded-lg border border-neutral-800 bg-neutral-950 p-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.token_scanner_enabled ?? true}
                onChange={(e) => setSettings({ ...settings, token_scanner_enabled: e.target.checked })}
              />
              <span>Allow Community Token Security Scans</span>
            </label>
          </div>

          <div>
            <label className="block text-neutral-400 mb-1">Escalation Contact Handle (Telegram/Discord)</label>
            <input
              value={settings.escalation_contact || ""}
              onChange={(e) => setSettings({ ...settings, escalation_contact: e.target.value })}
              placeholder="@community_mod"
              className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-white"
            />
          </div>

          <button type="submit" disabled={saving} className="inline-flex items-center gap-1.5 rounded-lg bg-[#00ff66] px-4 py-2 font-semibold text-black">
            <ShieldAlert className="w-3.5 h-3.5" /> {saving ? "Saving..." : "Save Moderation Policy"}
          </button>
        </form>
      )}
    </div>
  )
}
