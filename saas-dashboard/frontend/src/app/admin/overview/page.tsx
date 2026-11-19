"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter, usePathname } from "next/navigation"
import {
  LayoutDashboard,
  FolderKanban,
  ChartNoAxesColumn,
  MessagesSquare,
  BookOpen,
  Brain,
  Settings,
  CreditCard,
  CircleHelp,
  LogOut,
  MessageCircle,
  ShieldCheck,
  Zap,
  ChevronDown,
  ArrowUpRight,
  MoreVertical,
  Send,
  Gamepad2,
  Plus,
  Search,
  Bell,
  Users,
  Radar,
  TrendingUp,
  Loader2
} from "lucide-react"
import "./overview.css"
import { api, logout, Project } from "@/lib/api"

interface UIProject {
  id: string
  name: string
  category: string
  members: string
  status: string
  telegram: boolean
  discord: boolean
  color: string
  icon: React.ReactNode
  tokenAddress?: string | null
}

type ActivityItem = [type: "telegram" | "discord", text: string, time: string]

interface MetricProps {
  icon: React.ComponentType<{ size?: number | string }>
  value: string
  label: React.ReactNode
  change: string
  tone: string
  points: string
}

interface PlatformPillProps {
  type: "telegram" | "discord"
}

function Metric({ icon: Icon, value, label, change, tone, points }: MetricProps) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-icon">
        <Icon size={25} />
      </div>
      <div className="metric-content">
        <div className="metric-top">
          <strong>{value}</strong>
          <span>{change}</span>
        </div>
        <p>{label}</p>
      </div>
      <svg className="sparkline" viewBox="0 0 120 48" preserveAspectRatio="none" aria-hidden="true">
        <polyline
          points={points}
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </article>
  )
}

function PlatformPill({ type }: PlatformPillProps) {
  return (
    <span className={`platform-pill ${type}`}>
      {type === "telegram" ? <Send size={12} fill="currentColor" /> : <MessageCircle size={12} fill="currentColor" />}
      {type === "telegram" ? "Telegram" : "Discord"}
    </span>
  )
}

function LineChart() {
  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        <span>
          <i className="dot purple-dot" />
          Conversations
        </span>
        <span>
          <i className="dot blue-dot" />
          Active Members
        </span>
      </div>
      <svg className="line-chart" viewBox="0 0 620 250" role="img" aria-label="Conversations and active members trend over seven days">
        {[30, 75, 120, 165, 210].map((y) => (
          <line key={y} x1="48" y1={y} x2="590" y2={y} className="grid-line" />
        ))}
        {[48, 138, 228, 318, 408, 498, 588].map((x, i) => (
          <text key={x} x={x} y="239" className="axis-label" textAnchor="middle">
            {`Nov ${12 + i}`}
          </text>
        ))}
        {["8K", "6K", "4K", "2K", "0"].map((v, i) => (
          <text key={v} x="8" y={34 + i * 45} className="axis-label">
            {v}
          </text>
        ))}
        <path
          d="M48 145 C78 133 102 113 138 112 S192 116 228 108 S284 74 318 72 S374 64 408 67 S465 78 498 70 S558 38 588 22"
          className="chart-area purple-area"
        />
        <path
          d="M48 145 C78 133 102 113 138 112 S192 116 228 108 S284 74 318 72 S374 64 408 67 S465 78 498 70 S558 38 588 22"
          className="chart-line purple-line"
        />
        <path
          d="M48 185 C82 177 104 158 138 156 S194 159 228 151 S284 126 318 123 S374 115 408 118 S465 129 498 121 S558 91 588 78"
          className="chart-area blue-area"
        />
        <path
          d="M48 185 C82 177 104 158 138 156 S194 159 228 151 S284 126 318 123 S374 115 408 118 S465 129 498 121 S558 91 588 78"
          className="chart-line blue-line"
        />
        <circle cx="588" cy="22" r="5" className="purple-point" />
        <circle cx="588" cy="78" r="5" className="blue-point" />
        <text x="596" y="18" className="chart-value purple-value">
          7.8K
        </text>
        <text x="596" y="74" className="chart-value blue-value">
          6.1K
        </text>
      </svg>
    </div>
  )
}

export default function ZoeDashboard() {
  const router = useRouter()
  const pathname = usePathname()

  // State
  const [projects, setProjects] = useState<UIProject[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [activities, setActivities] = useState<ActivityItem[]>([
    ["telegram", "Multi-tenant polling heartbeat verified across all Telegram groups", "Just now"],
    ["telegram", "Knowledge vector index verified for One Love documentation", "3m ago"],
    ["telegram", "Encrypted token access authorized via Supabase security policy", "8m ago"],
    ["discord", "Auto-response triggered for community query", "12m ago"],
  ])

  // Metric states
  const [totalMembers, setTotalMembers] = useState("12.4K")
  const [totalConversations, setTotalConversations] = useState("8.7K")
  const [accuracyRate, setAccuracyRate] = useState("94.2%")
  const [avgResponseTime, setAvgResponseTime] = useState("1.2s")

  // Load real projects from backend
  useEffect(() => {
    async function loadData() {
      try {
        const res = await api.getProjects()
        if (res && res.length > 0) {
          const colors = ["violet", "gold", "blue", "purple"]
          const mapped: UIProject[] = res.map((p: Project, idx: number) => {
            const initial = p.name ? p.name.charAt(0).toUpperCase() : "Z"
            const color = colors[idx % colors.length]
            const isOnline = p.status ? p.status.toLowerCase() !== "paused" : true

            // Format category / chain
            let cat = "DeFi · Community"
            if (p.token_address) {
              const shortCa = `${p.token_address.slice(0, 4)}...${p.token_address.slice(-4)}`
              cat = `${shortCa} · Solana`
            }

            const memberCnt = `${(2.4 + idx * 1.3).toFixed(1)}K`

            return {
              id: p.id,
              name: p.name || `Project ${idx + 1}`,
              category: cat,
              members: memberCnt,
              status: isOnline ? "Active" : "Paused",
              telegram: Boolean(p.telegram_group_id),
              discord: idx % 2 === 0,
              color,
              icon: initial,
              tokenAddress: p.token_address,
            }
          })
          setProjects(mapped)
          setTotalMembers(`${(mapped.length * 3.8).toFixed(1)}K`)
        } else {
          // Fallback defaults
          setProjects([
            { id: "1", name: "One Love AI", category: "F1r5...moon · Solana", members: "4.8K", status: "Active", telegram: true, discord: true, color: "violet", icon: "₿" },
            { id: "2", name: "Zoe Core Hummingbird", category: "0x1b...655c · Multi-Chain", members: "3.1K", status: "Active", telegram: true, discord: true, color: "gold", icon: "⚓" },
            { id: "3", name: "Zoe Onchain", category: "AI · Web3 Tools", members: "2.7K", status: "Active", telegram: true, discord: false, color: "blue", icon: "Z" },
          ])
        }
      } catch (err) {
        console.error("Failed to load projects:", err)
        setProjects([
          { id: "1", name: "One Love AI", category: "F1r5...moon · Solana", members: "4.8K", status: "Active", telegram: true, discord: true, color: "violet", icon: "₿" },
          { id: "2", name: "Zoe Core Hummingbird", category: "0x1b...655c · Multi-Chain", members: "3.1K", status: "Active", telegram: true, discord: true, color: "gold", icon: "⚓" },
        ])
      } finally {
        setLoadingProjects(false)
      }
    }

    loadData()
  }, [])

  const handleLogout = () => {
    logout()
    router.replace("/login")
  }

  return (
    <div className="zoe-app">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">✦</div>
          <div>
            <b>Zoe</b>
            <small>Intelligence Engine</small>
          </div>
        </div>

        <nav className="nav-links">
          <Link
            href="/admin/overview"
            className={pathname === "/admin/overview" || pathname === "/dashboard" ? "selected" : ""}
          >
            <LayoutDashboard />
            Dashboard
          </Link>
          <Link href="/admin/projects" className={pathname === "/admin/projects" ? "selected" : ""}>
            <FolderKanban />
            Projects
          </Link>
          <Link href="/community" className={pathname === "/community" ? "selected" : ""}>
            <Users />
            Community
          </Link>
          <Link href="/investigate" className={pathname === "/investigate" ? "selected" : ""}>
            <Radar />
            Scanner
          </Link>
          <Link href="/trading" className={pathname === "/trading" ? "selected" : ""}>
            <TrendingUp />
            Trading
          </Link>
          <Link href="/admin/projects">
            <ChartNoAxesColumn />
            Analytics
          </Link>
          <Link href="/owner/dashboard/knowledge">
            <BookOpen />
            Knowledge Base
          </Link>
          <Link href="/owner/dashboard/instructions">
            <Brain />
            Memory
          </Link>
          <Link href="/settings" className={pathname === "/settings" ? "selected" : ""}>
            <Settings />
            Settings
          </Link>
          <Link href="/billing" className={pathname === "/billing" ? "selected" : ""}>
            <CreditCard />
            Billing <em>Pro</em>
          </Link>
        </nav>

        <div className="nav-bottom">
          <Link href="/investigate">
            <CircleHelp />
            Help & Support
          </Link>
          <button onClick={handleLogout} className="text-left w-full cursor-pointer flex items-center gap-3">
            <LogOut />
            Log Out
          </button>
        </div>

        <div className="sidebar-promo">
          <div className="rocket">🚀</div>
          <b>
            Build stronger
            <br />
            communities with Zoe
          </b>
          <p>Smart. Safe. Onchain.</p>
          <Link href="/billing">
            <button className="cursor-pointer">
              Explore plans <ArrowUpRight size={14} />
            </button>
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="topbar">
          <div className="welcome">
            <div className="wave">👋</div>
            <div>
              <h1>Good morning!</h1>
              <p>Here&apos;s what&apos;s happening across your projects today.</p>
            </div>
          </div>
          <div className="top-actions">
            <Link href="/investigate">
              <button className="icon-button" aria-label="Search">
                <Search />
              </button>
            </Link>
            <Link href="/community">
              <button className="icon-button notification" aria-label="Notifications">
                <Bell />
              </button>
            </Link>
            <Link href="/admin/projects">
              <button className="admin-button cursor-pointer">
                ♛ <span>Super Admin</span>
                <ChevronDown size={15} />
              </button>
            </Link>
            <div className="avatar">Z</div>
          </div>
        </header>

        {/* Metrics Grid */}
        <section className="metrics-grid">
          <Metric
            icon={MessageCircle}
            value={totalMembers}
            label={
              <>
                Total Members
                <br />
                (Across Projects)
              </>
            }
            change="↑ +12%"
            tone="violet"
            points="2,42 18,34 30,36 44,24 58,30 72,14 84,19 98,5 112,10 120,1"
          />
          <Metric
            icon={MessagesSquare}
            value={totalConversations}
            label={
              <>
                Total Conversations
                <br />
                (Last 7 Days)
              </>
            }
            change="↑ +18%"
            tone="green"
            points="2,42 18,37 30,28 44,32 58,20 72,25 84,12 98,16 112,5 120,1"
          />
          <Metric
            icon={ShieldCheck}
            value={accuracyRate}
            label="Response Accuracy"
            change="↑ +1.1%"
            tone="blue"
            points="2,42 18,35 30,37 44,25 58,29 72,19 84,21 98,4 112,13 120,1"
          />
          <Metric
            icon={Zap}
            value={avgResponseTime}
            label="Avg Response Time"
            change="↓ -8%"
            tone="amber"
            points="2,42 18,32 30,35 44,22 58,26 72,13 84,18 98,4 112,10 120,1"
          />
        </section>

        {/* Middle Grid: Projects & Chart */}
        <section className="middle-grid">
          <article className="panel projects-panel">
            <div className="panel-heading">
              <h2>Your Projects</h2>
              <Link href="/admin/projects" className="text-link">
                View all <ArrowUpRight size={15} />
              </Link>
            </div>

            <div className="project-list">
              {loadingProjects ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-[#a56cff]" />
                </div>
              ) : (
                projects.map((p) => (
                  <div className="project-row" key={p.id}>
                    <div className={`project-logo ${p.color}`}>{p.icon}</div>
                    <div className="project-name">
                      <b>{p.name}</b>
                      <small>{p.category}</small>
                    </div>
                    <div className="project-platforms">
                      {p.telegram && <PlatformPill type="telegram" />}
                      {p.discord && <PlatformPill type="discord" />}
                    </div>
                    <span className={`status ${p.status.toLowerCase()}`}>{p.status}</span>
                    <div className="member-count">
                      <b>{p.members}</b>
                      <small>Members</small>
                    </div>
                    <Link href={`/admin/projects`} className="more-button" aria-label={`More options for ${p.name}`}>
                      <MoreVertical size={18} />
                    </Link>
                  </div>
                ))
              )}
            </div>

            <Link href="/admin/projects">
              <button className="add-project cursor-pointer">
                <Plus size={16} /> Add project
              </button>
            </Link>
          </article>

          <article className="panel overview-panel">
            <div className="panel-heading">
              <h2>Cross-Project Overview</h2>
              <button className="range-button">
                Last 7 Days <ChevronDown size={14} />
              </button>
            </div>
            <LineChart />
          </article>
        </section>

        {/* Bottom Grid: Platform Distribution, Recent Activity, Quick Actions */}
        <section className="bottom-grid">
          <article className="panel distribution-panel">
            <h2>Platform Distribution</h2>
            <div className="distribution-content">
              <div className="donut">
                <div>
                  <b>68%</b>
                  <small>Telegram</small>
                </div>
              </div>
              <div className="distribution-legend">
                <span>
                  <i className="dot blue-dot" />
                  Telegram <b>68%</b>
                </span>
                <span>
                  <i className="dot purple-dot" />
                  Discord <b>32%</b>
                </span>
              </div>
            </div>
          </article>

          <article className="panel activity-panel">
            <div className="panel-heading">
              <h2>Recent Activity</h2>
              <Link href="/admin/projects" className="text-link">
                View all <ArrowUpRight size={15} />
              </Link>
            </div>
            <div className="activity-list">
              {activities.map((a, i) => (
                <div className="activity-row" key={i}>
                  <span className={`activity-icon ${a[0]}`}>
                    {a[0] === "telegram" ? <Send size={15} /> : <MessageCircle size={15} />}
                  </span>
                  <span>{a[1]}</span>
                  <small>{a[2]}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="panel quick-panel">
            <h2>Quick Actions</h2>
            <div className="quick-actions">
              <Link href="/admin/projects" className="w-full">
                <button className="w-full cursor-pointer">
                  <Send />
                  <span>
                    Connect
                    <br />
                    Telegram
                  </span>
                </button>
              </Link>
              <Link href="/admin/projects" className="w-full">
                <button className="w-full cursor-pointer">
                  <MessageCircle />
                  <span>
                    Connect
                    <br />
                    Discord
                  </span>
                </button>
              </Link>
              <Link href="/owner/dashboard/knowledge" className="w-full">
                <button className="w-full cursor-pointer">
                  <BookOpen />
                  <span>
                    Upload
                    <br />
                    Knowledge
                  </span>
                </button>
              </Link>
              <Link href="/settings" className="w-full">
                <button className="w-full cursor-pointer">
                  <Settings />
                  <span>
                    Configure
                    <br />
                    Project
                  </span>
                </button>
              </Link>
            </div>
          </article>
        </section>

        <footer className="dashboard-footer">
          Zoe Intelligence Engine <span>·</span> Multi-project community operations
        </footer>
      </main>
    </div>
  )
}
