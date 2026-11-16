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
  Check
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
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="text-xs font-semibold text-foreground p-0 hover:bg-transparent"
          >
            Project Name
            <ArrowUpDown className="ml-2 h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        ),
        cell: ({ row }) => {
          const proj = row.original
          return (
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-md bg-secondary border border-border flex items-center justify-center text-foreground shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className="font-semibold text-foreground text-xs truncate">{proj.name}</div>
                {proj.token_address ? (
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="font-mono text-[11px] text-muted-foreground truncate max-w-[160px]">
                      {proj.token_address}
                    </span>
                    <button
                      onClick={() => copyToClipboard(proj.token_address!, proj.id)}
                      className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                      title="Copy Token Address"
                    >
                      {copiedId === proj.id ? (
                        <Check className="h-2.5 w-2.5 text-emerald-600" />
                      ) : (
                        <Copy className="h-2.5 w-2.5" />
                      )}
                    </button>
                  </div>
                ) : (
                  <span className="text-[11px] text-muted-foreground">ID: {proj.id.slice(0, 8)}...</span>
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
            <div className="font-mono text-xs text-foreground bg-muted/60 border border-border px-2 py-0.5 rounded-md w-fit">
              {groupId}
            </div>
          ) : (
            <span className="inline-flex items-center text-[11px] text-muted-foreground bg-secondary border border-border px-2 py-0.5 rounded-md">
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
            className="text-xs font-semibold text-foreground p-0 hover:bg-transparent"
          >
            Status
            <ArrowUpDown className="ml-2 h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        ),
        cell: ({ row }) => {
          const status = row.original.status
          const isHealthy = !status || status === "active" || status === "online"
          const isDeploying = status === "deploying"

          if (isHealthy) {
            return (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                Online
              </span>
            )
          }
          if (isDeploying) {
            return (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-600 animate-ping" />
                Deploying
              </span>
            )
          }
          return (
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-0.5 rounded-full">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-600" />
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
            className="text-xs font-semibold text-foreground p-0 hover:bg-transparent"
          >
            Created At
            <ArrowUpDown className="ml-2 h-3.5 w-3.5 text-muted-foreground" />
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
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
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
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-md cursor-pointer"
                  >
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-popover border border-border text-popover-foreground shadow-md rounded-md p-1">
                  <DropdownMenuLabel className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-2 py-1.5">
                    Project Actions
                  </DropdownMenuLabel>
                  <DropdownMenuItem
                    onClick={() => {
                      setEditProject(proj)
                      setEditGroupId(proj.telegram_group_id || "")
                      setEditError(null)
                    }}
                    className="cursor-pointer gap-2 hover:bg-secondary text-foreground text-xs py-1.5 rounded-sm"
                  >
                    <Edit className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>Edit Group ID</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-border" />
                  <DropdownMenuItem
                    onClick={() => handleDelete(proj.id)}
                    className="cursor-pointer gap-2 text-destructive hover:bg-destructive/10 hover:text-destructive text-xs py-1.5 rounded-sm"
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Active Projects
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your AI agents, Telegram group bindings, and secure credentials.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            disabled={loading}
            className="border-border bg-card hover:bg-secondary text-foreground text-xs h-9 cursor-pointer shadow-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          {/* Deploy New Bot Modal */}
          <Dialog open={isDeployOpen} onOpenChange={setIsDeployOpen}>
            <DialogTrigger asChild>
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90 text-xs h-9 px-4 font-medium shadow-sm cursor-pointer">
                <Plus className="h-3.5 w-3.5 mr-1.5" />
                Add Project
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px] bg-card border border-border text-foreground shadow-xl rounded-lg">
              <DialogHeader>
                <DialogTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Bot className="h-5 w-5 text-foreground" />
                  Deploy New Bot to Zoe Engine
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground">
                  Register a new Telegram bot token and connect it directly to the runtime engine.
                </DialogDescription>
              </DialogHeader>

              {deployError && (
                <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
                  <span>{deployError}</span>
                </div>
              )}

              <form onSubmit={handleDeploy} className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <Label htmlFor="bot-name" className="text-xs font-medium text-foreground">
                    Bot / Project Name <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="bot-name"
                    placeholder="e.g. Acme Community AI"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="h-9 text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="bot-token" className="text-xs font-medium text-foreground">
                    Telegram Bot Token <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="bot-token"
                    type="password"
                    placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                    required
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    className="h-9 text-xs font-mono"
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Obtained from @BotFather. AES-256 encrypted before saving to database.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="group-id" className="text-xs font-medium text-foreground">
                    Telegram Group ID <span className="text-muted-foreground font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="group-id"
                    placeholder="e.g. -1001234567890"
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="h-9 text-xs font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="token-address" className="text-xs font-medium text-foreground">
                    Token Contract Address <span className="text-muted-foreground font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="token-address"
                    placeholder="e.g. 0x... or Solana Mint"
                    value={tokenAddress}
                    onChange={(e) => setTokenAddress(e.target.value)}
                    className="h-9 text-xs font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="custom-instructions" className="text-xs font-medium text-foreground">
                    Custom Persona Instructions <span className="text-muted-foreground font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="custom-instructions"
                    placeholder="e.g. Act as a welcoming assistant for our DeFi token."
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    className="h-9 text-xs"
                  />
                </div>

                <DialogFooter className="pt-3 border-t border-border flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={deploySubmitting}
                    onClick={() => setIsDeployOpen(false)}
                    className="text-xs h-9"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={deploySubmitting || !name || !botToken}
                    className="text-xs h-9 px-4 font-medium disabled:opacity-50 cursor-pointer"
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
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search projects or contracts..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="text-xs pl-9 h-9"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1 bg-secondary/80 border border-border p-1 rounded-md">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              statusFilter === "all"
                ? "bg-card text-foreground shadow-xs font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All ({data.length})
          </button>
          <button
            onClick={() => setStatusFilter("online")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1.5 ${
              statusFilter === "online"
                ? "bg-card text-emerald-700 shadow-xs font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            Online
          </button>
          <button
            onClick={() => setStatusFilter("deploying")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1.5 ${
              statusFilter === "deploying"
                ? "bg-card text-amber-700 shadow-xs font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-amber-600" />
            Deploying
          </button>
        </div>
      </div>

      {/* shadcn Clean Light Data Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden shadow-xs">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-muted-foreground text-xs py-3 px-4 font-semibold">
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
                <TableCell colSpan={columns.length} className="h-32 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                    <span className="text-xs">Loading projects from Zoe Engine...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="py-3 px-4 text-xs">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-32 text-center text-muted-foreground text-xs">
                  <div className="space-y-1">
                    <p className="font-medium text-foreground">No projects found</p>
                    <p className="text-xs text-muted-foreground">Click &quot;Add Project&quot; above to register an autonomous Telegram bot.</p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
        <div>
          Showing {table.getFilteredRowModel().rows.length} of {data.length} registered project(s)
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="h-8 px-3 text-xs disabled:opacity-40 cursor-pointer"
          >
            Previous
          </Button>
          <span className="text-xs">
            Page {table.getState().pagination.pageIndex + 1} of {Math.max(1, table.getPageCount())}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="h-8 px-3 text-xs disabled:opacity-40 cursor-pointer"
          >
            Next
          </Button>
        </div>
      </div>

      {/* Edit Group ID Modal */}
      {editProject && (
        <Dialog open={!!editProject} onOpenChange={(open) => !open && setEditProject(null)}>
          <DialogContent className="sm:max-w-[450px] bg-card border border-border text-foreground shadow-xl rounded-lg">
            <DialogHeader>
              <DialogTitle className="text-base font-semibold text-foreground">
                Edit Telegram Group for {editProject.name}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Update the authorized group chat ID where this bot responds.
              </DialogDescription>
            </DialogHeader>

            {editError && (
              <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
                <span>{editError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateGroup} className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <Label htmlFor="edit-group-id" className="text-xs font-medium text-foreground">
                  Telegram Group ID
                </Label>
                <Input
                  id="edit-group-id"
                  placeholder="e.g. -1001234567890"
                  value={editGroupId}
                  onChange={(e) => setEditGroupId(e.target.value)}
                  className="font-mono text-xs h-9"
                />
              </div>

              <DialogFooter className="pt-3 border-t border-border flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditProject(null)}
                  className="text-xs h-9"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={editSubmitting}
                  className="text-xs h-9 px-4 font-medium cursor-pointer"
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
