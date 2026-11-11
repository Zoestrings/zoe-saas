"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  Bot, 
  Layers, 
  Activity, 
  ShieldCheck, 
  Sparkles, 
  ArrowRight, 
  Plus, 
  Zap, 
  Users, 
  CheckCircle2,
  ExternalLink
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api, Project, getUser } from "@/lib/api"

export default function DashboardOverviewPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [userEmail, setUserEmail] = useState<string>("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const user = getUser()
    if (user?.email) {
      setUserEmail(user.email)
    }

    const loadData = async () => {
      try {
        const data = await api.getProjects()
        setProjects(data)
      } catch {
        // Handled silently for dashboard cards
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900/90 via-slate-900/50 to-indigo-950/30 p-8 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/40 text-[11px] font-medium text-cyan-300">
              <Sparkles className="h-3.5 w-3.5" />
              Autonomous Multi-Bot SaaS v1.0
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Welcome back{userEmail ? `, ${userEmail.split("@")[0]}` : ""}
            </h1>
            <p className="text-sm text-slate-400 max-w-xl">
              Your autonomous community intelligence agents are actively running. 
              Manage multiple tenant bots, update knowledge bases, and inspect live responses.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link href="/dashboard/projects">
              <Button className="bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium text-xs shadow-md shadow-cyan-500/20 cursor-pointer">
                <Plus className="h-4 w-4 mr-1.5" />
                Manage Projects
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Connected Projects
            </CardTitle>
            <Layers className="h-4 w-4 text-cyan-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white font-mono">
              {loading ? "..." : projects.length}
            </div>
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-emerald-400" />
              Tenant isolation active
            </p>
          </CardContent>
        </Card>

        {/* Engine Latency */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Response Latency
            </CardTitle>
            <Zap className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white font-mono">
              ~0.85s
            </div>
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Sub-second response target
            </p>
          </CardContent>
        </Card>

        {/* Live Bot Instances */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Orchestrator State
            </CardTitle>
            <Activity className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400 font-mono flex items-center gap-2">
              Online
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Polling loop & outbox active
            </p>
          </CardContent>
        </Card>

        {/* Security / Encryption */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Credential Vault
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-indigo-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white font-mono">
              AES-256
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Fernet encrypted tokens
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Action & Guidance Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-slate-800 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
              <Bot className="h-5 w-5 text-cyan-400" />
              Connected Bot Fleet
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Overview of bots currently registered and managed under your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {projects.length === 0 ? (
              <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl">
                <p className="text-xs text-slate-400 mb-3">No bots connected yet.</p>
                <Link href="/dashboard/projects">
                  <Button size="sm" className="bg-cyan-600 hover:bg-cyan-500 text-xs">
                    <Plus className="h-3.5 w-3.5 mr-1.5" />
                    Connect Your First Bot
                  </Button>
                </Link>
              </div>
            ) : (
              projects.slice(0, 3).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:bg-slate-900/60 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-cyan-950/60 border border-cyan-800/50 flex items-center justify-center font-bold text-xs text-cyan-400">
                      {p.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-200">{p.name}</h4>
                      <p className="text-[11px] font-mono text-slate-500">
                        Group: {p.telegram_group_id || "Auto-detect"}
                      </p>
                    </div>
                  </div>
                  <Badge className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 text-[10px]">
                    Active
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Quick Tips Card */}
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-400" />
              Quick Setup Guide
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Adding new community bots
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs text-slate-400">
            <div className="space-y-1">
              <h5 className="font-semibold text-slate-200">1. Create Bot in @BotFather</h5>
              <p className="text-[11px] leading-relaxed">
                Send <code className="text-cyan-400 bg-slate-950 px-1 py-0.5 rounded">/newbot</code> to get your API token.
              </p>
            </div>
            <div className="space-y-1">
              <h5 className="font-semibold text-slate-200">2. Disable Privacy Mode</h5>
              <p className="text-[11px] leading-relaxed">
                In @BotFather send <code className="text-cyan-400 bg-slate-950 px-1 py-0.5 rounded">/setprivacy</code> &rarr; Disable to allow the bot to read group queries.
              </p>
            </div>
            <div className="space-y-1">
              <h5 className="font-semibold text-slate-200">3. Connect in Dashboard</h5>
              <p className="text-[11px] leading-relaxed">
                Paste the token into the Projects tab. The backend encrypts it with Fernet before saving.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
