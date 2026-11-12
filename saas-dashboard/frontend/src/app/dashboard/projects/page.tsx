"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  Bot, 
  Plus, 
  RefreshCw, 
  ShieldCheck, 
  AlertCircle, 
  Loader2, 
  Calendar,
  ExternalLink,
  Copy,
  Check,
  BrainCircuit,
  ArrowRight
} from "lucide-react"
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api, Project } from "@/lib/api"

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  // Dialog & Form State
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [projectName, setProjectName] = useState("")
  const [botToken, setBotToken] = useState("")
  const [groupId, setGroupId] = useState("")

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCA(text)
    setTimeout(() => setCopiedCA(null), 2000)
  }

  const fetchProjects = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getProjects()
      setProjects(data)
    } catch (err: any) {
      setError(err.message || "Failed to load projects from backend.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!projectName.trim()) {
      setFormError("Project name is required.")
      return
    }
    if (!botToken.trim()) {
      setFormError("Telegram bot token is required.")
      return
    }

    setSubmitting(true)
    try {
      await api.createProject({
        name: projectName.trim(),
        telegram_bot_token: botToken.trim(),
        telegram_group_id: groupId.trim() || undefined,
      })

      setProjectName("")
      setBotToken("")
      setGroupId("")
      setIsDialogOpen(false)

      await fetchProjects()
    } catch (err: any) {
      setFormError(err.message || "Failed to register project.")
    } finally {
      setSubmitting(false)
    }
  }

  const coreFleets = [
    {
      id: "onelove",
      name: "One Love AI",
      botUsername: "@OneLoveManager_bot",
      tokenSymbol: "$ONELOVE",
      chain: "Solana",
      ca: "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon",
      status: "Online",
      chunks: 5,
      group: "-5214407126",
      socials: {
        twitter: "https://x.com/thecaptrobbie?s=11",
        telegram: "https://t.me/ONELOVECoinCrew",
        tiktok: "https://www.tiktok.com/@captain.robbie"
      }
    },
    {
      id: "live_test",
      name: "Zoe Core Hummingbird",
      botUsername: "@zoe_live_test_bot",
      tokenSymbol: "$FLY",
      chain: "Multi-Chain",
      ca: "0x1b44f3514812d835eb1bdb0acb33d3ff3351655c",
      status: "Online",
      chunks: 2,
      group: "Verified Testnet",
      socials: {}
    }
  ]

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "Recently"
    try {
      return new Date(dateString).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric"
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Active Projects
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your AI agents, Telegram group bindings, and secure credentials.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            disabled={loading}
            className="border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs h-9"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-9 px-4 rounded-md font-medium cursor-pointer">
                <Plus className="h-3.5 w-3.5 mr-1.5" />
                Add Project
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[480px] bg-white border border-slate-200 text-slate-900 shadow-xl rounded-lg">
              <DialogHeader>
                <DialogTitle className="text-lg font-semibold text-slate-900">
                  Register New Project
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-500">
                  Connect a Telegram bot token. The secret is securely encrypted using AES-256 before storage.
                </DialogDescription>
              </DialogHeader>

              {formError && (
                <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <form onSubmit={handleCreateProject} className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <Label htmlFor="projectName" className="text-xs font-medium text-slate-700">
                    Project Name
                  </Label>
                  <Input
                    id="projectName"
                    placeholder="e.g. Acme Community AI"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    required
                    className="bg-white border-slate-200 text-slate-900 text-xs h-9 focus:ring-1 focus:ring-slate-400"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="botToken" className="text-xs font-medium text-slate-700">
                    Telegram Bot Token
                  </Label>
                  <Input
                    id="botToken"
                    type="password"
                    placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    required
                    className="bg-white border-slate-200 text-slate-900 font-mono text-xs h-9 focus:ring-1 focus:ring-slate-400"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="groupId" className="text-xs font-medium text-slate-700">
                    Telegram Group ID (Optional)
                  </Label>
                  <Input
                    id="groupId"
                    placeholder="e.g. -1001234567890"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="bg-white border-slate-200 text-slate-900 font-mono text-xs h-9 focus:ring-1 focus:ring-slate-400"
                  />
                </div>

                <DialogFooter className="pt-4 border-t border-slate-100">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                    className="border-slate-200 text-slate-700 text-xs h-9"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-9 px-4 font-medium"
                  >
                    {submitting && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                    Save Project
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Core Projects Cards */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-slate-900">
          Core Deployed Bots
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {coreFleets.map((fleet) => (
            <Card key={fleet.id} className="enterprise-card border border-slate-200 shadow-sm bg-white p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-900 text-sm">{fleet.name}</h3>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      {fleet.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{fleet.botUsername}</p>
                </div>
                <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                  {fleet.tokenSymbol} · {fleet.chain}
                </span>
              </div>

              {/* Contract Address Box */}
              <div className="mt-4 p-2.5 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-between gap-2">
                <div className="truncate text-xs font-mono text-slate-600">
                  {fleet.ca}
                </div>
                <button
                  onClick={() => copyToClipboard(fleet.ca)}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors cursor-pointer"
                  title="Copy address"
                >
                  {copiedCA === fleet.ca ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                  <span className="text-[11px] font-medium">{copiedCA === fleet.ca ? "Copied" : "Copy"}</span>
                </button>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>Group ID: <strong className="font-mono text-slate-700 font-medium">{fleet.group}</strong></span>
                <Link
                  href={`/projects/${fleet.id}`}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-white text-[11px] font-medium transition-colors cursor-pointer"
                >
                  <BrainCircuit className="h-3 w-3" />
                  Train & Scrape
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Database Registered Tenants */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-slate-900">
          Custom Registered Projects
        </h2>

        {error && (
          <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <Card className="enterprise-card border border-slate-200 shadow-sm bg-white overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow className="border-b border-slate-200">
                <TableHead className="text-xs font-semibold text-slate-600 pl-6">Project Name</TableHead>
                <TableHead className="text-xs font-semibold text-slate-600">Telegram Group ID</TableHead>
                <TableHead className="text-xs font-semibold text-slate-600">Registered</TableHead>
                <TableHead className="text-xs font-semibold text-slate-600 text-right pr-6">Security</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-32 text-center text-slate-400">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-slate-400 mb-2" />
                    <span className="text-xs">Loading projects...</span>
                  </TableCell>
                </TableRow>
              ) : projects.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-32 text-center text-slate-400">
                    <p className="text-sm font-medium text-slate-600">No custom projects yet</p>
                    <p className="text-xs text-slate-400 mt-1">Click "Add Project" above to register an additional Telegram bot.</p>
                  </TableCell>
                </TableRow>
              ) : (
                projects.map((proj) => (
                  <TableRow key={proj.id} className="border-b border-slate-100 hover:bg-slate-50/70 transition-colors">
                    <TableCell className="font-medium text-slate-900 pl-6 text-sm">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 text-slate-400" />
                        <span>{proj.name}</span>
                      </div>
                    </TableCell>

                    <TableCell className="text-xs text-slate-600 font-mono">
                      {proj.telegram_group_id || (
                        <span className="text-slate-400 italic font-sans text-xs">Auto-routing</span>
                      )}
                    </TableCell>

                    <TableCell className="text-xs text-slate-500">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        {formatDate(proj.created_at)}
                      </div>
                    </TableCell>

                    <TableCell className="text-right pr-6">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                        AES-256
                      </span>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </div>
    </div>
  )
}
