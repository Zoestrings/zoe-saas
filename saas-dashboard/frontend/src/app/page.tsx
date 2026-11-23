"use client"

import Link from "next/link"
import {
  Sparkles,
  Bot,
  Radar,
  Bookmark,
  Crown,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Lock,
  Globe,
  Bell,
  Check,
  ExternalLink,
  ChevronRight,
  Cpu
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ZoeLogo } from "@/components/zoe-logo"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col font-sans selection:bg-[#00ff66] selection:text-black">
      {/* Glow decorative gradients */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[#00ff66]/10 blur-[140px] pointer-events-none rounded-full" />
      <div className="fixed bottom-0 right-0 w-[500px] h-[300px] bg-[#00ff66]/5 blur-[120px] pointer-events-none rounded-full" />

      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#0a0a0a]/80 border-b border-neutral-800/80">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <ZoeLogo size={36} glow variant="full" />
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-neutral-400">
            <a href="#features" className="hover:text-[#00ff66] transition-colors">
              Features
            </a>
            <a href="#scanner" className="hover:text-[#00ff66] transition-colors">
              Intelligence Scanner
            </a>
            <a href="#monitoring" className="hover:text-[#00ff66] transition-colors">
              Surveillance
            </a>
            <a href="#pricing" className="hover:text-[#00ff66] transition-colors">
              Pricing
            </a>
          </nav>

          {/* Auth Actions */}
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button
                variant="ghost"
                className="text-xs font-bold text-neutral-300 hover:text-white hover:bg-neutral-900 rounded-full px-4 h-10 cursor-pointer"
              >
                Sign In
              </Button>
            </Link>

            <Link href="/register">
              <Button
                className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-black text-xs rounded-full px-5 h-10 shadow-lg shadow-[#00ff66]/20 cursor-pointer transition-all hover:scale-105"
              >
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 px-6 max-w-7xl mx-auto text-center space-y-8 flex flex-col items-center">
        {/* Glowing Brand Mark Hero Element */}
        <div className="relative mb-2 group">
          <div className="absolute -inset-4 bg-gradient-to-r from-[#00ff66]/30 via-[#00d2ff]/20 to-transparent rounded-full blur-2xl opacity-60 group-hover:opacity-90 transition duration-700" />
          <div className="relative h-24 w-24 rounded-3xl bg-[#0f141a]/90 border border-[#212833] flex items-center justify-center shadow-2xl backdrop-blur-xl">
            <ZoeLogo size={78} glow variant="mark" />
          </div>
        </div>

        {/* Pulsing Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#00ff66]/10 border border-[#00ff66]/30 text-xs font-bold text-[#00ff66] shadow-sm animate-pulse">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Next-Gen Autonomous Web3 Intelligence · Live on Solana</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tight text-white max-w-4xl leading-[1.1]">
          Meet <span className="text-[#00ff66]">Zoe</span>: Your AI-Powered Web3 Community Manager &amp; Intelligence Scanner.
        </h1>

        {/* Subtitle */}
        <p className="text-base sm:text-lg text-neutral-400 max-w-2xl font-normal leading-relaxed">
          Autonomous 24/7 Telegram community management, institutional-grade on-chain contract audits, honeypot detection, and 15-minute background liquidity surveillance.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
          <Link href="/register">
            <Button
              className="w-full sm:w-auto h-13 px-8 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-black text-sm shadow-xl shadow-[#00ff66]/25 cursor-pointer transition-all hover:scale-105 flex items-center justify-center gap-2"
            >
              <span>Get Started Free</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>

          <Link href="/investigate">
            <Button
              variant="outline"
              className="w-full sm:w-auto h-13 px-8 rounded-full border-neutral-700 bg-neutral-900/80 hover:bg-neutral-800 text-white font-bold text-sm cursor-pointer transition-all flex items-center justify-center gap-2 shadow-lg"
            >
              <Radar className="h-4 w-4 text-[#00ff66]" />
              <span>Launch Live Scanner</span>
            </Button>
          </Link>
        </div>

        {/* Fast Metrics Strip */}
        <div className="pt-12 grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-12 text-center border-t border-neutral-900 max-w-3xl w-full">
          <div>
            <div className="text-2xl sm:text-3xl font-black text-white font-mono">&lt; 2s</div>
            <div className="text-[11px] text-neutral-500 font-semibold uppercase mt-0.5">Scan Latency</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-[#00ff66] font-mono">100%</div>
            <div className="text-[11px] text-neutral-500 font-semibold uppercase mt-0.5">On-Chain Evidence</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-white font-mono">24/7</div>
            <div className="text-[11px] text-neutral-500 font-semibold uppercase mt-0.5">Bot Surveillance</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-[#00ff66] font-mono">$0</div>
            <div className="text-[11px] text-neutral-500 font-semibold uppercase mt-0.5">Processor Fees</div>
          </div>
        </div>

        {/* Terminal Visual Showcase */}
        <div id="scanner" className="w-full max-w-5xl pt-10">
          <div className="rounded-3xl border border-neutral-800 bg-[#121212] shadow-2xl p-4 sm:p-6 text-left space-y-4 relative overflow-hidden">
            {/* Window Dots */}
            <div className="flex items-center justify-between border-b border-neutral-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-rose-500/80 inline-block" />
                <span className="h-3 w-3 rounded-full bg-amber-500/80 inline-block" />
                <span className="h-3 w-3 rounded-full bg-[#00ff66]/80 inline-block" />
                <span className="ml-2 font-mono text-xs text-neutral-500">zoe-intelligence-terminal.sh</span>
              </div>
              <span className="text-[11px] font-mono bg-[#00ff66]/10 text-[#00ff66] px-2.5 py-0.5 rounded-full border border-[#00ff66]/30">
                Solana Mainnet
              </span>
            </div>

            {/* Terminal Body */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-2xl bg-black/60 border border-neutral-800 space-y-1">
                <div className="text-[10px] uppercase font-bold text-neutral-500">Safety Score</div>
                <div className="text-2xl font-black text-[#00ff66] font-mono">92 / 100</div>
                <div className="text-[11px] text-emerald-400 font-semibold">Healthy Tokenomics</div>
              </div>

              <div className="p-4 rounded-2xl bg-black/60 border border-neutral-800 space-y-1">
                <div className="text-[10px] uppercase font-bold text-neutral-500">Liquidity &amp; LP Lock</div>
                <div className="text-2xl font-black text-white font-mono">$1,450,200</div>
                <div className="text-[11px] text-[#00ff66] font-semibold">Mint Revoked · LP Locked</div>
              </div>

              <div className="p-4 rounded-2xl bg-black/60 border border-neutral-800 space-y-1">
                <div className="text-[10px] uppercase font-bold text-neutral-500">Honeypot Audit</div>
                <div className="text-2xl font-black text-white font-mono">0% / 0% Tax</div>
                <div className="text-[11px] text-emerald-400 font-semibold">Unrestricted Trading</div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 text-xs text-neutral-300 font-mono flex items-center justify-between">
              <div className="truncate">
                <span className="text-[#00ff66] font-bold">zoe@audit:~$</span> investigate --ca DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
              </div>
              <span className="text-neutral-500 text-[10px]">Verified in 1.4s</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid Section (3 Pillars) */}
      <section id="features" className="py-24 px-6 border-t border-neutral-900 bg-[#0c0c0c] relative">
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <span className="text-xs font-bold text-[#00ff66] uppercase tracking-wider">
              Comprehensive Platform Capabilities
            </span>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white">
              Engineered for Modern Web3 Ecosystems
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400">
              Three synchronized autonomous engines protecting your holders and growing your community around the clock.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1: AI Community Manager */}
            <div className="p-8 rounded-3xl bg-[#121212] border border-neutral-800 flex flex-col justify-between shadow-2xl hover:border-neutral-700 transition-all group">
              <div className="space-y-5">
                <div className="h-14 w-14 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] group-hover:scale-110 transition-transform">
                  <Bot className="h-7 w-7" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-white">AI Community Manager</h3>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    24/7 intelligent Telegram moderation, semantic vector search over project documentation, custom bot personas, and automated anti-FUD defense.
                  </p>
                </div>
              </div>

              <div className="pt-6 border-t border-neutral-800/80 mt-6 space-y-2">
                <div className="text-[11px] font-semibold text-neutral-300 flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>Sub-second response latencies</span>
                </div>
                <div className="text-[11px] font-semibold text-neutral-300 flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>FAISS semantic knowledge ingestion</span>
                </div>
              </div>
            </div>

            {/* Feature 2: Token Intelligence Scanner */}
            <div className="p-8 rounded-3xl bg-[#121212] border border-neutral-800 flex flex-col justify-between shadow-2xl hover:border-[#00ff66]/40 transition-all group">
              <div className="space-y-5">
                <div className="h-14 w-14 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] group-hover:scale-110 transition-transform">
                  <Radar className="h-7 w-7" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-white">Token Intelligence Scanner</h3>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    Deep on-chain contract security audits. Instant verification of Honeypot status, mint &amp; freeze authority, top 10 holder distribution, and LP lock status.
                  </p>
                </div>
              </div>

              <div className="pt-6 border-t border-neutral-800/80 mt-6 space-y-2">
                <div className="text-[11px] font-semibold text-neutral-300 flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>Solana &amp; EVM multi-chain support</span>
                </div>
                <div className="text-[11px] font-semibold text-neutral-300 flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>Quantified 0-100 Safety Score</span>
                </div>
              </div>
            </div>

            {/* Feature 3: Continuous Monitoring */}
            <div id="monitoring" className="p-8 rounded-3xl bg-[#121212] border border-neutral-800 flex flex-col justify-between shadow-2xl hover:border-neutral-700 transition-all group">
              <div className="space-y-5">
                <div className="h-14 w-14 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] group-hover:scale-110 transition-transform">
                  <Bookmark className="h-7 w-7" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-white">Continuous Surveillance</h3>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    Autonomous 15-minute background loop monitoring liquidity pools. If liquidity drains by &gt;20%, Zoe fires high-priority alerts to protect your treasury.
                  </p>
                </div>
              </div>

              <div className="pt-6 border-t border-neutral-800/80 mt-6 space-y-2">
                <div className="text-[11px] font-semibold text-neutral-300 flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>Rug-pull &amp; liquidity dump detection</span>
                </div>
                <div className="text-[11px] font-semibold text-neutral-300 flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>Customizable surveillance watchlists</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 px-6 max-w-7xl mx-auto space-y-16">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold text-[#00ff66] uppercase tracking-wider">
            Simple, Transparent Pricing
          </span>
          <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white">
            Monetized On-Chain with Solana USDT
          </h2>
          <p className="text-xs sm:text-sm text-neutral-400">
            Pay directly on-chain from your Phantom or Solflare wallet. No credit cards, no monthly lock-ins, zero intermediaries.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Free Tier */}
          <div className="rounded-3xl border border-neutral-800 bg-[#121212] p-8 flex flex-col justify-between shadow-xl">
            <div className="space-y-6">
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">Basic Access</span>
                <h3 className="text-2xl font-black text-white">Free Plan</h3>
                <p className="text-xs text-neutral-400">Essential on-chain contract validation for crypto traders.</p>
              </div>

              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">$0</span>
                <span className="text-xs text-neutral-500 font-semibold">/ forever</span>
              </div>

              <div className="pt-4 border-t border-neutral-800 space-y-3">
                <div className="text-xs font-bold text-neutral-300 uppercase tracking-wider">Included:</div>
                <ul className="space-y-2.5 text-xs text-neutral-400">
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                    <span>GoPlus Security Audit (Honeypot, Mint, Freeze)</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                    <span>DexScreener pair liquidity &amp; volume metrics</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                    <span>Top 10 holders distribution calculation</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-neutral-500 shrink-0" />
                    <span>Deployer wallet identification</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="pt-8">
              <Link href="/register">
                <Button
                  variant="outline"
                  className="w-full h-12 rounded-full border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white font-bold text-xs cursor-pointer"
                >
                  Create Free Account
                </Button>
              </Link>
            </div>
          </div>

          {/* Pro Tier */}
          <div className="rounded-3xl border-2 border-[#00ff66] bg-gradient-to-b from-[#121212] to-[#0a1f12] p-8 flex flex-col justify-between shadow-2xl shadow-[#00ff66]/10 relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-[#00ff66] text-black text-[10px] font-black tracking-wider uppercase px-4 py-1 rounded-bl-2xl">
              POPULAR
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-[#00ff66] uppercase tracking-wider flex items-center gap-1.5">
                  <Crown className="h-3.5 w-3.5" />
                  Institutional Grade
                </span>
                <h3 className="text-2xl font-black text-white">Pro Plan</h3>
                <p className="text-xs text-neutral-300">Unlocks autonomous AI analysis, founder OSINT, and 24/7 background surveillance.</p>
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black text-white">$20</span>
                <span className="text-xs text-neutral-400 font-semibold">USDT / month</span>
                <span className="text-[10px] text-[#00ff66] font-mono bg-[#00ff66]/10 px-2 py-0.5 rounded-full border border-[#00ff66]/30">
                  Solana SPL
                </span>
              </div>

              <div className="pt-4 border-t border-neutral-800 space-y-3">
                <div className="text-xs font-bold text-white uppercase tracking-wider">Everything in Free, plus:</div>
                <ul className="space-y-2.5 text-xs text-neutral-200">
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                    <span className="font-semibold text-white">Groq AI Analyst Executive Health Synthesis</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                    <span className="font-semibold text-white">Deep OSINT Project &amp; Founder Socials Verification</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                    <span className="font-semibold text-white">15-minute Continuous Surveillance Daemon</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                    <span>Instant Liquidity Dump Alerts (&gt;20% LP drain detection)</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-[#00ff66] shrink-0" />
                    <span>Unlimited PDF audit report downloads</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="pt-8">
              <Link href="/register">
                <Button
                  className="w-full h-12 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-black text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 transition-all flex items-center justify-center gap-2"
                >
                  <Crown className="h-4 w-4" />
                  <span>Start Pro with Solana USDT</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-neutral-900 bg-black/80 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-neutral-500">
          <div className="flex items-center gap-3">
            <div className="h-7 w-7 rounded-xl bg-[#00ff66] text-black flex items-center justify-center font-bold">
              <Sparkles className="h-3.5 w-3.5 fill-black" />
            </div>
            <span className="font-bold text-white">Zoe SaaS Intelligence Terminal</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/login" className="hover:text-white transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="hover:text-white transition-colors">
              Register
            </Link>
            <Link href="/investigate" className="hover:text-[#00ff66] transition-colors">
              Scanner
            </Link>
            <a
              href="https://solscan.io/account/4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#00ff66] transition-colors flex items-center gap-1"
            >
              <span>Treasury</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          <div className="text-[11px]">
            &copy; 2026 Zoe Intelligence. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
