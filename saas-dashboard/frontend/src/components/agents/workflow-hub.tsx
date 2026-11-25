"use client"

import { useState, useEffect } from "react"
import { api, WorkflowTemplate } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { GitFork, Play, Clock, CheckCircle, ArrowRight, Layers, Sparkles } from "lucide-react"

export function WorkflowHub() {
  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [runningId, setRunningId] = useState<string | null>(null)
  const [runResult, setRunResult] = useState<any | null>(null)

  useEffect(() => {
    loadWorkflows()
  }, [])

  const loadWorkflows = async () => {
    try {
      setLoading(true)
      const data = await api.getWorkflows()
      setWorkflows(data)
    } catch (err) {
      console.error("Failed to load workflows:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleExecuteWorkflow = async (workflowId: string) => {
    setRunningId(workflowId)
    setRunResult(null)
    try {
      const res = await api.runWorkflow(workflowId, "Ethereum")
      setRunResult(res)
    } catch (err) {
      console.error("Workflow execution failed:", err)
    } finally {
      setRunningId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <GitFork className="w-5 h-5 text-cyan-400" /> Autonomous Agent Workflows (Module 7 & 8)
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Pre-configured multi-step DAG execution pipelines coordinating specialized agents with automated step dependencies.
        </p>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-slate-500">Loading autonomous workflows...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Preset Standard Workflows */}
          <Card className="border-cyan-500/30 bg-slate-900/40 hover:border-cyan-500/60 transition flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="border-cyan-500 text-cyan-400 text-[10px]">
                  Standard Template
                </Badge>
                <Badge variant="outline" className="border-emerald-800 text-emerald-400 text-[10px]">
                  Ready
                </Badge>
              </div>
              <CardTitle className="text-sm font-semibold text-slate-100 mt-2">
                Full Web3 Due Diligence
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Executes Research -&gt; News -&gt; DEX Market -&gt; Security Scan -&gt; Fact Verification in sequence.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-[11px] text-slate-500 flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-cyan-400" /> 5 Steps across 5 Agents
              </div>
              <Button
                onClick={() => handleExecuteWorkflow("project_due_diligence")}
                disabled={runningId !== null}
                className="w-full bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-8"
              >
                {runningId === "project_due_diligence" ? (
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 animate-spin" /> Running DAG...
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5">
                    <Play className="w-3.5 h-3.5" /> Execute Due Diligence
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="border-slate-700 text-slate-400 text-[10px]">
                  Standard Template
                </Badge>
                <Badge variant="outline" className="border-emerald-800 text-emerald-400 text-[10px]">
                  Ready
                </Badge>
              </div>
              <CardTitle className="text-sm font-semibold text-slate-100 mt-2">
                Daily Sector Market Intelligence
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Aggregates sector narrative velocity, CT social sentiment, and DEX volume metrics.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-[11px] text-slate-500 flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-cyan-400" /> 4 Steps across 4 Agents
              </div>
              <Button
                onClick={() => handleExecuteWorkflow("daily_market_intel")}
                disabled={runningId !== null}
                className="w-full bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs h-8"
              >
                {runningId === "daily_market_intel" ? (
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 animate-spin" /> Running DAG...
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5">
                    <Play className="w-3.5 h-3.5" /> Run Market Intel
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="border-slate-700 text-slate-400 text-[10px]">
                  Standard Template
                </Badge>
                <Badge variant="outline" className="border-emerald-800 text-emerald-400 text-[10px]">
                  Ready
                </Badge>
              </div>
              <CardTitle className="text-sm font-semibold text-slate-100 mt-2">
                Smart Contract & Security Audit
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Evaluates honeypots, mint/freeze authorities, and vulnerability heuristics.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-[11px] text-slate-500 flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-cyan-400" /> 3 Steps across 3 Agents
              </div>
              <Button
                onClick={() => handleExecuteWorkflow("security_audit_pipeline")}
                disabled={runningId !== null}
                className="w-full bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs h-8"
              >
                {runningId === "security_audit_pipeline" ? (
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 animate-spin" /> Running DAG...
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5">
                    <Play className="w-3.5 h-3.5" /> Run Security Audit
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Execution Result Log */}
      {runResult && (
        <Card className="border-cyan-500/40 bg-slate-950 p-4 animate-in fade-in duration-300">
          <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-sm text-cyan-400 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" /> Workflow Execution Succeeded
            </CardTitle>
            <Badge variant="outline" className="text-xs font-mono border-slate-700">
              {runResult.execution_time_ms || 0} ms
            </Badge>
          </CardHeader>
          <CardContent className="p-0 space-y-3">
            <div className="p-3 bg-slate-900/60 rounded-md border border-slate-800 text-xs font-mono text-slate-300 max-h-48 overflow-y-auto">
              <pre>{JSON.stringify(runResult.step_outputs || runResult.step_results, null, 2)}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
