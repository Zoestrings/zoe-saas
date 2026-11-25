"use client"

import React, { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { Briefcase, FileSpreadsheet, Gem, Plus, Trash2, Users } from "lucide-react"
import { api } from "@/lib/api"

export default function OwnerWorkspacePage() {
  const [tab, setTab] = useState<"team" | "nft" | "investor" | "invoices">("team")
  const [members, setMembers] = useState<any[]>([])
  const [collections, setCollections] = useState<any[]>([])
  const [nftLeads, setNftLeads] = useState<any[]>([])
  const [pipeline, setPipeline] = useState<any[]>([])
  const [invoices, setInvoices] = useState<any[]>([])

  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState<"admin" | "editor" | "viewer">("viewer")
  const [colName, setColName] = useState("")
  const [colChain, setColChain] = useState("solana")
  const [leadHandle, setLeadHandle] = useState("")
  const [invName, setInvName] = useState("")
  const [invType, setInvType] = useState("vc")
  const [msg, setMsg] = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    try {
      const [tRes, cRes, lRes, pRes, iRes] = await Promise.all([
        api.listOwnerTeam(),
        api.listNFTCollections(),
        api.listNFTLeads(),
        api.listInvestorPipeline(),
        api.listBillingInvoices(),
      ])
      setMembers(tRes.members || [])
      setCollections(cRes.collections || [])
      setNftLeads(lRes.leads || [])
      setPipeline(pRes.pipeline || [])
      setInvoices(iRes.invoices || [])
    } catch (err: any) {
      setMsg(err?.message || "Failed to load workspace")
    }
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Organization Workspace: Team, NFT Growth, Investors &amp; Invoices</h1>
          <p className="text-xs text-slate-400 mt-1">
            Private, tenant-isolated operations for your organization
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/owner/social" className="rounded-lg border border-cyan-500/40 px-3 py-1.5 text-xs text-cyan-300 hover:bg-cyan-500/10">
            Social &amp; Growth
          </Link>
          <Link href="/owner/dashboard" className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs hover:bg-slate-800">
            Back to Dashboard
          </Link>
        </div>
      </div>

      {msg && <div className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 p-3 text-xs text-cyan-200">{msg}</div>}

      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        <button onClick={() => setTab("team")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "team" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <Users className="w-3.5 h-3.5" /> Team ({members.length})
        </button>
        <button onClick={() => setTab("nft")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "nft" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <Gem className="w-3.5 h-3.5" /> NFT Growth &amp; Sales ({collections.length})
        </button>
        <button onClick={() => setTab("investor")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "investor" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <Briefcase className="w-3.5 h-3.5" /> Investor Intelligence ({pipeline.length})
        </button>
        <button onClick={() => setTab("invoices")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${tab === "invoices" ? "bg-cyan-500 text-black" : "bg-slate-900 text-slate-300"}`}>
          <FileSpreadsheet className="w-3.5 h-3.5" /> Invoices ({invoices.length})
        </button>
      </div>

      {tab === "team" && (
        <div className="space-y-4">
          <form
            onSubmit={async (e) => {
              e.preventDefault()
              if (!inviteEmail.trim()) return
              await api.inviteOwnerTeamMember({ member_email: inviteEmail, role: inviteRole })
              setInviteEmail("")
              await loadAll()
            }}
            className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 flex flex-wrap gap-2"
          >
            <input value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder="teammate@project.xyz" className="flex-1 min-w-[200px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white" />
            <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value as any)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white">
              <option value="viewer">Viewer (Read-Only)</option>
              <option value="editor">Editor</option>
              <option value="admin">Org Admin</option>
            </select>
            <button type="submit" className="inline-flex items-center gap-1 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-black">
              <Plus className="w-3.5 h-3.5" /> Invite Member
            </button>
          </form>

          <div className="space-y-2">
            {members.map((m) => (
              <div key={m.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-3 text-xs flex items-center justify-between">
                <div>
                  <span className="font-semibold text-white">{m.member_email}</span>{" "}
                  <span className="text-slate-400">({m.role} · {m.status})</span>
                </div>
                <button onClick={() => api.removeOwnerTeamMember(m.id).then(loadAll)} className="text-rose-400 hover:text-rose-300">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "nft" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <form
              onSubmit={async (e) => {
                e.preventDefault()
                if (!colName.trim()) return
                await api.createNFTCollection({ name: colName, chain: colChain })
                setColName("")
                await loadAll()
              }}
              className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-2 text-xs"
            >
              <div className="font-semibold text-white">Register NFT Collection &amp; Mint Campaign</div>
              <div className="flex gap-2">
                <input value={colName} onChange={(e) => setColName(e.target.value)} placeholder="Collection name..." className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
                <select value={colChain} onChange={(e) => setColChain(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white">
                  <option value="solana">Solana</option>
                  <option value="ethereum">Ethereum</option>
                  <option value="base">Base</option>
                </select>
                <button type="submit" className="rounded-lg bg-cyan-500 px-3 py-2 font-semibold text-black">Add</button>
              </div>
            </form>

            <form
              onSubmit={async (e) => {
                e.preventDefault()
                if (!leadHandle.trim()) return
                await api.createNFTLead({ handle_or_wallet: leadHandle })
                setLeadHandle("")
                await loadAll()
              }}
              className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-2 text-xs"
            >
              <div className="font-semibold text-white">Add Opt-In Buyer Lead</div>
              <div className="flex gap-2">
                <input value={leadHandle} onChange={(e) => setLeadHandle(e.target.value)} placeholder="Wallet or opt-in handle..." className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
                <button type="submit" className="rounded-lg border border-violet-500/40 bg-violet-500/20 px-3 py-2 text-violet-200">Save Lead</button>
              </div>
            </form>
          </div>

          <div className="space-y-2 text-xs">
            {collections.map((c) => (
              <div key={c.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-3 flex justify-between">
                <div>
                  <span className="font-semibold text-white">{c.name}</span> ({c.chain}) · Referral:{" "}
                  <span className="font-mono text-cyan-300">{c.referral_code}</span>
                </div>
                <span className="text-slate-400">Verified Sales: {c.verified_sales_count}</span>
              </div>
            ))}
            {nftLeads.length > 0 && <div className="text-slate-400 pt-2">Buyer Leads: {nftLeads.length} recorded</div>}
          </div>
        </div>
      )}

      {tab === "investor" && (
        <div className="space-y-4">
          <form
            onSubmit={async (e) => {
              e.preventDefault()
              if (!invName.trim()) return
              await api.createInvestorPipelineEntry({ investor_name: invName, firm_type: invType })
              setInvName("")
              await loadAll()
            }}
            className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 flex flex-wrap gap-2 text-xs"
          >
            <input value={invName} onChange={(e) => setInvName(e.target.value)} placeholder="VC, Angel, or Ecosystem Grant..." className="flex-1 min-w-[200px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            <select value={invType} onChange={(e) => setInvType(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white">
              <option value="vc">VC Fund</option>
              <option value="angel">Angel</option>
              <option value="grant">Ecosystem Grant</option>
              <option value="ecosystem_fund">Ecosystem Fund</option>
            </select>
            <button type="submit" className="rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-black">Add to Private Pipeline</button>
          </form>

          <div className="space-y-2 text-xs">
            {pipeline.map((p) => (
              <div key={p.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-3 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-white">{p.investor_name}</span>{" "}
                  <span className="text-slate-400">({p.firm_type})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-cyan-300">{p.stage}</span>
                  <button onClick={() => api.deleteInvestorPipelineEntry(p.id).then(loadAll)} className="text-rose-400">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "invoices" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-2 text-xs">
          {invoices.length === 0 ? (
            <p className="text-slate-400">No invoices generated yet.</p>
          ) : (
            invoices.map((inv) => (
              <div key={inv.id} className="flex justify-between rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                <span>
                  <strong className="text-white">{inv.id}</strong> — {inv.plan.toUpperCase()} (${inv.amount_usdt} USDT)
                </span>
                <span className="text-emerald-400">{inv.status} · {new Date(inv.issued_at).toLocaleDateString()}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
