"use client"

import { Settings, Shield, Sliders, Database, Key, CheckCircle2, Lock } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

export default function DashboardSettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="pb-4 border-b border-slate-800">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Settings className="h-6 w-6 text-cyan-400" />
          Engine & Cloud Settings
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Global LLM router failover, Supabase credentials, and encryption vault configuration.
        </p>
      </div>

      {/* Database / Cloud Status */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
              <Database className="h-4 w-4 text-emerald-400" />
              Supabase PostgreSQL Connection
            </CardTitle>
            <Badge className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 text-[10px]">
              Connected
            </Badge>
          </div>
          <CardDescription className="text-xs text-slate-400">
            Active multi-tenant database endpoint with Row Level Security (RLS)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs text-slate-300">Supabase Project URL</Label>
            <Input 
              value="https://lgpovjspaptgtbvkimmx.supabase.co" 
              disabled 
              className="bg-slate-950/80 border-slate-800 text-slate-300 font-mono text-xs" 
            />
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 pt-1">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Table <code className="text-cyan-400">public.projects</code> active with RLS policies</span>
          </div>
        </CardContent>
      </Card>

      {/* Encryption Vault */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
            <Lock className="h-4 w-4 text-indigo-400" />
            Credential Vault Security
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Fernet symmetric cipher details for bot credentials
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs text-slate-300">Cipher Specification</Label>
            <Input 
              value="AES-128-CBC + HMAC-SHA256 (Fernet Specification)" 
              disabled 
              className="bg-slate-950/80 border-slate-800 text-slate-300 font-mono text-xs" 
            />
          </div>
          <p className="text-[11px] text-slate-500">
            Bot tokens are encrypted in memory prior to transmission to Supabase, guaranteeing zero-plaintext storage.
          </p>
        </CardContent>
      </Card>

      {/* LLM Router */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
            <Key className="h-4 w-4 text-cyan-400" />
            LLM Provider Configuration
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Primary and failover inference providers for the intelligence engine.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <Label className="text-xs text-slate-300">Primary Provider</Label>
            <Input 
              value="Groq (Llama-3.3-70b-versatile)" 
              disabled 
              className="bg-slate-950/80 border-slate-800 text-slate-300 font-mono text-xs" 
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-slate-300">Failover Provider</Label>
            <Input 
              value="Anthropic (Claude 3.5 Sonnet)" 
              disabled 
              className="bg-slate-950/80 border-slate-800 text-slate-300 font-mono text-xs" 
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
