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
  Sparkles,
  ExternalLink,
  Cpu,
  Layers
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

const navigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Bot Fleets", href: "/dashboard/projects", icon: Bot, badge: "2 Live" },
  { name: "Live Telemetry", href: "/dashboard/logs", icon: MessageSquareCode, badge: "Stream" },
  { name: "Cloud & Vault", href: "/dashboard/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-slate-800/80 bg-[#090d16]/95 backdrop-blur-2xl h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/70 gap-3 bg-gradient-to-r from-slate-900/40 to-transparent">
        <div className="relative flex items-center justify-center">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 ring-1 ring-white/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
          </span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-white text-base tracking-tight font-sans">
              Zoe Engine
            </span>
            <span className="text-[9px] uppercase font-mono font-semibold px-1.5 py-0.2 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              PRO
            </span>
          </div>
          <span className="text-[11px] font-medium text-slate-400 tracking-tight">Autonomous Multi-Tenant SaaS</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2.5 text-[10px] font-bold uppercase tracking-widest text-slate-500 font-mono">
          Command Mesh
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-cyan-500/15 via-indigo-500/10 to-transparent text-white font-semibold border border-cyan-500/30 shadow-sm shadow-cyan-500/10"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40 border border-transparent"
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-gradient-to-b from-cyan-400 to-indigo-500 rounded-r-full shadow-sm shadow-cyan-400" />
              )}
              <item.icon
                className={cn(
                  "h-4 w-4 transition-transform duration-200 group-hover:scale-110",
                  isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200"
                )}
              />
              <span className="flex-1 text-[13px]">{item.name}</span>
              {item.badge && (
                <Badge 
                  variant="outline" 
                  className={cn(
                    "text-[10px] px-1.5 py-0 h-4 border font-mono font-normal",
                    isActive
                      ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                      : "bg-slate-800 text-slate-400 border-slate-700 group-hover:border-slate-600"
                  )}
                >
                  {item.badge}
                </Badge>
              )}
            </Link>
          )
        })}
      </div>

      {/* Cloud & Network Telemetry Card */}
      <div className="p-3 m-3 rounded-2xl border border-slate-800/90 bg-gradient-to-b from-slate-900/70 to-slate-950/90 shadow-xl">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-slate-300 font-medium flex items-center gap-1.5 text-[11px]">
            <Activity className="h-3 w-3 text-emerald-400 animate-pulse" />
            Railway Mesh
          </span>
          <span className="text-emerald-400 font-mono text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60">
            ONLINE
          </span>
        </div>
        <div className="space-y-1.5 pt-1 text-[11px] text-slate-400 border-t border-slate-800/70">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 text-slate-400">
              <ShieldCheck className="h-3 w-3 text-cyan-400" />
              AES-256 Vault
            </span>
            <span className="font-mono text-cyan-400 text-[10px]">Active</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 text-slate-400">
              <Cpu className="h-3 w-3 text-indigo-400" />
              Llama-3.3-70b
            </span>
            <span className="font-mono text-indigo-300 text-[10px]">Groq</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
