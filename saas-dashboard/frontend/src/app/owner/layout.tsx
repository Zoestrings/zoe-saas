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
  Sparkles,
  Radar,
  MessageSquare,
  Users
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
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0a0a0a] text-neutral-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Verifying owner session...</p>
      </div>
    )
  }

  const navItems = [
    { label: "My Bot", href: "/owner/dashboard", icon: Bot },
    { label: "Community", href: "/community", icon: Users },
    { label: "Intelligence Scanner", href: "/investigate", icon: Radar },
    { label: "Conversation Logs", href: "/owner/logs", icon: MessageSquare },
    { label: "Knowledge Base", href: "/owner/dashboard/knowledge", icon: BrainCircuit },
    { label: "Instructions", href: "/owner/dashboard/instructions", icon: FileCode },
  ]

  return (
    <div className="min-h-screen w-full bg-[#0a0a0a] text-white flex flex-col font-sans">
      {/* Top Glassmorphic Navigation Header */}
      <header className="sticky top-0 z-40 border-b border-neutral-800 bg-[#0a0a0a]/90 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/owner/dashboard" className="flex items-center gap-2.5 group">
            <div className="h-9 w-9 rounded-xl bg-[#00ff66] text-black flex items-center justify-center shadow-lg shadow-[#00ff66]/20 font-bold">
              <Sparkles className="h-5 w-5 fill-black text-black" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-white text-base">Zoe Platform</span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 px-2 py-0.5 rounded-full">
                  Client Portal
                </span>
              </div>
              <p className="text-[11px] text-neutral-400">Autonomous Agent Management</p>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center gap-1.5">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                    isActive
                      ? "bg-neutral-800 text-[#00ff66] border border-[#00ff66]/40 shadow-sm"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-900"
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
          <div className="hidden sm:flex items-center gap-2.5 text-xs text-neutral-400 bg-neutral-900 border border-neutral-800 px-3 py-1.5 rounded-full">
            <UserIcon className="h-3.5 w-3.5 text-[#00ff66]" />
            <span className="text-neutral-300 font-medium">{user?.email || "Project Owner"}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="text-neutral-400 hover:text-rose-400 hover:bg-rose-950/20 text-xs h-8 px-3 rounded-full cursor-pointer"
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

