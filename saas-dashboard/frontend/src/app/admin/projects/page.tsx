"use client"

import * as React from "react"
import { useState, useEffect, useMemo } from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
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
  ExternalLink, 
  ArrowUpDown, 
  CheckCircle2, 
  AlertCircle, 
  StopCircle, 
  Loader2,
  Copy,
  Check,
  ShieldCheck,
  Filter,
  SlidersHorizontal
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
import { api, Project } from "@/lib/api"

export default function AdminProjectsPage() {
  const [data, setData] = useState<Project[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState<string>("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  // Modal states
  const [isDeployOpen, setIsDeployOpen] = useState(false)
  const [deploySubmitting, setDeploySubmitting] = useState(false)
  const [deployError, setDeployError] = useState<string | null>(null)

  // Form fields for Deploy Bot
  const [name, setName] = useState("")
  const [botToken, setBotToken] = useState("")
  const [tokenAddress, setTokenAddress] = useState("")
  const [groupId, setGroupId] = useState("")
  const [customInstructions, setCustomInstructions] = useState("")

  // Edit Group Modal state
  const [editProject, setEditProject] = useState<Project | null>(null)
  const [editGroupId, setEditGroupId] = useState("")
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)

  // Delete state
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Copied token state
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Fetch Projects from FastAPI using Bearer Token
  const fetchProjects = async () => {
    setLoading(true)
    try {
      const projects = await api.getProjects()
      setData(projects || [])
    } catch (err: any) {
      console.error("Failed to fetch projects:", err)
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
        telegram_bot_token: botToken.trim(),
        token_address: tokenAddress.trim(),
        telegram_group_id: groupId.trim() || undefined,
        custom_instructions: customInstructions.trim() || undefined,
      })

      // Reset form
      setName("")
      setBotToken("")
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

  // Handle Edit Group ID
  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editProject) return
    setEditSubmitting(true)
    setEditError(null)

    try {
      await api.patchProject(editProject.id, {
        telegram_group_id: editGroupId.trim(),
      })
      setEditProject(null)
      fetchProjects()
    } catch (err: any) {
      setEditError(err.message || "Failed to update group ID.")
    } finally {
      setEditSubmitting(false)
    }
  }

  // Handle Delete Project
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to stop and delete this project? This action cannot be undone.")) {
      return
    }
    setDeletingId(id)
    try {
      await api.deleteProject(id)
      fetchProjects()
    } catch (err: any) {
      alert(err.message || "Failed to delete project.")
    } finally {
      setDeletingId(null)
    }
  }

  // Filtered dataset by status
  const filteredData = useMemo(() => {
    if (statusFilter === "all") return data
    if (statusFilter === "online") return data.filter((p) => !p.status || p.status === "active" || p.status === "online")
    if (statusFilter === "deploying") return data.filter((p) => p.status === "deploying")
    if (statusFilter === "error") return data.filter((p) => p.status === "error" || p.status === "stopped")
    return data
  }, [data, statusFilter])

  // Table Column Definitions
  const columns = useMemo<ColumnDef<Project>[]>(
    () => [
      {
        accessorKey: "name",
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="text-xs font-semibold text-slate-300 hover:text-white p-0 hover:bg-transparent"
          >
            Project Name
            <ArrowUpDown className="ml-2 h-3.5 w-3.5" />
          </Button>
        ),
        cell: ({ row }) => {
          const proj = row.original
          return (
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-slate-800 border border-slate-700/80 flex items-center justify-center text-cyan-400 shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className="font-semibold text-white text-xs truncate">{proj.name}</div>
                {proj.token_address ? (
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="font-mono text-[10px] text-slate-400 truncate max-w-[140px]">
                      {proj.token_address}
                    </span>
                    <button
                      onClick={() => copyToClipboard(proj.token_address!, proj.id)}
                      className="text-slate-500 hover:text-slate-300 transition-colors"
                      title="Copy Token Address"
                    >
                      {copiedId === proj.id ? (
                        <Check className="h-2.5 w-2.5 text-emerald-400" />
                      ) : (
                        <Copy className="h-2.5 w-2.5" />
                      )}
                    </button>
                  </div>
                ) : (
                  <span className="text-[10px] text-slate-500">ID: {proj.id.slice(0, 8)}...</span>
                )}
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: "telegram_group_id",
        header: "Bot Username / Target",
        cell: ({ row }) => {
          const groupId = row.original.telegram_group_id
          return groupId ? (
            <div className="font-mono text-xs text-slate-300 bg-slate-950/60 border border-slate-800/80 px-2 py-0.5 rounded w-fit">
              {groupId}
            </div>
          ) : (
            <span className="inline-flex items-center text-[10px] text-slate-400 bg-slate-800/60 border border-slate-700/60 px-2 py-0.5 rounded">
              Direct Messages (DMs)
            </span>
          )
        },
      },
      {
        accessorKey: "status",
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="text-xs font-semibold text-slate-300 hover:text-white p-0 hover:bg-transparent"
          >
            Status
            <ArrowUpDown className="ml-2 h-3.5 w-3.5" />
          </Button>
        ),
        cell: ({ row }) => {
          const status = row.original.status
          const isHealthy = !status || status === "active" || status === "online"
          const isDeploying = status === "deploying"
          const isStopped = status === "stopped" || status === "error"

          if (isHealthy) {
            return (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Online
              </span>
            )
          }
          if (isDeploying) {
            return (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-amber-400 bg-amber-950/60 border border-amber-800/60 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                Deploying
              </span>
            )
          }
          return (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-rose-400 bg-rose-950/60 border border-rose-800/60 px-2.5 py-0.5 rounded-full">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
              {status || "Error"}
            </span>
          )
        },
      },
      {
        accessorKey: "created_at",
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="text-xs font-semibold text-slate-300 hover:text-white p-0 hover:bg-transparent"
          >
            Created At
            <ArrowUpDown className="ml-2 h-3.5 w-3.5" />
          </Button>
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
            } catch {}
          }
          return (
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Calendar className="h-3.5 w-3.5 text-slate-500" />
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
          return (
            <div className="flex items-center justify-end gap-1">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg cursor-pointer"
                  >
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-slate-900 border border-slate-800 text-slate-200 shadow-xl rounded-xl p-1">
                  <DropdownMenuLabel className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 py-1.5">
                    Project Actions
                  </DropdownMenuLabel>
                  <DropdownMenuItem
                    onClick={() => {
                      setEditProject(proj)
                      setEditGroupId(proj.telegram_group_id || "")
                      setEditError(null)
                    }}
                    className="cursor-pointer gap-2 hover:bg-slate-800 text-slate-300 hover:text-white text-xs py-1.5 rounded-md"
                  >
                    <Edit className="h-3.5 w-3.5 text-slate-400" />
                    <span>Edit Group ID</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-slate-800" />
                  <DropdownMenuItem
                    onClick={() => handleDelete(proj.id)}
                    className="cursor-pointer gap-2 text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 text-xs py-1.5 rounded-md"
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
        pageSize: 8,
      },
    },
  })

  return (
    <div className="space-y-6">
      {/* Header and Add Project Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Bot className="h-6 w-6 text-cyan-400" />
            Active Fleet Projects
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Super Admin directory of all registered autonomous Telegram bots running on the Zoe Engine.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            disabled={loading}
            className="border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-slate-300 text-xs h-9 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          {/* Deploy New Bot Modal */}
          <Dialog open={isDeployOpen} onOpenChange={setIsDeployOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs h-9 px-4 font-medium shadow-lg shadow-cyan-600/20 cursor-pointer">
                <Plus className="h-3.5 w-3.5 mr-1.5" />
                Deploy New Bot
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px] bg-slate-900 border border-slate-800 text-slate-100 shadow-2xl rounded-2xl">
              <DialogHeader>
                <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
                  <Bot className="h-5 w-5 text-cyan-400" />
                  Deploy New Bot to Zoe Engine
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-400">
                  Register a new Telegram bot token and connect it directly to the runtime engine.
                </DialogDescription>
              </DialogHeader>

              {deployError && (
                <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                  <span>{deployError}</span>
                </div>
              )}

              <form onSubmit={handleDeploy} className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <Label htmlFor="bot-name" className="text-xs font-semibold text-slate-300">
                    Bot / Project Name <span className="text-rose-400">*</span>
                  </Label>
                  <Input
                    id="bot-name"
                    placeholder="e.g. Acme Community AI"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="bg-slate-950/80 border-slate-800 text-white text-xs h-9 focus:border-cyan-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="bot-token" className="text-xs font-semibold text-slate-300">
                    Telegram Bot Token <span className="text-rose-400">*</span>
                  </Label>
                  <Input
                    id="bot-token"
                    type="password"
                    placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                    required
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    className="bg-slate-950/80 border-slate-800 text-white font-mono text-xs h-9 focus:border-cyan-500"
                  />
                  <p className="text-[10px] text-slate-500">
                    Obtained from @BotFather. AES-256 encrypted before saving to database.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="group-id" className="text-xs font-semibold text-slate-300">
                    Telegram Group ID <span className="text-slate-500 font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="group-id"
                    placeholder="e.g. -1001234567890"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="bg-slate-950/80 border-slate-800 text-white font-mono text-xs h-9 focus:border-cyan-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="token-address" className="text-xs font-semibold text-slate-300">
                    Token Contract Address <span className="text-slate-500 font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="token-address"
                    placeholder="e.g. 0x... or Solana Mint"
                    value={tokenAddress}
                    onChange={(e) => setTokenAddress(e.target.value)}
                    className="bg-slate-950/80 border-slate-800 text-white font-mono text-xs h-9 focus:border-cyan-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="custom-instructions" className="text-xs font-semibold text-slate-300">
                    Custom Persona Instructions <span className="text-slate-500 font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="custom-instructions"
                    placeholder="e.g. Act as a welcoming assistant for our DeFi token."
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    className="bg-slate-950/80 border-slate-800 text-white text-xs h-9 focus:border-cyan-500"
                  />
                </div>

                <DialogFooter className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={deploySubmitting}
                    onClick={() => setIsDeployOpen(false)}
                    className="border-slate-800 text-slate-400 hover:text-white text-xs h-9"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={deploySubmitting || !name || !botToken}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-9 px-4 font-medium disabled:opacity-50 cursor-pointer"
                  >
                    {deploySubmitting && <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />}
                    {deploySubmitting ? "Deploying..." : "Deploy Bot"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Advanced Filter & Search Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative max-w-sm w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search projects or contracts..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="bg-slate-900/60 border-slate-800 text-white text-xs pl-9 h-9 focus:border-cyan-500"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 border border-slate-800 p-1 rounded-lg">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              statusFilter === "all"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All ({data.length})
          </button>
          <button
            onClick={() => setStatusFilter("online")}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              statusFilter === "online"
                ? "bg-slate-800 text-emerald-400 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Online
          </button>
          <button
            onClick={() => setStatusFilter("deploying")}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              statusFilter === "deploying"
                ? "bg-slate-800 text-amber-400 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Deploying
          </button>
        </div>
      </div>

      {/* shadcn Data Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-2xl backdrop-blur-sm">
        <Table>
          <TableHeader className="bg-slate-950/60 border-b border-slate-800">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="border-slate-800 hover:bg-transparent">
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-slate-400 text-xs py-3.5 px-4 font-semibold">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>

          <TableBody>
            {loading ? (
              <TableRow className="border-slate-800">
                <TableCell colSpan={columns.length} className="h-40 text-center text-slate-400">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
                    <span className="text-xs">Querying Zoe Fleet from FastAPI engine...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="py-3 px-4 text-xs">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow className="border-slate-800">
                <TableCell colSpan={columns.length} className="h-40 text-center text-slate-500 text-xs">
                  No projects found matching the filter criteria.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <div className="text-[11px]">
          Showing {table.getFilteredRowModel().rows.length} of {data.length} registered project(s)
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="border-slate-800 bg-slate-900/60 text-slate-300 text-xs h-8 px-3 disabled:opacity-30 cursor-pointer"
          >
            Previous
          </Button>
          <span className="text-[11px] text-slate-400">
            Page {table.getState().pagination.pageIndex + 1} of {Math.max(1, table.getPageCount())}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="border-slate-800 bg-slate-900/60 text-slate-300 text-xs h-8 px-3 disabled:opacity-30 cursor-pointer"
          >
            Next
          </Button>
        </div>
      </div>

      {/* Edit Group ID Modal */}
      {editProject && (
        <Dialog open={!!editProject} onOpenChange={(open) => !open && setEditProject(null)}>
          <DialogContent className="sm:max-w-[450px] bg-slate-900 border border-slate-800 text-slate-100 shadow-2xl rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-base font-bold text-white">
                Edit Telegram Group for {editProject.name}
              </DialogTitle>
              <DialogDescription className="text-xs text-slate-400">
                Update the authorized group chat ID where this bot responds.
              </DialogDescription>
            </DialogHeader>

            {editError && (
              <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{editError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateGroup} className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <Label htmlFor="edit-group-id" className="text-xs font-semibold text-slate-300">
                  Telegram Group ID
                </Label>
                <Input
                  id="edit-group-id"
                  placeholder="e.g. -1001234567890"
                  value={editGroupId}
                  onChange={(e) => setEditGroupId(e.target.value)}
                  className="bg-slate-950/80 border-slate-800 text-white font-mono text-xs h-9 focus:border-cyan-500"
                />
              </div>

              <DialogFooter className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditProject(null)}
                  className="border-slate-800 text-slate-400 text-xs h-9"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={editSubmitting}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-9 px-4 font-medium cursor-pointer"
                >
                  {editSubmitting ? "Saving..." : "Save Changes"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

