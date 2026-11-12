"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { LogOut, Search, Terminal, ExternalLink, ShieldCheck, Zap, Globe } from "lucide-react"
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
    <header className="h-16 border-b border-slate-800/80 bg-[#07090e]/80 backdrop-blur-xl px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Search & Breadcrumb info */}
      <div className="flex items-center gap-4 max-w-lg w-full">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-3.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search projects, tokens, or FAISS chunks..."
            className="w-full bg-slate-900/60 border border-slate-800/90 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/60 transition-all"
          />
        </div>
        <div className="hidden lg:flex items-center gap-1.5">
          <Badge variant="outline" className="text-[11px] font-mono text-cyan-400 bg-cyan-950/30 border-cyan-800/40 py-0.5">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping mr-1.5 inline-block" />
            Supabase RLS Active
          </Badge>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Railway Cloud Live Pill */}
        <a 
          href="https://zoe-saas-production.up.railway.app/health" 
          target="_blank" 
          rel="noreferrer"
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl border border-slate-800/80 bg-slate-900/60 hover:bg-slate-800/60 transition-all text-xs text-slate-300 group cursor-pointer"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-mono text-emerald-400 text-[11px] font-medium">Railway 24/7 Live</span>
          <ExternalLink className="h-3 w-3 text-slate-500 group-hover:text-slate-300 transition-colors" />
        </a>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 p-1 rounded-full hover:bg-slate-800/60 transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500/50 cursor-pointer">
              <Avatar className="h-8 w-8 border border-cyan-500/30 bg-gradient-to-tr from-cyan-950 to-indigo-950 shadow-md">
                <AvatarFallback className="text-xs font-bold text-cyan-300 bg-transparent">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64 bg-slate-900/95 border-slate-800/90 text-slate-200 shadow-2xl backdrop-blur-2xl rounded-xl p-1">
            <div className="p-3 border-b border-slate-800/70">
              <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Operator Account</p>
              <p className="text-xs font-semibold text-white truncate mt-0.5">{email}</p>
            </div>
            <Link href="/dashboard/settings">
              <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-slate-800/80 text-slate-300 py-2 rounded-lg text-xs">
                <ShieldCheck className="h-4 w-4 text-cyan-400" />
                <span>Security & Cipher Vault</span>
              </DropdownMenuItem>
            </Link>
            <DropdownMenuSeparator className="bg-slate-800/80" />
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer gap-2 text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 py-2 rounded-lg text-xs"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign Out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
