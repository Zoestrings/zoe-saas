"use client"

import * as React from "react"
import { useState, useEffect, useMemo, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  ArrowUpRight, 
  RefreshCw, 
  Search, 
  Loader2, 
  AlertCircle, 
  Check, 
  Copy, 
  RotateCcw, 
  Wallet, 
  PieChart, 
  ArrowRightLeft, 
  ExternalLink,
  ShieldCheck,
  Sparkles,
  Info
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { 
  api, 
  PaperWalletResponse, 
  PaperPosition, 
  PaperTradeItem, 
  InvestigationReport 
} from "@/lib/api"

// Quick token suggestions
const SAMPLE_TOKENS = [
  { name: "Solana", symbol: "SOL", ca: "So11111111111111111111111111111111111111112" },
  { name: "Jupiter", symbol: "JUP", ca: "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN" },
  { name: "PEPE (ETH)", symbol: "PEPE", ca: "0x6982508145454Ce325dDbE47a25d4ec3d2311933" },
  { name: "Virtuals (Base)", symbol: "VIRTUAL", ca: "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b" },
  { name: "One Love", symbol: "ONELOVE", ca: "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon" },
]

function TradingTerminalContent() {
  const searchParams = useSearchParams()
  const caFromUrl = searchParams.get("ca")

  // Selected Token State
  const [tokenAddress, setTokenAddress] = useState<string>(
    caFromUrl || "So11111111111111111111111111111111111111112"
  )
  const [tokenSearchInput, setTokenSearchInput] = useState<string>(
    caFromUrl || "So11111111111111111111111111111111111111112"
  )
  const [tokenInfo, setTokenInfo] = useState<{
    name: string
    symbol: string
    price: number
    chain?: string
    chainId?: string
    liquidity?: number
    fdv?: number
  } | null>(null)
  const [tokenLoading, setTokenLoading] = useState<boolean>(false)

  // Trade Form State
  const [tradeType, setTradeType] = useState<"buy" | "sell">("buy")
  const [amountUsdt, setAmountUsdt] = useState<string>("100")
  const [executing, setExecuting] = useState<boolean>(false)
  const [tradeSuccessMsg, setTradeSuccessMsg] = useState<string | null>(null)
  const [tradeError, setTradeError] = useState<string | null>(null)

  // Wallet and Positions State
  const [wallet, setWallet] = useState<PaperWalletResponse | null>(null)
  const [walletLoading, setWalletLoading] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<"positions" | "history">("positions")

  // Reset Modal
  const [isResetOpen, setIsResetOpen] = useState(false)
  const [resetting, setResetting] = useState(false)

  // Credits & AI Pre-Trade Research State (Pillar 2)
  const [credits, setCredits] = useState<number | null>(null)
  const [researchOpen, setResearchOpen] = useState(false)
  const [researchLoading, setResearchLoading] = useState(false)
  const [researchError, setResearchError] = useState<string | null>(null)
  const [researchResult, setResearchResult] = useState<{
    token_name?: string
    token_symbol?: string
    bullets: string[]
    disclaimer: string
  } | null>(null)

  // Copied state
  const [copied, setCopied] = useState(false)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Fetch Wallet Data & Credit Balance
  const loadWallet = async () => {
    setWalletLoading(true)
    try {
      const [data, ent] = await Promise.allSettled([
        api.getPaperWallet(),
        api.getEntitlement(),
      ])
      if (data.status === "fulfilled") {
        setWallet(data.value)
      }
      if (ent.status === "fulfilled" && ent.value) {
        setCredits(ent.value.credits ?? 0)
      }
    } catch (err: any) {
      console.error("Failed to load paper wallet:", err)
    } finally {
      setWalletLoading(false)
    }
  }

  // Run AI Pre-Trade Research Brief (10 Credits)
  const handleRunAiResearch = async () => {
    setResearchOpen(true)
    setResearchLoading(true)
    setResearchError(null)
    setResearchResult(null)
    try {
      const res = await api.runTradingResearch(tokenAddress)
      setResearchResult({
        token_name: res.token_name,
        token_symbol: res.token_symbol,
        bullets: res.bullets || [],
        disclaimer: res.disclaimer || "This is AI-generated research, not financial advice.",
      })
      if (typeof res.credits_remaining === "number") {
        setCredits(res.credits_remaining)
      } else {
        const ent = await api.getEntitlement().catch(() => null)
        if (ent) setCredits(ent.credits ?? 0)
      }
    } catch (err: any) {
      setResearchError(err?.message || "Failed to run AI research. Please check your credit balance.")
    } finally {
      setResearchLoading(false)
    }
  }

  // Fetch Token Market Data via Scanner API
  const loadTokenMarketData = async (ca: string) => {
    setTokenLoading(true)
    setTradeError(null)
    try {
      const res: InvestigationReport = await api.investigate(ca)
      if (res && res.valid) {
        setTokenInfo({
          name: res.name || res.market?.name || "Unknown Token",
          symbol: res.symbol || res.market?.symbol || "TOKEN",
          price: res.market?.price_usd || 0.0,
          chain: res.chain || "Solana",
          chainId: res.market?.chain_id || (ca.startsWith("0x") ? "ethereum" : "solana"),
          liquidity: res.market?.liquidity_usd ?? undefined,
          fdv: res.market?.market_cap ?? undefined,
        })
      } else {
        // Default fallback price if scanner failed
        const isEvm = ca.startsWith("0x")
        setTokenInfo({
          name: res?.name || (isEvm ? "EVM Asset" : "Solana Asset"),
          symbol: res?.symbol || (isEvm ? "ETH" : "SOL"),
          price: 150.0,
          chain: isEvm ? "Ethereum" : "Solana",
          chainId: isEvm ? "ethereum" : "solana",
        })
      }
    } catch (err) {
      // Fallback
      const isEvm = ca.startsWith("0x")
      setTokenInfo({
        name: isEvm ? "EVM Asset" : "Solana Asset",
        symbol: isEvm ? "ETH" : "TOKEN",
        price: 1.0,
        chain: isEvm ? "Ethereum" : "Solana",
        chainId: isEvm ? "ethereum" : "solana",
      })
    } finally {
      setTokenLoading(false)
    }
  }

  // Initial Load & URL CA Sync
  useEffect(() => {
    loadWallet()
  }, [])

  useEffect(() => {
    if (caFromUrl && caFromUrl.trim()) {
      const ca = caFromUrl.trim()
      setTokenAddress(ca)
      setTokenSearchInput(ca)
      loadTokenMarketData(ca)
    } else {
      loadTokenMarketData(tokenAddress)
    }
  }, [caFromUrl])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const clean = tokenSearchInput.trim()
    if (!clean) return
    setTokenAddress(clean)
    loadTokenMarketData(clean)
  }

  const handleSelectSample = (sample: typeof SAMPLE_TOKENS[0]) => {
    setTokenSearchInput(sample.ca)
    setTokenAddress(sample.ca)
    loadTokenMarketData(sample.ca)
  }

  // Owned Position for Current Selected Token
  const currentPosition = useMemo<PaperPosition | undefined>(() => {
    if (!wallet || !wallet.positions) return undefined
    return wallet.positions.find(
      (p) => p.token_address.toLowerCase() === tokenAddress.toLowerCase()
    )
  }, [wallet, tokenAddress])

  // Calculated Output Token / USDT
  const calculatedTokens = useMemo(() => {
    const usdtNum = parseFloat(amountUsdt) || 0
    const price = tokenInfo?.price || 0
    if (price <= 0 || usdtNum <= 0) return 0
    return usdtNum / price
  }, [amountUsdt, tokenInfo])

  // Quick Amount Presets
  const setPercentageAmount = (percent: number) => {
    if (tradeType === "buy") {
      const balance = wallet?.balance_usdt || 0
      const calc = (balance * (percent / 100)).toFixed(2)
      setAmountUsdt(calc)
    } else {
      if (!currentPosition || !tokenInfo?.price) {
        setAmountUsdt("0")
        return
      }
      const positionValue = currentPosition.token_amount * tokenInfo.price
      const calc = (positionValue * (percent / 100)).toFixed(2)
      setAmountUsdt(calc)
    }
  }

  // Execute Simulated Paper Trade
  const handleExecuteTrade = async () => {
    const val = parseFloat(amountUsdt)
    if (isNaN(val) || val <= 0) {
      setTradeError("Please enter a valid USDT amount greater than 0.")
      return
    }

    if (tradeType === "buy" && wallet && val > wallet.balance_usdt) {
      setTradeError(
        `Insufficient virtual funds. Available: $${wallet.balance_usdt.toFixed(2)} USDT.`
      )
      return
    }

    if (tradeType === "sell") {
      if (!currentPosition || currentPosition.token_amount <= 0) {
        setTradeError("You do not hold any tokens in this position to sell.")
        return
      }
    }

    setExecuting(true)
    setTradeError(null)
    setTradeSuccessMsg(null)

    try {
      const res = await api.executePaperTrade({
        token_address: tokenAddress,
        trade_type: tradeType,
        amount_usdt: val,
        token_name: tokenInfo?.name || "Simulated Token",
      })

      setTradeSuccessMsg(res.message || "Simulated trade executed successfully!")
      setTimeout(() => setTradeSuccessMsg(null), 5000)
      loadWallet()
    } catch (err: any) {
      setTradeError(err.message || "Failed to execute paper trade.")
    } finally {
      setExecuting(false)
    }
  }

  // Quick Sell from Open Positions table
  const handleQuickSell = (pos: PaperPosition) => {
    setTokenAddress(pos.token_address)
    setTokenSearchInput(pos.token_address)
    setTradeType("sell")
    loadTokenMarketData(pos.token_address)
    setAmountUsdt(pos.current_value_usdt.toFixed(2))
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  // Reset Wallet Handler
  const handleConfirmReset = async () => {
    setResetting(true)
    try {
      await api.resetPaperWallet()
      setIsResetOpen(false)
      loadWallet()
    } catch (err: any) {
      alert(err.message || "Failed to reset paper wallet.")
    } finally {
      setResetting(false)
    }
  }

  const getChainBadgeStyle = (chain?: string) => {
    const c = (chain || "Solana").toLowerCase()
    if (c.includes("eth")) return "bg-purple-500/10 text-purple-400 border-purple-500/30"
    if (c.includes("base")) return "bg-blue-500/10 text-blue-400 border-blue-500/30"
    if (c.includes("bsc") || c.includes("binance")) return "bg-amber-500/10 text-amber-400 border-amber-500/30"
    if (c.includes("arbitrum")) return "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
    if (c.includes("polygon")) return "bg-violet-500/10 text-violet-400 border-violet-500/30"
    return "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
  }

  // DexScreener Chart Embed URL (Dynamically routes to solana, ethereum, base, bsc, etc.)
  const chartUrl = useMemo(() => {
    const rawChain = (tokenInfo?.chainId || (tokenAddress.startsWith("0x") ? "ethereum" : "solana")).toLowerCase()
    return `https://dexscreener.com/${rawChain}/${tokenAddress}?embed=1&theme=dark&trades=0&info=0`
  }, [tokenAddress, tokenInfo])

  return (
    <div className="space-y-6 pb-16">
      {/* Mega-Module 11 Paper Trading Notice Banner */}
      <div className="p-4 rounded-3xl bg-[#121212] border border-[#00ff66]/30 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shrink-0">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-sm">🧪 Paper Trading Engine</span>
              <span className="text-[10px] bg-[#00ff66]/20 text-[#00ff66] font-bold px-2 py-0.5 rounded-full border border-[#00ff66]/30 uppercase tracking-wider">
                Risk-Free Simulation
              </span>
            </div>
            <p className="text-xs text-[#818c99] mt-0.5">
              Practice trading Solana &amp; EVM tokens with $10,000 USDT virtual money. Prices, liquidity, and charts streamed live from DexScreener.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-center">
          {credits !== null && (
            <div className="px-3 py-1.5 rounded-full bg-[#161b22] border border-[#00ff66]/30 text-xs font-mono text-white flex items-center gap-1.5">
              <Sparkles className="h-3 w-3 text-[#00ff66]" />
              <span>{credits.toLocaleString()} Credits</span>
            </div>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={loadWallet}
            disabled={walletLoading}
            className="border-[#212833] bg-[#161b22] hover:bg-[#1f2631] text-white text-xs h-9 px-3.5 rounded-full cursor-pointer"
          >
            <RefreshCw className={`h-3 w-3 mr-1.5 ${walletLoading ? "animate-spin text-[#00ff66]" : ""}`} />
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsResetOpen(true)}
            className="border-neutral-800 bg-[#161b22] hover:bg-rose-950/30 hover:border-rose-500/40 text-neutral-300 hover:text-rose-400 text-xs h-9 px-3.5 rounded-full cursor-pointer"
          >
            <RotateCcw className="h-3 w-3 mr-1.5" />
            Reset $10k
          </Button>
        </div>
      </div>

      {/* Main 2-Column Trading Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Chart & Trade Execution Panel */}
        <div className="lg:col-span-8 space-y-6">
          {/* Token Selector & Search Bar */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-5 shadow-xl space-y-4">
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#818c99]" />
                <Input
                  placeholder="Paste Solana or EVM contract address (e.g. So11... or 0x6982...)..."
                  value={tokenSearchInput}
                  onChange={(e) => setTokenSearchInput(e.target.value)}
                  className="pl-10 bg-[#161b22] border-[#212833] text-white text-xs h-10 rounded-xl focus:border-[#00ff66] font-mono"
                />
              </div>
              <Button
                type="submit"
                disabled={tokenLoading}
                className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-5 rounded-xl cursor-pointer"
              >
                {tokenLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Load Chart"}
              </Button>
            </form>

            {/* Quick Sample Suggestions */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-[11px] font-semibold text-[#818c99]">Quick Markets:</span>
              {SAMPLE_TOKENS.map((s) => (
                <button
                  key={s.symbol}
                  type="button"
                  onClick={() => handleSelectSample(s)}
                  className={`px-3 py-1 rounded-full border text-[11px] font-semibold transition-all cursor-pointer ${
                    tokenAddress.toLowerCase() === s.ca.toLowerCase()
                      ? "bg-[#00ff66] text-black border-[#00ff66]"
                      : "bg-[#161b22] border-[#212833] text-[#818c99] hover:text-white hover:border-neutral-600"
                  }`}
                >
                  ${s.symbol}
                </button>
              ))}
            </div>
          </div>

          {/* Token Live Header & DexScreener Chart Embed */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl overflow-hidden shadow-2xl">
            {/* Header info */}
            <div className="p-5 border-b border-[#212833] flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] font-black text-sm">
                  {tokenInfo?.symbol ? tokenInfo.symbol[0] : "T"}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-white tracking-tight">
                      {tokenInfo?.name || "Token Asset"}
                    </h2>
                    <span className="text-xs font-mono text-[#00ff66] font-semibold">
                      ${tokenInfo?.symbol || "TOKEN"}
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${getChainBadgeStyle(tokenInfo?.chain)}`}>
                      {tokenInfo?.chain || "Solana"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[11px] font-mono text-[#818c99] truncate max-w-[200px]">
                      {tokenAddress}
                    </span>
                    <button
                      onClick={() => copyToClipboard(tokenAddress)}
                      className="text-[#818c99] hover:text-[#00ff66] transition-colors cursor-pointer"
                      title="Copy Address"
                    >
                      {copied ? <Check className="h-3 w-3 text-[#00ff66]" /> : <Copy className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Price & Stats */}
              <div className="flex items-center gap-6">
                <div>
                  <span className="text-[10px] text-[#818c99] uppercase font-bold tracking-wider block">
                    Live Dex Price
                  </span>
                  <div className="text-xl font-black text-white font-mono mt-0.5">
                    ${tokenInfo?.price ? tokenInfo.price.toFixed(tokenInfo.price < 0.01 ? 6 : 2) : "0.00"}
                  </div>
                </div>

                {tokenInfo?.liquidity !== undefined && (
                  <div>
                    <span className="text-[10px] text-[#818c99] uppercase font-bold tracking-wider block">
                      Liquidity
                    </span>
                    <div className="text-sm font-bold text-neutral-300 font-mono mt-0.5">
                      ${tokenInfo.liquidity ? tokenInfo.liquidity.toLocaleString() : "N/A"}
                    </div>
                  </div>
                )}

                <Link
                  href={`/investigate?ca=${encodeURIComponent(tokenAddress)}`}
                  className="inline-flex items-center gap-1 text-xs text-[#00ff66] hover:underline font-bold bg-[#00ff66]/10 px-3 py-1.5 rounded-full border border-[#00ff66]/30"
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Scan Token
                </Link>
              </div>
            </div>

            {/* Embedded Live Chart */}
            <div className="relative w-full h-[450px] bg-black">
              <iframe
                src={chartUrl}
                title="DexScreener Live Chart"
                className="w-full h-full border-0"
                loading="lazy"
              />
            </div>
          </div>

          {/* Buy & Sell Execution Panel */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 shadow-xl space-y-5">
            <div className="flex items-center justify-between pb-4 border-b border-[#212833]">
              <div className="flex items-center gap-2">
                <ArrowRightLeft className="h-5 w-5 text-[#00ff66]" />
                <h3 className="font-bold text-white text-base">Simulated Order Book</h3>
              </div>

              {/* Buy / Sell Toggle Tabs */}
              <div className="flex items-center bg-[#161b22] p-1 rounded-2xl border border-[#212833]">
                <button
                  type="button"
                  onClick={() => setTradeType("buy")}
                  className={`px-6 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    tradeType === "buy"
                      ? "bg-[#00ff66] text-black shadow-lg shadow-[#00ff66]/20"
                      : "text-neutral-400 hover:text-white"
                  }`}
                >
                  BUY
                </button>
                <button
                  type="button"
                  onClick={() => setTradeType("sell")}
                  className={`px-6 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    tradeType === "sell"
                      ? "bg-rose-500 text-white shadow-lg shadow-rose-500/20"
                      : "text-neutral-400 hover:text-white"
                  }`}
                >
                  SELL
                </button>
              </div>
            </div>

            {/* Success & Error Banners */}
            {tradeSuccessMsg && (
              <div className="p-3.5 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
                <Check className="h-4 w-4 shrink-0" />
                <span>{tradeSuccessMsg}</span>
              </div>
            )}

            {tradeError && (
              <div className="p-3.5 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{tradeError}</span>
              </div>
            )}

            {/* Inputs & Sliders */}
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#818c99]">
                  {tradeType === "buy" ? "Virtual USDT Available" : "Token Shares Held"}
                </span>
                <span className="font-mono text-white font-bold">
                  {tradeType === "buy"
                    ? `$${(wallet?.balance_usdt || 0).toLocaleString()} USDT`
                    : `${currentPosition?.token_amount ? currentPosition.token_amount.toFixed(4) : "0.0000"} ${tokenInfo?.symbol || "TOKEN"}`}
                </span>
              </div>

              {/* Amount input */}
              <div className="space-y-1.5">
                <div className="relative">
                  <Input
                    type="number"
                    step="any"
                    placeholder="0.00"
                    value={amountUsdt}
                    onChange={(e) => setAmountUsdt(e.target.value)}
                    className="bg-[#161b22] border-[#212833] text-white text-base font-mono h-12 rounded-2xl focus:border-[#00ff66] pr-20"
                  />
                  <div className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-[#818c99] pointer-events-none">
                    USDT
                  </div>
                </div>
              </div>

              {/* Percentage Presets */}
              <div className="grid grid-cols-4 gap-2">
                {[25, 50, 75, 100].map((pct) => (
                  <button
                    key={pct}
                    type="button"
                    onClick={() => setPercentageAmount(pct)}
                    className="py-1.5 rounded-xl bg-[#161b22] hover:bg-[#1f2631] border border-[#212833] text-[#818c99] hover:text-[#00ff66] text-xs font-mono font-bold transition-colors cursor-pointer"
                  >
                    {pct === 100 ? "MAX" : `${pct}%`}
                  </button>
                ))}
              </div>

              {/* Output Summary Pill */}
              <div className="p-4 rounded-2xl bg-[#0e1116] border border-[#212833] flex items-center justify-between text-xs">
                <span className="text-[#818c99]">
                  {tradeType === "buy" ? "Estimated Tokens Received:" : "Estimated USDT Return:"}
                </span>
                <span className="font-mono font-bold text-white text-sm">
                  {tradeType === "buy"
                    ? `${calculatedTokens.toLocaleString(undefined, { maximumFractionDigits: 4 })} ${tokenInfo?.symbol || "TOKEN"}`
                    : `$${(parseFloat(amountUsdt) || 0).toLocaleString()} USDT`}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2.5">
                <Button
                  type="button"
                  onClick={handleRunAiResearch}
                  disabled={researchLoading || tokenLoading}
                  variant="outline"
                  className="w-full h-11 rounded-2xl border-[#00ff66]/40 bg-[#00ff66]/10 hover:bg-[#00ff66]/20 text-[#00ff66] font-bold text-xs tracking-wide cursor-pointer transition-all"
                >
                  🧠 Run AI Research (10 Credits)
                </Button>

                <Button
                  type="button"
                  onClick={handleExecuteTrade}
                  disabled={executing || tokenLoading}
                  className={`w-full h-12 rounded-2xl font-black text-sm tracking-wide shadow-xl cursor-pointer transition-all ${
                    tradeType === "buy"
                      ? "bg-[#00ff66] hover:bg-[#00e65c] text-black shadow-[#00ff66]/20"
                      : "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/20"
                  }`}
                >
                  {executing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Simulating On-Chain Swap...
                    </>
                  ) : (
                    `EXECUTE SIMULATED ${tradeType.toUpperCase()} ($${(parseFloat(amountUsdt) || 0).toFixed(2)} USDT)`
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Virtual Portfolio & Positions */}
        <div className="lg:col-span-4 space-y-6">
          {/* Virtual Portfolio Overview Card */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#212833]">
              <div className="flex items-center gap-2">
                <Wallet className="h-5 w-5 text-[#00ff66]" />
                <h3 className="font-bold text-white text-base">Paper Wallet</h3>
              </div>
              <span className="text-[10px] bg-neutral-800 text-[#00ff66] font-bold px-2.5 py-0.5 rounded-full border border-neutral-700">
                LIVE P&L
              </span>
            </div>

            {/* Total Portfolio Value */}
            <div className="space-y-1">
              <span className="text-xs text-[#818c99] uppercase font-bold tracking-wider">
                Total Portfolio Value
              </span>
              <div className="text-3xl font-black text-white tracking-tight font-mono">
                ${(wallet?.total_portfolio_value_usdt || 10000.0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            {/* P&L & Cash Split */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 rounded-2xl bg-[#161b22] border border-[#212833]">
                <span className="text-[11px] text-[#818c99] block">Virtual Cash</span>
                <span className="text-sm font-bold text-white font-mono mt-0.5 block">
                  ${(wallet?.balance_usdt || 10000.0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#161b22] border border-[#212833]">
                <span className="text-[11px] text-[#818c99] block">Total Return (P&L)</span>
                <div className={`text-sm font-bold font-mono mt-0.5 flex items-center gap-1 ${
                  (wallet?.total_pnl_usdt || 0) >= 0 ? "text-[#00ff66]" : "text-rose-400"
                }`}>
                  {(wallet?.total_pnl_usdt || 0) >= 0 ? (
                    <TrendingUp className="h-3.5 w-3.5" />
                  ) : (
                    <TrendingDown className="h-3.5 w-3.5" />
                  )}
                  <span>
                    {(wallet?.total_pnl_usdt || 0) >= 0 ? "+" : ""}
                    ${(wallet?.total_pnl_usdt || 0).toFixed(2)} ({wallet?.total_pnl_percent || 0}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Positions & Trade History Tabs */}
          <div className="bg-[#12161c] border border-[#212833] rounded-3xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#212833] pb-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveTab("positions")}
                  className={`text-xs font-bold pb-2 transition-all cursor-pointer ${
                    activeTab === "positions"
                      ? "text-[#00ff66] border-b-2 border-[#00ff66]"
                      : "text-[#818c99] hover:text-white"
                  }`}
                >
                  Open Positions ({wallet?.positions?.length || 0})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("history")}
                  className={`text-xs font-bold pb-2 transition-all cursor-pointer ${
                    activeTab === "history"
                      ? "text-[#00ff66] border-b-2 border-[#00ff66]"
                      : "text-[#818c99] hover:text-white"
                  }`}
                >
                  Trade Log ({wallet?.recent_trades?.length || 0})
                </button>
              </div>
            </div>

            {/* Tab 1: Open Positions */}
            {activeTab === "positions" && (
              <div className="space-y-3">
                {!wallet?.positions || wallet.positions.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#818c99]">
                    No open positions yet. Use the order book to simulate buying tokens.
                  </div>
                ) : (
                  wallet.positions.map((pos) => {
                    const isProfit = pos.unrealized_pnl_usdt >= 0
                    return (
                      <div
                        key={pos.token_address}
                        className="p-3.5 rounded-2xl bg-[#161b22] border border-[#212833] space-y-2.5 hover:border-[#00ff66]/30 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-bold text-white text-xs block">
                              {pos.token_name}
                            </span>
                            <span className="text-[10px] text-[#818c99] font-mono">
                              {pos.token_amount.toFixed(4)} shares
                            </span>
                          </div>

                          <div className="text-right">
                            <span className="text-xs font-bold text-white font-mono block">
                              ${pos.current_value_usdt.toFixed(2)}
                            </span>
                            <span
                              className={`text-[10px] font-bold font-mono ${
                                isProfit ? "text-[#00ff66]" : "text-rose-400"
                              }`}
                            >
                              {isProfit ? "+" : ""}
                              ${pos.unrealized_pnl_usdt.toFixed(2)} ({pos.unrealized_pnl_percent}%)
                            </span>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-[#212833] flex items-center justify-between text-[11px] text-[#818c99]">
                          <span>Avg Entry: ${pos.avg_buy_price.toFixed(pos.avg_buy_price < 0.01 ? 6 : 4)}</span>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleQuickSell(pos)}
                            className="h-6 px-2 text-[10px] font-bold text-rose-400 hover:text-white hover:bg-rose-950/40 rounded-lg cursor-pointer"
                          >
                            Sell Position
                          </Button>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            )}

            {/* Tab 2: Trade History */}
            {activeTab === "history" && (
              <div className="space-y-3">
                {!wallet?.recent_trades || wallet.recent_trades.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#818c99]">
                    No simulated trades recorded yet.
                  </div>
                ) : (
                  wallet.recent_trades.map((t) => {
                    const isBuy = t.trade_type === "buy"
                    let timeFormatted = "Recently"
                    if (t.created_at) {
                      try {
                        timeFormatted = new Date(t.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      } catch {}
                    }

                    return (
                      <div
                        key={t.id}
                        className="p-3 rounded-2xl bg-[#161b22] border border-[#212833] flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase ${
                              isBuy
                                ? "bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {t.trade_type}
                          </span>
                          <div>
                            <span className="font-semibold text-white block truncate max-w-[120px]">
                              {t.token_name || "Token"}
                            </span>
                            <span className="text-[10px] text-[#818c99]">{timeFormatted}</span>
                          </div>
                        </div>

                        <div className="text-right font-mono">
                          <span className="font-bold text-white block">
                            ${t.amount_usdt.toFixed(2)}
                          </span>
                          <span className="text-[10px] text-[#818c99]">
                            @{t.price_at_trade < 0.01 ? t.price_at_trade.toFixed(6) : t.price_at_trade.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reset Confirmation Dialog */}
      <Dialog open={isResetOpen} onOpenChange={setIsResetOpen}>
        <DialogContent className="w-[92vw] sm:max-w-[420px] max-h-[85vh] overflow-y-auto bg-[#12161c] border border-neutral-800 text-white rounded-3xl p-5 sm:p-6 shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <RotateCcw className="h-5 w-5 text-rose-400" />
              Reset Simulated Portfolio
            </DialogTitle>
            <DialogDescription className="text-xs text-[#818c99] pt-2">
              Are you sure you want to reset your paper trading balance? This will clear all open simulated positions and restore your virtual balance to $10,000.00 USDT.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="pt-4 border-t border-[#212833] mt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsResetOpen(false)}
              className="text-xs text-[#818c99] hover:text-white hover:bg-[#181d24] rounded-xl h-10"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleConfirmReset}
              disabled={resetting}
              className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs h-10 px-5 rounded-xl cursor-pointer"
            >
              {resetting ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : "Confirm Reset"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Pre-Trade Intelligence Brief Modal */}
      <Dialog open={researchOpen} onOpenChange={setResearchOpen}>
        <DialogContent className="bg-[#12161c] border-[#212833] text-white rounded-3xl max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[#00ff66]" />
              <span>Pre-Trade Intelligence Brief</span>
              {researchResult?.token_symbol && (
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                  {researchResult.token_symbol}
                </span>
              )}
            </DialogTitle>
            <DialogDescription className="text-xs text-[#818c99]">
              Objective multi-source analysis combining DexScreener liquidity, GoPlus/RugCheck holders, and X sentiment.
            </DialogDescription>
          </DialogHeader>

          <div className="py-2">
            {researchLoading ? (
              <div className="py-10 flex flex-col items-center justify-center gap-3 text-neutral-400">
                <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
                <p className="text-xs font-medium text-white">Analyzing liquidity, holder concentration, and X sentiment...</p>
              </div>
            ) : researchError ? (
              <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{researchError}</span>
              </div>
            ) : researchResult ? (
              <div className="rounded-2xl bg-neutral-950/60 backdrop-blur-xl border border-neutral-800/80 p-5 space-y-4">
                <ul className="space-y-3">
                  {researchResult.bullets.map((bullet, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs sm:text-sm text-neutral-200 leading-relaxed">
                      <span className="h-5 w-5 rounded-full bg-[#00ff66]/15 border border-[#00ff66]/30 text-[#00ff66] font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>

                <div className="pt-3 border-t border-neutral-800/80 flex items-center gap-2 text-[11px] text-neutral-400">
                  <Info className="h-3.5 w-3.5 text-neutral-500 shrink-0" />
                  <span>{researchResult.disclaimer}</span>
                </div>
              </div>
            ) : null}
          </div>

          <DialogFooter className="border-t border-[#212833] pt-3">
            <Button
              type="button"
              onClick={() => setResearchOpen(false)}
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-9 px-5 rounded-xl cursor-pointer"
            >
              Close Brief
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default function TradingTerminalPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 flex flex-col items-center justify-center gap-3 text-[#818c99] text-xs">
          <Loader2 className="h-6 w-6 animate-spin text-[#00ff66]" />
          <span>Loading Paper Trading Terminal...</span>
        </div>
      }
    >
      <TradingTerminalContent />
    </Suspense>
  )
}
