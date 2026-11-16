"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  LogOut, 
  Search, 
  Settings, 
  Bell, 
  Plus,
  Cpu,
  User as UserIcon,
  Sparkles
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { getUser, logout, User } from "@/lib/api"

export function AdminHeader() {
  const [user, setUser] = useState<User | null>(null)

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
    <header className="h-20 border-b border-neutral-800 bg-[#0a0a0a] px-6 md:px-8 flex items-center justify-between sticky top-0 z-30 select-none">
      {/* Pill Search Bar - WealthWave style */}
      <div className="flex items-center gap-4 max-w-md w-full">
        <div className="relative w-full">
          <Search className="absolute left-4 top-3 h-4 w-4 text-neutral-500" />
          <input
            type="text"
            placeholder="Search projects, tokens, or system events..."
            className="w-full bg-neutral-800 border border-neutral-700 rounded-full pl-10 pr-4 py-2 text-xs text-white placeholder:text-neutral-500 focus:outline-none focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66] transition-all"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* WealthWave Neon Green Action Button */}
        <Link href="/admin/projects">
          <Button className="bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs h-10 px-5 rounded-full shadow-lg shadow-[#00ff66]/20 flex items-center gap-2 cursor-pointer transition-all">
            <Plus className="h-4 w-4 stroke-[3]" />
            <span>Add Project</span>
          </Button>
        </Link>

        {/* Circular Notification Bell */}
        <div className="relative">
          <button 
            type="button" 
            aria-label="View notifications"
            className="h-10 w-10 rounded-full border border-neutral-800 bg-neutral-900 flex items-center justify-center text-white hover:border-[#00ff66]/50 transition-colors cursor-pointer"
          >
            <Bell className="h-4 w-4" />
          </button>
          <span className="absolute 1 top-1 right-1 h-2.5 w-2.5 rounded-full bg-[#00ff66] ring-2 ring-[#0a0a0a]" />
        </div>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 p-0.5 rounded-full hover:ring-2 hover:ring-[#00ff66]/40 transition-all focus:outline-none cursor-pointer">
              <Avatar className="h-10 w-10 border border-neutral-800 bg-neutral-900 text-white">
                <AvatarFallback className="text-xs font-bold text-[#00ff66]">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60 bg-[#121212] border border-neutral-800 text-white shadow-2xl rounded-2xl p-2 backdrop-blur-xl">
            <div className="p-3 border-b border-neutral-800">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">
                  Signed In
                </span>
                <span className="text-[10px] font-bold text-black bg-[#00ff66] px-2 py-0.5 rounded-full">
                  Super Admin
                </span>
              </div>
              <p className="text-xs font-semibold text-white truncate">{email}</p>
            </div>
            
            <div className="py-1">
              <Link href="/admin/settings">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-neutral-800 hover:text-[#00ff66] text-white py-2 rounded-xl text-xs">
                  <Settings className="h-4 w-4 text-neutral-400" />
                  <span>Platform Settings</span>
                </DropdownMenuItem>
              </Link>
              <Link href="/admin/overview">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-neutral-800 hover:text-[#00ff66] text-white py-2 rounded-xl text-xs">
                  <Cpu className="h-4 w-4 text-neutral-400" />
                  <span>Fleet Overview</span>
                </DropdownMenuItem>
              </Link>
            </div>

            <DropdownMenuSeparator className="bg-neutral-800" />
            
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer gap-2 text-rose-400 hover:bg-rose-950/30 hover:text-rose-300 py-2 rounded-xl text-xs font-semibold"
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
