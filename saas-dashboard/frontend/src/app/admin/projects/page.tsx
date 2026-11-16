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
  Sparkles
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
                    <span className="font-mono text-[11px] text-[#818c99] truncate max-w-[160px]">
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
        accessorKey: "telegram_group_id",
        header: "Bot Username / Target",
        cell: ({ row }) => {
          const groupId = row.original.telegram_group_id
          return groupId ? (
            <div className="font-mono text-xs text-white bg-[#161b22] border border-[#212833] px-3 py-1 rounded-full w-fit">
              {groupId}
            </div>
          ) : (
            <span className="inline-flex items-center text-[11px] text-[#818c99] bg-[#161b22] border border-[#212833] px-2.5 py-0.5 rounded-full">
              Direct Messages (DMs)
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
            Status
            <ArrowUpDown className="h-3.5 w-3.5 text-[#818c99]" />
          </button>
        ),
        cell: ({ row }) => {
          const status = row.original.status
          const isHealthy = !status || status === "active" || status === "online"
          const isDeploying = status === "deploying"

          if (isHealthy) {
            return (
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#00ff66] bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66] animate-pulse" />
                Online
              </span>
            )
          }
          if (isDeploying) {
            return (
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                Deploying
              </span>
            )
          }
          return (
            <span className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/30 px-3 py-1 rounded-full">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
              {status || "Error"}
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
            Created At
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
            } catch {}
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
          return (
            <div className="flex items-center justify-end gap-1">
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
                    Project Actions
                  </DropdownMenuLabel>
                  <DropdownMenuItem
                    onClick={() => {
                      setEditProject(proj)
                      setEditGroupId(proj.telegram_group_id || "")
                      setEditError(null)
                    }}
                    className="cursor-pointer gap-2 hover:bg-[#181d24] text-white hover:text-[#00ff66] text-xs py-2 rounded-xl"
                  >
                    <Edit className="h-3.5 w-3.5 text-[#818c99]" />
                    <span>Edit Group ID</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-[#212833]" />
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
        pageSize: 8,
      },
    },
  })

  return (
    <div className="space-y-6 pb-12">
      {/* WealthWave Header and Add Project Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#212833]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Active Projects
          </h1>
          <p className="text-xs text-[#818c99] mt-1">
            Manage your AI agents, Telegram group bindings, and secure credentials.
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
            <DialogContent className="sm:max-w-[500px] bg-[#12161c] border border-[#212833] text-white shadow-2xl rounded-3xl p-6">
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
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="h-10 text-xs bg-[#161b22] border-[#212833] text-white rounded-full"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="bot-token" className="text-xs font-semibold text-white">
                    Telegram Bot Token <span className="text-[#00ff66]">*</span>
                  </Label>
                  <Input
                    id="bot-token"
                    type="password"
                    placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                    required
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    className="h-10 text-xs font-mono bg-[#161b22] border-[#212833] text-white rounded-full"
                  />
                  <p className="text-[11px] text-[#818c99]">
                    Obtained from @BotFather. AES-256 encrypted before saving to database.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="group-id" className="text-xs font-semibold text-white">
                    Telegram Group ID <span className="text-[#818c99] font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="group-id"
                    placeholder="e.g. -1001234567890"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="h-10 text-xs font-mono bg-[#161b22] border-[#212833] text-white rounded-full"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="token-address" className="text-xs font-semibold text-white">
                    Token Contract Address <span className="text-[#818c99] font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="token-address"
                    placeholder="e.g. 0x... or Solana Mint"
                    value={tokenAddress}
                    onChange={(e) => setTokenAddress(e.target.value)}
                    className="h-10 text-xs font-mono bg-[#161b22] border-[#212833] text-white rounded-full"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="custom-instructions" className="text-xs font-semibold text-white">
                    Custom Persona Instructions <span className="text-[#818c99] font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="custom-instructions"
                    placeholder="e.g. Act as a welcoming assistant for our DeFi token."
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    className="h-10 text-xs bg-[#161b22] border-[#212833] text-white rounded-full"
                  />
                </div>

                <DialogFooter className="pt-3 border-t border-[#212833] flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={deploySubmitting}
                    onClick={() => setIsDeployOpen(false)}
                    className="text-xs h-10 px-5 rounded-full border-[#212833] text-[#818c99] hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={deploySubmitting || !name || !botToken}
                    className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-6 rounded-full shadow-lg shadow-[#00ff66]/20 disabled:opacity-50 cursor-pointer"
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
          <Search className="absolute left-4 top-3 h-4 w-4 text-[#6e7886]" />
          <Input
            placeholder="Search projects or contracts..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="text-xs pl-10 h-10 bg-[#12161c] border-[#212833] text-white rounded-full placeholder:text-[#6e7886]"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1.5 bg-[#12161c] border border-[#212833] p-1.5 rounded-full">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
              statusFilter === "all"
                ? "bg-[#1f2631] text-[#00ff66] shadow-sm"
                : "text-[#818c99] hover:text-white"
            }`}
          >
            All ({data.length})
          </button>
          <button
            onClick={() => setStatusFilter("online")}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              statusFilter === "online"
                ? "bg-[#1f2631] text-[#00ff66] shadow-sm"
                : "text-[#818c99] hover:text-white"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-[#00ff66]" />
            Online
          </button>
          <button
            onClick={() => setStatusFilter("deploying")}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              statusFilter === "deploying"
                ? "bg-[#1f2631] text-amber-400 shadow-sm"
                : "text-[#818c99] hover:text-white"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            Deploying
          </button>
        </div>
      </div>

      {/* WealthWave Dark Data Table */}
      <div className="rounded-3xl border border-[#212833] bg-[#12161c] overflow-hidden shadow-2xl">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-[#818c99] text-xs py-4 px-5 font-bold uppercase tracking-wider">
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
              <TableRow>
                <TableCell colSpan={columns.length} className="h-36 text-center text-[#818c99]">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-[#00ff66]" />
                    <span className="text-xs font-semibold text-white">Loading projects from Zoe Engine...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="py-4 px-5 text-xs">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-36 text-center text-[#818c99] text-xs">
                  <div className="space-y-1">
                    <p className="font-bold text-white text-sm">No projects found</p>
                    <p className="text-xs text-[#818c99]">Click &quot;Add Project&quot; above to register an autonomous Telegram bot.</p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-xs text-[#818c99] px-2">
        <div>
          Showing {table.getFilteredRowModel().rows.length} of {data.length} registered project(s)
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="h-9 px-4 rounded-full border-[#212833] bg-[#12161c] text-white text-xs disabled:opacity-30 cursor-pointer"
          >
            Previous
          </Button>
          <span className="text-xs font-medium text-white px-2">
            Page {table.getState().pagination.pageIndex + 1} of {Math.max(1, table.getPageCount())}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="h-9 px-4 rounded-full border-[#212833] bg-[#12161c] text-white text-xs disabled:opacity-30 cursor-pointer"
          >
            Next
          </Button>
        </div>
      </div>

      {/* Edit Group ID Modal */}
      {editProject && (
        <Dialog open={!!editProject} onOpenChange={(open) => !open && setEditProject(null)}>
          <DialogContent className="sm:max-w-[450px] bg-[#12161c] border border-[#212833] text-white shadow-2xl rounded-3xl p-6">
            <DialogHeader>
              <DialogTitle className="text-base font-bold text-white">
                Edit Telegram Group for {editProject.name}
              </DialogTitle>
              <DialogDescription className="text-xs text-[#818c99]">
                Update the authorized group chat ID where this bot responds.
              </DialogDescription>
            </DialogHeader>

            {editError && (
              <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{editError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateGroup} className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <Label htmlFor="edit-group-id" className="text-xs font-semibold text-white">
                  Telegram Group ID
                </Label>
                <Input
                  id="edit-group-id"
                  placeholder="e.g. -1001234567890"
                  value={editGroupId}
                  onChange={(e) => setEditGroupId(e.target.value)}
                  className="font-mono text-xs h-10 bg-[#161b22] border-[#212833] text-white rounded-full"
                />
              </div>

              <DialogFooter className="pt-3 border-t border-[#212833] flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditProject(null)}
                  className="text-xs h-10 px-5 rounded-full border-[#212833] text-[#818c99] hover:text-white"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={editSubmitting}
                  className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-6 rounded-full shadow-lg shadow-[#00ff66]/20 cursor-pointer"
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
