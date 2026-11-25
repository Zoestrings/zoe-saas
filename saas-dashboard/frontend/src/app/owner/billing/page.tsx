"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import {
  Crown,
  CheckCircle2,
  Copy,
  Check,
  ShieldCheck,
  Zap,
  Sparkles,
  ArrowRight,
  Loader2,
  Clock,
  ExternalLink,
  Wallet,
  AlertCircle,
  FileCheck,
  RefreshCw,
  Coins
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  EntitlementResponse,
  CreateInvoiceResponse,
  Invoice
} from "@/lib/api"

export default function BillingPage() {
  const [entitlement, setEntitlement] = useState<EntitlementResponse | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  // Payment flow state
  const [invoice, setInvoice] = useState<CreateInvoiceResponse | null>(null)
  const [creatingInvoice, setCreatingInvoice] = useState(false)
  const [txHash, setTxHash] = useState("")
  const [verifying, setVerifying] = useState(false)
  const [verifyError, setVerifyError] = useState<string | null>(null)
  const [verifySuccess, setVerifySuccess] = useState<string | null>(null)

  // Copy state
  const [copiedWallet, setCopiedWallet] = useState(false)
  const [copiedAmount, setCopiedAmount] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [entData, invData] = await Promise.all([
        api.getEntitlement().catch((err) => {
          console.warn("Notice: Failed to fetch entitlement:", err)
          return {
            plan: "free" as const,
            is_pro: false,
            expires_at: null,
            receiving_wallet: "4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA"
          }
        }),
        api.getInvoices().catch((err) => {
          console.warn("Notice: Failed to fetch invoices:", err)
          return []
        })
      ])
      setEntitlement(entData)
      setInvoices(invData || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Payment item description
  const [selectedItemName, setSelectedItemName] = useState<string>("Pro Plan Subscription ($20 USDT)")

  const handleCreateInvoice = async (creditAmount: number = 0, priceUsdt: number = 20) => {
    setCreatingInvoice(true)
    setVerifyError(null)
    setVerifySuccess(null)
    try {
      if (creditAmount > 0) {
        setSelectedItemName(`${creditAmount.toLocaleString()} Credits Top-Up ($${priceUsdt} USDT)`)
      } else {
        setSelectedItemName("Pro Plan Subscription ($20 USDT)")
      }
      const newInvoice = await api.createInvoice({ credit_amount: creditAmount, price_usdt: priceUsdt })
      setInvoice(newInvoice)
      // Scroll smoothly down to payment box
      setTimeout(() => {
        document.getElementById("payment-box")?.scrollIntoView({ behavior: "smooth" })
      }, 150)
    } catch (err: any) {
      setVerifyError(err.message || "Failed to generate invoice.")
    } finally {
      setCreatingInvoice(false)
    }
  }

  const handleVerifyPayment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!invoice) return
    const cleanHash = txHash.trim()
    if (!cleanHash) {
      setVerifyError("Please enter your transaction signature (TxID).")
      return
    }

    setVerifying(true)
    setVerifyError(null)
    setVerifySuccess(null)

    try {
      const res = await api.verifyPayment(invoice.invoice_id, cleanHash)
      setVerifySuccess(res.message || "Payment verified! Pro Plan unlocked.")
      setTxHash("")
      // Reload entitlement & invoice history
      await loadData()
    } catch (err: any) {
      setVerifyError(err.message || "On-chain verification failed. Please verify the transaction hash.")
    } finally {
      setVerifying(false)
    }
  }

  const copyToClipboard = (text: string, type: "wallet" | "amount") => {
    navigator.clipboard.writeText(text)
    if (type === "wallet") {
      setCopiedWallet(true)
      setTimeout(() => setCopiedWallet(false), 2500)
    } else {
      setCopiedAmount(true)
      setTimeout(() => setCopiedAmount(false), 2500)
    }
  }

  const receivingWallet = entitlement?.receiving_wallet || invoice?.receiving_wallet || "4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA"
  const isPro = entitlement?.is_pro || false

  return (
    <div className="space-y-10 pb-20">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full text-xs font-bold text-[#00ff66]">
            <Crown className="h-3.5 w-3.5" />
            Zoe Subscription & Entitlements · Solana On-Chain
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white">
            Upgrade Plan & Billing
          </h1>
          <p className="text-xs text-neutral-400 max-w-2xl">
            Zero third-party payment processors. Subscriptions are settled directly on-chain in USDT on Solana and verified automatically.
          </p>
        </div>

        {/* Current Plan & Credit Balance Badges */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="px-4 py-2 rounded-2xl border border-cyan-500/40 bg-cyan-500/10 text-[#00f0ff] text-xs font-bold flex items-center gap-2 shadow-sm shadow-cyan-500/10">
            <Coins className="h-4 w-4 text-[#00f0ff]" />
            <span>CREDITS: {Number(entitlement?.credits || 0).toLocaleString()} (${((Number(entitlement?.credits || 0)) * 0.01).toFixed(2)} USDT)</span>
          </div>

          <div className={`px-4 py-2 rounded-2xl border text-xs font-bold flex items-center gap-2 ${
            isPro 
              ? "bg-[#00ff66]/10 border-[#00ff66]/40 text-[#00ff66]"
              : "bg-neutral-900 border-neutral-800 text-neutral-300"
          }`}>
            <Sparkles className="h-4 w-4" />
            <span>PLAN: {isPro ? "PRO SUBSCRIBER" : "FREE TIER"}</span>
          </div>

          <Button
            variant="outline"
            size="icon"
            onClick={loadData}
            disabled={loading}
            className="h-10 w-10 rounded-full border-neutral-800 bg-[#121212] hover:bg-neutral-800 text-white cursor-pointer"
            title="Refresh Status"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#00ff66]" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Pro Plan Active Banner */}
      {isPro && (
        <div className="p-6 rounded-3xl bg-[#00ff66]/10 border border-[#00ff66]/30 shadow-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-[#00ff66] text-black flex items-center justify-center font-black shrink-0 shadow-lg shadow-[#00ff66]/20">
              <Crown className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>Pro Subscription Active</span>
                <span className="text-[10px] bg-[#00ff66]/20 text-[#00ff66] px-2 py-0.5 rounded-full border border-[#00ff66]/40 font-mono">
                  ACTIVE
                </span>
              </h3>
              <p className="text-xs text-neutral-300 mt-0.5">
                Full unlimited access to AI Analyst summaries, deep OSINT founder research, and 15-minute autonomous surveillance.
              </p>
              {entitlement?.expires_at && (
                <p className="text-[11px] text-[#00ff66] font-mono mt-1 flex items-center gap-1.5">
                  <Clock className="h-3 w-3" />
                  <span>Valid until: {new Date(entitlement.expires_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</span>
                </p>
              )}
            </div>
          </div>

          <Link href="/owner/investigate">
            <Button className="h-10 px-5 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 flex items-center gap-1.5">
              <span>Open Scanner</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      )}

      {/* Plan Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Free Plan */}
        <div className="rounded-3xl border border-neutral-800 bg-[#121212] p-8 flex flex-col justify-between shadow-2xl relative">
          <div className="space-y-6">
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">Basic Tier</span>
              <h3 className="text-2xl font-black text-white">Free Plan</h3>
              <p className="text-xs text-neutral-400">Essential on-chain contract and liquidity verification.</p>
            </div>

            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-black text-white">$0</span>
              <span className="text-xs text-neutral-500 font-semibold">/ month</span>
            </div>

            <div className="pt-4 border-t border-neutral-800/80 space-y-3">
              <div className="text-xs font-bold text-neutral-300 uppercase tracking-wider">Features Included:</div>
              <ul className="space-y-2.5 text-xs text-neutral-400">
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                  <span>Standard GoPlus security audit (Honeypot, Mint, Freeze)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                  <span>DexScreener pair liquidity & volume metrics</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                  <span>Top 10 holders distribution calculation</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                  <span>LP lock & creator wallet identification</span>
                </li>
                <li className="flex items-center gap-2.5 text-neutral-600 line-through">
                  <span>Groq AI Analyst summary & risk interpretation</span>
                </li>
                <li className="flex items-center gap-2.5 text-neutral-600 line-through">
                  <span>Deep OSINT founder identity & socials scraping</span>
                </li>
                <li className="flex items-center gap-2.5 text-neutral-600 line-through">
                  <span>15-minute autonomous surveillance background daemon</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-8">
            <Button
              disabled
              variant="outline"
              className="w-full h-12 rounded-full border-neutral-800 bg-neutral-900/60 text-neutral-500 font-bold text-xs"
            >
              {!isPro ? "Current Plan" : "Default"}
            </Button>
          </div>
        </div>

        {/* Pro Plan */}
        <div className="rounded-3xl border-2 border-[#00ff66]/70 bg-gradient-to-b from-[#121212] via-[#121212] to-[#0a1f12] p-8 flex flex-col justify-between shadow-2xl shadow-[#00ff66]/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 bg-[#00ff66] text-black text-[10px] font-black tracking-wider uppercase px-4 py-1 rounded-bl-2xl">
            MOST POPULAR
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-[#00ff66] uppercase tracking-wider flex items-center gap-1.5">
                <Crown className="h-3.5 w-3.5" />
                Institutional Intelligence
              </span>
              <h3 className="text-2xl font-black text-white">Pro Plan</h3>
              <p className="text-xs text-neutral-300">Unlocks autonomous AI analysis, founder OSINT, and 24/7 background surveillance.</p>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black text-white">$20</span>
              <span className="text-xs text-neutral-400 font-semibold">USDT / month</span>
              <span className="text-[10px] text-[#00ff66] font-mono bg-[#00ff66]/10 px-2 py-0.5 rounded-full border border-[#00ff66]/30">
                Solana Network
              </span>
            </div>

            <div className="pt-4 border-t border-neutral-800 space-y-3">
              <div className="text-xs font-bold text-white uppercase tracking-wider">Everything in Free, plus:</div>
              <ul className="space-y-2.5 text-xs text-neutral-200">
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                  <span className="font-semibold text-white">AI Analyst: Deterministic Groq LLM project health synthesis</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                  <span className="font-semibold text-white">OSINT & Founder Intelligence (Website, X, Telegram, LinkedIn)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                  <span className="font-semibold text-white">24/7 Background Surveillance Daemon (15-min automated sweep)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                  <span>Instant Liquidity Dump Alerts (&gt;20% LP drain detection)</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                  <span>Quantified Safety Score (0-100) with visual radial gauge</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                  <span>Unlimited saved investigations & audit PDF exports</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-8">
            <Button
              type="button"
              onClick={() => handleCreateInvoice(0, 20)}
              disabled={creatingInvoice || (isPro && !invoice)}
              className="w-full h-12 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-black text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 transition-all flex items-center justify-center gap-2"
            >
              {creatingInvoice ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Generating Solana Invoice...</span>
                </>
              ) : isPro ? (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Renew / Extend Subscription ($20 USDT)</span>
                </>
              ) : (
                <>
                  <Crown className="h-4 w-4" />
                  <span>Upgrade to Pro ($20 USDT)</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Top-Up Credits Section */}
      <div className="space-y-6 pt-4">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-[11px] font-bold text-[#00f0ff] uppercase tracking-wider mb-2">
              <Coins className="h-3.5 w-3.5" />
              <span>Pay-Per-Use Credit Sinks · 1 Credit = $0.01 USDT</span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">
              Top-Up Credits
            </h2>
            <p className="text-xs text-neutral-400 mt-1 max-w-xl">
              Fund your high-computation Web3 intelligence on demand. Use credits for deep smart-contract audits, contract generation, and AI investigations without recurring subscription lock-in.
            </p>
          </div>

          <div className="text-right text-xs text-neutral-400 bg-neutral-900/60 border border-neutral-800 rounded-2xl px-4 py-2.5">
            <span className="font-bold text-white block">Credit Sinks Breakdown:</span>
            <span>Audit: 50cr · Gen: 30cr · Scan: 15cr · X CT: 10cr · Web: 5cr</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Starter Pack */}
          <div className="rounded-3xl border border-neutral-800 bg-[#121212] p-7 flex flex-col justify-between shadow-xl relative hover:border-neutral-700 transition">
            <div className="space-y-5">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Pay-As-You-Go</span>
                <h3 className="text-xl font-black text-white">Starter Pack</h3>
                <p className="text-xs text-neutral-400">Essential credits for developers and traders testing contracts.</p>
              </div>

              <div className="p-4 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-center">
                <div className="text-3xl font-black text-white font-mono">500 <span className="text-xs font-sans text-neutral-400 font-normal">Credits</span></div>
                <div className="text-sm font-bold text-[#00ff66] font-mono mt-0.5">$5.00 USDT</div>
                <div className="text-[10px] text-neutral-500 mt-1">$0.01 per credit</div>
              </div>

              <ul className="space-y-2 text-xs text-neutral-300">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00ff66] shrink-0" />
                  <span><strong>10</strong> Full Smart-Contract Audits</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00ff66] shrink-0" />
                  <span><strong>33</strong> Deep Token Security Scans</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00ff66] shrink-0" />
                  <span><strong>50</strong> Crypto Twitter Sentiment Checks</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00ff66] shrink-0" />
                  <span>Credits never expire</span>
                </li>
              </ul>
            </div>

            <div className="pt-6">
              <Button
                type="button"
                onClick={() => handleCreateInvoice(500, 5)}
                disabled={creatingInvoice}
                className="w-full h-11 rounded-full bg-neutral-800 hover:bg-[#00ff66] hover:text-black text-white font-bold text-xs cursor-pointer transition-all flex items-center justify-center gap-2"
              >
                {creatingInvoice ? <Loader2 className="h-4 w-4 animate-spin" /> : <Coins className="h-4 w-4" />}
                <span>Buy 500 Credits ($5 USDT)</span>
              </Button>
            </div>
          </div>

          {/* Pro Pack (Best Value) */}
          <div className="rounded-3xl border-2 border-[#00f0ff] bg-gradient-to-b from-[#121212] via-[#121212] to-[#081a24] p-7 flex flex-col justify-between shadow-2xl shadow-cyan-500/10 relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-[#00f0ff] text-black text-[10px] font-black tracking-wider uppercase px-4 py-1 rounded-bl-2xl">
              BEST VALUE
            </div>

            <div className="space-y-5">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-[#00f0ff] uppercase tracking-wider flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  Power Trader &amp; Dev
                </span>
                <h3 className="text-xl font-black text-white">Pro Pack</h3>
                <p className="text-xs text-neutral-300">High-volume intelligence pack with 100 bonus credits included.</p>
              </div>

              <div className="p-4 rounded-2xl bg-black/60 border border-cyan-500/30 text-center">
                <div className="text-3xl font-black text-white font-mono">1,600 <span className="text-xs font-sans text-neutral-400 font-normal">Credits</span></div>
                <div className="text-sm font-bold text-[#00f0ff] font-mono mt-0.5">$15.00 USDT</div>
                <div className="text-[10px] text-cyan-400 font-mono mt-1">~$0.009 / credit (100 Bonus)</div>
              </div>

              <ul className="space-y-2 text-xs text-neutral-200">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00f0ff] shrink-0" />
                  <span className="text-white font-semibold"><strong>32</strong> Full Smart-Contract Audits</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00f0ff] shrink-0" />
                  <span><strong>53</strong> Contract Generations</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00f0ff] shrink-0" />
                  <span><strong>106</strong> Deep Token Security Scans</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00f0ff] shrink-0" />
                  <span><strong>160</strong> X Sentiment Checks</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#00f0ff] shrink-0" />
                  <span>Credits never expire</span>
                </li>
              </ul>
            </div>

            <div className="pt-6">
              <Button
                type="button"
                onClick={() => handleCreateInvoice(1600, 15)}
                disabled={creatingInvoice}
                className="w-full h-11 rounded-full bg-[#00f0ff] hover:bg-[#00cce6] text-black font-black text-xs cursor-pointer shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2"
              >
                {creatingInvoice ? <Loader2 className="h-4 w-4 animate-spin" /> : <Coins className="h-4 w-4" />}
                <span>Buy 1,600 Credits ($15 USDT)</span>
              </Button>
            </div>
          </div>

          {/* Whale Pack */}
          <div className="rounded-3xl border border-amber-500/40 bg-gradient-to-b from-[#121212] via-[#121212] to-[#1c1608] p-7 flex flex-col justify-between shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-amber-400 text-black text-[10px] font-black tracking-wider uppercase px-4 py-1 rounded-bl-2xl">
              WHALE · 20% OFF
            </div>

            <div className="space-y-5">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1">
                  <Crown className="h-3 w-3" />
                  Institutional Volume
                </span>
                <h3 className="text-xl font-black text-white">Whale Pack</h3>
                <p className="text-xs text-neutral-300">Maximum bulk power: 500 bonus credits for algorithmic traders.</p>
              </div>

              <div className="p-4 rounded-2xl bg-black/60 border border-amber-500/30 text-center">
                <div className="text-3xl font-black text-white font-mono">4,500 <span className="text-xs font-sans text-neutral-400 font-normal">Credits</span></div>
                <div className="text-sm font-bold text-amber-400 font-mono mt-0.5">$40.00 USDT</div>
                <div className="text-[10px] text-amber-300 font-mono mt-1">~$0.008 / credit (500 Bonus)</div>
              </div>

              <ul className="space-y-2 text-xs text-neutral-200">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  <span className="text-white font-semibold"><strong>90</strong> Full Smart-Contract Audits</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  <span><strong>150</strong> Contract Generations</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  <span><strong>300</strong> Deep Token Security Scans</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  <span><strong>450</strong> X Sentiment Checks</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  <span>Credits never expire</span>
                </li>
              </ul>
            </div>

            <div className="pt-6">
              <Button
                type="button"
                onClick={() => handleCreateInvoice(4500, 40)}
                disabled={creatingInvoice}
                className="w-full h-11 rounded-full bg-amber-400 hover:bg-amber-300 text-black font-black text-xs cursor-pointer shadow-lg shadow-amber-400/20 transition-all flex items-center justify-center gap-2"
              >
                {creatingInvoice ? <Loader2 className="h-4 w-4 animate-spin" /> : <Coins className="h-4 w-4" />}
                <span>Buy 4,500 Credits ($40 USDT)</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Processing Card (Generated Invoice) */}
      {invoice && (
        <div id="payment-box" className="p-8 rounded-3xl bg-[#121212] border-2 border-[#00ff66] shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-800 pb-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-[#00ff66] text-black flex items-center justify-center font-black">
                <Wallet className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-black text-white tracking-tight">
                  Complete Your Payment on Solana
                </h3>
                <p className="text-xs text-neutral-400">
                  Invoice ID: <span className="font-mono text-neutral-300">{invoice.invoice_id}</span>
                </p>
                <p className="text-xs text-[#00f0ff] font-semibold mt-0.5 flex items-center gap-1.5">
                  <Coins className="h-3.5 w-3.5" />
                  <span>{selectedItemName}</span>
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[11px] text-neutral-400 font-semibold block uppercase">Amount Due</span>
              <span className="text-2xl font-black text-[#00ff66] font-mono">{(invoice.amount_usdt || 20).toFixed(2)} USDT</span>
            </div>
          </div>

          {/* Payment Steps Instructions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Step 1: Destination Wallet */}
            <div className="p-5 rounded-2xl bg-neutral-900/80 border border-neutral-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">
                  1. Send {(invoice.amount_usdt || 20).toFixed(2)} USDT to Receiving Wallet
                </span>
                <span className="text-[10px] bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full font-mono">
                  Solana SPL
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-black/60 border border-neutral-800 flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-white break-all select-all">
                  {receivingWallet}
                </span>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(receivingWallet, "wallet")}
                  className="shrink-0 h-8 px-2.5 rounded-lg border-neutral-700 bg-neutral-900 hover:bg-[#00ff66] hover:text-black text-white text-xs cursor-pointer"
                >
                  {copiedWallet ? <Check className="h-3.5 w-3.5 text-[#00ff66]" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>

              <p className="text-[11px] text-neutral-500 leading-relaxed">
                Send exactly <strong className="text-neutral-300">{(invoice.amount_usdt || 20).toFixed(2)} USDT</strong> (or USDC) to this address using Phantom, Solflare, or any crypto exchange.
              </p>
            </div>

            {/* Step 2: Verification Input */}
            <form onSubmit={handleVerifyPayment} className="p-5 rounded-2xl bg-neutral-900/80 border border-neutral-800 space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider block">
                  2. Paste Transaction Signature (TxID)
                </span>

                <Input
                  type="text"
                  placeholder="Paste transaction signature (e.g. 5K7eZ... or dev_test_tx)..."
                  value={txHash}
                  onChange={(e) => setTxHash(e.target.value)}
                  className="h-11 bg-black/60 border-neutral-700 rounded-xl font-mono text-xs text-white placeholder:text-neutral-500 focus:border-[#00ff66]"
                />
              </div>

              <Button
                type="submit"
                disabled={verifying}
                className="w-full h-11 rounded-xl bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 transition-all flex items-center justify-center gap-2"
              >
                {verifying ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Verifying On Solana Blockchain...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    <span>{invoice.credit_amount ? "Verify Payment & Add Credits" : "Verify Payment & Activate Pro"}</span>
                  </>
                )}
              </Button>
            </form>
          </div>

          {/* Feedback Alerts */}
          {verifyError && (
            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
              <span>{verifyError}</span>
            </div>
          )}

          {verifySuccess && (
            <div className="p-4 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/40 text-xs text-[#00ff66] flex items-center gap-3">
              <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
              <span className="font-bold">{verifySuccess}</span>
            </div>
          )}
        </div>
      )}

      {/* Invoice History Table */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <FileCheck className="h-4 w-4 text-[#00ff66]" />
          <h2 className="text-lg font-bold text-white tracking-tight">Billing & Invoice History</h2>
          <span className="text-xs bg-neutral-900 text-neutral-400 px-2.5 py-0.5 rounded-full border border-neutral-800 font-mono">
            {invoices.length} Invoices
          </span>
        </div>

        <div className="rounded-3xl border border-neutral-800 bg-[#121212] overflow-hidden shadow-2xl">
          <Table>
            <TableHeader>
              <TableRow className="border-b border-neutral-800 hover:bg-transparent">
                <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                  Invoice ID
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
                  Date
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {loading && invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-28 text-center text-neutral-500 text-xs">
                    <Loader2 className="h-5 w-5 animate-spin text-[#00ff66] mx-auto mb-2" />
                    <span>Loading invoice records...</span>
                  </TableCell>
                </TableRow>
              ) : invoices.length > 0 ? (
                invoices.map((inv) => (
                  <TableRow
                    key={inv.id}
                    className="border-b border-neutral-800/60 hover:bg-neutral-900/60 transition-colors"
                  >
                    <TableCell className="py-3.5 px-5 text-xs font-mono text-neutral-300">
                      {inv.id.slice(0, 8)}...
                    </TableCell>
                    <TableCell className="py-3.5 px-5 text-xs font-bold text-white">
                      ${inv.amount_usdt.toFixed(2)} USDT
                    </TableCell>
                    <TableCell className="py-3.5 px-5 text-xs">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                        inv.status === "paid"
                          ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                          : "bg-amber-950/40 text-amber-400 border-amber-800/40"
                      }`}>
                        {inv.status}
                      </span>
                    </TableCell>
                    <TableCell className="py-3.5 px-5 text-xs font-mono text-neutral-400">
                      {inv.tx_hash ? (
                        <a
                          href={`https://solscan.io/tx/${inv.tx_hash}`}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:text-[#00ff66] hover:underline inline-flex items-center gap-1"
                        >
                          <span>{inv.tx_hash.slice(0, 6)}...{inv.tx_hash.slice(-6)}</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        "--"
                      )}
                    </TableCell>
                    <TableCell className="py-3.5 px-5 text-xs text-neutral-400 text-right">
                      {new Date(inv.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric"
                      })}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-neutral-500 text-xs">
                    No billing invoices generated yet.
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

