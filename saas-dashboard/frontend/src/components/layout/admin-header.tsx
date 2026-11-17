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
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  Check,
  ExternalLink,
  Clock
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
import { api, getUser, logout, User, SecurityAlert } from "@/lib/api"

export function AdminHeader() {
  const [user, setUser] = useState<User | null>(null)
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [bellOpen, setBellOpen] = useState<boolean>(false)

  const fetchAlerts = async () => {
    try {
      const data = await api.getAlerts()
      setAlerts(data || [])
      const unread = (data || []).filter((a) => !a.is_read).length
      setUnreadCount(unread)
    } catch (err) {
      console.debug("Failed to fetch notification alerts:", err)
    }
  }

  useEffect(() => {
    const currentUser = getUser()
    if (currentUser) {
      setUser(currentUser)
    }
    fetchAlerts()

    // Poll for live alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleOpenBell = async (open: boolean) => {
    setBellOpen(open)
    if (open && unreadCount > 0) {
      try {
        await api.markAlertsRead()
        setUnreadCount(0)
        setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })))
      } catch (err) {
        console.debug("Failed to mark alerts as read:", err)
      }
    }
  }

  const handleMarkAllRead = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.markAlertsRead()
      setUnreadCount(0)
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })))
    } catch (err) {
      console.debug("Failed to mark all as read:", err)
    }
  }

  const formatAlertTime = (isoStr?: string | null) => {
    if (!isoStr) return "Just now"
    try {
      const diffSec = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000)
      if (diffSec < 60) return "Just now"
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
      return `${Math.floor(diffSec / 86400)}d ago`
    } catch {
      return "Recent"
    }
  }

  const email = user?.email || "admin@zoe.community"
  const displayName = user?.display_name || email.split("@")[0]
  const initials = displayName.slice(0, 2).toUpperCase() || "ZA"

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

        {/* Real-Time Notification Bell Dropdown */}
        <DropdownMenu open={bellOpen} onOpenChange={handleOpenBell}>
          <DropdownMenuTrigger asChild>
            <div className="relative cursor-pointer">
              <button 
                type="button" 
                aria-label="View notifications"
                className="h-10 w-10 rounded-full border border-neutral-800 bg-neutral-900 flex items-center justify-center text-white hover:border-[#00ff66]/50 transition-colors focus:outline-none cursor-pointer"
              >
                <Bell className={`h-4 w-4 ${unreadCount > 0 ? "text-white animate-bounce" : "text-neutral-400"}`} />
              </button>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 h-5 min-w-5 px-1 rounded-full bg-rose-500 text-white text-[10px] font-black flex items-center justify-center ring-2 ring-[#0a0a0a] shadow-lg animate-pulse">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </div>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" className="w-80 sm:w-96 bg-[#121212] border border-neutral-800 text-white shadow-2xl rounded-3xl p-0 backdrop-blur-2xl overflow-hidden z-50">
            {/* Notification Header */}
            <div className="p-4 border-b border-neutral-800/80 bg-neutral-900/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Notifications &amp; Alerts
                </span>
                {unreadCount > 0 ? (
                  <span className="text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded-full font-bold">
                    {unreadCount} New
                  </span>
                ) : (
                  <span className="text-[10px] bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 px-2 py-0.5 rounded-full font-bold">
                    Up to date
                  </span>
                )}
              </div>

              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  className="text-[11px] text-[#00ff66] hover:underline font-semibold cursor-pointer"
                >
                  Mark all as read
                </button>
              )}
            </div>

            {/* Scrollable Alerts List */}
            <div className="max-h-80 overflow-y-auto divide-y divide-neutral-800/60">
              {alerts.length > 0 ? (
                alerts.map((alert) => {
                  const isDrop = alert.alert_type === "liquidity_drop" || alert.message.toLowerCase().includes("drop")

                  return (
                    <div 
                      key={alert.id}
                      className={`p-3.5 hover:bg-neutral-800/40 transition-colors flex items-start gap-3 ${
                        !alert.is_read ? "bg-neutral-900/40" : ""
                      }`}
                    >
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                        isDrop ? "bg-rose-500/10 text-rose-400 border border-rose-500/30" : "bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30"
                      }`}>
                        {isDrop ? <AlertTriangle className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                      </div>

                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-xs font-bold text-white truncate">
                            {alert.token_name ? `$${alert.token_name}` : "Token Alert"}
                          </span>
                          <span className="text-[10px] text-neutral-500 flex items-center gap-1 shrink-0 font-mono">
                            <Clock className="h-2.5 w-2.5" />
                            {formatAlertTime(alert.created_at)}
                          </span>
                        </div>

                        <p className="text-[11px] text-neutral-300 leading-snug line-clamp-2">
                          {alert.message}
                        </p>

                        {alert.contract_address && (
                          <div className="pt-1 flex items-center justify-between">
                            <span className="font-mono text-[10px] text-neutral-500">
                              {alert.contract_address.slice(0, 4)}...{alert.contract_address.slice(-4)}
                            </span>
                            <Link
                              href={`/investigate?ca=${encodeURIComponent(alert.contract_address)}`}
                              className="text-[11px] font-bold text-[#00ff66] hover:underline inline-flex items-center gap-1"
                            >
                              <span>Investigate</span>
                              <ExternalLink className="h-2.5 w-2.5" />
                            </Link>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="p-8 text-center space-y-2">
                  <div className="h-10 w-10 rounded-full bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-500 mx-auto">
                    <Bell className="h-5 w-5" />
                  </div>
                  <p className="text-xs font-bold text-white">No active alerts</p>
                  <p className="text-[11px] text-neutral-500 max-w-xs mx-auto">
                    Continuous monitoring will ping you here if liquidity drops or honeypot mechanisms trigger.
                  </p>
                </div>
              )}
            </div>

            {/* Notification Footer */}
            <div className="p-3 border-t border-neutral-800 bg-neutral-900/60 text-center">
              <Link
                href="/watchlist"
                className="text-xs font-bold text-[#00ff66] hover:underline inline-flex items-center gap-1"
              >
                <span>View Full Watchlist &amp; Alerts &rarr;</span>
              </Link>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

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
                  {user?.role === "super_admin" ? "Super Admin" : "Pro User"}
                </span>
              </div>
              <p className="text-xs font-semibold text-white truncate">{displayName}</p>
              <p className="text-[11px] text-neutral-500 truncate">{email}</p>
            </div>
            
            <div className="py-1">
              <Link href="/settings">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-neutral-800 hover:text-[#00ff66] text-white py-2 rounded-xl text-xs font-semibold">
                  <UserIcon className="h-4 w-4 text-[#00ff66]" />
                  <span>Account Settings</span>
                </DropdownMenuItem>
              </Link>
              <Link href="/admin/settings">
                <DropdownMenuItem className="cursor-pointer gap-2 hover:bg-neutral-800 hover:text-[#00ff66] text-white py-2 rounded-xl text-xs">
                  <Settings className="h-4 w-4 text-neutral-400" />
                  <span>System Health</span>
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
