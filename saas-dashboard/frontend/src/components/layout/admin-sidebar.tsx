"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Bot, 
  Settings, 
  Sparkles,
  ShieldAlert,
  Layers,
  ChevronRight,
  Activity
} from "lucide-react"
import { cn } from "@/lib/utils"

const adminNav = [
  { 
    name: "Overview", 
    href: "/admin/overview", 
    icon: LayoutDashboard,
    description: "Fleet metrics & health"
  },
  { 
    name: "Projects", 
    href: "/admin/projects", 
    icon: Bot,
    description: "Manage all tenant bots"
  },
  { 
    name: "Settings", 
    href: "/admin/settings", 
    icon: Settings,
    description: "System & API keys"
  },
]

export function AdminSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-slate-800 bg-[#0d131f] text-slate-200 h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/80 gap-3">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white font-bold text-base shadow-lg shadow-cyan-500/20">
          <Sparkles className="h-5 w-5" />
        </div>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-white text-sm tracking-tight">
              Zoe Engine
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-indigo-950 text-indigo-400 border border-indigo-800/60 px-1.5 py-0.2 rounded">
              Admin
            </span>
          </div>
          <span className="text-[11px] text-slate-400 truncate">Autonomous Fleet Console</span>
        </div>
      </div>

      {/* Navigation Group */}
      <div className="flex-1 py-5 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Platform Management
        </div>

        {adminNav.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/admin/overview" && pathname.startsWith(item.href))
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all relative",
                isActive
                  ? "bg-slate-800/90 text-cyan-400 shadow-sm border border-slate-700/80 font-semibold"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 transition-colors",
                  isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200"
                )}
              />
              <div className="flex-1 min-w-0">
                <div className="truncate text-xs">{item.name}</div>
              </div>

              {isActive && (
                <div className="h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
              )}
            </Link>
          )
        })}
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
        <div className="rounded-lg bg-slate-950/70 border border-slate-800/80 p-3 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">FastAPI Runtime</span>
            <span className="inline-flex items-center gap-1 font-medium text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Connected
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Supabase Auth</span>
            <span className="text-slate-300 font-mono text-[10px]">JWT Active</span>
          </div>
        </div>
      </div>
    </aside>
  )
}

