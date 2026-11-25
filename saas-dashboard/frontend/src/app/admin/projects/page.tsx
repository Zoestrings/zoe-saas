"use client"

import * as React from "react"
import { useState, useEffect, useMemo } from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import {
  Bot,
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Edit,
  Trash2,
  Calendar,
  ArrowUpDown,
  AlertCircle,
  Loader2,
  Copy,
  Check,
  Sparkles,
  ShieldAlert,
  PlayCircle,
  PauseCircle,
  Mail,
  Crown,
  Send,
  MessageSquare,
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { api, AdminProjectItem } from "@/lib/api"

export default function AdminProjectsPage() {
  const [data, setData] = useState<AdminProjectItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState<string>("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  // Modal states for Deploy Bot
  const [isDeployOpen, setIsDeployOpen] = useState(false)
  const [deploySubmitting, setDeploySubmitting] = useState(false)
  const [deployError, setDeployError] = useState<string | null>(null)

  // Form fields for Deploy Bot
  const [platform, setPlatform] = useState<"telegram" | "discord" | "twitter">("telegram")
  const [name, setName] = useState("")
  const [botToken, setBotToken] = useState("")
  const [discordToken, setDiscordToken] = useState("")
  const [twitterApiKey, setTwitterApiKey] = useState("")
  const [twitterApiSecret, setTwitterApiSecret] = useState("")
  const [twitterAccessToken, setTwitterAccessToken] = useState("")
  const [twitterAccessSecret, setTwitterAccessSecret] = useState("")
  const [apiKey, setApiKey] = useState("")
  const [tokenAddress, setTokenAddress] = useState("")
  const [groupId, setGroupId] = useState("")
  const [customInstructions, setCustomInstructions] = useState("")

  // Suspend Confirmation Modal state
  const [suspendProjectTarget, setSuspendProjectTarget] = useState<AdminProjectItem | null>(null)
  const [suspendLoading, setSuspendLoading] = useState(false)
  const [suspendError, setSuspendError] = useState<string | null>(null)

  // Assign Owner Modal state
  const [assignProjectTarget, setAssignProjectTarget] = useState<AdminProjectItem | null>(null)
  const [assignEmail, setAssignEmail] = useState("")
  const [assignLoading, setAssignLoading] = useState(false)
  const [assignError, setAssignError] = useState<string | null>(null)

  // Action status message
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null)

  // Agent Registry Tab state (Pillar 3)
  const [activeTab, setActiveTab] = useState<"projects" | "registry">("projects")
  const [personas, setPersonas] = useState<{
    id: string
    name: string
    description: string
    system_prompt: string
  }[]>([])
  const [personasLoading, setPersonasLoading] = useState(false)

  useEffect(() => {
    setPersonasLoading(true)
    api
      .getAgentPersonas()
      .then((list) => setPersonas(Array.isArray(list) ? list : []))
      .catch(() => {})
      .finally(() => setPersonasLoading(false))
  }, [])

  const handleAssignOwner = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!assignProjectTarget || !assignEmail.trim()) return
    setAssignLoading(true)
    setAssignError(null)
    try {
      const res = await api.assignProjectOwner(assignProjectTarget.id, assignEmail.trim())
      setActionSuccessMessage(res.message || `Project successfully assigned to ${assignEmail.trim()}`)
      setAssignProjectTarget(null)
      setAssignEmail("")
      await fetchProjects()
      setTimeout(() => setActionSuccessMessage(null), 5000)
    } catch (err: any) {
      setAssignError(err.message || "Failed to assign project owner")
    } finally {
      setAssignLoading(false)
    }
  }

  // Copied token state
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Fetch Projects from Master Admin Endpoint
  const fetchProjects = async () => {
    setLoading(true)
    try {
      const projects = await api.getAdminAllProjects()
      setData(projects || [])
    } catch (err: any) {
      console.warn("Falling back to standard getProjects:", err)
      try {
        const fallback = await api.getProjects()
        setData((fallback || []).map((p) => ({
          ...p,
          status: p.status || "active",
          created_at: p.created_at || new Date().toISOString(),
          owner_email: "current_user",
          plan: "free",
        })))
      } catch (e) {
        console.error("Failed to load projects:", e)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  // Handle Deploy New Bot
  const handleDeploy = async (e: React.FormEvent) => {
    e.preventDefault()
    setDeploySubmitting(true)
    setDeployError(null)

    try {
      await api.createProject({
        name: name.trim(),
        platform,
        telegram_bot_token: platform === "telegram" ? botToken.trim() : undefined,
        discord_token: platform === "discord" ? discordToken.trim() : undefined,
        twitter_api_key: platform === "twitter" ? twitterApiKey.trim() : undefined,
        twitter_api_secret: platform === "twitter" ? twitterApiSecret.trim() : undefined,
        twitter_access_token: platform === "twitter" ? twitterAccessToken.trim() : undefined,
        twitter_access_secret: platform === "twitter" ? twitterAccessSecret.trim() : undefined,
        api_key: apiKey.trim() || undefined,
        token_address: tokenAddress.trim() || undefined,
        telegram_group_id: groupId.trim() || undefined,
        custom_instructions: customInstructions.trim() || undefined,
      })

      // Reset form
      setName("")
      setBotToken("")
      setDiscordToken("")
      setTwitterApiKey("")
      setTwitterApiSecret("")
      setTwitterAccessToken("")
      setTwitterAccessSecret("")
      setApiKey("")
      setTokenAddress("")
      setGroupId("")
      setCustomInstructions("")
      setIsDeployOpen(false)
      fetchProjects()
    } catch (err: any) {
      setDeployError(err.message || "Failed to deploy bot.")
    } finally {
      setDeploySubmitting(false)
    }
  }

  // Handle Suspend Project
  const handleConfirmSuspend = async () => {
    if (!suspendProjectTarget) return
    setSuspendLoading(true)
    setSuspendError(null)

    try {
      await api.suspendProject(suspendProjectTarget.id)
      setActionSuccessMessage(`Project "${suspendProjectTarget.name}" suspended successfully.`)
      setTimeout(() => setActionSuccessMessage(null), 4000)
      setSuspendProjectTarget(null)
      fetchProjects()
    } catch (err: any) {
      setSuspendError(err.message || "Failed to suspend project.")
    } finally {
      setSuspendLoading(false)
    }
  }

  // Handle Reactivate Project
  const handleActivate = async (proj: AdminProjectItem) => {
    try {
      await api.activateProject(proj.id)
      setActionSuccessMessage(`Project "${proj.name}" reactivated successfully.`)
      setTimeout(() => setActionSuccessMessage(null), 4000)
      fetchProjects()
    } catch (err: any) {
      alert(err.message || "Failed to reactivate project.")
    }
  }

  // Handle Delete Project
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this project? This will permanently remove its database record.")) {
      return
    }
    try {
      await api.deleteProject(id)
      fetchProjects()
    } catch (err: any) {
      alert(err.message || "Failed to delete project.")
    }
  }

  // Filtered dataset by status
  const filteredData = useMemo(() => {
    if (statusFilter === "all") return data
    if (statusFilter === "online") return data.filter((p) => p.status === "active" || p.status === "online" || !p.status)
    if (statusFilter === "suspended") return data.filter((p) => p.status === "suspended")
    return data
  }, [data, statusFilter])

  // Table Column Definitions
  const columns = useMemo<ColumnDef<AdminProjectItem>[]>(
    () => [
      {
        accessorKey: "name",
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="flex items-center gap-1.5 text-xs font-semibold text-white hover:text-[#00ff66] transition-colors cursor-pointer"
          >
            Project Name
            <ArrowUpDown className="h-3.5 w-3.5 text-[#818c99]" />
          </button>
        ),
        cell: ({ row }) => {
          const proj = row.original
          return (
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/20 flex items-center justify-center text-[#00ff66] shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className="font-bold text-white text-xs truncate">{proj.name}</div>
                {proj.token_address ? (
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="font-mono text-[11px] text-[#818c99] truncate max-w-[150px]">
                      {proj.token_address}
                    </span>
                    <button
                      onClick={() => copyToClipboard(proj.token_address!, proj.id)}
                      className="text-[#818c99] hover:text-[#00ff66] transition-colors cursor-pointer"
                      title="Copy Token Address"
                    >
                      {copiedId === proj.id ? (
                        <Check className="h-2.5 w-2.5 text-[#00ff66]" />
                      ) : (
                        <Copy className="h-2.5 w-2.5" />
                      )}
                    </button>
                  </div>
                ) : (
                  <span className="text-[11px] text-[#818c99]">ID: {proj.id.slice(0, 8)}...</span>
                )}
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: "owner_email",
        header: "Owner Email",
        cell: ({ row }) => {
          const email = row.original.owner_email || "Unknown"
          return (
            <div className="flex items-center gap-2 text-xs text-neutral-300">
              <Mail className="h-3.5 w-3.5 text-[#818c99]" />
              <span className="font-medium truncate max-w-[200px]">{email}</span>
            </div>
          )
        },
      },
      {
        accessorKey: "plan",
        header: "Plan",
        cell: ({ row }) => {
          const plan = (row.original.plan || "free").toLowerCase()
          const isPro = plan === "pro"
          return (
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${isPro
                ? "bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 shadow-sm shadow-[#00ff66]/10"
                : "bg-neutral-800 text-neutral-400 border border-neutral-700"
              }`}>
              {isPro && <Crown className="h-3 w-3 text-[#00ff66]" />}
              {isPro ? "PRO" : "FREE"}
            </span>
          )
        },
      },
      {
        accessorKey: "platform",
        header: "Platform",
        cell: ({ row }) => {
          const plat = (row.original.platform || "telegram").toLowerCase()
          if (plat === "discord") {
            return (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#5865F2]/10 text-[#5865F2] border border-[#5865F2]/30">
                <MessageSquare className="h-3 w-3" />
                Discord
              </span>
            )
          }
          if (plat === "twitter" || plat === "x") {
            return (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/30">
                <span className="font-bold">𝕏</span>
                Twitter
              </span>
            )
          }
          return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#2AABEE]/10 text-[#2AABEE] border border-[#2AABEE]/30">
              <Send className="h-3 w-3" />
              Telegram
            </span>
          )
        },
      },
      {
        accessorKey: "status",
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="flex items-center gap-1.5 text-xs font-semibold text-white hover:text-[#00ff66] transition-colors cursor-pointer"
          >
            Bot Status
            <ArrowUpDown className="h-3.5 w-3.5 text-[#818c99]" />
          </button>
        ),
        cell: ({ row }) => {
          const status = (row.original.status || "active").toLowerCase()
          const isSuspended = status === "suspended"
          const isOnline = status === "active" || status === "online"

          if (isSuspended) {
            return (
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/30 px-3 py-1 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                Suspended
              </span>
            )
          }
          if (isOnline) {
            return (
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#00ff66] bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66] animate-pulse" />
                Online
              </span>
            )
          }
          return (
            <span className="inline-flex items-center gap-1.5 text-xs font-bold text-neutral-400 bg-neutral-800 border border-neutral-700 px-3 py-1 rounded-full">
              <span className="h-1.5 w-1.5 rounded-full bg-neutral-400" />
              {status}
            </span>
          )
        },
      },
      {
        accessorKey: "created_at",
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="flex items-center gap-1.5 text-xs font-semibold text-white hover:text-[#00ff66] transition-colors cursor-pointer"
          >
            Created Date
            <ArrowUpDown className="h-3.5 w-3.5 text-[#818c99]" />
          </button>
        ),
        cell: ({ row }) => {
          const raw = row.original.created_at
          let dateStr = "Recently"
          if (raw) {
            try {
              dateStr = new Date(raw).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })
            } catch { }
          }
          return (
            <div className="flex items-center gap-1.5 text-xs text-[#818c99]">
              <Calendar className="h-3.5 w-3.5 text-[#818c99]" />
              <span>{dateStr}</span>
            </div>
          )
        },
      },
      {
        id: "actions",
        header: () => <div className="text-right">Actions</div>,
        cell: ({ row }) => {
          const proj = row.original
          const isSuspended = proj.status === "suspended"

          return (
            <div className="flex items-center justify-end gap-2">
              {isSuspended ? (
                <Button
                  size="sm"
                  onClick={() => handleActivate(proj)}
                  className="h-8 px-3 rounded-xl bg-[#00ff66]/10 hover:bg-[#00ff66]/20 text-[#00ff66] border border-[#00ff66]/40 text-xs font-bold cursor-pointer"
                >
                  <PlayCircle className="h-3.5 w-3.5 mr-1" />
                  Reactivate
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => setSuspendProjectTarget(proj)}
                  className="h-8 px-3 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold cursor-pointer"
                >
                  <PauseCircle className="h-3.5 w-3.5 mr-1" />
                  Suspend
                </Button>
              )}

              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setAssignProjectTarget(proj)
                  setAssignEmail(proj.owner_email && proj.owner_email !== "Unknown" && proj.owner_email !== "current_user" ? proj.owner_email : "")
                  setAssignError(null)
                }}
                className="h-8 px-2.5 rounded-xl border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-xs font-bold cursor-pointer"
              >
                <Crown className="h-3.5 w-3.5 mr-1" />
                Assign
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="h-8 w-8 p-0 text-[#818c99] hover:text-white hover:bg-[#181d24] rounded-full cursor-pointer"
                  >
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-[#12161c] border border-[#212833] text-white shadow-2xl rounded-2xl p-1.5">
                  <DropdownMenuLabel className="text-[10px] font-bold uppercase tracking-wider text-[#818c99] px-2.5 py-1.5">
                    Tenant Control
                  </DropdownMenuLabel>
                  <DropdownMenuItem
                    onClick={() => {
                      setAssignProjectTarget(proj)
                      setAssignEmail(proj.owner_email && proj.owner_email !== "Unknown" && proj.owner_email !== "current_user" ? proj.owner_email : "")
                      setAssignError(null)
                    }}
                    className="cursor-pointer gap-2 text-cyan-400 hover:bg-cyan-950/30 hover:text-cyan-300 text-xs py-2 rounded-xl font-semibold"
                  >
                    <Crown className="h-3.5 w-3.5" />
                    <span>Assign Owner</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleDelete(proj.id)}
                    className="cursor-pointer gap-2 text-rose-400 hover:bg-rose-950/30 hover:text-rose-300 text-xs py-2 rounded-xl font-semibold"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Delete Bot</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )
        },
      },
    ],
    [copiedId]
  )

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  })

  return (
    <div className="space-y-6 pb-12">
      {/* Header and Add Project Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#212833]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Bot className="h-6 w-6 text-[#00ff66]" />
            All Tenant Projects
          </h1>
          <p className="text-xs text-[#818c99] mt-1">
            Super Admin master directory: manage tenant bots, subscription tiers, and enforce suspension.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            disabled={loading}
            className="border-[#212833] bg-[#12161c] hover:bg-[#181d24] text-white text-xs h-10 px-4 rounded-full cursor-pointer shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin text-[#00ff66]" : ""}`} />
            Refresh
          </Button>

          {/* Deploy New Bot Modal */}
          <Dialog open={isDeployOpen} onOpenChange={setIsDeployOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-5 rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer transition-all">
                <Plus className="h-4 w-4 mr-1.5 stroke-[3]" />
                Add Project
              </Button>
            </DialogTrigger>
            <DialogContent className="w-[92vw] sm:max-w-[500px] max-h-[85vh] overflow-y-auto bg-[#12161c] border border-[#212833] text-white shadow-2xl rounded-3xl p-5 sm:p-6">
              <DialogHeader>
                <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
                  <Bot className="h-5 w-5 text-[#00ff66]" />
                  Deploy New Bot to Zoe Engine
                </DialogTitle>
                <DialogDescription className="text-xs text-[#818c99]">
                  Register a new Telegram bot token and connect it directly to the runtime engine.
                </DialogDescription>
              </DialogHeader>

              {deployError && (
                <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                  <span>{deployError}</span>
                </div>
              )}

              <form onSubmit={handleDeploy} className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <Label htmlFor="bot-name" className="text-xs font-semibold text-white">
                    Bot / Project Name <span className="text-[#00ff66]">*</span>
                  </Label>
                  <Input
                    id="bot-name"
                    placeholder="e.g. Acme Community AI"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="bg-[#161b22] border-[#212833] text-white text-xs h-10 rounded-xl focus:border-[#00ff66]"
                  />
                </div>

                {/* Platform Selector */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white block">
                    Platform Gateway <span className="text-[#00ff66]">*</span>
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setPlatform("telegram")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                        platform === "telegram"
                          ? "border-[#2AABEE] bg-[#2AABEE]/15 text-[#2AABEE]"
                          : "border-[#212833] bg-[#161b22] text-[#818c99] hover:text-white"
                      }`}
                    >
                      <Send className="h-3.5 w-3.5" /> Telegram
                    </button>
                    <button
                      type="button"
                      onClick={() => setPlatform("discord")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                        platform === "discord"
                          ? "border-[#5865F2] bg-[#5865F2]/15 text-[#5865F2]"
                          : "border-[#212833] bg-[#161b22] text-[#818c99] hover:text-white"
                      }`}
                    >
                      <MessageSquare className="h-3.5 w-3.5" /> Discord
                    </button>
                    <button
                      type="button"
                      onClick={() => setPlatform("twitter")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                        platform === "twitter"
                          ? "border-sky-400 bg-sky-500/15 text-sky-400"
                          : "border-[#212833] bg-[#161b22] text-[#818c99] hover:text-white"
                      }`}
                    >
                      <span className="font-bold text-sm">𝕏</span> Twitter
                    </button>
                  </div>
                </div>

                {/* Telegram Fields */}
                {platform === "telegram" && (
                  <>
                    <div className="space-y-1.5">
                      <Label htmlFor="bot-token" className="text-xs font-semibold text-white">
                        Telegram Bot Token <span className="text-[#00ff66]">*</span>
                      </Label>
                      <Input
                        id="bot-token"
                        type="password"
                        placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                        value={botToken}
                        onChange={(e) => setBotToken(e.target.value)}
                        required={platform === "telegram"}
                        className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
                      />
                      <p className="text-[10px] text-[#818c99]">Obtained from @BotFather on Telegram.</p>
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="group-id" className="text-xs font-semibold text-white">
                        Telegram Group ID (Optional)
                      </Label>
                      <Input
                        id="group-id"
                        placeholder="e.g. -1001234567890"
                        value={groupId}
                        onChange={(e) => setGroupId(e.target.value)}
                        className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
                      />
                    </div>
                  </>
                )}

                {/* Discord Fields */}
                {platform === "discord" && (
                  <div className="space-y-1.5">
                    <Label htmlFor="discord-token" className="text-xs font-semibold text-white">
                      Discord Bot Token <span className="text-[#5865F2]">*</span>
                    </Label>
                    <Input
                      id="discord-token"
                      type="password"
                      placeholder="MTAyNz...Discord Bot Token"
                      value={discordToken}
                      onChange={(e) => setDiscordToken(e.target.value)}
                      required={platform === "discord"}
                      className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-[#5865F2]"
                    />
                    <p className="text-[10px] text-[#818c99]">Obtained from Discord Developer Portal &gt; Applications &gt; Bot.</p>
                  </div>
                )}

                {/* Twitter / X Fields */}
                {platform === "twitter" && (
                  <div className="space-y-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="tw-api-key" className="text-xs font-semibold text-white">
                        Twitter API Key (Consumer Key) <span className="text-sky-400">*</span>
                      </Label>
                      <Input
                        id="tw-api-key"
                        type="password"
                        placeholder="Twitter API Key"
                        value={twitterApiKey}
                        onChange={(e) => setTwitterApiKey(e.target.value)}
                        required={platform === "twitter"}
                        className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-sky-400"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="tw-api-secret" className="text-xs font-semibold text-white">
                        Twitter API Key Secret <span className="text-sky-400">*</span>
                      </Label>
                      <Input
                        id="tw-api-secret"
                        type="password"
                        placeholder="Twitter API Secret"
                        value={twitterApiSecret}
                        onChange={(e) => setTwitterApiSecret(e.target.value)}
                        required={platform === "twitter"}
                        className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-sky-400"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-1.5">
                        <Label htmlFor="tw-access-token" className="text-xs font-semibold text-white">
                          Access Token <span className="text-sky-400">*</span>
                        </Label>
                        <Input
                          id="tw-access-token"
                          type="password"
                          placeholder="Access Token"
                          value={twitterAccessToken}
                          onChange={(e) => setTwitterAccessToken(e.target.value)}
                          required={platform === "twitter"}
                          className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-sky-400"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="tw-access-secret" className="text-xs font-semibold text-white">
                          Access Token Secret <span className="text-sky-400">*</span>
                        </Label>
                        <Input
                          id="tw-access-secret"
                          type="password"
                          placeholder="Access Token Secret"
                          value={twitterAccessSecret}
                          onChange={(e) => setTwitterAccessSecret(e.target.value)}
                          required={platform === "twitter"}
                          className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-sky-400"
                        />
                      </div>
                    </div>
                    <p className="text-[10px] text-[#818c99]">Generated in Twitter Developer Portal (Read & Write permissions).</p>
                  </div>
                )}

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="api-key" className="text-xs font-semibold text-white">
                      LLM / AI API Key (Optional)
                    </Label>
                    <span className="text-[10px] text-[#818c99]">Groq, OpenAI, or OpenRouter</span>
                  </div>
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="gsk_... or sk-..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
                  />
                  <p className="text-[10px] text-[#818c99]">
                    Provide a custom API key for high-speed inference, or leave blank to use platform default.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="token-addr" className="text-xs font-semibold text-white">
                    Token Address (Solana Mint / EVM Contract — Optional)
                  </Label>
                  <Input
                    id="token-addr"
                    placeholder="e.g. 7vfCXTUXx5WJV5JADk17DUJ4ksau7utNKj4b963voxs4"
                    value={tokenAddress}
                    onChange={(e) => setTokenAddress(e.target.value)}
                    className="bg-[#161b22] border-[#212833] text-white font-mono text-xs h-10 rounded-xl focus:border-[#00ff66]"
                  />
                </div>

                <DialogFooter className="pt-4 border-t border-[#212833]">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setIsDeployOpen(false)}
                    className="text-xs text-[#818c99] hover:text-white hover:bg-[#181d24] rounded-xl h-10"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={deploySubmitting}
                    className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-5 rounded-xl shadow-lg shadow-[#00ff66]/20 cursor-pointer"
                  >
                    {deploySubmitting ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                        Deploying...
                      </>
                    ) : (
                      "Confirm & Deploy"
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Success banner */}
      {actionSuccessMessage && (
        <div className="p-3.5 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
          <Check className="h-4 w-4 shrink-0" />
          <span>{actionSuccessMessage}</span>
        </div>
      )}

      {/* Tab Switcher: Tenant Projects vs Agent Registry */}
      <div className="flex items-center gap-2 border-b border-[#212833] pb-3">
        <button
          type="button"
          onClick={() => setActiveTab("projects")}
          className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === "projects"
              ? "bg-[#00ff66] text-black shadow-md shadow-[#00ff66]/15"
              : "bg-[#12161c] border border-[#212833] text-[#818c99] hover:text-white"
          }`}
        >
          <Bot className="h-3.5 w-3.5" />
          <span>Tenant Projects</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("registry")}
          className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === "registry"
              ? "bg-[#00ff66] text-black shadow-md shadow-[#00ff66]/15"
              : "bg-[#12161c] border border-[#212833] text-[#818c99] hover:text-white"
          }`}
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Agent Registry</span>
        </button>
      </div>

      {activeTab === "registry" ? (
        <div className="space-y-4">
          <div className="p-5 rounded-3xl bg-[#12161c] border border-[#212833] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[#00ff66]" />
                <span>Zoe Summonable Agent Registry</span>
              </h2>
              <p className="text-xs text-[#818c99] mt-1">
                Users can switch Zoe&apos;s active persona in Telegram using <code className="text-[#00ff66]">/summon &lt;agent_name&gt;</code> or return to JARVIS with <code className="text-[#00ff66]">/summon default</code>.
              </p>
            </div>
          </div>

          {personasLoading ? (
            <div className="py-12 flex items-center justify-center text-[#818c99] gap-2 text-xs">
              <Loader2 className="h-5 w-5 animate-spin text-[#00ff66]" />
              <span>Loading Agent Registry...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {personas.map((agent) => (
                <div
                  key={agent.id}
                  className="p-5 rounded-3xl bg-[#12161c] border border-[#212833] hover:border-[#00ff66]/40 transition-colors space-y-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-bold text-white">{agent.name}</h3>
                    <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                      /summon {agent.id}
                    </span>
                  </div>
                  <p className="text-xs text-[#818c99] leading-relaxed">{agent.description}</p>
                  <div className="p-3 rounded-2xl bg-[#0e1116] border border-[#212833] text-[11px] font-mono text-neutral-300">
                    <span className="text-[#818c99] block mb-1 uppercase text-[9px] tracking-wider">System Prompt:</span>
                    {agent.system_prompt}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <>
      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#818c99]" />
          <Input
            placeholder="Search projects by name, owner, or address..."
            value={globalFilter ?? ""}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-10 bg-[#12161c] border-[#212833] text-white text-xs h-10 rounded-full focus:border-[#00ff66] w-full"
          />
        </div>

        {/* Status Filter Badges */}
        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${statusFilter === "all"
                ? "bg-[#00ff66] text-black shadow-md shadow-[#00ff66]/10"
                : "bg-[#12161c] border border-[#212833] text-[#818c99] hover:text-white"
              }`}
          >
            All Projects ({data.length})
          </button>
          <button
            onClick={() => setStatusFilter("online")}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${statusFilter === "online"
                ? "bg-[#00ff66] text-black shadow-md shadow-[#00ff66]/10"
                : "bg-[#12161c] border border-[#212833] text-[#818c99] hover:text-white"
              }`}
          >
            Online
          </button>
          <button
            onClick={() => setStatusFilter("suspended")}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${statusFilter === "suspended"
                ? "bg-rose-500 text-white shadow-md shadow-rose-500/10"
                : "bg-[#12161c] border border-[#212833] text-[#818c99] hover:text-white"
              }`}
          >
            Suspended
          </button>
        </div>
      </div>

      {/* Master Projects Table Card */}
      <div className="bg-[#12161c] border border-[#212833] rounded-3xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-[#161b22]/70 border-b border-[#212833]">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id} className="border-[#212833] hover:bg-transparent">
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      className="text-xs font-bold text-[#818c99] uppercase tracking-wider py-3.5 px-4"
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody className="divide-y divide-[#212833]">
              {loading ? (
                <TableRow>
                  <TableCell colSpan={columns.length} className="h-40 text-center">
                    <div className="flex flex-col items-center justify-center gap-2 text-xs text-[#818c99]">
                      <Loader2 className="h-6 w-6 animate-spin text-[#00ff66]" />
                      <span>Loading tenant projects...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className="border-[#212833] hover:bg-[#181d24]/60 transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id} className="py-3.5 px-4">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={columns.length} className="h-32 text-center text-xs text-[#818c99]">
                    No projects found matching the criteria.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination Footer */}
        <div className="flex items-center justify-between p-4 border-t border-[#212833] text-xs text-[#818c99]">
          <div>
            Showing{" "}
            <strong className="text-white">
              {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}
            </strong>{" "}
            to{" "}
            <strong className="text-white">
              {Math.min(
                (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                table.getFilteredRowModel().rows.length
              )}
            </strong>{" "}
            of <strong className="text-white">{table.getFilteredRowModel().rows.length}</strong> projects
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="border-[#212833] bg-[#161b22] text-white hover:bg-[#1f2631] text-xs h-8 px-3 rounded-xl disabled:opacity-30 cursor-pointer"
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="border-[#212833] bg-[#161b22] text-white hover:bg-[#1f2631] text-xs h-8 px-3 rounded-xl disabled:opacity-30 cursor-pointer"
            >
              Next
            </Button>
          </div>
        </div>
      </div>
        </>
      )}

      {/* Suspend Confirmation Dialog */}
      <Dialog open={!!suspendProjectTarget} onOpenChange={(open) => !open && setSuspendProjectTarget(null)}>
        <DialogContent className="w-[92vw] sm:max-w-[450px] max-h-[85vh] overflow-y-auto bg-[#12161c] border border-rose-900/60 text-white shadow-2xl rounded-3xl p-5 sm:p-6">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-500" />
              Confirm Project Suspension
            </DialogTitle>
            <DialogDescription className="text-xs text-[#818c99] pt-2">
              Are you sure you want to suspend <strong className="text-white">{suspendProjectTarget?.name}</strong>?
              This will immediately halt its polling loop, remove its Telegram bot from runtime memory, and set its status to suspended.
            </DialogDescription>
          </DialogHeader>

          {suspendError && (
            <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2 mt-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{suspendError}</span>
            </div>
          )}

          <DialogFooter className="pt-4 border-t border-[#212833] mt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setSuspendProjectTarget(null)}
              className="text-xs text-[#818c99] hover:text-white hover:bg-[#181d24] rounded-xl h-10"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleConfirmSuspend}
              disabled={suspendLoading}
              className="bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs h-10 px-5 rounded-xl shadow-lg shadow-rose-600/20 cursor-pointer"
            >
              {suspendLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                  Suspending...
                </>
              ) : (
                "Confirm Suspension"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Owner Dialog */}
      <Dialog open={!!assignProjectTarget} onOpenChange={(open) => !open && setAssignProjectTarget(null)}>
        <DialogContent className="w-[92vw] sm:max-w-[450px] max-h-[85vh] overflow-y-auto bg-[#12161c] border border-cyan-900/60 text-white shadow-2xl rounded-3xl p-5 sm:p-6">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <Crown className="h-5 w-5 text-cyan-400" />
              Assign Project Owner
            </DialogTitle>
            <DialogDescription className="text-xs text-[#818c99] pt-2">
              Assign <strong className="text-white">{assignProjectTarget?.name}</strong> to a client or founder account. Once assigned, this bot will appear exclusively on their Project Owner Dashboard.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleAssignOwner} className="space-y-4 mt-2">
            <div>
              <Label className="text-xs text-[#818c99]">Owner Email Address</Label>
              <Input
                type="email"
                required
                placeholder="e.g. founder@zoe.test or client@company.com"
                value={assignEmail}
                onChange={(e) => setAssignEmail(e.target.value)}
                className="mt-1.5 bg-[#161b22] border-[#212833] focus:border-cyan-400 text-white text-xs h-10 rounded-xl"
              />
              <p className="text-[11px] text-[#818c99] mt-1">
                The user must have registered an account with this email address.
              </p>
            </div>

            {assignError && (
              <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{assignError}</span>
              </div>
            )}

            <DialogFooter className="pt-4 border-t border-[#212833]">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setAssignProjectTarget(null)}
                className="text-xs text-[#818c99] hover:text-white hover:bg-[#181d24] rounded-xl h-10"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={assignLoading || !assignEmail.trim()}
                className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold text-xs h-10 px-5 rounded-xl shadow-lg shadow-cyan-500/20 cursor-pointer"
              >
                {assignLoading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                    Assigning...
                  </>
                ) : (
                  "Confirm Assignment"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
