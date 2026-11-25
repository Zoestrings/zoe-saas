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
  Bookmark,
  MessageSquare,
  Users,
  Lock,
  Flame,
  CreditCard,
  Crown,
  ArrowRight,
  LayoutDashboard,
  Settings,
  Menu,
  X,
  ShieldCheck,
  ChevronRight
} from "lucide-react"
import { getToken, getUser, removeToken, isSuperAdmin, User, api, EntitlementResponse } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { ZoeLogo } from "@/components/zoe-logo"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"

interface NavSection {
  title: string
  items: {
    label: string
    href: string
    icon: React.ComponentType<{ className?: string }>
    isPremium?: boolean
    badge?: string
  }[]
}

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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const token = getToken()
    const currentUser = getUser()
    if (!token) {
      router.replace("/login")
    } else if (isSuperAdmin()) {
      router.replace("/admin/overview")
    } else {
      setUser(currentUser)
      setIsAuthenticated(true)
      api.getEntitlement()
        .then((res) => setEntitlement(res))
        .catch((err) => {
          console.warn("Could not load entitlement in owner layout:", err)
          setEntitlement({ plan: "free", is_pro: false, expires_at: null, receiving_wallet: "" })
        })
    }
  }, [router])

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

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

  const navSections: NavSection[] = [
    {
      title: "Overview",
      items: [
        { label: "Dashboard", href: "/owner/dashboard", icon: LayoutDashboard },
        { label: "My Projects", href: "/owner/project", icon: Bot },
        { label: "Analytics & Reports", href: "/owner/analytics", icon: Sparkles },
        { label: "Notifications", href: "/owner/notifications", icon: MessageSquare },
      ],
    },
    {
      title: "Community Management",
      items: [
        { label: "Telegram Management", href: "/owner/integrations/telegram", icon: MessageSquare },
        { label: "Discord Management", href: "/owner/integrations/discord", icon: Users },
        { label: "Knowledge Base", href: "/owner/dashboard/knowledge", icon: BrainCircuit },
        { label: "AI Personality", href: "/owner/dashboard/instructions", icon: FileCode },
        { label: "Moderation & Security", href: "/owner/moderation", icon: ShieldCheck },
        { label: "Activity & Escalations", href: "/owner/logs", icon: Flame },
      ],
    },
    {
      title: "Web3 Intelligence",
      items: [
        { label: "Web3 Scanner", href: "/owner/investigate", icon: Radar },
        { label: "Token & Market Intel", href: "/trading", icon: Sparkles },
        { label: "Research & Social", href: "/owner/social", icon: BrainCircuit },
        { label: "Watchlists & Alerts", href: "/watchlist", icon: Bookmark },
      ],
    },
    {
      title: "Growth & Business",
      items: [
        { label: "Growth & Campaigns", href: "/owner/social", icon: Flame },
        { label: "NFT Growth & Sales", href: "/owner/workspace", icon: Crown },
        { label: "Investor Intelligence", href: "/owner/workspace", icon: Users },
      ],
    },
    {
      title: "AI Automation",
      items: [
        { label: "AI Agents & Workflows", href: "/dashboard/agents", icon: Bot },
      ],
    },
    {
      title: "Account & Billing",
      items: [
        { label: "Credits & Billing", href: "/owner/billing", icon: CreditCard },
        { label: "Team & Invoices", href: "/owner/workspace", icon: Users },
        { label: "Organization Settings", href: "/settings", icon: Settings },
      ],
    },
  ]

  const handleNavClick = (e: React.MouseEvent, item: { label: string; isPremium?: boolean }) => {
    if (item.isPremium && isFree) {
      e.preventDefault()
      setLockedFeatureName(item.label)
      setUpgradeModalOpen(true)
    }
  }

  const renderNavLinks = () => (
    <div className="space-y-6">
      {navSections.map((sec) => (
        <div key={sec.title} className="space-y-1.5">
          <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-neutral-500 font-mono">
            {sec.title}
          </div>
          <div className="space-y-1">
            {sec.items.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              const isLocked = item.isPremium && isFree

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={(e) => handleNavClick(e, item)}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all group cursor-pointer ${isActive
                    ? "bg-[#00ff66]/15 text-[#00ff66] border border-[#00ff66]/30 shadow-sm shadow-[#00ff66]/10"
                    : isLocked
                      ? "text-neutral-400 hover:text-amber-400 hover:bg-neutral-900/60"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-900/80"
                    }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`h-4 w-4 transition-colors ${isActive ? "text-[#00ff66]" : isLocked ? "text-amber-400/80 group-hover:text-amber-400" : "text-neutral-400 group-hover:text-white"
                      }`} />
                    <span>{item.label}</span>
                  </div>

                  {isLocked ? (
                    <span className="flex items-center gap-1 text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      <Lock className="h-2.5 w-2.5" />
                      <span>PRO</span>
                    </span>
                  ) : item.badge ? (
                    <span className="text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30">
                      {item.badge}
                    </span>
                  ) : null}
                </Link>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )

  return (
    <div className="min-h-screen w-full bg-[#0a0a0a] text-white flex flex-col md:flex-row font-sans selection:bg-[#00ff66] selection:text-black">
      {/* Top Header on Mobile (< md) */}
      <header className="md:hidden sticky top-0 z-40 bg-[#0a0a0a]/95 backdrop-blur-md px-4 py-3 border-b border-neutral-800 flex items-center justify-between">
        <Link href="/owner/dashboard" className="flex items-center gap-2.5">
          <ZoeLogo size={32} glow variant="mark" />
          <div>
            <span className="font-bold text-white text-sm tracking-tight block leading-tight">Zoe</span>
            <span className="text-[10px] text-[#00ff66] font-mono tracking-wider uppercase">Intelligence</span>
          </div>
        </Link>

        <div className="flex items-center gap-2">
          <Link href="/owner/billing">
            <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border font-bold ${!isFree ? "bg-[#00ff66]/10 border-[#00ff66]/40 text-[#00ff66]" : "bg-amber-500/10 border-amber-500/40 text-amber-400"
              }`}>
              {!isFree ? "PRO" : "FREE"}
            </span>
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-300 hover:text-white cursor-pointer"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="relative z-10 w-72 max-w-[85vw] h-full bg-[#0c0d14] border-r border-neutral-800 p-5 flex flex-col overflow-y-auto">
            <div className="flex items-center justify-between pb-5 border-b border-neutral-800 mb-5">
              <Link href="/owner/dashboard" className="flex items-center gap-2.5" onClick={() => setMobileMenuOpen(false)}>
                <ZoeLogo size={32} glow variant="mark" />
                <div>
                  <span className="font-bold text-white text-sm block leading-tight">Zoe</span>
                  <span className="text-[10px] text-[#00ff66] block font-mono tracking-wider uppercase">Intelligence</span>
                </div>
              </Link>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 rounded-lg bg-neutral-900 text-neutral-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1">
              {renderNavLinks()}
            </div>

            <div className="pt-5 border-t border-neutral-800 mt-6 space-y-3">
              <div className="flex items-center gap-2 text-xs text-neutral-300">
                <UserIcon className="h-4 w-4 text-[#00ff66]" />
                <span className="truncate">{user?.email || "Owner"}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="w-full justify-start text-xs text-neutral-400 hover:text-rose-400 hover:bg-rose-950/20 rounded-xl"
              >
                <LogOut className="h-3.5 w-3.5 mr-2" />
                Sign Out
              </Button>
            </div>
          </aside>
        </div>
      )}

      {/* Desktop Permanent Left Sidebar (md:flex) */}
      <aside className="hidden md:flex flex-col w-60 lg:w-64 min-h-screen bg-[#0c0d14] border-r border-[#1b1f2e] p-5 shrink-0 sticky top-0 h-screen overflow-y-auto">
        {/* Brand Header */}
        <div className="pb-5 border-b border-neutral-800/80 mb-5">
          <Link href="/owner/dashboard" className="flex items-center gap-3 group">
            <ZoeLogo size={36} glow variant="full" badge="CLIENT" />
          </Link>
        </div>

        {/* Grouped Nav Items */}
        <div className="flex-1 space-y-6">
          {renderNavLinks()}
        </div>

        {/* Pro Promo Banner if Free */}
        {isFree && (
          <div className="my-4 p-3.5 rounded-2xl bg-gradient-to-br from-amber-500/10 via-neutral-900/60 to-transparent border border-amber-500/30 text-center space-y-2">
            <div className="text-[11px] font-bold text-white flex items-center justify-center gap-1.5 text-amber-400">
              <Crown className="h-3.5 w-3.5" />
              <span>Unlock Pro Intel</span>
            </div>
            <p className="text-[10px] text-neutral-400 leading-tight">
              Get 24/7 wallet surveillance, honeypot scanner, and OSINT founder lookups.
            </p>
            <Link href="/owner/billing">
              <Button size="sm" className="w-full h-7 text-[10px] font-bold bg-[#00ff66] hover:bg-[#00e65c] text-black rounded-lg cursor-pointer">
                Upgrade ($20/mo)
              </Button>
            </Link>
          </div>
        )}

        {/* Bottom User Profile & Sign Out */}
        <div className="pt-4 border-t border-neutral-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="h-7 w-7 rounded-full bg-neutral-800 border border-neutral-700 flex items-center justify-center text-[#00ff66] shrink-0 font-bold text-xs">
                {user?.email ? user.email[0].toUpperCase() : "O"}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-white truncate max-w-[120px]">
                  {user?.email || "Project Owner"}
                </div>
                <div className="text-[10px] text-neutral-400 font-mono">
                  {!isFree ? "Pro Plan" : "Free Tier"}
                </div>
              </div>
            </div>

            <Link href="/owner/billing">
              <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border font-bold ${!isFree
                ? "bg-[#00ff66]/10 border-[#00ff66]/40 text-[#00ff66]"
                : "bg-amber-500/10 border-amber-500/40 text-amber-400"
                }`}>
                {!isFree ? "PRO" : "FREE"}
              </span>
            </Link>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start text-xs text-neutral-400 hover:text-rose-400 hover:bg-rose-950/20 rounded-xl h-8 px-2 cursor-pointer transition-colors"
          >
            <LogOut className="h-3.5 w-3.5 mr-2" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Scoped Content */}
      <main className="flex-1 min-w-0 p-4 sm:p-6 md:p-8 max-w-7xl mx-auto w-full relative">
        {/* Subtle Brand Watermark in Bottom-Right Corner */}
        <div
          aria-hidden="true"
          className="fixed bottom-[-60px] right-[-60px] pointer-events-none z-0 opacity-[0.035] select-none drop-shadow-[0_0_50px_rgba(0,255,102,0.3)]"
        >
          <ZoeLogo variant="watermark" size={540} />
        </div>

        <div className="relative z-10">
          {children}
        </div>
      </main>

      {/* Upgrade Required Paywall Modal */}
      <Dialog open={upgradeModalOpen} onOpenChange={setUpgradeModalOpen}>
        <DialogContent className="w-[92vw] sm:max-w-md max-h-[85vh] overflow-y-auto bg-[#121212] border border-neutral-800 text-white rounded-3xl p-6">
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

          <DialogFooter className="flex flex-col sm:flex-row gap-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setUpgradeModalOpen(false)}
              className="w-full sm:w-auto text-xs text-neutral-400 hover:text-white rounded-full h-10"
            >
              Maybe Later
            </Button>
            <Link href="/owner/billing" className="w-full sm:w-auto" onClick={() => setUpgradeModalOpen(false)}>
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
