"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { LogOut, Search, Settings, ExternalLink } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
    <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Search */}
      <div className="flex items-center gap-4 max-w-md w-full">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search projects, documents, or logs..."
            className="w-full bg-slate-50 border border-slate-200 rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400 focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Cloud Status */}
        <a 
          href="https://zoe-saas-production.up.railway.app/health" 
          target="_blank" 
          rel="noreferrer"
          className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors text-xs text-slate-600"
        >
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="font-medium text-slate-700">API Operational</span>
          <ExternalLink className="h-3 w-3 text-slate-400" />
        </a>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 p-1 rounded-full hover:bg-slate-100 transition-colors focus:outline-none cursor-pointer">
              <Avatar className="h-8 w-8 border border-slate-200 bg-slate-100">
                <AvatarFallback className="text-xs font-medium text-slate-700">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 bg-white border border-slate-200 text-slate-900 shadow-lg rounded-lg p-1">
            <div className="p-3 border-b border-slate-100">
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Signed In As</p>
              <p className="text-xs font-medium text-slate-900 truncate mt-0.5">{email}</p>
            </div>
            <Link href="/dashboard/settings">
              <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-slate-50 text-slate-700 py-2 rounded-md text-xs">
                <Settings className="h-4 w-4 text-slate-400" />
                <span>Account & Settings</span>
              </DropdownMenuItem>
            </Link>
            <DropdownMenuSeparator className="bg-slate-100" />
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer gap-2 text-rose-600 hover:bg-rose-50 hover:text-rose-700 py-2 rounded-md text-xs"
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
