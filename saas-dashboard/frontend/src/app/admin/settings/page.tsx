"use client"

import { useState } from "react"
import { 
  ShieldCheck, 
  Database, 
  Cpu, 
  ExternalLink,
  CheckCircle2,
  Lock,
  Globe,
  Key,
  Server,
  Sparkles
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function AdminSettingsPage() {
  const cloudVars = [
    { name: "SUPABASE_URL", status: "Active", desc: "PostgreSQL multi-tenant database" },
    { name: "SUPABASE_KEY", status: "Active", desc: "Client anonymous authentication key" },
    { name: "ENCRYPTION_KEY", status: "Active", desc: "Fernet AES-256 cipher key" },
    { name: "ENGINE_SHARED_SECRET", status: "Active", desc: "Zero-Railway Dynamic Spawning Bridge" },
    { name: "GROQ_API_KEY", status: "Active", desc: "Cloud AI inference provider" },
    { name: "ZOE_BOT_TOKEN", status: "Active", desc: "Main Platform Admin Bot (@ZoeCoreBot)" },
  ]

  const allowlistedDomains = [
    "onelovesailingcoin.com",
    "x.com",
    "twitter.com",
    "t.me",
    "tiktok.com",
    "dexscreener.com",
    "solscan.io",
    "github.com"
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="pb-4 border-b border-[#212833]">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Server className="h-6 w-6 text-[#00ff66]" />
          Settings & Infrastructure
        </h1>
        <p className="text-xs text-[#818c99] mt-1">
          Review cloud platform status, security encryption, and external integration policies for the Zoe Engine.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: 2 Cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cloud & Database */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-[#212833]">
              <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Database & Storage</h3>
                <p className="text-xs text-[#818c99]">Connected to Supabase PostgreSQL with Row Level Security</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs py-2 border-b border-[#212833]">
                <span className="text-[#818c99]">PostgreSQL Cloud Provider</span>
                <span className="font-bold text-white">Supabase (AWS us-east-1)</span>
              </div>
              <div className="flex items-center justify-between text-xs py-2 border-b border-[#212833]">
                <span className="text-[#818c99]">Schema Version</span>
                <span className="font-mono text-[#00ff66] font-bold">v2.1 (Multi-tenant RBAC + Auto-Migration)</span>
              </div>
              <div className="flex items-center justify-between text-xs py-2">
                <span className="text-[#818c99]">Keepalive Automation</span>
                <span className="inline-flex items-center gap-1.5 text-[#00ff66] font-bold">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  GitHub Actions Active
                </span>
              </div>
            </div>
          </div>

          {/* Environment Variables & Secrets */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-[#212833]">
              <div className="h-10 w-10 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <Key className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Environment Secrets</h3>
                <p className="text-xs text-[#818c99]">Railway encrypted cloud configuration</p>
              </div>
            </div>

            <div className="divide-y divide-[#212833]">
              {cloudVars.map((v, i) => (
                <div key={i} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono text-white font-bold">{v.name}</span>
                    <p className="text-[11px] text-[#818c99] mt-0.5">{v.desc}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#00ff66] bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-0.5 rounded-full">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66]" />
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Security Card */}
        <div className="space-y-6">
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-[#212833]">
              <div className="h-10 w-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Security Policy</h3>
                <p className="text-xs text-[#818c99]">Domain boundaries</p>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-[#818c99] leading-relaxed">
                Zoe Knowledge Ingestion is restricted to verified domains to prevent unauthorized data exfiltration.
              </p>

              <div className="pt-2">
                <span className="text-[10px] font-bold text-[#818c99] uppercase tracking-wider block mb-2">
                  Allowlisted Domains
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {allowlistedDomains.map((dom) => (
                    <span
                      key={dom}
                      className="px-2.5 py-1 rounded-full bg-[#161b22] border border-[#212833] text-[11px] font-mono text-[#00ff66]"
                    >
                      {dom}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
