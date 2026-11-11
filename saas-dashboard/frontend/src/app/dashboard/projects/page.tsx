"use client"

import { useEffect, useState } from "react"
import { 
  Bot, 
  Plus, 
  RefreshCw, 
  Send, 
  ShieldCheck, 
  AlertCircle, 
  Loader2, 
  Layers, 
  Calendar,
  CheckCircle2,
  ExternalLink,
  Lock
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api, Project } from "@/lib/api"

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Dialog & Form State
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [projectName, setProjectName] = useState("")
  const [botToken, setBotToken] = useState("")
  const [groupId, setGroupId] = useState("")

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

      // Reset form & close dialog
      setProjectName("")
      setBotToken("")
      setGroupId("")
      setIsDialogOpen(false)

      // Refresh list
      await fetchProjects()
    } catch (err: any) {
      setFormError(err.message || "Failed to create project. Please verify inputs.")
    } finally {
      setSubmitting(false)
    }
  }

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return "Just now"
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Bot className="h-7 w-7 text-cyan-400" />
            Project Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure, deploy, and monitor autonomous Telegram community bots.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            disabled={loading}
            className="border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-slate-300 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          {/* Create New Project Modal Dialog */}
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium text-xs shadow-md shadow-cyan-500/20 cursor-pointer">
                <Plus className="h-4 w-4 mr-1.5" />
                Create New Project
              </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-[520px] bg-slate-900 border-slate-800 text-slate-100 shadow-2xl">
              <DialogHeader>
                <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
                  <Bot className="h-5 w-5 text-cyan-400" />
                  Connect New Telegram Bot
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-400">
                  Credentials are encrypted using AES-256 Fernet before storage in Supabase.
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleCreateProject} className="space-y-4 py-2">
                {formError && (
                  <div className="flex items-start gap-2.5 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs">
                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5 text-rose-400" />
                    <span>{formError}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="proj-name" className="text-xs font-semibold text-slate-200">
                    Project Name *
                  </Label>
                  <Input
                    id="proj-name"
                    placeholder="e.g. One Love ($ONELOVE)"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    required
                    className="bg-slate-950/70 border-slate-800 text-slate-100 placeholder:text-slate-600 focus-visible:ring-cyan-500"
                  />
                  <p className="text-[11px] text-slate-500">The public brand or community identity of the bot.</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bot-token" className="text-xs font-semibold text-slate-200 flex items-center justify-between">
                    <span>Telegram Bot Token *</span>
                    <span className="text-[11px] text-cyan-400 font-mono flex items-center gap-1 font-normal">
                      <Lock className="h-3 w-3" /> Encrypted at rest
                    </span>
                  </Label>
                  <Input
                    id="bot-token"
                    type="password"
                    placeholder="e.g. 0000000000:AAFlmO4_kLqU9ZexampleTokenSecret"
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    required
                    className="bg-slate-950/70 border-slate-800 text-slate-100 placeholder:text-slate-600 font-mono text-xs focus-visible:ring-cyan-500"
                  />
                  <p className="text-[11px] text-slate-500">Obtain from @BotFather in Telegram. Never logged in plaintext.</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="group-id" className="text-xs font-semibold text-slate-200">
                    Telegram Group ID (Optional)
                  </Label>
                  <Input
                    id="group-id"
                    placeholder="e.g. -5214407126"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="bg-slate-950/70 border-slate-800 text-slate-100 placeholder:text-slate-600 font-mono text-xs focus-visible:ring-cyan-500"
                  />
                  <p className="text-[11px] text-slate-500">Leave blank to auto-detect from incoming group mentions.</p>
                </div>

                <DialogFooter className="pt-4 border-t border-slate-800">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                    disabled={submitting}
                    className="border-slate-800 bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium text-xs shadow-md shadow-cyan-500/20 cursor-pointer"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                        Encrypting & Saving...
                      </>
                    ) : (
                      <>
                        Save & Connect Bot
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Main Content Area */}
      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-950/30 border border-rose-900/60 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold text-white">Connection Error</h4>
            <p className="text-xs text-rose-300 mt-0.5">{error}</p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={fetchProjects}
            className="border-rose-800 hover:bg-rose-900/50 text-xs"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Projects Table Card */}
      <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-xl shadow-xl overflow-hidden">
        <CardHeader className="border-b border-slate-800/80 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
                <Layers className="h-4 w-4 text-cyan-400" />
                Active Projects & Bot Instances
              </CardTitle>
              <CardDescription className="text-xs text-slate-400 mt-0.5">
                All community bots registered under your enterprise account
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs font-mono bg-slate-950 border-slate-800 text-cyan-400">
              {projects.length} Total
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
              <p className="text-xs font-medium">Querying encrypted project database...</p>
            </div>
          ) : projects.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center text-center px-4">
              <div className="h-14 w-14 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-4 shadow-inner">
                <Bot className="h-7 w-7 text-slate-500" />
              </div>
              <h3 className="text-base font-semibold text-white">No projects found</h3>
              <p className="text-xs text-slate-400 max-w-sm mt-1 mb-6">
                You haven&apos;t connected any Telegram bots to your account yet. Click below to add your first community project.
              </p>
              <Button
                onClick={() => setIsDialogOpen(true)}
                className="bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium text-xs shadow-md shadow-cyan-500/20"
              >
                <Plus className="h-4 w-4 mr-1.5" />
                Add Your First Bot
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-slate-950/60">
                <TableRow className="border-slate-800 hover:bg-transparent">
                  <TableHead className="text-xs font-semibold text-slate-400 pl-6 py-3.5">Project Name</TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400">Status</TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400">Telegram Group ID</TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400">Created At</TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 text-right pr-6">Security</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((proj) => (
                  <TableRow
                    key={proj.id}
                    className="border-slate-800/60 hover:bg-slate-850/40 transition-colors"
                  >
                    <TableCell className="font-medium text-white pl-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 font-bold text-xs">
                          {proj.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-sm text-slate-100">{proj.name}</div>
                          <div className="text-[11px] font-mono text-slate-500">{proj.id}</div>
                        </div>
                      </div>
                    </TableCell>

                    <TableCell>
                      <Badge className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 text-[11px] font-medium flex items-center gap-1.5 w-fit px-2 py-0.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Live / Active
                      </Badge>
                    </TableCell>

                    <TableCell className="text-xs text-slate-300 font-mono">
                      {proj.telegram_group_id ? (
                        <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800/80 text-slate-300">
                          {proj.telegram_group_id}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">Auto-routing</span>
                      )}
                    </TableCell>

                    <TableCell className="text-xs text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-500" />
                        {formatDate(proj.created_at)}
                      </div>
                    </TableCell>

                    <TableCell className="text-right pr-6">
                      <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-cyan-950/30 border border-cyan-900/40 text-cyan-400 text-[11px] font-medium">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        Fernet Encrypted
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
