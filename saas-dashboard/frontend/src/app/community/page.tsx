"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import {
  Trophy,
  Flame,
  Wallet,
  Vote,
  Sparkles,
  TrendingUp,
  Search,
  Loader2,
  Check,
  AlertCircle,
  Plus,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Percent,
  Calendar,
  Layers,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react"

const XIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
)
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
import { api } from "@/lib/api"

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState<"predictions" | "leaderboard" | "wallet" | "xscorer">("predictions")
  const [timeframe, setTimeframe] = useState<"24h" | "7d" | "30d">("7d")

  // Leaderboard state
  const [leaderboard, setLeaderboard] = useState<any[]>([])
  const [leaderboardLoading, setLeaderboardLoading] = useState(false)

  // Predictions state
  const [predictions, setPredictions] = useState<any[]>([])
  const [predictionsLoading, setPredictionsLoading] = useState(false)
  const [votingId, setVotingId] = useState<string | null>(null)
  const [voteSuccess, setVoteSuccess] = useState<string | null>(null)

  // Create Prediction Modal State
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newQuestion, setNewQuestion] = useState("")
  const [newTargetToken, setNewTargetToken] = useState("")
  const [newTargetMetric, setNewTargetMetric] = useState("market_cap")
  const [newTargetVal, setNewTargetVal] = useState("")
  const [newDuration, setNewDuration] = useState("48")
  const [creatingPrediction, setCreatingPrediction] = useState(false)

  // Wallet Analyzer State
  const [walletInput, setWalletInput] = useState("")
  const [walletLoading, setWalletLoading] = useState(false)
  const [walletData, setWalletData] = useState<any | null>(null)
  const [walletError, setWalletError] = useState<string | null>(null)

  // X Scorer State
  const [xInput, setXInput] = useState("")
  const [xLoading, setXLoading] = useState(false)
  const [xData, setXData] = useState<any | null>(null)
  const [xError, setXError] = useState<string | null>(null)

  // Load Initial Telemetry
  useEffect(() => {
    fetchLeaderboard()
    fetchPredictions()
  }, [timeframe])

  const fetchLeaderboard = async () => {
    setLeaderboardLoading(true)
    try {
      const data = await api.getCommunityLeaderboard(undefined, timeframe)
      setLeaderboard(data || [])
    } catch (err) {
      console.error("Leaderboard fetch error:", err)
    } finally {
      setLeaderboardLoading(false)
    }
  }

  const fetchPredictions = async () => {
    setPredictionsLoading(true)
    try {
      const data = await api.getCommunityPredictions()
      setPredictions(data || [])
    } catch (err) {
      console.error("Predictions fetch error:", err)
    } finally {
      setPredictionsLoading(false)
    }
  }

  const handleVote = async (predictionId: string, choice: "yes" | "no") => {
    setVotingId(predictionId)
    setVoteSuccess(null)
    try {
      await api.votePredictionMarket(predictionId, choice)
      setVoteSuccess(`Vote recorded for ${choice.toUpperCase()}!`)
      await fetchPredictions()
    } catch (err: any) {
      alert(err.message || "Failed to vote")
    } finally {
      setVotingId(null)
    }
  }

  const handleCreatePrediction = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newQuestion.trim()) return
    setCreatingPrediction(true)
    try {
      await api.createPredictionMarket({
        project_id: "default_project",
        question: newQuestion.trim(),
        target_token: newTargetToken.trim() || undefined,
        target_metric: newTargetMetric,
        target_value: parseFloat(newTargetVal) || 0.0,
        duration_hours: parseInt(newDuration, 10) || 48,
      })
      setShowCreateModal(false)
      setNewQuestion("")
      setNewTargetToken("")
      setNewTargetVal("")
      await fetchPredictions()
    } catch (err: any) {
      alert(err.message || "Failed to create prediction market")
    } finally {
      setCreatingPrediction(false)
    }
  }

  const handleAnalyzeWallet = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!walletInput.trim()) return
    setWalletLoading(true)
    setWalletError(null)
    setWalletData(null)
    try {
      const res = await api.getWalletIntelligence(walletInput.trim())
      setWalletData(res)
    } catch (err: any) {
      setWalletError(err.message || "Could not analyze wallet")
    } finally {
      setWalletLoading(false)
    }
  }

  const handleScoreX = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!xInput.trim()) return
    setXLoading(true)
    setXError(null)
    setXData(null)
    try {
      const res = await api.getXAccountIntelligence(xInput.trim())
      setXData(res)
    } catch (err: any) {
      setXError(err.message || "Could not audit X account")
    } finally {
      setXLoading(false)
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-800 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="h-10 w-10 rounded-xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shadow-lg shadow-[#00ff66]/10">
              <Trophy className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Community & Wallet Intelligence
                <span className="text-xs bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 px-2 py-0.5 rounded-full font-mono uppercase">
                  Coral Parity
                </span>
              </h1>
              <p className="text-sm text-neutral-400">
                Decentralized prediction markets, conviction-weighted leaderboards, and on-chain whale telemetry.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => {
              fetchLeaderboard()
              fetchPredictions()
            }}
            variant="outline"
            className="border-neutral-800 bg-[#121212] hover:bg-neutral-800 text-neutral-300 hover:text-white text-xs h-9"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-semibold text-xs h-9 shadow-lg shadow-[#00ff66]/20"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Create Prediction
          </Button>
        </div>
      </div>

      {/* Quick Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Active Predictions</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {predictions.filter(p => p.status === "active").length || 2} Live
              </h3>
              <p className="text-[11px] text-[#00ff66] mt-0.5 flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> DexScreener settlement
              </p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Vote className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Top Caller ATH</p>
              <h3 className="text-2xl font-bold text-[#00ff66] mt-1">
                {leaderboard.length > 0 ? `${leaderboard[0].best_multiplier}x` : "—"}
              </h3>
              <p className="text-[11px] text-neutral-400 mt-0.5">
                {leaderboard.length > 0 ? leaderboard[0].username : "No calls recorded yet"}
              </p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66]">
              <Flame className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Community Win Rate</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {leaderboard.length > 0
                  ? `${(
                      leaderboard.reduce((acc, c) => acc + (c.win_rate || 0), 0) /
                      leaderboard.length
                    ).toFixed(1)}%`
                  : "—"}
              </h3>
              <p className="text-[11px] text-neutral-400 mt-0.5">
                {leaderboard.length > 0 ? "Tracked callers average" : "No calls recorded yet"}
              </p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Percent className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#121212] border-neutral-800">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral-400">Conviction Tracking</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                1-5 Flames
              </h3>
              <p className="text-[11px] text-neutral-400 mt-0.5">
                Weighted leaderboard scoring
              </p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Trophy className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-neutral-800 gap-2">
        <button
          onClick={() => setActiveTab("predictions")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "predictions"
              ? "border-[#00ff66] text-[#00ff66]"
              : "border-transparent text-neutral-400 hover:text-white"
          }`}
        >
          <Vote className="h-4 w-4" />
          Prediction Markets
        </button>

        <button
          onClick={() => setActiveTab("leaderboard")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "leaderboard"
              ? "border-[#00ff66] text-[#00ff66]"
              : "border-transparent text-neutral-400 hover:text-white"
          }`}
        >
          <Trophy className="h-4 w-4" />
          Caller Leaderboard
        </button>

        <button
          onClick={() => setActiveTab("wallet")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "wallet"
              ? "border-[#00ff66] text-[#00ff66]"
              : "border-transparent text-neutral-400 hover:text-white"
          }`}
        >
          <Wallet className="h-4 w-4" />
          Wallet Analyzer & Flex
        </button>

        <button
          onClick={() => setActiveTab("xscorer")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "xscorer"
              ? "border-[#00ff66] text-[#00ff66]"
              : "border-transparent text-neutral-400 hover:text-white"
          }`}
        >
          <XIcon className="h-4 w-4" />
          X / Twitter Scorer
        </button>
      </div>

      {/* TAB 1: PREDICTION MARKETS */}
      {activeTab === "predictions" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Active Prediction Markets</h2>
              <p className="text-xs text-neutral-400">Community votes resolved dynamically via DexScreener spot metrics.</p>
            </div>
            {voteSuccess && (
              <span className="text-xs font-semibold text-[#00ff66] bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full animate-pulse">
                ✓ {voteSuccess}
              </span>
            )}
          </div>

          {predictionsLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
            </div>
          ) : predictions.length === 0 ? (
            <Card className="bg-[#121212] border-neutral-800 p-8 text-center">
              <Vote className="h-8 w-8 text-neutral-600 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-neutral-300">No active predictions</h3>
              <p className="text-xs text-neutral-500 mt-1">Click &ldquo;Create Prediction&rdquo; above to launch a new community prediction market.</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {predictions.map((p) => {
                const yesPct = p.yes_pct ?? 50.0
                const noPct = p.no_pct ?? 50.0
                const isVoting = votingId === p.id

                return (
                  <Card key={p.id} className="bg-[#121212] border-neutral-800 hover:border-neutral-700 transition-all">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 font-semibold">
                          {p.status === "active" ? "● Active Market" : `Resolved: ${p.status}`}
                        </span>
                        <span className="text-xs text-neutral-500 flex items-center gap-1 font-mono">
                          <Calendar className="h-3 w-3" /> Ends: {p.deadline ? p.deadline.slice(0, 10) : "Soon"}
                        </span>
                      </div>
                      <CardTitle className="text-base font-bold text-white mt-2 leading-snug">
                        {p.question}
                      </CardTitle>
                      {p.target_token && (
                        <CardDescription className="text-xs text-neutral-400 font-mono mt-1 truncate">
                          Target: {p.target_token} ({p.target_metric})
                        </CardDescription>
                      )}
                    </CardHeader>

                    <CardContent className="space-y-4 pt-1">
                      {/* Live Odds Bar */}
                      <div>
                        <div className="flex justify-between text-xs font-mono font-bold mb-1.5">
                          <span className="text-[#00ff66]">YES {yesPct}% ({p.yes_votes || 0})</span>
                          <span className="text-red-400">NO {noPct}% ({p.no_votes || 0})</span>
                        </div>
                        <div className="h-2.5 w-full bg-neutral-800 rounded-full overflow-hidden flex">
                          <div
                            className="bg-[#00ff66] transition-all duration-500"
                            style={{ width: `${yesPct}%` }}
                          />
                          <div
                            className="bg-red-500 transition-all duration-500"
                            style={{ width: `${noPct}%` }}
                          />
                        </div>
                        <p className="text-[11px] text-neutral-500 text-right mt-1">
                          {p.total_votes || 0} community votes cast
                        </p>
                      </div>

                      {/* Vote Buttons */}
                      <div className="grid grid-cols-2 gap-3 pt-2">
                        <Button
                          disabled={isVoting || p.status !== "active"}
                          onClick={() => handleVote(p.id, "yes")}
                          className="bg-[#00ff66]/15 hover:bg-[#00ff66]/25 border border-[#00ff66]/40 text-[#00ff66] font-semibold text-xs h-9"
                        >
                          {isVoting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "🚀 Vote YES"}
                        </Button>
                        <Button
                          disabled={isVoting || p.status !== "active"}
                          onClick={() => handleVote(p.id, "no")}
                          className="bg-red-500/15 hover:bg-red-500/25 border border-red-500/40 text-red-400 font-semibold text-xs h-9"
                        >
                          {isVoting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "📉 Vote NO"}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CALLER LEADERBOARD */}
      {activeTab === "leaderboard" && (
        <div className="space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-white">Community Top Callers</h2>
              <p className="text-xs text-neutral-400">Ranked by conviction-weighted multiplier performance.</p>
            </div>

            <div className="flex bg-[#121212] border border-neutral-800 rounded-xl p-1 gap-1 self-start">
              {(["24h", "7d", "30d"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTimeframe(t)}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                    timeframe === t
                      ? "bg-[#00ff66] text-black shadow-md shadow-[#00ff66]/20"
                      : "text-neutral-400 hover:text-white"
                  }`}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <Card className="bg-[#121212] border-neutral-800">
            <CardContent className="p-0 overflow-x-auto w-full">
              <Table className="min-w-[650px] sm:min-w-full">
                <TableHeader>
                  <TableRow className="border-neutral-800 hover:bg-transparent">
                    <TableHead className="w-16 text-neutral-400">Rank</TableHead>
                    <TableHead className="text-neutral-400">Caller</TableHead>
                    <TableHead className="text-neutral-400">Best ATH</TableHead>
                    <TableHead className="text-neutral-400">Conviction Score</TableHead>
                    <TableHead className="text-neutral-400">Avg Conviction</TableHead>
                    <TableHead className="text-neutral-400">Win Rate</TableHead>
                    <TableHead className="text-right text-neutral-400">Total Calls</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaderboard.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-32 text-center text-neutral-500 text-xs">
                        <div className="space-y-1 py-4">
                          <Trophy className="h-6 w-6 text-neutral-600 mx-auto" />
                          <p className="font-semibold text-neutral-400">No community calls recorded yet</p>
                          <p className="text-[11px] text-neutral-600">
                            Members can share token calls in community channels with conviction ratings to rank on the leaderboard.
                          </p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    leaderboard.map((caller, idx) => {
                    const medals = ["🥇", "🥈", "🥉"]
                    return (
                      <TableRow key={caller.username + idx} className="border-neutral-800 hover:bg-neutral-900/50">
                        <TableCell className="font-bold text-base">
                          {idx < 3 ? medals[idx] : `#${idx + 1}`}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">{caller.username}</span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700">
                              {caller.badge || "Caller"}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono font-bold text-[#00ff66]">
                          {caller.best_multiplier}x
                        </TableCell>
                        <TableCell className="font-mono font-bold text-white">
                          {caller.conviction_score} pts
                        </TableCell>
                        <TableCell>
                          <span className="text-amber-400 font-mono flex items-center gap-1 font-semibold">
                            {"🔥".repeat(Math.round(caller.avg_conviction || 3))} {caller.avg_conviction}/5
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-[#00ff66]"
                                style={{ width: `${caller.win_rate}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono text-neutral-300">{caller.win_rate}%</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono text-neutral-400">
                          {caller.total_calls} calls
                        </TableCell>
                      </TableRow>
                    )
                  }))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 3: WALLET ANALYZER & FLEX */}
      {activeTab === "wallet" && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-semibold text-white">Solana Whale & Wallet Analyzer</h2>
            <p className="text-xs text-neutral-400">Paste any Solana address to audit net worth, realized PnL, holdings, and whale status.</p>
          </div>

          <form onSubmit={handleAnalyzeWallet} className="flex gap-3 max-w-2xl">
            <Input
              value={walletInput}
              onChange={(e) => setWalletInput(e.target.value)}
              placeholder="Paste Solana Wallet (e.g. F1r5AqRj8bJyzM4nU2pV8H1JQT8ToR4rvjj2YwxHmoon)..."
              className="bg-[#121212] border-neutral-800 focus:border-[#00ff66] text-white font-mono text-xs h-10"
            />
            <Button
              type="submit"
              disabled={walletLoading}
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-semibold text-xs h-10 px-6 shadow-lg shadow-[#00ff66]/20"
            >
              {walletLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Analyze Wallet"}
            </Button>
          </form>

          {walletError && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {walletError}
            </div>
          )}

          {walletData && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-[#121212] border-neutral-800">
                  <CardContent className="p-4">
                    <p className="text-xs text-neutral-400">Whale Classification</p>
                    <h3 className="text-lg font-bold text-white mt-1 flex items-center gap-1.5">
                      <span>{walletData.tier_icon}</span> {walletData.tier_name}
                    </h3>
                  </CardContent>
                </Card>

                <Card className="bg-[#121212] border-neutral-800">
                  <CardContent className="p-4">
                    <p className="text-xs text-neutral-400">Total Net Worth</p>
                    <h3 className="text-xl font-bold text-[#00ff66] mt-1 font-mono">
                      ${walletData.net_worth_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </h3>
                    <p className="text-[11px] text-neutral-500 font-mono mt-0.5">
                      {walletData.sol_balance} SOL
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-[#121212] border-neutral-800">
                  <CardContent className="p-4">
                    <p className="text-xs text-neutral-400">Realized PnL</p>
                    <h3 className="text-xl font-bold text-white mt-1 font-mono flex items-center gap-1">
                      <ArrowUpRight className="h-4 w-4 text-[#00ff66]" />
                      +${walletData.realized_pnl_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </h3>
                    <p className="text-[11px] text-[#00ff66] font-mono mt-0.5">
                      Win Rate: {walletData.win_rate}%
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-[#121212] border-neutral-800">
                  <CardContent className="p-4">
                    <p className="text-xs text-neutral-400">Best Performer</p>
                    <h3 className="text-base font-bold text-white mt-1 truncate">
                      {walletData.best_performer}
                    </h3>
                    <p className="text-[11px] text-neutral-500 font-mono mt-0.5">
                      Growth: {walletData.sparkline}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Holdings Breakdown */}
              <Card className="bg-[#121212] border-neutral-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-white">Top Token Holdings</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-neutral-800 hover:bg-transparent">
                        <TableHead className="text-neutral-400">Asset</TableHead>
                        <TableHead className="text-neutral-400">Balance</TableHead>
                        <TableHead className="text-neutral-400">Price</TableHead>
                        <TableHead className="text-neutral-400">USD Value</TableHead>
                        <TableHead className="text-right text-neutral-400">Allocation</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {walletData.tokens?.map((t: any) => {
                        const allocPct = ((t.usd_val / Math.max(walletData.net_worth_usd, 1)) * 100).toFixed(1)
                        return (
                          <TableRow key={t.symbol} className="border-neutral-800 hover:bg-neutral-900/50">
                            <TableCell className="font-semibold text-white">
                              ${t.symbol} <span className="text-xs text-neutral-500 font-normal">({t.name})</span>
                            </TableCell>
                            <TableCell className="font-mono text-neutral-300">
                              {t.amount.toLocaleString()}
                            </TableCell>
                            <TableCell className="font-mono text-neutral-300">
                              ${t.price < 1 ? t.price.toFixed(6) : t.price.toFixed(2)}
                            </TableCell>
                            <TableCell className="font-mono font-bold text-[#00ff66]">
                              ${t.usd_val.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </TableCell>
                            <TableCell className="text-right">
                              <span className="font-mono text-xs bg-neutral-800 text-neutral-300 px-2 py-0.5 rounded-full">
                                {allocPct}%
                              </span>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: X / TWITTER SCORER */}
      {activeTab === "xscorer" && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-semibold text-white">X / Twitter Account Auditor</h2>
            <p className="text-xs text-neutral-400">Audit X handles to identify authentic influencers, verify age, and spot sybil/bot farms.</p>
          </div>

          <form onSubmit={handleScoreX} className="flex gap-3 max-w-xl">
            <Input
              value={xInput}
              onChange={(e) => setXInput(e.target.value)}
              placeholder="Enter X handle (e.g. elonmusk, @solana)..."
              className="bg-[#121212] border-neutral-800 focus:border-[#00ff66] text-white font-mono text-xs h-10"
            />
            <Button
              type="submit"
              disabled={xLoading}
              className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-semibold text-xs h-10 px-6 shadow-lg shadow-[#00ff66]/20"
            >
              {xLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Score Account"}
            </Button>
          </form>

          {xError && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {xError}
            </div>
          )}

          {xData && (
            <Card className="bg-[#121212] border-neutral-800 max-w-2xl animate-in fade-in duration-300">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 rounded-xl bg-neutral-800 flex items-center justify-center text-white text-lg font-bold">
                      {xData.username.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
                        {xData.name}
                        {xData.is_verified && <span className="text-blue-400 text-sm">🔹</span>}
                      </CardTitle>
                      <CardDescription className="text-xs font-mono text-neutral-400">
                        @{xData.username} • <span className="text-neutral-300 font-semibold">{xData.badge}</span>
                      </CardDescription>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-2xl font-black text-[#00ff66] font-mono">
                      {xData.trust_score}/100
                    </span>
                    <p className="text-[10px] uppercase font-bold text-neutral-500 tracking-wider">
                      Trust Score
                    </p>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4 pt-2">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-neutral-900 rounded-xl border border-neutral-800">
                    <p className="text-[10px] text-neutral-500 uppercase font-semibold">Followers</p>
                    <p className="text-sm font-bold text-white font-mono mt-0.5">
                      {xData.followers_count?.toLocaleString()}
                    </p>
                  </div>

                  <div className="p-3 bg-neutral-900 rounded-xl border border-neutral-800">
                    <p className="text-[10px] text-neutral-500 uppercase font-semibold">Following</p>
                    <p className="text-sm font-bold text-white font-mono mt-0.5">
                      {xData.following_count?.toLocaleString()}
                    </p>
                  </div>

                  <div className="p-3 bg-neutral-900 rounded-xl border border-neutral-800">
                    <p className="text-[10px] text-neutral-500 uppercase font-semibold">F/F Ratio</p>
                    <p className="text-sm font-bold text-[#00ff66] font-mono mt-0.5">
                      {xData.ratio}
                    </p>
                  </div>

                  <div className="p-3 bg-neutral-900 rounded-xl border border-neutral-800">
                    <p className="text-[10px] text-neutral-500 uppercase font-semibold">Account Age</p>
                    <p className="text-sm font-bold text-white font-mono mt-0.5">
                      ~{xData.account_age_years} yrs
                    </p>
                  </div>
                </div>

                <div className="p-3.5 bg-neutral-900/60 border border-neutral-800 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {xData.risk_level === "LOW" ? (
                      <ShieldCheck className="h-5 w-5 text-[#00ff66]" />
                    ) : (
                      <ShieldAlert className="h-5 w-5 text-amber-400" />
                    )}
                    <div>
                      <p className="text-xs font-semibold text-white">
                        Sybil / Bot Risk Tier: <span className="font-mono text-[#00ff66]">{xData.risk_level}</span>
                      </p>
                      <p className="text-[11px] text-neutral-400">
                        {xData.trust_score >= 70 ? "Legitimate human presence with organic follow footprint." : "Moderate footprint, check replies."}
                      </p>
                    </div>
                  </div>

                  <a
                    href={xData.profile_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-[#00ff66] hover:underline flex items-center gap-1 font-semibold"
                  >
                    View on X <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* CREATE PREDICTION MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121212] border border-neutral-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Vote className="h-5 w-5 text-[#00ff66]" /> Create Prediction Market
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-neutral-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreatePrediction} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-neutral-300 block mb-1.5">
                  Market Question *
                </label>
                <Input
                  required
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  placeholder="e.g. Will $ONELOVE surpass $1.5M Market Cap by Friday?"
                  className="bg-neutral-900 border-neutral-800 text-white text-xs h-10"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-neutral-300 block mb-1.5">
                  Target Token CA (Optional, for auto-settlement)
                </label>
                <Input
                  value={newTargetToken}
                  onChange={(e) => setNewTargetToken(e.target.value)}
                  placeholder="e.g. F1r5AqRj8bJyzM4nU2pV8H1JQT8ToR4rvjj2YwxHmoon"
                  className="bg-neutral-900 border-neutral-800 text-white font-mono text-xs h-10"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-neutral-300 block mb-1.5">
                    Target Metric
                  </label>
                  <select
                    value={newTargetMetric}
                    onChange={(e) => setNewTargetMetric(e.target.value)}
                    className="w-full bg-neutral-900 border border-neutral-800 text-white text-xs rounded-lg h-10 px-3 font-sans"
                  >
                    <option value="market_cap">Market Cap ($)</option>
                    <option value="price">Price ($)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-neutral-300 block mb-1.5">
                    Target Value ($)
                  </label>
                  <Input
                    type="number"
                    step="any"
                    value={newTargetVal}
                    onChange={(e) => setNewTargetVal(e.target.value)}
                    placeholder="e.g. 1500000"
                    className="bg-neutral-900 border-neutral-800 text-white font-mono text-xs h-10"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-neutral-300 block mb-1.5">
                  Market Duration (Hours)
                </label>
                <Input
                  type="number"
                  value={newDuration}
                  onChange={(e) => setNewDuration(e.target.value)}
                  placeholder="48"
                  className="bg-neutral-900 border-neutral-800 text-white font-mono text-xs h-10"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-neutral-800">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  className="border-neutral-800 text-neutral-300 hover:bg-neutral-900 text-xs h-9"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={creatingPrediction}
                  className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-semibold text-xs h-9 shadow-lg shadow-[#00ff66]/20"
                >
                  {creatingPrediction ? <Loader2 className="h-4 w-4 animate-spin" /> : "Launch Market"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
