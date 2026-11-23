"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  DollarSign,
  TrendingUp,
  Users,
  CheckCircle2,
  Clock,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  Search,
  ShieldAlert,
  Loader2,
  Wallet,
  ArrowUpRight,
  Filter,
  Sparkles,
  Crown
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
import {
  api,
  getUser,
  AdminRevenueResponse,
  AdminRevenueInvoice,
  AdminSystemHealthResponse
} from "@/lib/api"

export default function AdminRevenuePage() {
  const router = useRouter()
  const [data, setData] = useState<AdminRevenueResponse | null>(null)
  const [health, setHealth] = useState<AdminSystemHealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<"all" | "paid" | "pending">("all")

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const loadRevenueData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [res, sysHealth] = await Promise.allSettled([
        api.getAdminRevenue(),
        api.getAdminSystemHealth(),
      ])
      if (res.status === "fulfilled") setData(res.value)
      if (sysHealth.status === "fulfilled") setHealth(sysHealth.value)
    } catch (err: any) {
      setError(err.message || "Failed to load platform revenue analytics.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const currentUser = getUser()
    if (currentUser && currentUser.role && currentUser.role !== "super_admin") {
      // Non-super-admins are barred from revenue intelligence
      setError("Access denied: You must be a Super Admin to view platform revenue.")
      setLoading(false)
      return
    }
    loadRevenueData()
  }, [])

  if (error && error.includes("Access denied")) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
        <div className="h-16 w-16 rounded-3xl bg-rose-950/40 border border-rose-800/60 flex items-center justify-center text-rose-400">
          <ShieldAlert className="h-8 w-8" />
        </div>
        <div className="space-y-1 max-w-md">
          <h2 className="text-xl font-black text-white">Super Admin Access Required</h2>
          <p className="text-xs text-neutral-400">
            Platform revenue intelligence and on-chain invoice audit trails are restricted to authorized platform administrators.
          </p>
        </div>
        <Link href="/admin/overview">
          <Button className="h-10 px-6 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20">
            Return to Admin Overview
          </Button>
        </Link>
      </div>
    )
  }

  const invoices = data?.invoices || []
  const summary = data?.summary || {
    total_revenue: 0,
    paid_invoices_count: 0,
    pending_invoices_count: 0,
    active_pro_subscribers: 0,
    monthly_run_rate: 0
  }

  // Filter & Search Logic
  const filteredInvoices = invoices.filter((inv) => {
    const matchesStatus =
      statusFilter === "all" ? true : inv.status.toLowerCase() === statusFilter

    const query = searchQuery.trim().toLowerCase()
    const matchesQuery =
      !query ||
      inv.email.toLowerCase().includes(query) ||
      inv.id.toLowerCase().includes(query) ||
      (inv.tx_hash && inv.tx_hash.toLowerCase().includes(query))

    return matchesStatus && matchesQuery
  })

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full text-xs font-bold text-[#00ff66]">
            <DollarSign className="h-3.5 w-3.5" />
            Zoe Financial Intelligence · Super Admin Portal
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white">
            Revenue & Subscriptions
          </h1>
          <p className="text-xs text-neutral-400 max-w-2xl">
            Real-time on-chain Solana USDT subscription settlements, subscriber volumes, and immutable transaction audit trails.
          </p>
        </div>

        {/* Global Action Controls */}
        <div className="flex items-center gap-3">
          {/* System Health Badge */}
          <div
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-semibold border ${
              health?.status === "healthy"
                ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400"
                : health?.status === "degraded"
                ? "bg-amber-950/40 border-amber-500/40 text-amber-400"
                : "bg-neutral-900 border-neutral-700 text-neutral-300"
            }`}
            title={`Supabase: ${health?.services?.supabase?.status || "ok"} · Engine: ${health?.services?.engine?.status || "ok"} · Groq AI: ${health?.services?.ai?.status || "ok"}`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                health?.status === "healthy"
                  ? "bg-emerald-400 animate-pulse"
                  : "bg-amber-400"
              }`}
            />
            <span>{health?.status === "healthy" ? "Engine: Operational" : "Engine: Checking..."}</span>
          </div>

          <a
            href="https://solscan.io/account/4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-xs font-semibold text-white transition-all shadow-md"
          >
            <Wallet className="h-3.5 w-3.5 text-[#00ff66]" />
            <span>Treasury Wallet</span>
            <ExternalLink className="h-3 w-3 text-neutral-400" />
          </a>

          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={loadRevenueData}
            disabled={loading}
            className="h-10 w-10 rounded-full border-neutral-800 bg-[#121212] hover:bg-neutral-800 text-white cursor-pointer"
            title="Refresh Revenue"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#00ff66]" : ""}`} />
          </Button>
        </div>
      </div>

      {/* 4 WealthWave Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Vibrant Hero Card (Total Revenue Settled) */}
        <div className="bg-[#00ff66] text-black rounded-3xl p-6 flex flex-col justify-between shadow-xl shadow-[#00ff66]/10 relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider text-black/80">
              Total Revenue
            </span>
            <div className="h-8 w-8 rounded-full bg-black/10 flex items-center justify-center">
              <DollarSign className="h-4 w-4 text-black" />
            </div>
          </div>

          <div className="my-3">
            <div className="text-3xl sm:text-4xl font-black tracking-tight text-black font-mono">
              ${summary.total_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] font-bold text-black/70 mt-1">
              USDT (Solana Mainnet)
            </div>
          </div>

          <div className="pt-3 border-t border-black/15 text-[11px] font-bold text-black/80 flex items-center gap-1.5">
            <TrendingUp className="h-3.5 w-3.5 text-black" />
            <span>100% On-Chain · $0 Gateway Fees</span>
          </div>
        </div>

        {/* Card 2: Active Pro Subscribers */}
        <Card className="bg-[#121212] border-neutral-800 rounded-3xl p-6 flex flex-col justify-between shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">
              Pro Subscribers
            </span>
            <div className="h-8 w-8 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <Crown className="h-4 w-4" />
            </div>
          </div>

          <div className="my-3">
            <div className="text-3xl sm:text-4xl font-black tracking-tight text-white font-mono">
              {summary.active_pro_subscribers}
            </div>
            <div className="text-[11px] text-neutral-500 mt-1">
              Active Entitlements ($20/mo)
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5 text-[#00ff66]" />
            <span>Monthly Recurring SaaS Users</span>
          </div>
        </Card>

        {/* Card 3: Monthly Run Rate (MRR) */}
        <Card className="bg-[#121212] border-neutral-800 rounded-3xl p-6 flex flex-col justify-between shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">
              Projected MRR
            </span>
            <div className="h-8 w-8 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>

          <div className="my-3">
            <div className="text-3xl sm:text-4xl font-black tracking-tight text-white font-mono">
              ${summary.monthly_run_rate.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] text-neutral-500 mt-1">
              Monthly Run Rate
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
            <span>Compounding Subscription ARR</span>
          </div>
        </Card>

        {/* Card 4: Settlement Health */}
        <Card className="bg-[#121212] border-neutral-800 rounded-3xl p-6 flex flex-col justify-between shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">
              Settlement Status
            </span>
            <div className="h-8 w-8 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>

          <div className="my-3">
            <div className="text-3xl sm:text-4xl font-black tracking-tight text-white font-mono flex items-baseline gap-2">
              <span>{summary.paid_invoices_count}</span>
              <span className="text-xs text-neutral-500 font-normal">/ {summary.paid_invoices_count + summary.pending_invoices_count}</span>
            </div>
            <div className="text-[11px] text-neutral-500 mt-1">
              {summary.pending_invoices_count} Pending Invoices
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-amber-400" />
            <span>Autonomous RPC Verification</span>
          </div>
        </Card>
      </div>

      {/* Invoices Table Section */}
      <div className="space-y-4">
        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-[#00ff66]" />
            <h2 className="text-lg font-bold text-white tracking-tight">Invoice Audit Trail</h2>
            <span className="text-xs bg-neutral-900 text-neutral-400 px-2.5 py-0.5 rounded-full border border-neutral-800 font-mono">
              {filteredInvoices.length} Records
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3.5 top-2.5 h-3.5 w-3.5 text-neutral-500" />
              <Input
                type="text"
                placeholder="Search email, ID, TxHash..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 pl-9 pr-3 bg-neutral-900 border-neutral-800 rounded-full text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66]"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex items-center bg-neutral-900 border border-neutral-800 rounded-full p-1 gap-1">
              <button
                type="button"
                onClick={() => setStatusFilter("all")}
                className={`px-3 py-1 rounded-full text-[11px] font-bold cursor-pointer transition-colors ${
                  statusFilter === "all" ? "bg-[#00ff66] text-black" : "text-neutral-400 hover:text-white"
                }`}
              >
                All ({invoices.length})
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("paid")}
                className={`px-3 py-1 rounded-full text-[11px] font-bold cursor-pointer transition-colors ${
                  statusFilter === "paid" ? "bg-[#00ff66] text-black" : "text-neutral-400 hover:text-white"
                }`}
              >
                Paid ({summary.paid_invoices_count})
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("pending")}
                className={`px-3 py-1 rounded-full text-[11px] font-bold cursor-pointer transition-colors ${
                  statusFilter === "pending" ? "bg-amber-400 text-black" : "text-neutral-400 hover:text-white"
                }`}
              >
                Pending ({summary.pending_invoices_count})
              </button>
            </div>
          </div>
        </div>

        {/* WealthWave Table */}
        <div className="rounded-3xl border border-neutral-800 bg-[#121212] overflow-x-auto w-full shadow-2xl">
          <Table className="min-w-[650px] sm:min-w-full">
            <TableHeader>
              <TableRow className="border-b border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  User Email
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Amount
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Status
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Transaction Signature
                </TableHead>
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider text-right">
                  Settled Date
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {loading && invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-neutral-500 text-xs">
                    <Loader2 className="h-5 w-5 animate-spin text-[#00ff66] mx-auto mb-2" />
                    <span>Aggregating on-chain subscription revenue...</span>
                  </TableCell>
                </TableRow>
              ) : filteredInvoices.length > 0 ? (
                filteredInvoices.map((inv) => (
                  <TableRow
                    key={inv.id}
                    className="border-b border-neutral-800/60 hover:bg-neutral-900/60 transition-colors"
                  >
                    {/* User Email */}
                    <TableCell className="py-4 px-5 text-xs">
                      <div className="flex items-center gap-3">
                        <div className="h-7 w-7 rounded-full bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-300 font-bold text-xs uppercase">
                          {inv.email ? inv.email[0] : "U"}
                        </div>
                        <div>
                          <span className="font-bold text-white block">
                            {inv.email}
                          </span>
                          <span className="text-[10px] font-mono text-neutral-500">
                            ID: {inv.id.slice(0, 8)}...
                          </span>
                        </div>
                      </div>
                    </TableCell>

                    {/* Amount */}
                    <TableCell className="py-4 px-5 text-xs font-mono font-bold text-white">
                      ${inv.amount_usdt.toFixed(2)} USDT
                    </TableCell>

                    {/* Status Badge */}
                    <TableCell className="py-4 px-5 text-xs">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                        inv.status === "paid"
                          ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                          : "bg-amber-950/40 text-amber-400 border-amber-800/40"
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${inv.status === "paid" ? "bg-[#00ff66]" : "bg-amber-400"}`} />
                        <span>{inv.status}</span>
                      </span>
                    </TableCell>

                    {/* Tx Hash */}
                    <TableCell className="py-4 px-5 text-xs font-mono">
                      {inv.tx_hash ? (
                        <div className="inline-flex items-center gap-2">
                          <a
                            href={`https://solscan.io/tx/${inv.tx_hash}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[#00ff66] hover:underline inline-flex items-center gap-1"
                          >
                            <span>{inv.tx_hash.slice(0, 6)}...{inv.tx_hash.slice(-6)}</span>
                            <ExternalLink className="h-3 w-3" />
                          </a>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(inv.tx_hash!, inv.id)}
                            className="text-neutral-500 hover:text-white transition-colors cursor-pointer"
                            title="Copy Tx Hash"
                          >
                            {copiedId === inv.id ? (
                              <Check className="h-3 w-3 text-[#00ff66]" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </button>
                        </div>
                      ) : (
                        <span className="text-neutral-500 italic">Unverified (Pending TxID)</span>
                      )}
                    </TableCell>

                    {/* Date */}
                    <TableCell className="py-4 px-5 text-xs text-neutral-400 text-right">
                      {new Date(inv.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit"
                      })}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-28 text-center text-neutral-500 text-xs">
                    No invoices found matching your current filter.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}

