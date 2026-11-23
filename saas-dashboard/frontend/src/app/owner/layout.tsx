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
  Users,
  Lock,
  Wallet,
  TrendingUp,
  CreditCard,
  Crown,
  ArrowRight
} from "lucide-react"
import { getToken, getUser, removeToken, User, api, EntitlementResponse } from "@/lib/api"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"

export default function OwnerLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [entitlement, setEntitlement] = useState<EntitlementResponse | null>(null)
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const [lockedFeatureName, setLockedFeatureName] = useState("Premium Intelligence")

  useEffect(() => {
    const token = getToken()
    const currentUser = getUser()
    if (!token) {
      router.replace("/login")
    } else {
      setUser(currentUser)
      setIsAuthenticated(true)
      // Fetch entitlement status
      api.getEntitlement()
        .then((res) => setEntitlement(res))
        .catch((err) => {
          console.warn("Could not load entitlement in owner layout:", err)
          setEntitlement({ plan: "free", is_pro: false, expires_at: null, receiving_wallet: "" })
        })
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

  const isFree = !entitlement?.is_pro && (entitlement?.plan !== "pro")

  const navItems = [
    { label: "My Bot", href: "/owner/dashboard", icon: Bot, isPremium: false },
    { label: "Community", href: "/community", icon: Users, isPremium: false },
    { label: "Scanner", href: "/investigate", icon: Radar, isPremium: true },
    { label: "Wallet Intel", href: "/community", icon: Wallet, isPremium: true },
    { label: "Trading", href: "/trading", icon: TrendingUp, isPremium: true },
    { label: "Knowledge Base", href: "/owner/dashboard/knowledge", icon: BrainCircuit, isPremium: false },
    { label: "Instructions", href: "/owner/dashboard/instructions", icon: FileCode, isPremium: false },
    { label: "Logs", href: "/owner/logs", icon: MessageSquare, isPremium: false },
    { label: "Billing", href: "/billing", icon: CreditCard, isPremium: false },
  ]

  const handleNavClick = (e: React.MouseEvent, item: typeof navItems[0]) => {
    if (item.isPremium && isFree) {
      e.preventDefault()
      setLockedFeatureName(item.label)
      setUpgradeModalOpen(true)
    }
  }

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
          <nav className="hidden lg:flex items-center gap-1.5">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              const isLocked = item.isPremium && isFree

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={(e) => handleNavClick(e, item)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                    isActive
                      ? "bg-neutral-800 text-[#00ff66] border border-[#00ff66]/40 shadow-sm"
                      : isLocked
                      ? "text-neutral-400 hover:text-amber-400 hover:bg-neutral-900"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-900"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{item.label}</span>
                  {isLocked && (
                    <Lock className="h-3 w-3 text-amber-400 ml-0.5" />
                  )}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* User Info & Actions */}
        <div className="flex items-center gap-3">
          {/* Plan Badge */}
          <Link href="/billing">
            <div className={`hidden sm:flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full border cursor-pointer transition-all ${
              !isFree
                ? "bg-[#00ff66]/10 border-[#00ff66]/40 text-[#00ff66] shadow-sm shadow-[#00ff66]/10"
                : "bg-amber-500/10 border-amber-500/40 text-amber-400 hover:bg-amber-500/20"
            }`}>
              <Crown className="h-3 w-3" />
              <span>{!isFree ? "PRO" : "FREE PLAN"}</span>
            </div>
          </Link>

          <div className="hidden sm:flex items-center gap-2 text-xs text-neutral-400 bg-neutral-900 border border-neutral-800 px-3 py-1.5 rounded-full">
            <UserIcon className="h-3.5 w-3.5 text-[#00ff66]" />
            <span className="text-neutral-300 font-medium truncate max-w-[140px]">{user?.email || "Project Owner"}</span>
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

      {/* Upgrade Required Paywall Modal */}
      <Dialog open={upgradeModalOpen} onOpenChange={setUpgradeModalOpen}>
        <DialogContent className="sm:max-w-md bg-[#121212] border border-neutral-800 text-white rounded-3xl p-6">
          <DialogHeader className="space-y-3">
            <div className="h-12 w-12 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 mx-auto">
              <Lock className="h-6 w-6" />
            </div>
            <DialogTitle className="text-xl font-black text-center text-white">
              Upgrade Required
            </DialogTitle>
            <DialogDescription className="text-center text-xs text-neutral-400 leading-relaxed">
              <span className="font-semibold text-white">{lockedFeatureName}</span> is a premium Zoe feature. Upgrade to the Pro plan for $20/month to unlock advanced on-chain tools for your bot and community.
            </DialogDescription>
          </DialogHeader>

          <div className="p-4 rounded-2xl bg-neutral-900/80 border border-neutral-800 space-y-2 my-2 text-xs text-neutral-300">
            <div className="font-bold text-white uppercase text-[11px] tracking-wider text-[#00ff66]">
              Unlocked on Pro:
            </div>
            <ul className="space-y-1.5 text-neutral-300">
              <li className="flex items-center gap-2">✦ Deep OSINT founder research & socials verification</li>
              <li className="flex items-center gap-2">✦ Real-time Solana wallet PnL, net worth flex & whale radar</li>
              <li className="flex items-center gap-2">✦ Autonomous 15-min token liquidity surveillance daemon</li>
            </ul>
          </div>

          <DialogFooter className="flex sm:flex-row gap-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setUpgradeModalOpen(false)}
              className="w-full sm:w-auto text-xs text-neutral-400 hover:text-white rounded-full h-10"
            >
              Maybe Later
            </Button>
            <Link href="/billing" className="w-full sm:w-auto" onClick={() => setUpgradeModalOpen(false)}>
              <Button className="w-full h-10 px-6 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-black text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 flex items-center justify-center gap-1.5">
                <span>Upgrade to Pro ($20)</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

