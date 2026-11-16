"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { 
  Bot, 
  BrainCircuit, 
  FileCode, 
  LogOut, 
  Loader2, 
  User as UserIcon,
  Sparkles
} from "lucide-react"
import { getToken, getUser, removeToken, User } from "@/lib/api"
import { Button } from "@/components/ui/button"

export default function OwnerLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = getToken()
    const currentUser = getUser()
    if (!token) {
      router.replace("/login")
    } else {
      setUser(currentUser)
      setIsAuthenticated(true)
    }
  }, [router])

  const handleLogout = () => {
    removeToken()
    router.replace("/login")
  }

  if (isAuthenticated === null) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0b0f19] text-slate-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        <p className="text-sm font-medium">Verifying owner session...</p>
      </div>
    )
  }

  const navItems = [
    { label: "My Bot", href: "/owner/dashboard", icon: Bot },
    { label: "Knowledge Base", href: "/owner/dashboard/knowledge", icon: BrainCircuit },
    { label: "Instructions", href: "/owner/dashboard/instructions", icon: FileCode },
  ]

  return (
    <div className="min-h-screen w-full bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      {/* Top Glassmorphic Navigation Header */}
      <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#0b0f19]/80 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/owner/dashboard" className="flex items-center gap-2.5 group">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-white text-base">Zoe</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider bg-cyan-950 text-cyan-400 border border-cyan-800/60 px-1.5 py-0.5 rounded">
                  Client Portal
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Autonomous Agent Management</p>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-slate-800 text-cyan-400 border border-slate-700/80 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* User Info & Actions */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2.5 text-xs text-slate-400 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-full">
            <UserIcon className="h-3.5 w-3.5 text-cyan-400" />
            <span className="text-slate-300 font-medium">{user?.email || "Project Owner"}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 text-xs h-8 px-2.5 cursor-pointer"
          >
            <LogOut className="h-3.5 w-3.5 mr-1.5" />
            Sign Out
          </Button>
        </div>
      </header>

      {/* Main Scoped Content */}
      <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
        {children}
      </main>
    </div>
  )
}
