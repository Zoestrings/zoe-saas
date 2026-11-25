"use client"

import { useEffect, useState } from "react"
import {
  Crown,
  DollarSign,
  AlertTriangle,
  Sparkles,
  Loader2,
  CheckCircle2,
  Sliders,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"

export default function AdminBillingControlPage() {
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<{
    total_revenue_usdt: number
    active_subscriptions: number
    failed_payments: any[]
    recent_credit_transactions: any[]
  }>({
    total_revenue_usdt: 0,
    active_subscriptions: 0,
    failed_payments: [],
    recent_credit_transactions: [],
  })
  const [plans, setPlans] = useState<any[]>([])

  // Credit Adjustment Form
  const [targetUserId, setTargetUserId] = useState("")
  const [adjustAmount, setAdjustAmount] = useState("100")
  const [adjustReason, setAdjustReason] = useState("")
  const [adjusting, setAdjusting] = useState(false)
  const [adjustMsg, setAdjustMsg] = useState<string | null>(null)
  const [adjustErr, setAdjustErr] = useState<string | null>(null)

  const loadBillingControl = async () => {
    setLoading(true)
    try {
      const [ov, pl] = await Promise.allSettled([
        api.getAdminBillingOverview(),
        api.getSubscriptionPlans(),
      ])
      if (ov.status === "fulfilled" && ov.value) setOverview(ov.value)
      if (pl.status === "fulfilled" && Array.isArray(pl.value)) setPlans(pl.value)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBillingControl()
  }, [])

  const handleAdjustCredits = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!targetUserId.trim() || !adjustReason.trim()) return
    setAdjusting(true)
    setAdjustMsg(null)
    setAdjustErr(null)
    try {
      const res = await api.adminAdjustCredits(
        targetUserId.trim(),
        parseInt(adjustAmount, 10) || 0,
        adjustReason.trim()
      )
      setAdjustMsg(res.message || "Credits adjusted successfully.")
      setTargetUserId("")
      setAdjustReason("")
      await loadBillingControl()
    } catch (err: any) {
      setAdjustErr(err?.message || "Failed to adjust credits.")
    } finally {
      setAdjusting(false)
    }
  }

  return (
    <div className="space-y-8 pb-16 max-w-6xl mx-auto">
      <div className="p-6 rounded-3xl bg-[#121212] border border-[#00ff66]/30 shadow-2xl flex items-center gap-3.5">
        <div className="h-12 w-12 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shrink-0">
          <Crown className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight">
            Super Admin Billing Control Center
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Monitor platform revenue, active Pro subscriptions, failed payments, configurable plans, and credit audit logs.
          </p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-[#121212] border-neutral-800 rounded-3xl">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs text-neutral-400">Total Revenue (Verified)</span>
              <p className="text-2xl font-black text-[#00ff66] font-mono mt-1">
                ${overview.total_revenue_usdt.toLocaleString(undefined, { minimumFractionDigits: 2 })} USDT
              </p>
            </div>
            <DollarSign className="h-7 w-7 text-[#00ff66]/60" />
          </CardContent>
        </Card>

        <Card className="bg-[#121212] border-neutral-800 rounded-3xl">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs text-neutral-400">Active Pro Subscriptions</span>
              <p className="text-2xl font-black text-white font-mono mt-1">
                {overview.active_subscriptions}
              </p>
            </div>
            <Crown className="h-7 w-7 text-amber-400/70" />
          </CardContent>
        </Card>

        <Card className="bg-[#121212] border-neutral-800 rounded-3xl">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs text-neutral-400">Failed Payments</span>
              <p className="text-2xl font-black text-rose-400 font-mono mt-1">
                {overview.failed_payments.length}
              </p>
            </div>
            <AlertTriangle className="h-7 w-7 text-rose-400/70" />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Grant / Adjust Credits */}
        <Card className="lg:col-span-5 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <Sliders className="h-4 w-4 text-[#00ff66]" />
              <span>Admin Credit Adjustment</span>
            </CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Grant or deduct credits for any tenant with immutable audit logging.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAdjustCredits} className="space-y-4">
              {adjustMsg && (
                <div className="p-3 rounded-xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{adjustMsg}</span>
                </div>
              )}
              {adjustErr && (
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs">
                  {adjustErr}
                </div>
              )}
              <div className="space-y-1.5">
                <Label className="text-xs text-white">Target User ID</Label>
                <Input
                  placeholder="UUID or user_id"
                  value={targetUserId}
                  onChange={(e) => setTargetUserId(e.target.value)}
                  required
                  className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-white">Credit Delta (+ to grant, - to deduct)</Label>
                <Input
                  type="number"
                  value={adjustAmount}
                  onChange={(e) => setAdjustAmount(e.target.value)}
                  required
                  className="bg-neutral-950 border-neutral-800 text-white font-mono text-xs h-10 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-white">Audit Reason</Label>
                <Input
                  placeholder="e.g. Enterprise onboarding grant"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  required
                  className="bg-neutral-950 border-neutral-800 text-white text-xs h-10 rounded-xl"
                />
              </div>
              <Button
                type="submit"
                disabled={adjusting}
                className="w-full h-10 rounded-xl bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer"
              >
                {adjusting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
                Apply Credit Adjustment
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Configurable Plans & Audit Trail */}
        <Card className="lg:col-span-7 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white">Configurable Plans &amp; Audit Trail</CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Active subscription tiers and recent credit transactions across tenants.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {plans.map((p) => (
                <div key={p.id} className="p-3.5 rounded-2xl bg-neutral-950/70 border border-neutral-800">
                  <p className="text-xs font-bold text-white">{p.name}</p>
                  <p className="text-sm font-mono text-[#00ff66] mt-0.5">${p.price_usdt} USDT</p>
                  <p className="text-[11px] text-neutral-400 mt-1">{p.monthly_credits} credits/mo</p>
                </div>
              ))}
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {loading ? (
                <div className="py-6 text-center text-xs text-neutral-400">Loading audit trail...</div>
              ) : overview.recent_credit_transactions.length === 0 ? (
                <div className="p-4 rounded-2xl border border-dashed border-neutral-800 text-center text-xs text-neutral-500">
                  No credit transactions recorded yet.
                </div>
              ) : (
                overview.recent_credit_transactions.map((tx) => (
                  <div key={tx.id} className="p-3 rounded-xl bg-neutral-950/60 border border-neutral-800 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-mono text-white">{tx.action_type}</span>
                      <span className="text-neutral-500 ml-2">({tx.user_id.slice(0, 12)})</span>
                    </div>
                    <div className="font-mono">
                      <span className="text-[#00ff66]">{tx.amount} cr</span>
                      <span className="text-neutral-500 ml-2">Bal: {tx.balance_after}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
