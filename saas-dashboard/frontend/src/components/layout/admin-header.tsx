"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  LogOut, 
  Search, 
  Settings, 
  Bell, 
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
    <header className="h-16 border-b border-border bg-card px-6 md:px-8 flex items-center justify-between sticky top-0 z-30 select-none">
      {/* Search Bar - shadcn style */}
      <div className="flex items-center gap-4 max-w-md w-full">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search projects, tokens, or system events..."
            className="w-full bg-muted/40 border border-input rounded-md pl-9 pr-12 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring focus:bg-background transition-all"
          />
          <div className="absolute right-2.5 top-2 flex items-center gap-0.5 pointer-events-none text-[10px] bg-secondary text-muted-foreground px-1.5 py-0.5 rounded border border-border font-mono">
            <Command className="h-2.5 w-2.5" /> K
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Backend API status */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md border border-border bg-secondary/50 text-xs text-foreground">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-medium">FastAPI Engine</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button 
            type="button" 
            aria-label="View notifications"
            className="h-8 w-8 rounded-md border border-border bg-background flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors cursor-pointer"
          >
            <Bell className="h-4 w-4" />
          </button>
          {notificationsCount > 0 && (
            <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-primary text-[10px] font-bold text-primary-foreground flex items-center justify-center">
              {notificationsCount}
            </span>
          )}
        </div>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 p-0.5 rounded-full hover:bg-secondary transition-colors focus:outline-none cursor-pointer">
              <Avatar className="h-8 w-8 border border-border bg-secondary text-foreground">
                <AvatarFallback className="text-xs font-semibold text-foreground">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60 bg-popover border border-border text-popover-foreground shadow-lg rounded-lg p-1.5">
            <div className="p-2.5 border-b border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Signed In
                </span>
                <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded">
                  Super Admin
                </span>
              </div>
              <p className="text-xs font-medium text-foreground truncate">{email}</p>
            </div>
            
            <div className="py-1">
              <Link href="/admin/settings">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-secondary text-foreground py-2 rounded-md text-xs">
                  <Settings className="h-4 w-4 text-muted-foreground" />
                  <span>Platform Settings</span>
                </DropdownMenuItem>
              </Link>
              <Link href="/admin/overview">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-secondary text-foreground py-2 rounded-md text-xs">
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                  <span>Fleet Overview</span>
                </DropdownMenuItem>
              </Link>
            </div>

            <DropdownMenuSeparator className="bg-border" />
            
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer gap-2 text-destructive hover:bg-destructive/10 hover:text-destructive py-2 rounded-md text-xs font-medium"
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
