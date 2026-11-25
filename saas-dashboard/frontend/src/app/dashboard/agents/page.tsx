"use client"

import * as React from "react"
import { useState } from "react"
import Link from "next/link"
import {
  Bot,
  Layers,
  GitFork,
  Activity,
  ArrowLeft,
  Sparkles,
  ShieldCheck,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AgentOrchestratorConsole } from "@/components/agents/agent-orchestrator-console"
import { AgentDirectory } from "@/components/agents/agent-directory"
import { WorkflowHub } from "@/components/agents/workflow-hub"
import { AgentAnalyticsView } from "@/components/agents/agent-analytics-view"

type AgentTab = "orchestrator" | "directory" | "workflows" | "analytics"

export default function AgentsDashboardPage() {
  const [activeTab, setActiveTab] = useState<AgentTab>("orchestrator")

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/projects">
            <Button variant="ghost" size="sm" className="h-8 text-xs text-slate-400 hover:text-slate-100">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-800/50 text-cyan-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                Zoe Autonomous Agents <span className="text-[10px] text-cyan-400 font-mono">PHASE 4</span>
              </h1>
              <p className="text-[10px] text-slate-400">
                Multi-Agent Orchestration, Specialized Specialists & Autonomous DAG Workflows
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-cyan-800/60 bg-cyan-950/30 text-cyan-300 text-xs hidden sm:flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            Sandboxed Security &amp; Tenant Isolation
          </Badge>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Tab Navigation Pill Bar */}
        <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900/60 border border-slate-800/80 overflow-x-auto">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab("orchestrator")}
            className={`text-xs h-8 flex items-center gap-2 px-3 rounded-lg transition ${
              activeTab === "orchestrator"
                ? "bg-cyan-600 text-white shadow-md font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Central Orchestrator
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab("directory")}
            className={`text-xs h-8 flex items-center gap-2 px-3 rounded-lg transition ${
              activeTab === "directory"
                ? "bg-cyan-600 text-white shadow-md font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            Specialized Agents (10)
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab("workflows")}
            className={`text-xs h-8 flex items-center gap-2 px-3 rounded-lg transition ${
              activeTab === "workflows"
                ? "bg-cyan-600 text-white shadow-md font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            Autonomous Workflows
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab("analytics")}
            className={`text-xs h-8 flex items-center gap-2 px-3 rounded-lg transition ${
              activeTab === "analytics"
                ? "bg-cyan-600 text-white shadow-md font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Telemetry &amp; Audit Logs
          </Button>
        </div>

        {/* Tab View Content */}
        <div className="pt-2">
          {activeTab === "orchestrator" && <AgentOrchestratorConsole />}
          {activeTab === "directory" && <AgentDirectory />}
          {activeTab === "workflows" && <WorkflowHub />}
          {activeTab === "analytics" && <AgentAnalyticsView />}
        </div>
      </main>
    </div>
  )
}
