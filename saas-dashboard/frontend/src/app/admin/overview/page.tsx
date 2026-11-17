"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  Bot, 
  DollarSign, 
  Users, 
  Crown, 
  ArrowUpRight, 
  RefreshCw, 
  Activity, 
  Sparkles, 
  ShieldCheck, 
  Calendar,
  AlertCircle,
  TrendingUp,
  Clock
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, AdminOverviewResponse } from "@/lib/api"

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getAdminOverview()
      setData(res)
    } catch (err: any) {
      console.error("Failed to load admin overview:", err)
      setError(err.message || "Failed to load master overview data.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const summary = data?.summary || {
    total_revenue: 0,
    total_users: 0,
    total_projects: 0,
    active_bots: 0,
    pro_subscribers: 0,
  }

  const recentSignups = data?.recent_signups || []
  const revenueChart = data?.revenue_chart || []

  const maxRevenue = Math.max(...revenueChart.map(p => p.revenue), 50)

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#212833]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Sparkles className="h-6 w-6 text-[#00ff66]" />
            Master Command Center
          </h1>
          <p className="text-xs text-[#818c99] mt-1">
            Real-time platform overview: subscribers, active bots, revenue, and system health.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="border-[#212833] bg-[#12161c] hover:bg-[#181d24] text-white text-xs h-10 px-4 rounded-full cursor-pointer shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin text-[#00ff66]" : ""}`} />
            Refresh
          </Button>
          <Link href="/admin/revenue">
            <Button className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-4 rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer">
              <DollarSign className="h-3.5 w-3.5 mr-1 stroke-[3]" />
              View Revenue
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={loadData}
            className="text-rose-300 hover:text-white hover:bg-rose-900/40 text-xs"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Top 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Total Revenue (Neon Green Card) */}
        <div className="bg-[#00ff66] text-black rounded-3xl p-6 shadow-xl shadow-[#00ff66]/20 flex flex-col justify-between transition-all hover:scale-[1.01]">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-black flex items-center justify-center text-[#00ff66]">
              <DollarSign className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-black/10 text-black px-2.5 py-1 rounded-full border border-black/10">
              <TrendingUp className="h-3 w-3" /> All-Time
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-semibold text-black/70 uppercase tracking-wider block">
              Total Revenue
            </span>
            <div className="text-3xl font-black text-black tracking-tight mt-1">
              ${summary.total_revenue.toLocaleString()} <span className="text-xs font-bold text-black/80">USDT</span>
            </div>
          </div>
        </div>

        {/* Card 2: Active Fleet Bots */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between transition-all hover:border-[#00ff66]/40">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <Bot className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#1a212b] text-[#00ff66] px-2.5 py-1 rounded-full border border-[#212833]">
              <Activity className="h-3 w-3" /> Live
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-medium text-[#818c99] uppercase tracking-wider block">
              Active Bots
            </span>
            <div className="text-3xl font-bold text-white tracking-tight mt-1 flex items-baseline gap-2">
              <span className="text-[#00ff66]">{summary.active_bots}</span>
              <span className="text-xs text-[#818c99] font-normal">/ {summary.total_projects} total</span>
            </div>
          </div>
        </div>

        {/* Card 3: Total Registered Users */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between transition-all hover:border-cyan-400/40">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Users className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#1a212b] text-cyan-400 px-2.5 py-1 rounded-full border border-[#212833]">
              Accounts
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-medium text-[#818c99] uppercase tracking-wider block">
              Total Users
            </span>
            <div className="text-3xl font-bold text-white tracking-tight mt-1">
              {summary.total_users}
            </div>
          </div>
        </div>

        {/* Card 4: Pro Subscribers */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between transition-all hover:border-amber-400/40">
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Crown className="h-5 w-5" />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#1a212b] text-amber-400 px-2.5 py-1 rounded-full border border-[#212833]">
              Paid Tier
            </span>
          </div>

          <div className="mt-6">
            <span className="text-xs font-medium text-[#818c99] uppercase tracking-wider block">
              Pro Subscribers
            </span>
            <div className="text-3xl font-bold text-white tracking-tight mt-1 flex items-baseline gap-2">
              <span className="text-amber-400">{summary.pro_subscribers}</span>
              <span className="text-xs text-[#818c99] font-normal">Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row: 14-Day Revenue Chart & System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2 cols): 14-Day Revenue Chart */}
        <div className="lg:col-span-2 bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#212833]">
            <div>
              <h3 className="font-bold text-white text-base">Subscription Revenue Trend</h3>
              <p className="text-xs text-[#818c99] mt-0.5">Daily subscription income across all active tenants</p>
            </div>
            <span className="inline-flex items-center gap-1.5 text-xs text-[#00ff66] font-medium bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full">
              <span className="h-2 w-2 rounded-full bg-[#00ff66] animate-pulse" />
              14-Day Window
            </span>
          </div>

          {/* Bar Chart Visualization */}
          <div className="pt-2 pb-4">
            {revenueChart.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-xs text-[#818c99]">
                No revenue recorded yet in the past 14 days.
              </div>
            ) : (
              <div className="h-48 flex items-end justify-between gap-2 px-2">
                {revenueChart.map((point, idx) => {
                  const heightPercent = maxRevenue > 0 ? Math.max((point.revenue / maxRevenue) * 100, 4) : 4
                  const hasRevenue = point.revenue > 0
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-2 group relative">
                      {/* Tooltip */}
                      <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-black border border-neutral-700 text-white text-[10px] font-mono py-1 px-2 rounded-lg pointer-events-none whitespace-nowrap z-10 shadow-lg">
                        {point.date}: ${point.revenue} USDT
                      </div>
                      
                      {/* Bar */}
                      <div className="w-full bg-[#181d24] rounded-t-lg h-36 flex items-end overflow-hidden">
                        <div
                          style={{ height: `${heightPercent}%` }}
                          className={`w-full rounded-t-lg transition-all duration-500 ${
                            hasRevenue 
                              ? "bg-[#00ff66] shadow-[0_0_12px_rgba(0,255,102,0.4)]" 
                              : "bg-neutral-800"
                          }`}
                        />
                      </div>

                      {/* Date label */}
                      <span className="text-[10px] text-[#818c99] font-mono truncate max-w-[36px]">
                        {point.date.slice(5)}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-[#212833] flex items-center justify-between text-xs text-[#818c99]">
            <span>Subscription Rate: <strong className="text-white">$20 / month</strong></span>
            <span>Settlement: <strong className="text-[#00ff66]">Instant USDT on Solana</strong></span>
          </div>
        </div>

        {/* Right (1 col): Quick Control & Health Card */}
        <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between space-y-5">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#212833]">
              <h3 className="font-bold text-white text-base">Quick Controls</h3>
              <ShieldCheck className="h-4 w-4 text-[#00ff66]" />
            </div>

            <div className="space-y-3 pt-3">
              <Link href="/admin/projects" className="block p-3.5 rounded-2xl bg-[#161b22] border border-[#212833] hover:border-[#00ff66]/40 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-full bg-[#00ff66]/10 text-[#00ff66] flex items-center justify-center font-bold text-xs">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-bold text-white text-xs block">Manage Projects</span>
                      <span className="text-[10px] text-[#818c99]">Suspend or reactivate bots</span>
                    </div>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-[#818c99]" />
                </div>
              </Link>

              <Link href="/admin/revenue" className="block p-3.5 rounded-2xl bg-[#161b22] border border-[#212833] hover:border-[#00ff66]/40 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-xs">
                      <DollarSign className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-bold text-white text-xs block">Revenue & Invoices</span>
                      <span className="text-[10px] text-[#818c99]">On-chain audit logs</span>
                    </div>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-[#818c99]" />
                </div>
              </Link>

              <Link href="/admin/settings" className="block p-3.5 rounded-2xl bg-[#161b22] border border-[#212833] hover:border-[#00ff66]/40 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-full bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-xs">
                      <Activity className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-bold text-white text-xs block">System Health</span>
                      <span className="text-[10px] text-[#818c99]">FastAPI, RPC & DB metrics</span>
                    </div>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-[#818c99]" />
                </div>
              </Link>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#0e1116] border border-[#212833] text-center">
            <span className="text-[11px] text-[#818c99] block">Platform Access</span>
            <span className="text-xs font-bold text-[#00ff66] block mt-0.5">Super Admin Privileges Active</span>
          </div>
        </div>
      </div>

      {/* Recent Signups Table */}
      <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 text-white shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#212833]">
          <div>
            <h3 className="font-bold text-white text-base">Recent User Signups</h3>
            <p className="text-xs text-[#818c99] mt-0.5">Latest registered accounts across the platform</p>
          </div>
          <span className="text-xs text-[#818c99] font-mono">Last 5 registrations</span>
        </div>

        {recentSignups.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#818c99]">
            No users registered yet.
          </div>
        ) : (
          <div className="divide-y divide-[#212833]">
            {recentSignups.map((user) => {
              const isPro = user.plan === "pro"
              const isSuperAdmin = user.role === "super_admin"

              let formattedDate = "Recently"
              if (user.created_at) {
                try {
                  formattedDate = new Date(user.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric"
                  })
                } catch {}
              }

              return (
                <div key={user.id} className="py-3.5 flex items-center justify-between text-xs hover:bg-[#181d24]/50 rounded-xl px-2 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full bg-[#181d24] border border-[#212833] flex items-center justify-center font-bold text-xs text-[#00ff66]">
                      {user.email ? user.email[0].toUpperCase() : "U"}
                    </div>
                    <div>
                      <span className="font-semibold text-white block">{user.email}</span>
                      <span className="text-[11px] text-[#818c99] font-mono">ID: {user.id.slice(0, 10)}...</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Role badge */}
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      isSuperAdmin 
                        ? "bg-purple-500/10 text-purple-400 border border-purple-500/30" 
                        : "bg-neutral-800 text-neutral-300 border border-neutral-700"
                    }`}>
                      {user.role}
                    </span>

                    {/* Plan badge */}
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      isPro 
                        ? "bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 shadow-sm shadow-[#00ff66]/10" 
                        : "bg-neutral-800/80 text-neutral-400 border border-neutral-700"
                    }`}>
                      {isPro ? "PRO" : "FREE"}
                    </span>

                    {/* Date */}
                    <div className="flex items-center gap-1.5 text-[#818c99] text-[11px] w-28 justify-end">
                      <Clock className="h-3 w-3" />
                      <span>{formattedDate}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
