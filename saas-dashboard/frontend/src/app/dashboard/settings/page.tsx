"use client"

import { useState } from "react"
import { 
  ShieldCheck, 
  Database, 
  Cpu, 
  ExternalLink,
  CheckCircle2,
  Lock,
  Globe
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function DashboardSettingsPage() {
  const cloudVars = [
    { name: "SUPABASE_URL", status: "Active", desc: "PostgreSQL multi-tenant database" },
    { name: "SUPABASE_KEY", status: "Active", desc: "Client anonymous authentication key" },
    { name: "ENCRYPTION_KEY", status: "Active", desc: "Fernet AES-256 cipher key" },
    { name: "GROQ_API_KEY", status: "Active", desc: "Cloud AI inference provider" },
    { name: "ONELOVE_BOT_TOKEN", status: "Active", desc: "Telegram bot token for One Love" },
    { name: "LIVE_TEST_BOT_TOKEN", status: "Active", desc: "Telegram bot token for Hummingbird" },
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
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Settings & Infrastructure
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Review cloud platform status, security encryption, and external integration policies.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: 2 Cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cloud & Database */}
          <Card className="enterprise-card border border-slate-200 shadow-sm bg-white p-6">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
              <div className="p-2 rounded-md bg-slate-100 text-slate-700">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 text-sm">Database & Storage</h3>
                <p className="text-xs text-slate-500">Connected to Supabase PostgreSQL with Row Level Security</p>
              </div>
            </div>

            <div className="mt-4 space-y-3 text-xs text-slate-600">
              <div className="flex items-center justify-between p-3 rounded-md bg-slate-50 border border-slate-200">
                <div>
                  <div className="font-medium text-slate-900">PostgreSQL Instance</div>
                  <div className="text-slate-500 text-[11px] mt-0.5">lgpovjspaptgtbvkimmx.supabase.co</div>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Connected
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-slate-50 border border-slate-200">
                <div>
                  <div className="font-medium text-slate-900">Row Level Security (RLS)</div>
                  <div className="text-slate-500 text-[11px] mt-0.5">Multi-tenant project isolation enforced at database layer</div>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Enforced
                </span>
              </div>
            </div>
          </Card>

          {/* Environment Variables */}
          <Card className="enterprise-card border border-slate-200 shadow-sm bg-white p-6">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
              <div className="p-2 rounded-md bg-slate-100 text-slate-700">
                <Lock className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 text-sm">Environment Configuration</h3>
                <p className="text-xs text-slate-500">Cloud credentials loaded securely in the container runtime</p>
              </div>
            </div>

            <div className="mt-4 divide-y divide-slate-100">
              {cloudVars.map((v) => (
                <div key={v.name} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono font-medium text-slate-800">{v.name}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">{v.desc}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                    <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Security & Allowlist */}
        <div className="space-y-6">
          {/* Security Policy */}
          <Card className="enterprise-card border border-slate-200 shadow-sm bg-white p-6">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
              <div className="p-2 rounded-md bg-slate-100 text-slate-700">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 text-sm">Token Security</h3>
                <p className="text-xs text-slate-500">Zero-plaintext policy</p>
              </div>
            </div>

            <div className="mt-4 space-y-2 text-xs text-slate-600">
              <p>
                All Telegram bot tokens submitted via the dashboard are encrypted using <strong>Fernet AES-256</strong> before being stored in the database.
              </p>
              <p className="text-slate-500 pt-2 border-t border-slate-100 text-[11px]">
                Plaintext tokens are never stored on disk or exposed through the public API.
              </p>
            </div>
          </Card>

          {/* Domain Allowlist */}
          <Card className="enterprise-card border border-slate-200 shadow-sm bg-white p-6">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
              <div className="p-2 rounded-md bg-slate-100 text-slate-700">
                <Globe className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 text-sm">Approved Domains</h3>
                <p className="text-xs text-slate-500">Safety engine link verification</p>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
              {allowlistedDomains.map((domain) => (
                <span
                  key={domain}
                  className="px-2 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700 font-mono text-[11px]"
                >
                  {domain}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
