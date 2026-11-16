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
  Server
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
      <div className="pb-4 border-b border-border">
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          Settings & Infrastructure
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review cloud platform status, security encryption, and external integration policies for the Zoe Engine.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: 2 Cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cloud & Database */}
          <Card className="p-6 shadow-xs">
            <div className="flex items-center gap-3 pb-4 border-b border-border">
              <div className="p-2 rounded-md bg-secondary text-foreground">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground text-sm">Database & Storage</h3>
                <p className="text-xs text-muted-foreground">Connected to Supabase PostgreSQL with Row Level Security</p>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between text-xs py-2 border-b border-border">
                <span className="text-muted-foreground">PostgreSQL Cloud Provider</span>
                <span className="font-medium text-foreground">Supabase (AWS us-east-1)</span>
              </div>
              <div className="flex items-center justify-between text-xs py-2 border-b border-border">
                <span className="text-muted-foreground">Schema Version</span>
                <span className="font-mono text-foreground font-medium">v2.1 (Multi-tenant RBAC + Auto-Migration)</span>
              </div>
              <div className="flex items-center justify-between text-xs py-2">
                <span className="text-muted-foreground">Keepalive Automation</span>
                <span className="inline-flex items-center gap-1.5 text-emerald-700 font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  GitHub Actions Active
                </span>
              </div>
            </div>
          </Card>

          {/* Environment Variables & Secrets */}
          <Card className="p-6 shadow-xs">
            <div className="flex items-center gap-3 pb-4 border-b border-border">
              <div className="p-2 rounded-md bg-secondary text-foreground">
                <Key className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground text-sm">Environment Secrets</h3>
                <p className="text-xs text-muted-foreground">Railway encrypted cloud configuration</p>
              </div>
            </div>

            <div className="mt-4 divide-y divide-border">
              {cloudVars.map((v, i) => (
                <div key={i} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono text-foreground font-medium">{v.name}</span>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{v.desc}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Security Card */}
        <div className="space-y-6">
          <Card className="p-6 shadow-xs">
            <div className="flex items-center gap-3 pb-4 border-b border-border">
              <div className="p-2 rounded-md bg-secondary text-foreground">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground text-sm">Security & Scrape Policy</h3>
                <p className="text-xs text-muted-foreground">Domain boundaries</p>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <p className="text-xs text-muted-foreground leading-relaxed">
                Zoe Knowledge Ingestion is restricted to verified domains to prevent unauthorized data exfiltration.
              </p>

              <div className="pt-2">
                <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-2">
                  Allowlisted Domains
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {allowlistedDomains.map((dom) => (
                    <span
                      key={dom}
                      className="px-2 py-1 rounded bg-secondary border border-border text-[11px] font-mono text-foreground"
                    >
                      {dom}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
