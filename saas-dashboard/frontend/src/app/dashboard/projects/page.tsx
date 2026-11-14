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
  Copy,
  Check,
  BrainCircuit,
  Eye,
  EyeOff,
  Edit2,
  StopCircle,
  CheckCircle2
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

// Regex for client-side instant validation
const BOT_TOKEN_REGEX = /^\d{8,12}:[A-Za-z0-9_-]{32,}$/
const TOKEN_ADDR_REGEX = /^(0x[a-fA-F0-9]{40}|[A-Za-z0-9]{32,64})$/

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successToast, setSuccessToast] = useState<string | null>(null)
  const [copiedCA, setCopiedCA] = useState<string | null>(null)

  // Add Project Dialog & Form State
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [projectName, setProjectName] = useState("")
  const [botToken, setBotToken] = useState("")
  const [showToken, setShowToken] = useState(false)
  const [groupId, setGroupId] = useState("")
  const [tokenAddress, setTokenAddress] = useState("")
  const [tokenSymbol, setTokenSymbol] = useState("")

  // Edit Group ID Dialog State
  const [editProject, setEditProject] = useState<Project | null>(null)
  const [editGroupId, setEditGroupId] = useState("")
  const [savingEdit, setSavingEdit] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)

  // Stopping Bot State
  const [stoppingId, setStoppingId] = useState<string | null>(null)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCA(text)
    setTimeout(() => setCopiedCA(null), 2000)
  }

  const showToast = (msg: string) => {
    setSuccessToast(msg)
    setTimeout(() => setSuccessToast(null), 4000)
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

  // Validation calculations
  const isNameValid = projectName.trim().length >= 2
  const isTokenValid = BOT_TOKEN_REGEX.test(botToken.trim())
  const isAddressValid = TOKEN_ADDR_REGEX.test(tokenAddress.trim())
  const isFormValid = isNameValid && isTokenValid && isAddressValid

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!isNameValid) {
      setFormError("Project name must be at least 2 characters.")
      return
    }
    if (!isTokenValid) {
      setFormError("Invalid Telegram Bot Token format. Example: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
      return
    }
    if (!isAddressValid) {
      setFormError("Invalid Token Address. Must be a valid Solana (base58) or EVM (0x...) address.")
      return
    }

    setSubmitting(true)
    try {
      const created = await api.createProject({
        name: projectName.trim(),
        telegram_bot_token: botToken.trim(),
        telegram_group_id: groupId.trim() || undefined,
        token_address: tokenAddress.trim(),
        token_symbol: tokenSymbol.trim() || undefined,
      })

      setProjectName("")
      setBotToken("")
      setGroupId("")
      setTokenAddress("")
      setTokenSymbol("")
      setIsDialogOpen(false)

      showToast(`Project '${created.name}' successfully deployed to Zoe Engine!`)
      await fetchProjects()
    } catch (err: any) {
      setFormError(err.message || "Failed to deploy project to Zoe Engine.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleSaveGroupId = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editProject) return
    setSavingEdit(true)
    setEditError(null)

    try {
      await api.patchProject(editProject.id, {
        telegram_group_id: editGroupId.trim(),
      })
      showToast(`Group ID updated for '${editProject.name}'.`)
      setEditProject(null)
      await fetchProjects()
    } catch (err: any) {
      setEditError(err.message || "Failed to update Group ID.")
    } finally {
      setSavingEdit(false)
    }
  }

  const handleStopBot = async (proj: Project) => {
    if (!confirm(`Are you sure you want to stop bot '${proj.name}'?`)) return
    setStoppingId(proj.id)
    try {
      await api.deleteProject(proj.id)
      showToast(`Bot '${proj.name}' stopped.`)
      await fetchProjects()
    } catch (err: any) {
      setError(err.message || `Failed to stop bot '${proj.name}'.`)
    } finally {
      setStoppingId(null)
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
      status: "Live",
      group: "-5214407126",
    },
    {
      id: "live_test",
      name: "Zoe Core Hummingbird",
      botUsername: "@zoe_live_test_bot",
      tokenSymbol: "$FLY",
      chain: "Multi-Chain",
      ca: "0x1b44f3514812d835eb1bdb0acb33d3ff3351655c",
      status: "Live",
      group: "Verified Testnet",
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

  const renderStatusBadge = (status?: string | null, errorMsg?: string | null) => {
    const s = (status || "live").toLowerCase()
    if (s === "live" || s === "running") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Live
        </span>
      )
    }
    if (s === "deploying" || s === "starting") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
          <Loader2 className="h-3 w-3 animate-spin text-amber-500" />
          Deploying
        </span>
      )
    }
    if (s === "stopped") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          Stopped
        </span>
      )
    }
    return (
      <span 
        title={errorMsg || "Bot failed to initialize"}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200 cursor-help"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
        Failed
      </span>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Success Toast Banner */}
      {successToast && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{successToast}</span>
          </div>
          <button 
            onClick={() => setSuccessToast(null)} 
            className="text-emerald-600 hover:text-emerald-900 text-xs font-semibold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Active Projects
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Deploy, monitor, and hot-reload autonomous Telegram bots connected to the Zoe Engine.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            disabled={loading}
            className="border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs h-9 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          {/* Add Project Modal */}
          <Dialog 
            open={isDialogOpen} 
            onOpenChange={(open) => {
              // Prevent modal dismissal mid-request
              if (!submitting) {
                setIsDialogOpen(open)
                if (!open) setFormError(null)
              }
            }}
          >
            <DialogTrigger asChild>
              <Button className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-9 px-4 rounded-md font-medium cursor-pointer">
                <Plus className="h-3.5 w-3.5 mr-1.5" />
                Add Project
              </Button>
            </DialogTrigger>
            <DialogContent 
              aria-busy={submitting}
              className="sm:max-w-[500px] bg-white border border-slate-200 text-slate-900 shadow-xl rounded-lg"
            >
              <DialogHeader>
                <DialogTitle className="text-lg font-semibold text-slate-900">
                  Deploy New Bot to Zoe Engine
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-500">
                  Register your Telegram credentials and token contract. The bot poller starts automatically.
                </DialogDescription>
              </DialogHeader>

              {formError && (
                <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <form onSubmit={handleCreateProject} className="space-y-3.5 pt-2">
                {/* Project Name */}
                <div className="space-y-1">
                  <Label htmlFor="projectName" className="text-xs font-medium text-slate-700 flex items-center justify-between">
                    <span>Project Name <span className="text-rose-500">*</span></span>
                    {projectName && !isNameValid && (
                      <span className="text-[11px] text-rose-500 font-normal">Min 2 characters</span>
                    )}
                  </Label>
                  <Input
                    id="projectName"
                    disabled={submitting}
                    placeholder="e.g. Nexus Community AI"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    required
                    className="bg-white border-slate-200 text-slate-900 text-xs h-9 focus:ring-1 focus:ring-slate-400"
                  />
                </div>

                {/* Bot Token with Show/Hide Toggle */}
                <div className="space-y-1">
                  <Label htmlFor="botToken" className="text-xs font-medium text-slate-700 flex items-center justify-between">
                    <span>Telegram Bot Token <span className="text-rose-500">*</span></span>
                    {botToken && !isTokenValid && (
                      <span className="text-[11px] text-rose-500 font-normal">Format: 123456789:ABC...</span>
                    )}
                  </Label>
                  <div className="relative">
                    <Input
                      id="botToken"
                      disabled={submitting}
                      type={showToken ? "text" : "password"}
                      placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                      value={botToken}
                      onChange={(e) => setBotToken(e.target.value)}
                      required
                      className="bg-white border-slate-200 text-slate-900 font-mono text-xs h-9 pr-9 focus:ring-1 focus:ring-slate-400"
                    />
                    <button
                      type="button"
                      disabled={submitting}
                      onClick={() => setShowToken(!showToken)}
                      className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                      title={showToken ? "Hide token" : "Show token"}
                    >
                      {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Token Contract Address */}
                <div className="space-y-1">
                  <Label htmlFor="tokenAddress" className="text-xs font-medium text-slate-700 flex items-center justify-between">
                    <span>Token Contract Address <span className="text-rose-500">*</span></span>
                    {tokenAddress && !isAddressValid && (
                      <span className="text-[11px] text-rose-500 font-normal">Valid Solana or EVM address</span>
                    )}
                  </Label>
                  <Input
                    id="tokenAddress"
                    disabled={submitting}
                    placeholder="e.g. 0x... or Solana base58 address"
                    value={tokenAddress}
                    onChange={(e) => setTokenAddress(e.target.value)}
                    required
                    className="bg-white border-slate-200 text-slate-900 font-mono text-xs h-9 focus:ring-1 focus:ring-slate-400"
                  />
                </div>

                {/* Group ID (Optional) */}
                <div className="space-y-1">
                  <Label htmlFor="groupId" className="text-xs font-medium text-slate-700">
                    Group ID (Optional)
                  </Label>
                  <Input
                    id="groupId"
                    disabled={submitting}
                    placeholder="e.g. -1001234567890"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="bg-white border-slate-200 text-slate-900 font-mono text-xs h-9 focus:ring-1 focus:ring-slate-400"
                  />
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Leave blank to deploy to DMs or assign a group later.
                  </p>
                </div>

                <DialogFooter className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={submitting}
                    onClick={() => setIsDialogOpen(false)}
                    className="border-slate-200 text-slate-700 text-xs h-9"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting || !isFormValid}
                    className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-9 px-4 font-medium disabled:opacity-50 cursor-pointer"
                  >
                    {submitting && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                    {submitting ? "Deploying..." : "Deploy Bot"}
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
          Dynamic Registered Projects
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
                <TableHead className="text-xs font-semibold text-slate-600">Status</TableHead>
                <TableHead className="text-xs font-semibold text-slate-600">Registered</TableHead>
                <TableHead className="text-xs font-semibold text-slate-600 text-right pr-6">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-slate-400">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-slate-400 mb-2" />
                    <span className="text-xs">Loading projects from Zoe Engine...</span>
                  </TableCell>
                </TableRow>
              ) : projects.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-slate-400">
                    <p className="text-sm font-medium text-slate-600">No dynamic projects deployed yet</p>
                    <p className="text-xs text-slate-400 mt-1">Click "Add Project" above to deploy an autonomous bot to the Engine.</p>
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
                      {proj.token_address && (
                        <span className="text-[10px] font-mono text-slate-400 block mt-0.5 truncate max-w-[200px]">
                          {proj.token_address}
                        </span>
                      )}
                    </TableCell>

                    <TableCell className="text-xs text-slate-600 font-mono">
                      {proj.telegram_group_id ? (
                        <span className="inline-flex items-center gap-1 font-medium text-slate-800">
                          {proj.telegram_group_id}
                        </span>
                      ) : (
                        <span className="text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded text-[10px] border border-amber-200">
                          Unlocked (DMs)
                        </span>
                      )}
                    </TableCell>

                    <TableCell>
                      {renderStatusBadge(proj.status, proj.status_error)}
                    </TableCell>

                    <TableCell className="text-xs text-slate-500">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        {formatDate(proj.created_at)}
                      </div>
                    </TableCell>

                    <TableCell className="text-right pr-6">
                      <div className="flex items-center justify-end gap-2">
                        {/* Edit Group ID Button */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditProject(proj)
                            setEditGroupId(proj.telegram_group_id || "")
                            setEditError(null)
                          }}
                          className="h-7 px-2 text-[11px] text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer"
                          title="Edit Group ID"
                        >
                          <Edit2 className="h-3.5 w-3.5 mr-1" />
                          Edit Group
                        </Button>

                        {/* Stop Bot Button */}
                        {proj.status !== "stopped" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={stoppingId === proj.id}
                            onClick={() => handleStopBot(proj)}
                            className="h-7 px-2 text-[11px] text-rose-600 hover:text-rose-700 hover:bg-rose-50 cursor-pointer"
                            title="Stop bot worker"
                          >
                            {stoppingId === proj.id ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <StopCircle className="h-3.5 w-3.5 mr-1" />
                            )}
                            Stop
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </div>

      {/* Edit Group ID Modal */}
      <Dialog 
        open={Boolean(editProject)} 
        onOpenChange={(open) => {
          if (!open && !savingEdit) setEditProject(null)
        }}
      >
        <DialogContent className="sm:max-w-[420px] bg-white border border-slate-200 text-slate-900 shadow-xl rounded-lg">
          <DialogHeader>
            <DialogTitle className="text-base font-semibold text-slate-900">
              Update Telegram Group ID
            </DialogTitle>
            <DialogDescription className="text-xs text-slate-500">
              Lock or re-route <strong>{editProject?.name}</strong> to a specific Telegram group chat.
            </DialogDescription>
          </DialogHeader>

          {editError && (
            <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{editError}</span>
            </div>
          )}

          <form onSubmit={handleSaveGroupId} className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <Label htmlFor="editGroupId" className="text-xs font-medium text-slate-700">
                Telegram Group ID
              </Label>
              <Input
                id="editGroupId"
                disabled={savingEdit}
                placeholder="e.g. -1001234567890 (or leave empty for DMs)"
                value={editGroupId}
                onChange={(e) => setEditGroupId(e.target.value)}
                className="bg-white border-slate-200 text-slate-900 font-mono text-xs h-9 focus:ring-1 focus:ring-slate-400"
              />
              <p className="text-[11px] text-slate-400">
                The bot will immediately hot-reload and bind to this group.
              </p>
            </div>

            <DialogFooter className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={savingEdit}
                onClick={() => setEditProject(null)}
                className="border-slate-200 text-slate-700 text-xs h-9"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={savingEdit}
                className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-9 px-4 font-medium"
              >
                {savingEdit && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                {savingEdit ? "Updating..." : "Save Group ID"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
