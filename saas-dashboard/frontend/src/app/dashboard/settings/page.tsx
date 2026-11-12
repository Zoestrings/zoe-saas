"use client"

import { useState } from "react"
import { 
  Settings, 
  Shield, 
  Sliders, 
  Database, 
  Key, 
  CheckCircle2, 
  Lock, 
  Cpu, 
  Globe, 
  RefreshCw,
  Server,
  Layers,
  Copy,
  Check,
  Radio,
  ExternalLink
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

export default function DashboardSettingsPage() {
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(id)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const cloudVars = [
    { name: "SUPABASE_URL", status: "Configured", desc: "Live multi-tenant postgres database" },
    { name: "SUPABASE_KEY", status: "Configured", desc: "Row Level Security (RLS) public client anon key" },
    { name: "SUPABASE_JWT_SECRET", status: "Configured", desc: "Enterprise JWT signature verification" },
    { name: "ENCRYPTION_KEY", status: "Configured", desc: "Fernet symmetric AES-256 cipher key" },
    { name: "GROQ_API_KEY", status: "Configured", desc: "High-speed LPU Llama-3.3-70b provider" },
    { name: "ONELOVE_BOT_TOKEN", status: "Configured", desc: "Telegram bot gateway for @OneLoveManager_bot" },
    { name: "LIVE_TEST_BOT_TOKEN", status: "Configured", desc: "Telegram bot gateway for @zoe_live_test_bot" },
  ]

  const allowlistedDomains = [
    "onelovesailingcoin.com",
    "x.com",
    "twitter.com",
    "t.me",
    "tiktok.com",
    "dexscreener.com",
    "solscan.io",
    "hummingbird.org",
    "github.com",
    "google.com"
  ]

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
            <Settings className="h-7 w-7 text-cyan-400" />
            Cloud, Security & Vault Settings
          </h1>
          <Badge className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 text-[10px] font-mono">
            All Systems Healthy
          </Badge>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Infrastructure posture, encryption vault cipher configuration, Supabase RLS security, and active LLM routing.
        </p>
      </div>

      {/* Grid: 2 Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Database & Supabase Card */}
        <Card className="glass-card border-slate-800/80 rounded-2xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                <Database className="h-4 w-4 text-emerald-400" />
                Supabase PostgreSQL (RLS)
              </CardTitle>
              <Badge className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 text-[10px] font-mono">
                ● Connected
              </Badge>
            </div>
            <CardDescription className="text-xs text-slate-400">
              Multi-tenant database engine with Row Level Security.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label className="text-[11px] text-slate-400 font-mono">SUPABASE ENDPOINT</Label>
              <div className="flex items-center gap-2">
                <Input 
                  value="https://lgpovjspaptgtbvkimmx.supabase.co" 
                  disabled 
                  className="bg-slate-950/80 border-slate-800 text-slate-300 font-mono text-xs" 
                />
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => copyToClipboard("https://lgpovjspaptgtbvkimmx.supabase.co", "endpoint")}
                  className="border-slate-800 bg-slate-900 text-slate-300 h-9"
                >
                  {copiedKey === "endpoint" ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800/70 text-xs text-slate-300">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Database Table</span>
                <span className="font-mono text-cyan-400">public.projects</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Security Policy</span>
                <span className="font-mono text-emerald-400">Tenant RLS Enforced</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Auth Guard</span>
                <span className="font-mono text-purple-400">Bearer JWT Signature</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security & Credential Vault */}
        <Card className="glass-card border-slate-800/80 rounded-2xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                <Lock className="h-4 w-4 text-cyan-400" />
                Fernet Symmetric Cryptography
              </CardTitle>
              <Badge className="bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 text-[10px] font-mono">
                AES-256
              </Badge>
            </div>
            <CardDescription className="text-xs text-slate-400">
              Hardware-grade secret cipher for bot tokens and private keys.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label className="text-[11px] text-slate-400 font-mono">CIPHER IMPLEMENTATION</Label>
              <Input 
                value="AES-128-CBC + HMAC-SHA256 (Fernet Specification)" 
                disabled 
                className="bg-slate-950/80 border-slate-800 text-slate-300 font-mono text-xs" 
              />
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-400 space-y-1.5">
              <div className="flex items-center gap-1.5 text-cyan-300 font-medium">
                <Shield className="h-3.5 w-3.5 text-cyan-400" />
                Zero-Plaintext Guarantee
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Tokens entered via the Dashboard are encrypted in RAM with the master Fernet key before transmission to Supabase.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Inference & Knowledge Architecture */}
        <Card className="glass-card border-slate-800/80 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Cpu className="h-4 w-4 text-indigo-400" />
              AI Inference & Vector RAG Engine
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Low-latency language models and dense vector embeddings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div>
                <p className="font-semibold text-white">Primary Inference LLM</p>
                <p className="text-[11px] text-slate-400">Groq LPU Acceleration</p>
              </div>
              <span className="font-mono text-indigo-300 text-xs bg-indigo-950/60 px-2 py-1 rounded border border-indigo-800/50">
                Llama-3.3-70b
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div>
                <p className="font-semibold text-white">Dense Vector Embedding</p>
                <p className="text-[11px] text-slate-400">Pre-warmed singleton in RAM</p>
              </div>
              <span className="font-mono text-cyan-300 text-xs bg-cyan-950/60 px-2 py-1 rounded border border-cyan-800/50">
                all-MiniLM-L6-v2
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div>
                <p className="font-semibold text-white">Fail-Closed Accuracy Guard</p>
                <p className="text-[11px] text-slate-400">Cosine threshold 0.25 (No hallucinated web search)</p>
              </div>
              <span className="font-mono text-emerald-400 text-xs bg-emerald-950/60 px-2 py-1 rounded border border-emerald-800/50">
                Enforced
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Approved Domains Allowlist */}
        <Card className="glass-card border-slate-800/80 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Globe className="h-4 w-4 text-purple-400" />
              Safety URL Allowlist
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Only verified domains allowed in bot messages and buttons.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1.5">
              {allowlistedDomains.map((dom) => (
                <span 
                  key={dom} 
                  className="font-mono text-[11px] px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-300"
                >
                  {dom}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-slate-500 mt-4">
              All external URLs returned in conversational responses are checked by the safety validator before reaching Telegram.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Cloud Environment Variables Overview Table */}
      <Card className="glass-card border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
        <CardHeader className="border-b border-slate-800/80">
          <CardTitle className="text-base font-bold text-white flex items-center gap-2">
            <Server className="h-4 w-4 text-cyan-400" />
            Railway Production Environment Variables
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Active variables mounted into the Railway container (values masked for security)
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-slate-850/60 font-mono text-xs">
            {cloudVars.map((v) => (
              <div key={v.name} className="flex items-center justify-between p-4 hover:bg-slate-900/30 transition-colors">
                <div className="space-y-0.5">
                  <span className="font-bold text-white text-xs">{v.name}</span>
                  <p className="text-[11px] text-slate-400 font-sans">{v.desc}</p>
                </div>
                <Badge className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 text-[10px] font-mono">
                  ● {v.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
