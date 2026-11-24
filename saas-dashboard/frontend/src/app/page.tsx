"use client"

import React from "react"
import Link from "next/link"
import {
  Sparkles,
  Bot,
  Radar,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Globe,
  Bell,
  Cpu,
  Terminal,
  Activity,
  Layers,
  Search,
  ExternalLink,
  ChevronRight,
  Zap,
  Lock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ZoeLogo } from "@/components/zoe-logo"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col font-sans selection:bg-[#00e599] selection:text-black overflow-x-hidden">
      {/* Ambient Radial Background Glows */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[550px] bg-[radial-gradient(ellipse_at_center,_rgba(0,229,153,0.18)_0%,_rgba(0,180,255,0.08)_40%,_transparent_75%)] blur-[120px] pointer-events-none -z-10" />
      <div className="fixed bottom-0 right-0 w-[600px] h-[450px] bg-[radial-gradient(ellipse_at_center,_rgba(0,229,153,0.06)_0%,_rgba(0,112,243,0.04)_50%,_transparent_80%)] blur-[140px] pointer-events-none -z-10" />

      {/* Navigation Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-2xl bg-[#0a0a0a]/80 border-b border-neutral-800/80">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Brand Logo Lockup */}
          <Link href="/" className="flex items-center gap-3 group">
            <ZoeLogo size={38} glow variant="full" />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-neutral-400">
            <a href="#features" className="hover:text-[#00e599] transition-colors">
              Pillars &amp; Features
            </a>
            <a href="#terminal" className="hover:text-[#00e599] transition-colors">
              Live Terminal
            </a>
            <a href="#omnichannel" className="hover:text-[#00e599] transition-colors">
              Omnichannel
            </a>
            <a href="#pricing" className="hover:text-[#00e599] transition-colors">
              Pricing
            </a>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button
                variant="ghost"
                className="text-xs font-bold text-neutral-300 hover:text-white hover:bg-neutral-900 rounded-full px-5 h-10 cursor-pointer"
              >
                Sign In
              </Button>
            </Link>

            <Link href="/register">
              <Button className="bg-[#00e599] hover:bg-[#00c685] text-black font-extrabold text-xs rounded-full px-5 h-10 shadow-lg shadow-[#00e599]/20 cursor-pointer transition-all hover:scale-105">
                Deploy Zoe
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-28 px-6 max-w-6xl mx-auto text-center flex flex-col items-center">
        {/* Top 3D Metallic/Glass Brand Mark */}
        <div className="relative mb-6 group cursor-default">
          <div className="absolute -inset-6 bg-gradient-to-r from-[#00e599]/40 via-[#00d2ff]/30 to-transparent rounded-full blur-2xl opacity-70 group-hover:opacity-100 transition duration-700" />
          <div className="relative h-28 w-28 rounded-3xl bg-[#0d1217]/90 border border-white/10 flex items-center justify-center shadow-2xl backdrop-blur-xl">
            <ZoeLogo size={88} glow variant="mark" />
          </div>
        </div>

        {/* Live Status Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#00e599]/10 border border-[#00e599]/30 text-xs font-bold text-[#00e599] shadow-sm mb-6 animate-pulse">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Next-Gen Autonomous Web3 Intelligence · Live on Solana</span>
        </div>

        {/* Massive Headline */}
        <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white max-w-4xl leading-[1.08]">
          Zoe. The Web3 <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00e599] via-[#00d2ff] to-[#0070f3]">
            Intelligence Engine.
          </span>
        </h1>

        {/* Subheadline */}
        <p className="mt-8 text-lg sm:text-xl text-neutral-400 max-w-2xl font-normal leading-relaxed">
          Stop using generic bots. Deploy an autonomous AI agent that scans contracts, tracks whales, and protects your community 24/7.
        </p>

        {/* Hero CTAs */}
        <div className="mt-10 flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
          <Link href="/login" className="w-full sm:w-auto">
            <Button className="w-full sm:w-auto h-14 px-9 bg-[#00e599] hover:bg-[#00c685] text-black font-extrabold text-base rounded-2xl shadow-xl shadow-[#00e599]/25 cursor-pointer transition-all hover:scale-105 flex items-center justify-center gap-3">
              <span>Deploy Zoe Now</span>
              <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>

          <Link href="/investigate" className="w-full sm:w-auto">
            <Button
              variant="outline"
              className="w-full sm:w-auto h-14 px-8 border-neutral-700 bg-neutral-900/60 hover:bg-neutral-800 text-white font-bold text-sm rounded-2xl cursor-pointer transition-all flex items-center justify-center gap-2.5 backdrop-blur-md"
            >
              <Radar className="h-4 w-4 text-[#00e599]" />
              <span>Explore Live Scanner</span>
            </Button>
          </Link>
        </div>

        {/* Social Proof & Trust Badges */}
        <div className="mt-16 pt-10 border-t border-neutral-800/80 grid grid-cols-2 sm:grid-cols-4 gap-8 max-w-4xl w-full text-center">
          <div>
            <p className="text-2xl sm:text-3xl font-extrabold text-white">100K+</p>
            <p className="text-xs text-neutral-400 font-medium mt-1">Community Members Protected</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-extrabold text-white">$42M+</p>
            <p className="text-xs text-neutral-400 font-medium mt-1">On-Chain Volume Monitored</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-extrabold text-[#00e599]">&lt; 150ms</p>
            <p className="text-xs text-neutral-400 font-medium mt-1">Autonomous Latency</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-extrabold text-white">100%</p>
            <p className="text-xs text-neutral-400 font-medium mt-1">Verified On-Chain Intel</p>
          </div>
        </div>
      </section>

      {/* Live Interactive Terminal Preview */}
      <section id="terminal" className="relative py-16 px-6 max-w-5xl mx-auto w-full">
        <div className="relative rounded-3xl bg-[#0c1015] border border-white/10 shadow-2xl overflow-hidden backdrop-blur-xl">
          {/* Window Chrome Header */}
          <div className="px-6 py-4 bg-neutral-900/80 border-b border-neutral-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500/80" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <div className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-3 font-mono text-xs text-neutral-400 font-semibold flex items-center gap-2">
                <Terminal className="h-3.5 w-3.5 text-[#00e599]" />
                zoe-intelligence-terminal.sh
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-[#00e599] animate-ping" />
              <span className="text-[10px] font-mono uppercase text-[#00e599] font-bold">Node Live · RPC Synced</span>
            </div>
          </div>

          {/* Terminal Screen Simulation */}
          <div className="p-6 font-mono text-xs space-y-4 text-neutral-300 bg-[#080b0e]/95 overflow-x-auto">
            <div className="flex items-center gap-2 text-neutral-400">
              <span className="text-[#00e599] font-bold">zoe@intelligence:~$</span>
              <span>zoe scan --target 7EYnhaqoUN4vvi58pLz2i4nnmJpCjC1PuwZ28yK4pump --deep-audit</span>
            </div>

            <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-2.5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800 pb-2">
                <span className="text-white font-bold flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-[#00e599]" />
                  AUDIT RESULTS: $ZOE / SOLANA
                </span>
                <span className="px-2 py-0.5 rounded bg-[#00e599]/10 text-[#00e599] font-bold text-[10px] border border-[#00e599]/30">
                  RUG RISK: 0 / 100 (SAFEST)
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-neutral-300 pt-1">
                <div>
                  <span className="text-neutral-500 block text-[10px] uppercase font-bold">Liquidity Status</span>
                  <span className="text-[#00e599] font-bold">100% Raydium Burned</span>
                </div>
                <div>
                  <span className="text-neutral-500 block text-[10px] uppercase font-bold">Mint &amp; Freeze</span>
                  <span className="text-[#00e599] font-bold">Revoked &amp; Immutable</span>
                </div>
                <div>
                  <span className="text-neutral-500 block text-[10px] uppercase font-bold">Top 10 Holders</span>
                  <span className="text-white font-bold">11.4% (Decentralized)</span>
                </div>
              </div>
              <div className="pt-2 text-[11px] text-neutral-400 border-t border-neutral-800/60">
                <span className="text-[#00d2ff] font-semibold">OSINT Radar:</span> Deployer wallet verified. Zero prior rug associations detected across 42 Solana historical clusters.
              </div>
            </div>

            <div className="flex items-center gap-2 text-neutral-400 pt-1">
              <span className="text-[#00e599] font-bold">zoe@intelligence:~$</span>
              <span className="text-neutral-300">zoe live-monitor --community telegram --auto-protect</span>
            </div>
            <div className="text-neutral-400 pl-4 border-l-2 border-[#00e599]/40 space-y-1">
              <p className="text-emerald-400">✓ Ingested Telegram webhook stream (Channel @CryptoAlpha)</p>
              <p className="text-emerald-400">✓ Intercepted phishing drainer URL (User @fakedev99) — Blocked &amp; Deleted in 42ms</p>
              <p className="text-white">✓ Synced real-time crypto news intelligence (Bitcoin ATH · SEC ETF filing)</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Pillars Features Grid */}
      <section id="features" className="py-24 px-6 max-w-7xl mx-auto w-full">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#00e599]/10 border border-[#00e599]/20 text-xs font-bold text-[#00e599] mb-4">
            <Zap className="h-3.5 w-3.5" />
            <span>The 4 Core Pillars</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
            Engineered For The On-Chain Era.
          </h2>
          <p className="mt-4 text-base text-neutral-400">
            Four specialized intelligence engines operating in harmony to empower and safeguard Web3 projects.
          </p>
        </div>

        {/* The 4 Glassmorphism Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Card 1: On-Chain Intelligence */}
          <div className="p-8 rounded-3xl bg-white/[0.03] backdrop-blur-md border border-white/10 hover:border-[#00e599]/40 transition-all duration-300 group relative flex flex-col justify-between">
            <div className="space-y-4">
              <div className="h-14 w-14 rounded-2xl bg-[#00e599]/10 border border-[#00e599]/30 flex items-center justify-center text-[#00e599] group-hover:scale-110 transition-transform">
                <Radar className="h-7 w-7" />
              </div>
              <h3 className="text-2xl font-bold text-white group-hover:text-[#00e599] transition-colors">
                On-Chain Intelligence
              </h3>
              <p className="text-sm text-neutral-400 leading-relaxed">
                Real-time contract scanning for Honeypots, mint exploits, unburned liquidity, and dangerous authority permissions across Solana, Ethereum, and Base.
              </p>
            </div>
            <ul className="mt-6 space-y-2.5 text-xs text-neutral-300 border-t border-neutral-800/80 pt-6">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                <span>Instant LP lock &amp; burn verification</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                <span>GoPlus &amp; DexScreener deep security audit</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                <span>Automated Jupiter &amp; Raydium DEX buy links</span>
              </li>
            </ul>
          </div>

          {/* Card 2: Omnichannel Presence */}
          <div className="p-8 rounded-3xl bg-white/[0.03] backdrop-blur-md border border-white/10 hover:border-[#00d2ff]/40 transition-all duration-300 group relative flex flex-col justify-between">
            <div className="space-y-4">
              <div className="h-14 w-14 rounded-2xl bg-[#00d2ff]/10 border border-[#00d2ff]/30 flex items-center justify-center text-[#00d2ff] group-hover:scale-110 transition-transform">
                <Globe className="h-7 w-7" />
              </div>
              <h3 className="text-2xl font-bold text-white group-hover:text-[#00d2ff] transition-colors">
                Omnichannel Presence
              </h3>
              <p className="text-sm text-neutral-400 leading-relaxed">
                Deploy Zoe simultaneously into Telegram groups, Discord servers, X (Twitter) mentions, and Farcaster channels with one synchronized knowledge base.
              </p>
            </div>
            <ul className="mt-6 space-y-2.5 text-xs text-neutral-300 border-t border-neutral-800/80 pt-6">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00d2ff]" />
                <span>Unified project memory &amp; multi-platform RAG</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00d2ff]" />
                <span>Custom bot persona, tone, and slang guidelines</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00d2ff]" />
                <span>Group sentiment analytics &amp; engagement telemetry</span>
              </li>
            </ul>
          </div>

          {/* Card 3: Autonomous Moderation */}
          <div className="p-8 rounded-3xl bg-white/[0.03] backdrop-blur-md border border-white/10 hover:border-[#00e599]/40 transition-all duration-300 group relative flex flex-col justify-between">
            <div className="space-y-4">
              <div className="h-14 w-14 rounded-2xl bg-[#00e599]/10 border border-[#00e599]/30 flex items-center justify-center text-[#00e599] group-hover:scale-110 transition-transform">
                <ShieldCheck className="h-7 w-7" />
              </div>
              <h3 className="text-2xl font-bold text-white group-hover:text-[#00e599] transition-colors">
                Autonomous Moderation
              </h3>
              <p className="text-sm text-neutral-400 leading-relaxed">
                Neutralize wallet drainers, counterfeit contract drops, and automated raid bots before your community members fall victim to social engineering.
              </p>
            </div>
            <ul className="mt-6 space-y-2.5 text-xs text-neutral-300 border-t border-neutral-800/80 pt-6">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                <span>Sub-150ms malicious message deletion</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                <span>Anti-FUD proactive factual intervention</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                <span>Automated spammer kick, ban, and mute policies</span>
              </li>
            </ul>
          </div>

          {/* Card 4: OSINT & Whale Tracking */}
          <div className="p-8 rounded-3xl bg-white/[0.03] backdrop-blur-md border border-white/10 hover:border-[#0070f3]/40 transition-all duration-300 group relative flex flex-col justify-between">
            <div className="space-y-4">
              <div className="h-14 w-14 rounded-2xl bg-[#0070f3]/10 border border-[#0070f3]/30 flex items-center justify-center text-[#0070f3] group-hover:scale-110 transition-transform">
                <Activity className="h-7 w-7" />
              </div>
              <h3 className="text-2xl font-bold text-white group-hover:text-[#0070f3] transition-colors">
                OSINT &amp; Whale Tracking
              </h3>
              <p className="text-sm text-neutral-400 leading-relaxed">
                Trace deployer wallets to identify serial founders, detect insider accumulation, and track high-volume smart money trades in real time.
              </p>
            </div>
            <ul className="mt-6 space-y-2.5 text-xs text-neutral-300 border-t border-neutral-800/80 pt-6">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#0070f3]" />
                <span>Deployer historical transaction cluster analysis</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#0070f3]" />
                <span>Whale buy/sell threshold alerts directly to chat</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#0070f3]" />
                <span>Caller reputation scoring &amp; win rate tracking</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Pricing / Monetization Section */}
      <section id="pricing" className="py-20 px-6 max-w-5xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Transparent, Degen-Friendly Pricing
          </h2>
          <p className="mt-3 text-sm text-neutral-400">
            Start for free, upgrade when your community scales. Pay seamlessly with Solana USDT.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          {/* Free Tier */}
          <div className="p-8 rounded-3xl bg-[#0f141a]/60 border border-neutral-800 flex flex-col justify-between">
            <div className="space-y-4">
              <span className="text-xs font-mono uppercase font-bold text-neutral-400 tracking-wider">Community Starter</span>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">$0</span>
                <span className="text-xs text-neutral-400 font-semibold">/ month</span>
              </div>
              <p className="text-xs text-neutral-400">
                Perfect for launching new tokens and safeguarding early community groups.
              </p>

              <ul className="space-y-3 text-xs text-neutral-300 pt-4 border-t border-neutral-800">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500" />
                  <span>1 Autonomous Telegram Bot</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500" />
                  <span>Standard RAG Knowledge Base</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-neutral-500" />
                  <span>Basic Scam &amp; Spam Filter</span>
                </li>
              </ul>
            </div>

            <Link href="/register" className="mt-8">
              <Button variant="outline" className="w-full border-neutral-700 hover:bg-neutral-800 text-white font-bold text-xs rounded-xl h-12 cursor-pointer">
                Start Free
              </Button>
            </Link>
          </div>

          {/* Pro Tier */}
          <div className="p-8 rounded-3xl bg-gradient-to-b from-[#0e1f18] to-[#0a120e] border-2 border-[#00e599]/60 shadow-2xl shadow-[#00e599]/10 relative flex flex-col justify-between">
            <div className="absolute -top-3.5 right-6 px-3 py-1 rounded-full bg-[#00e599] text-black text-[10px] font-black uppercase tracking-wider">
              Recommended
            </div>

            <div className="space-y-4">
              <span className="text-xs font-mono uppercase font-bold text-[#00e599] tracking-wider">Zoe Pro Guardian</span>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">$20</span>
                <span className="text-xs text-neutral-400 font-semibold">/ month (USDT)</span>
              </div>
              <p className="text-xs text-neutral-300">
                Full-spectrum autonomous protection, live news intelligence, and unlimited whale monitoring.
              </p>

              <ul className="space-y-3 text-xs text-neutral-200 pt-4 border-t border-[#00e599]/20">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                  <span className="font-semibold text-white">Full On-Chain Token Scanner</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                  <span className="font-semibold text-white">Live Web3 News Intelligence Engine</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                  <span>OSINT &amp; Whale Wallet Radar</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#00e599]" />
                  <span>Sub-150ms Anti-Drainer Protection</span>
                </li>
              </ul>
            </div>

            <Link href="/login" className="mt-8">
              <Button className="w-full bg-[#00e599] hover:bg-[#00c685] text-black font-extrabold text-xs rounded-xl h-12 shadow-lg shadow-[#00e599]/20 cursor-pointer transition-all hover:scale-[1.02]">
                Deploy Pro Terminal
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Conversion Banner Section */}
      <section className="py-20 px-6 max-w-6xl mx-auto w-full text-center">
        <div className="p-12 sm:p-16 rounded-3xl bg-gradient-to-r from-[#0d1612] via-[#09151e] to-[#0d1612] border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-[#00e599]/10 rounded-full blur-[90px] pointer-events-none" />

          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Ready to upgrade your Web3 community?
          </h2>
          <p className="mt-4 text-base text-neutral-400 max-w-xl mx-auto">
            Deploy Zoe into your Telegram or Discord in under 60 seconds and experience the new standard of autonomous intelligence.
          </p>

          <div className="mt-8 flex justify-center">
            <Link href="/register">
              <Button className="h-14 px-10 bg-[#00e599] hover:bg-[#00c685] text-black font-extrabold text-base rounded-2xl shadow-xl shadow-[#00e599]/30 cursor-pointer transition-all hover:scale-105">
                Deploy Zoe Now
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-neutral-800/80 bg-[#07090c] py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <ZoeLogo size={32} variant="mark" glow />
            <div className="flex flex-col">
              <span className="font-extrabold text-white text-sm">Zoe Intelligence Engine</span>
              <span className="text-[11px] text-neutral-500 font-medium">Built for the on-chain era.</span>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-neutral-400 font-medium">
            <Link href="/investigate" className="hover:text-white transition-colors">
              Token Scanner
            </Link>
            <Link href="/trading" className="hover:text-white transition-colors">
              Trading Terminal
            </Link>
            <Link href="/login" className="hover:text-white transition-colors">
              Client Portal
            </Link>
            <Link href="/admin/overview" className="hover:text-white transition-colors">
              Admin
            </Link>
          </div>

          <div className="flex items-center gap-2 text-xs text-neutral-500 font-mono">
            <span className="h-2 w-2 rounded-full bg-[#00e599]" />
            <span>All Systems Nominal</span>
          </div>
        </div>

        <div className="max-w-7xl mx-auto mt-8 pt-8 border-t border-neutral-900 text-center text-xs text-neutral-600">
          &copy; 2026 Zoe Intelligence. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
