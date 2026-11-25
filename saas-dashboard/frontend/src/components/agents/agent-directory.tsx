"use client"

import { useState, useEffect } from "react"
import { api, AgentConfig } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Bot, Shield, Wrench, Plus, CheckCircle, Search, Sparkles } from "lucide-react"

export function AgentDirectory() {
  const [agents, setAgents] = useState<AgentConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [showBuilder, setShowBuilder] = useState(false)

  // Agent Builder Form State
  const [customName, setCustomName] = useState("")
  const [customDesc, setCustomDesc] = useState("")
  const [customCategory, setCustomCategory] = useState("intelligence")
  const [customTools, setCustomTools] = useState("web_search, crypto_news")
  const [builderLoading, setBuilderLoading] = useState(false)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      setLoading(true)
      const data = await api.getAgents()
      setAgents(data)
    } catch (err) {
      console.error("Failed to load agents:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!customName.trim() || !customDesc.trim()) return
    setBuilderLoading(true)
    try {
      const tools = customTools.split(",").map((t) => t.trim()).filter(Boolean)
      await api.createAgent({
        name: customName,
        description: customDesc,
        category: customCategory,
        approved_tools: tools,
        security_level: "read_only",
      })
      setCustomName("")
      setCustomDesc("")
      setShowBuilder(false)
      await loadAgents()
    } catch (err) {
      console.error("Failed to register agent:", err)
    } finally {
      setBuilderLoading(false)
    }
  }

  const categories = ["all", "intelligence", "security", "market", "operations"]

  const filteredAgents = agents.filter((agent) => {
    const matchesSearch =
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCat =
      selectedCategory === "all" ||
      agent.category?.toLowerCase() === selectedCategory.toLowerCase()
    return matchesSearch && matchesCat
  })

  return (
    <div className="space-y-6">
      {/* Header & Builder Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Bot className="w-5 h-5 text-cyan-400" /> Specialized Agent Directory & Marketplace
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse foundational specialist agents or build custom sandboxed agents with granular tool permissions.
          </p>
        </div>
        <Button
          onClick={() => setShowBuilder(!showBuilder)}
          className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-9"
        >
          <Plus className="w-4 h-4 mr-1.5" /> {showBuilder ? "Close Builder" : "Create Custom Agent"}
        </Button>
      </div>

      {/* Agent Builder Card */}
      {showBuilder && (
        <Card className="border-cyan-500/40 bg-slate-950 p-4 animate-in fade-in duration-300">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="text-base text-cyan-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4" /> Agent Builder (Module 5)
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Configure an autonomous specialist agent with strictly sandboxed capabilities and tool allowlists.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleCreateAgent} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-400">Agent Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Solana DePIN Specialist"
                  className="w-full bg-slate-900 border border-slate-800 rounded-md p-2 text-xs text-slate-100 mt-1 focus:outline-none focus:border-cyan-500"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400">Category</label>
                <select
                  className="w-full bg-slate-900 border border-slate-800 rounded-md p-2 text-xs text-slate-100 mt-1 focus:outline-none focus:border-cyan-500"
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                >
                  <option value="intelligence">Intelligence & Research</option>
                  <option value="security">Security & Risk</option>
                  <option value="market">Market & DEX</option>
                  <option value="operations">Community Operations</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">Description & Mission</label>
              <textarea
                required
                rows={2}
                placeholder="What is this agent's mission and area of expertise?"
                className="w-full bg-slate-900 border border-slate-800 rounded-md p-2 text-xs text-slate-100 mt-1 focus:outline-none focus:border-cyan-500"
                value={customDesc}
                onChange={(e) => setCustomDesc(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">Approved Tool Allowlists (comma-separated)</label>
              <input
                type="text"
                placeholder="web_search, crypto_news, dexscreener, knowledge_rag"
                className="w-full bg-slate-900 border border-slate-800 rounded-md p-2 text-xs text-slate-100 mt-1 focus:outline-none focus:border-cyan-500"
                value={customTools}
                onChange={(e) => setCustomTools(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setShowBuilder(false)} className="text-xs">
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={builderLoading} className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs">
                {builderLoading ? "Registering..." : "Register Agent"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1">
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(cat)}
              className={`text-xs h-7 capitalize ${
                selectedCategory === cat
                  ? "bg-cyan-600 hover:bg-cyan-500 text-white"
                  : "border-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {cat}
            </Button>
          ))}
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search agents or tools..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Agents Grid */}
      {loading ? (
        <div className="p-8 text-center text-xs text-slate-500">Loading specialist registry...</div>
      ) : filteredAgents.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-500 border border-slate-800 rounded-lg">
          No specialized agents found matching your query.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((ag) => (
            <Card key={ag.agent_id} className="border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800/40 text-cyan-400">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-semibold text-slate-100">{ag.name}</CardTitle>
                      <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-400 mt-0.5 capitalize">
                        {ag.category}
                      </Badge>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-[10px] border-emerald-800/50 bg-emerald-950/30 text-emerald-400 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> Active
                  </Badge>
                </div>
                <CardDescription className="text-xs text-slate-400 mt-2 line-clamp-2">
                  {ag.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
                    <Wrench className="w-3 h-3" /> Approved Tools
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {ag.approved_tools?.map((tool) => (
                      <span key={tool} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300 font-mono">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="text-[11px] uppercase tracking-wider font-semibold">{ag.security_level}</span>
                  </div>
                  <span className="text-[11px] font-mono text-cyan-400">{ag.credit_cost_per_call || 1} Credit</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
