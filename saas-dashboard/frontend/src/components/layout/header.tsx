"use client"

import { useEffect, useState } from "react"
import { LogOut, Search, Terminal, ExternalLink, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { getUser, logout } from "@/lib/api"

export function Header() {
  const [email, setEmail] = useState<string>("admin@zoe.community")

  useEffect(() => {
    const user = getUser()
    if (user?.email) {
      setEmail(user.email)
    }
  }, [])

  const initials = email
    .split("@")[0]
    .slice(0, 2)
    .toUpperCase() || "ZO"

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/70 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Search & Breadcrumb info */}
      <div className="flex items-center gap-4 max-w-md w-full">
        <div className="relative w-full max-w-xs">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search projects, bots, or logs..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
        <div className="hidden md:flex items-center gap-1.5">
          <Badge variant="outline" className="text-[11px] font-mono text-cyan-400 bg-cyan-950/20 border-cyan-900/50">
            Multi-Tenant Orchestrator Active
          </Badge>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Quick Live Bot status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 text-xs text-slate-300">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-mono text-emerald-400">Daemon Online</span>
        </div>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 p-1 rounded-full hover:bg-slate-800/60 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 cursor-pointer">
              <Avatar className="h-8 w-8 border border-cyan-500/40 bg-slate-800">
                <AvatarFallback className="text-xs font-semibold text-cyan-300 bg-cyan-950/80">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60 bg-slate-900 border-slate-800 text-slate-200 shadow-xl">
            <div className="p-3 border-b border-slate-800">
              <p className="text-xs font-medium text-slate-400">Signed in as</p>
              <p className="text-sm font-semibold text-white truncate">{email}</p>
            </div>
            <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-slate-800 text-slate-300 py-2">
              <ShieldCheck className="h-4 w-4 text-cyan-400" />
              <span>Security & Encryption</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-slate-800" />
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer gap-2 text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 py-2"
            >
              <LogOut className="h-4 w-4" />
              <span>Log Out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
