"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { Building2, Plus, ShieldCheck } from "lucide-react"
import { api } from "@/lib/api"

export default function AdminMarketAcquisitionPage() {
  const [leads, setLeads] = useState<any[]>([])
  const [compliance, setCompliance] = useState<any>(null)
  const [projectName, setProjectName] = useState("")
  const [ecosystem, setEcosystem] = useState("solana")
  const [contactChannel, setContactChannel] = useState("")
  const [error, setError] = useState<string | null>(null)

  const loadLeads = async () => {
    try {
      const res = await api.listAdminMarketAcquisition()
      setLeads(res.leads || [])
      setCompliance(res.compliance)
    } catch (err: any) {
      setError(err?.message || "Super Admin authorization required")
    }
  }

  useEffect(() => {
    loadLeads()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectName.trim()) return
    await api.createAdminMarketAcquisitionLead({
      project_name: projectName,
      ecosystem,
      contact_channel: contactChannel,
    })
    setProjectName("")
    setContactChannel("")
    await loadLeads()
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Building2 className="w-6 h-6 text-cyan-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Internal Market Acquisition Engine</h1>
            <p className="text-xs text-slate-400">
              Super Admin internal Zoe growth pipeline — strictly isolated from customer Investor &amp; Growth Intelligence
            </p>
          </div>
        </div>
        <Link href="/admin/overview" className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs hover:bg-slate-800">
          Back to Admin Overview
        </Link>
      </div>

      {error && <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-200">{error}</div>}

      {compliance && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-300 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>{compliance.policy_notice}</span>
        </div>
      )}

      <form onSubmit={handleCreate} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 flex flex-wrap gap-2">
        <input
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="Target Web3 project name..."
          className="flex-1 min-w-[200px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
        />
        <input
          value={ecosystem}
          onChange={(e) => setEcosystem(e.target.value)}
          placeholder="Ecosystem (solana, base...)"
          className="w-36 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
        />
        <input
          value={contactChannel}
          onChange={(e) => setContactChannel(e.target.value)}
          placeholder="Authorized contact / website..."
          className="flex-1 min-w-[180px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
        />
        <button type="submit" className="inline-flex items-center gap-1 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-black">
          <Plus className="w-3.5 h-3.5" /> Add Lead
        </button>
      </form>

      <div className="space-y-2">
        {leads.map((l) => (
          <div key={l.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-3 text-xs flex items-center justify-between">
            <div>
              <div className="font-semibold text-white">
                {l.project_name} <span className="text-slate-400">({l.ecosystem})</span>
              </div>
              <div className="text-slate-400">{l.contact_channel || "No contact recorded"}</div>
            </div>
            <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] text-cyan-300">{l.stage}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
