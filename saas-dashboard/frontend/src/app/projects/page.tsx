"use client"

import { useState } from "react"
import { 
  Bot, 
  Plus, 
  ExternalLink, 
  CheckCircle2, 
  Clock, 
  Key, 
  Layers, 
  Send, 
  Copy, 
  MoreVertical 
} from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"

interface Project {
  id: string
  name: string
  description: string
  botUsername: string
  groupId: string
  tokenAddress?: string
  tokenSymbol?: string
  botStatus: "Active" | "Configured" | "Inactive"
  dateCreated: string
  messagesProcessed: number
}

const initialProjects: Project[] = [
  {
    id: "live_test",
    name: "Hummingbird Ecosystem",
    description: "AI community intelligence agent for Hummingbird on Solana.",
    botUsername: "@ZoeCommunity_bot",
    groupId: "-5214407126 (zoehackx)",
    tokenAddress: "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf",
    tokenSymbol: "$FLY",
    botStatus: "Active",
    dateCreated: "Nov 5, 2026",
    messagesProcessed: 1482,
  },
  {
    id: "example_project",
    name: "DeFi Alpha DAO",
    description: "Automated whitepaper ingestion and governance support agent.",
    botUsername: "@ZoeAlphaBot",
    groupId: "-100192837482",
    botStatus: "Configured",
    dateCreated: "Nov 2, 2026",
    messagesProcessed: 320,
  },
]

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>(initialProjects)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  
  // Form State
  const [name, setName] = useState("")
  const [botToken, setBotToken] = useState("")
  const [groupId, setGroupId] = useState("")
  const [tokenAddress, setTokenAddress] = useState("")
  const [description, setDescription] = useState("")

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    const newProject: Project = {
      id: name.toLowerCase().replace(/\s+/g, "_"),
      name: name.trim(),
      description: description.trim() || "Autonomous Web3 Telegram community agent.",
      botUsername: botToken ? "@ZoeCustom_bot" : "Not Connected",
      groupId: groupId.trim() || "-100999888",
      tokenAddress: tokenAddress.trim() || undefined,
      botStatus: botToken ? "Active" : "Configured",
      dateCreated: "Just now",
      messagesProcessed: 0,
    }

    setProjects([newProject, ...projects])
    setIsDialogOpen(false)
    setName("")
    setBotToken("")
    setGroupId("")
    setTokenAddress("")
    setDescription("")
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header & Modal Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Projects & Community Bots
            <Badge variant="outline" className="text-xs font-mono text-cyan-400 border-cyan-500/40">
              {projects.length} Total
            </Badge>
          </h2>
          <p className="text-sm text-slate-400">
            Configure Telegram credentials, knowledge bases, and on-chain market contracts.
          </p>
        </div>

        {/* Create Project Modal Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-semibold shadow-lg shadow-cyan-500/20">
              <Plus className="h-4 w-4" />
              Create New Project
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[550px] border-slate-800 bg-slate-900 text-slate-100">
            <DialogHeader>
              <DialogTitle className="text-xl flex items-center gap-2 text-white">
                <Bot className="h-5 w-5 text-cyan-400" />
                Deploy New Agent Project
              </DialogTitle>
              <DialogDescription className="text-slate-400 text-sm">
                Enter your project details, Telegram bot credentials, and token contract address.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleCreateProject} className="space-y-4 py-3">
              <div className="space-y-2">
                <Label htmlFor="project-name">Project Name</Label>
                <Input
                  id="project-name"
                  placeholder="e.g. Hummingbird Protocol"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Short Description</Label>
                <Input
                  id="description"
                  placeholder="e.g. Web3 social data intelligence platform"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="bot-token" className="flex items-center gap-1.5">
                    <Key className="h-3.5 w-3.5 text-cyan-400" />
                    Telegram Bot Token
                  </Label>
                  <Input
                    id="bot-token"
                    type="password"
                    placeholder="8634345016:AA..."
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="group-id" className="flex items-center gap-1.5">
                    <Send className="h-3.5 w-3.5 text-cyan-400" />
                    Telegram Group ID
                  </Label>
                  <Input
                    id="group-id"
                    placeholder="-5214407126"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="contract-address">Token Contract Address (Optional / DexScreener)</Label>
                <Input
                  id="contract-address"
                  placeholder="e.g. Solana or EVM contract address"
                  value={tokenAddress}
                  onChange={(e) => setTokenAddress(e.target.value)}
                />
              </div>

              <DialogFooter className="pt-4 border-t border-slate-800 gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold"
                >
                  Save & Launch
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Project Cards Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {projects.map((project) => (
          <Card key={project.id} className="border-slate-800 bg-slate-900/60 hover:border-slate-700/80 transition-all flex flex-col justify-between">
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <CardTitle className="text-xl text-white">{project.name}</CardTitle>
                    <Badge
                      variant={project.botStatus === "Active" ? "success" : "secondary"}
                      className="text-xs"
                    >
                      {project.botStatus}
                    </Badge>
                  </div>
                  <CardDescription className="text-slate-400 text-sm">
                    {project.description}
                  </CardDescription>
                </div>
                <div className="h-10 w-10 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-cyan-400 flex-shrink-0">
                  <Bot className="h-5 w-5" />
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs font-mono">
                <div className="flex justify-between items-center text-slate-400">
                  <span>Bot Handle:</span>
                  <span className="text-cyan-400 font-semibold">{project.botUsername}</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Chat ID:</span>
                  <span className="text-slate-300">{project.groupId}</span>
                </div>
                {project.tokenAddress && (
                  <div className="flex justify-between items-center text-slate-400 pt-1 border-t border-slate-800/50">
                    <span>Contract Address:</span>
                    <span className="text-slate-300 truncate max-w-[180px]">{project.tokenAddress}</span>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-slate-500" />
                  <span>Created {project.dateCreated}</span>
                </div>
                <div className="font-mono text-cyan-400 font-medium">
                  {project.messagesProcessed.toLocaleString()} msgs processed
                </div>
              </div>
            </CardContent>

            <Separator className="bg-slate-800/80" />

            <CardFooter className="pt-4 flex items-center justify-between">
              <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-slate-200">
                View Knowledge Chunks
              </Button>
              <Button variant="secondary" size="sm" className="text-xs gap-1.5">
                Configure Bot
                <ExternalLink className="h-3 w-3 text-slate-500" />
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
