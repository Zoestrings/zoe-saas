"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Bot, 
  Activity, 
  Settings, 
  Layers
} from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Active Projects", href: "/dashboard/projects", icon: Bot, badge: "2 Active" },
  { name: "Activity Logs", href: "/dashboard/logs", icon: Activity },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-slate-200 bg-white h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200 gap-3">
        <div className="h-8 w-8 rounded-lg bg-slate-900 text-white flex items-center justify-center font-semibold text-sm">
          Z
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-900 text-sm tracking-tight">
              Zoe Platform
            </span>
          </div>
          <span className="text-xs text-slate-500 font-normal">Community Agent SaaS</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-slate-400">
          Menu
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-slate-100 text-slate-900 font-medium"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <item.icon
                className={cn(
                  "h-4 w-4",
                  isActive ? "text-slate-900" : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              <span className="flex-1 text-sm">{item.name}</span>
              {item.badge && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 font-medium">
                  {item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/50">
        <div className="flex items-center justify-between text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="font-medium text-slate-700">Railway Cloud</span>
          </div>
          <span className="text-[11px] text-slate-400">Live</span>
        </div>
      </div>
    </aside>
  )
}
