"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Bot, 
  MessageSquareCode, 
  Settings, 
  ShieldCheck, 
  Activity, 
  Sparkles 
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Projects", href: "/dashboard/projects", icon: Bot, badge: "Live" },
  { name: "Conversation Logs", href: "/dashboard/logs", icon: MessageSquareCode },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-slate-800 bg-slate-950/90 backdrop-blur-xl h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-white text-base tracking-wide flex items-center gap-1.5">
            Zoe Engine
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              v1.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Autonomous Web3 Agent</p>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-6 px-4 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Main Menu
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
                isActive
                  ? "bg-slate-800/90 text-cyan-400 font-semibold shadow-inner border border-slate-700/60"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              )}
            >
              <item.icon
                className={cn(
                  "h-4 w-4 transition-colors",
                  isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                )}
              />
              <span className="flex-1">{item.name}</span>
              {item.badge && (
                <Badge variant="default" className="text-[10px] px-1.5 py-0 h-4 bg-cyan-600 hover:bg-cyan-500">
                  {item.badge}
                </Badge>
              )}
            </Link>
          )
        })}
      </div>

      {/* System Status Footprint */}
      <div className="p-4 m-4 rounded-xl border border-slate-800/80 bg-slate-900/50">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
            Live Engine
          </span>
          <span className="text-emerald-400 font-mono font-medium">99.98%</span>
        </div>
        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-cyan-400" />
          Fail-Closed Safety Active
        </div>
      </div>
    </aside>
  )
}
