"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  LogOut, 
  Search, 
  Settings, 
  Bell, 
  ShieldCheck, 
  ExternalLink,
  Cpu,
  Command
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getUser, logout, User } from "@/lib/api"

export function AdminHeader() {
  const [user, setUser] = useState<User | null>(null)
  const [notificationsCount, setNotificationsCount] = useState<number>(3)

  useEffect(() => {
    const currentUser = getUser()
    if (currentUser) {
      setUser(currentUser)
    }
  }, [])

  const email = user?.email || "admin@zoe.community"
  const initials = email
    .split("@")[0]
    .slice(0, 2)
    .toUpperCase() || "ZA"

  return (
    <header className="h-16 border-b border-slate-800 bg-[#0d131f]/90 backdrop-blur-md px-6 md:px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Search Bar - shadcn style with keyboard shortcut badge */}
      <div className="flex items-center gap-4 max-w-md w-full">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search projects, tokens, or system events..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-9 pr-12 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-sans"
          />
          <div className="absolute right-2.5 top-2 flex items-center gap-0.5 pointer-events-none text-[10px] bg-slate-800/80 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700/60 font-mono">
            <Command className="h-2.5 w-2.5" /> K
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Backend API status */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg border border-slate-800 bg-slate-900/60 text-xs text-slate-300">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] font-medium">FastAPI Engine</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button 
            type="button" 
            aria-label="View notifications"
            className="h-8 w-8 rounded-lg border border-slate-800 bg-slate-900/60 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <Bell className="h-4 w-4" />
          </button>
          {notificationsCount > 0 && (
            <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-cyan-500 text-[10px] font-bold text-white flex items-center justify-center border-2 border-[#0d131f]">
              {notificationsCount}
            </span>
          )}
        </div>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-800/60 transition-colors focus:outline-none cursor-pointer">
              <Avatar className="h-8 w-8 border border-slate-700 bg-gradient-to-br from-indigo-900 to-slate-800 text-white">
                <AvatarFallback className="text-xs font-semibold text-cyan-300">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60 bg-slate-900 border border-slate-800 text-slate-200 shadow-2xl rounded-xl p-1.5 backdrop-blur-lg">
            <div className="p-3 border-b border-slate-800/80">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Signed In
                </span>
                <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/80 border border-cyan-800/60 px-1.5 py-0.2 rounded">
                  Super Admin
                </span>
              </div>
              <p className="text-xs font-medium text-white truncate">{email}</p>
            </div>
            
            <div className="py-1">
              <Link href="/admin/settings">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-slate-800 text-slate-300 hover:text-white py-2 rounded-md text-xs">
                  <Settings className="h-4 w-4 text-slate-400" />
                  <span>Platform Settings</span>
                </DropdownMenuItem>
              </Link>
              <Link href="/admin/overview">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-slate-800 text-slate-300 hover:text-white py-2 rounded-md text-xs">
                  <Cpu className="h-4 w-4 text-slate-400" />
                  <span>Fleet Overview</span>
                </DropdownMenuItem>
              </Link>
            </div>

            <DropdownMenuSeparator className="bg-slate-800" />
            
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer gap-2 text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 py-2 rounded-md text-xs"
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

