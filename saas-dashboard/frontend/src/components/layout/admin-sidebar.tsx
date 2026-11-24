"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Bot, 
  Settings, 
  LogOut,
  Sparkles,
  Activity,
  Layers,
  ShieldCheck,
  Radar,
  Bookmark,
  Crown,
  DollarSign,
  TrendingUp,
  Users
} from "lucide-react"
import { cn } from "@/lib/utils"
import { logout } from "@/lib/api"
import { ZoeLogo } from "@/components/zoe-logo"

const adminNav = [
  { 
    name: "Overview", 
    href: "/admin/overview", 
    icon: LayoutDashboard,
  },
  { 
    name: "Revenue", 
    href: "/admin/revenue", 
    icon: DollarSign,
  },
  { 
    name: "Projects", 
    href: "/admin/projects", 
    icon: Bot,
  },
  { 
    name: "Community", 
    href: "/community", 
    icon: Users,
  },
  { 
    name: "Intelligence Scanner", 
    href: "/investigate", 
    icon: Radar,
  },
  { 
    name: "Trading Terminal", 
    href: "/trading", 
    icon: TrendingUp,
  },
  { 
    name: "Watchlist", 
    href: "/watchlist", 
    icon: Bookmark,
  },
  { 
    name: "Upgrade Plan", 
    href: "/admin/billing", 
    icon: Crown,
  },
  { 
    name: "Settings", 
    href: "/settings", 
    icon: Settings,
  },
]

export function AdminSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-neutral-800 bg-[#121212] text-white h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="h-20 flex items-center px-6 border-b border-neutral-800 gap-3">
        <ZoeLogo size={36} glow variant="full" badge="ADMIN" />
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-6 px-4 space-y-2 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-neutral-500">
          Menu
        </div>

        {adminNav.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/admin/overview" && pathname.startsWith(item.href))
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3.5 px-4 py-3 rounded-2xl text-xs font-semibold transition-all",
                isActive
                  ? "bg-neutral-800 text-[#00ff66] border border-[#00ff66]/40 shadow-md shadow-[#00ff66]/5"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 transition-colors",
                  isActive ? "text-[#00ff66]" : "text-neutral-500 group-hover:text-white"
                )}
              />
              <span className="flex-1 text-xs">{item.name}</span>
            </Link>
          )
        })}
      </div>

      {/* WealthWave Style Bottom Section */}
      <div className="p-4 space-y-3 border-t border-neutral-800">
        {/* Engine Status Card */}
        <div className="rounded-2xl bg-neutral-900 border border-neutral-800 p-4 text-center space-y-2 shadow-inner">
          <span className="text-xs font-bold text-white block">Engine Core</span>
          <div className="inline-flex items-center gap-1.5 bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 px-3 py-1 rounded-full text-[10px] font-bold">
            <span className="h-1.5 w-1.5 rounded-full bg-[#00ff66] animate-pulse" />
            FastAPI Live
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="space-y-1 pt-1">
          <Link
            href="/settings"
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs text-neutral-400 hover:text-white hover:bg-neutral-900 transition-colors"
          >
            <Settings className="h-4 w-4" />
            <span>Account Settings</span>
          </Link>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs text-neutral-400 hover:text-rose-400 hover:bg-rose-950/20 transition-colors cursor-pointer"
          >
            <LogOut className="h-4 w-4" />
            <span>Log out</span>
          </button>
        </div>
      </div>
    </aside>
  )
}
