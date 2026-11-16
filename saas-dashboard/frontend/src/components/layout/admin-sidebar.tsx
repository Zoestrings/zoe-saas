"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Bot, 
  Settings, 
  Sparkles,
  ChevronRight,
  Activity,
  Layers
} from "lucide-react"
import { cn } from "@/lib/utils"

const adminNav = [
  { 
    name: "Overview", 
    href: "/admin/overview", 
    icon: LayoutDashboard,
  },
  { 
    name: "Projects", 
    href: "/admin/projects", 
    icon: Bot,
  },
  { 
    name: "Settings", 
    href: "/admin/settings", 
    icon: Settings,
  },
]

export function AdminSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-border bg-card text-card-foreground h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-border gap-3">
        <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm shadow-sm">
          Z
        </div>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-foreground text-sm tracking-tight">
              Zoe Platform
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-secondary text-secondary-foreground border border-border px-1.5 py-0.2 rounded">
              Admin
            </span>
          </div>
          <span className="text-xs text-muted-foreground truncate">Autonomous Agent SaaS</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-5 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Platform Menu
        </div>

        {adminNav.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/admin/overview" && pathname.startsWith(item.href))
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-secondary text-foreground font-medium shadow-xs"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 transition-colors",
                  isActive ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              <span className="flex-1 text-sm">{item.name}</span>
            </Link>
          )
        })}
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-border bg-muted/30">
        <div className="rounded-lg bg-card border border-border p-3 space-y-2 shadow-xs">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">FastAPI Engine</span>
            <span className="inline-flex items-center gap-1.5 font-medium text-emerald-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Supabase Auth</span>
            <span className="text-foreground font-mono text-[11px]">JWT Active</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
