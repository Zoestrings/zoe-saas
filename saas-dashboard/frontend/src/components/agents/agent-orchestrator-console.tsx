"use client"

import { useState } from "react"
import { api, OrchestrationResult } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Bot, Play, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, Clock, Layers, Sparkles } from "lucide-react"

export function AgentOrchestratorConsole() {
  const [goal, setGoal] = useState("Conduct comprehensive due diligence on Virtuals Protocol: news, market metrics, and contract verification")
  const [targetEntity, setTargetEntity] = useState("Virtuals Protocol")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<OrchestrationResult | null>(null)

  const handleOrchestrate = async () => {
    if (!goal.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.orchestrateGoal(goal, targetEntity)
      setResult(res)
    } catch (err: any) {
      setError(err?.message || "Orchestration failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-cyan-500/30 bg-slate-900/60 shadow-xl backdrop-blur">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl flex items-center gap-2 text-cyan-400">
                <Bot className="w-5 h-5" /> Central Agent Orchestrator
              </CardTitle>
              <CardDescription className="text-slate-400">
                Inspired by Virtuals Protocol & ElizaOS. Submit high-level Web3 goals; Zoe decomposes tasks across 10 specialized agents and synthesizes verified intelligence briefs.
              </CardDescription>
            </div>
            <Badge variant="outline" className="border-cyan-500 text-cyan-400 px-3 py-1 bg-cyan-950/40">
              Multi-Agent DAG
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Research Goal / Prompt
              </label>
              <textarea
                className="w-full h-24 bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition"
                placeholder="e.g. Audit smart contract for honeypot, fetch DEX volume, and verify CT sentiment for $SOL"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Target Protocol / CA
              </label>
              <input
                type="text"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition"
                placeholder="e.g. Solana or 0x..."
                value={targetEntity}
                onChange={(e) => setTargetEntity(e.target.value)}
              />
              <div className="pt-2">
                <Button
                  onClick={handleOrchestrate}
                  disabled={loading || !goal.trim()}
                  className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium shadow-lg shadow-cyan-950"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <Clock className="w-4 h-4 animate-spin" /> Orchestrating Agents...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Play className="w-4 h-4" /> Run Autonomous Plan
                    </span>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-red-300 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Preset Prompts */}
          <div className="flex flex-wrap gap-2 pt-2">
            <span className="text-xs text-slate-500 self-center">Presets:</span>
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7 border-slate-800 bg-slate-950/40 hover:bg-slate-800 text-slate-300"
              onClick={() => {
                setGoal("Full due diligence on Arbitrum: check DEX liquidity, TVL narrative, and latest news")
                setTargetEntity("Arbitrum")
              }}
            >
              Full Due Diligence
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7 border-slate-800 bg-slate-950/40 hover:bg-slate-800 text-slate-300"
              onClick={() => {
                setGoal("Audit contract security risks, mint authority, and holder concentration for Bonk")
                setTargetEntity("Bonk")
              }}
            >
              Security & Honeypot Scan
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7 border-slate-800 bg-slate-950/40 hover:bg-slate-800 text-slate-300"
              onClick={() => {
                setGoal("Evaluate AI Agent and DePIN narrative velocity and CT social sentiment")
                setTargetEntity("AI Agents")
              }}
            >
              Narrative & Sentiment Scan
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Execution Results DAG & Brief */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Execution Pipeline Header */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-slate-900/40 border-slate-800">
              <CardContent className="p-4">
                <p className="text-xs text-slate-500">Status</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-semibold uppercase text-emerald-400">{result.status}</span>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-900/40 border-slate-800">
              <CardContent className="p-4">
                <p className="text-xs text-slate-500">Execution Time</p>
                <p className="text-sm font-semibold text-slate-200 mt-1">
                  {result.total_time_ms || result.total_execution_time_ms || 0} ms
                </p>
              </CardContent>
            </Card>
            <Card className="bg-slate-900/40 border-slate-800">
              <CardContent className="p-4">
                <p className="text-xs text-slate-500">Agents Involved</p>
                <p className="text-sm font-semibold text-cyan-400 mt-1">
                  {result.agents_involved?.length || 0} Specialized Agents
                </p>
              </CardContent>
            </Card>
            <Card className="bg-slate-900/40 border-slate-800">
              <CardContent className="p-4">
                <p className="text-xs text-slate-500">Verification Gate</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <ShieldCheck className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm font-semibold text-cyan-400">Fact-Checked & Verified</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Subtask Execution Pipeline Map */}
          <Card className="border-slate-800 bg-slate-900/40">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" /> Multi-Agent Execution Pipeline (Audit Trail)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-3">
                {result.audit_trail?.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                      <div>
                        <p className="text-xs font-semibold text-slate-200 capitalize">
                          {step.agent?.replace("_agent", "").replace("_", " ")}
                        </p>
                        <p className="text-[10px] text-slate-500 font-mono">{step.latency_ms}ms</p>
                      </div>
                    </div>
                    {idx < (result.audit_trail?.length || 0) - 1 && (
                      <ArrowRight className="w-4 h-4 text-slate-600" />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Final Synthesized Intelligence Brief */}
          <Card className="border-cyan-500/40 bg-slate-950/80 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-lg text-cyan-400 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400" /> Synthesized Multi-Agent Intelligence Brief
              </CardTitle>
              <CardDescription className="text-slate-400">
                Verified outputs synthesized from collaborative specialist agent execution.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-lg text-slate-200 whitespace-pre-wrap font-sans text-sm leading-relaxed">
                {result.final_synthesis || result.final_output?.synthesized_summary || JSON.stringify(result.final_output, null, 2)}
              </div>

              {/* Individual Step Outputs Accordion/Card */}
              {result.step_results && Object.keys(result.step_results).length > 0 && (
                <div className="space-y-3 pt-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Individual Specialist Findings</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.entries(result.step_results).map(([stepKey, stepData]: [string, any]) => (
                      <div key={stepKey} className="p-3 bg-slate-900/40 border border-slate-800/60 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between text-cyan-400 font-medium capitalize">
                          <span>{stepKey.replace("step_", "")} Agent</span>
                          <Badge variant="outline" className="text-[10px] border-slate-700">Done</Badge>
                        </div>
                        <p className="text-slate-300 line-clamp-3">
                          {typeof stepData === "object" ? stepData?.summary || JSON.stringify(stepData) : String(stepData)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
