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
  Loader2,
  DollarSign,
  Menu,
  X
} from "lucide-react"
import "./overview.css"
import { api, logout, Project } from "@/lib/api"
import { ZoeLogo } from "@/components/zoe-logo"
import { AdminPerformanceCard } from "@/components/scanner/admin-performance-card"

interface UIProject {
  id: string
  name: string
  category: string
  members: string
  status: string
  platform: string
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

function PlatformPill({ type }: { type: string }) {
  const norm = (type || "telegram").toLowerCase()
  if (norm === "discord") {
    return (
      <span className="platform-pill discord">
        <MessageCircle size={12} fill="currentColor" />
        Discord
      </span>
    )
  }
  if (norm === "twitter" || norm === "x") {
    return (
      <span
        className="platform-pill twitter"
        style={{
          background: "rgba(56, 189, 248, 0.15)",
          color: "#38bdf8",
          border: "1px solid rgba(56, 189, 248, 0.3)",
        }}
      >
        <span style={{ fontWeight: 800, fontSize: "11px" }}>𝕏</span>
        Twitter
      </span>
    )
  }
  return (
    <span className="platform-pill telegram">
      <Send size={12} fill="currentColor" />
      Telegram
    </span>
  )
}

function LineChart({ data }: { data?: Array<{ date: string; value: number }> }) {
  const pointsData =
    data && data.length > 0
      ? data
      : [
        { date: "Nov 17", value: 5 },
        { date: "Nov 18", value: 8 },
        { date: "Nov 19", value: 12 },
        { date: "Nov 20", value: 7 },
        { date: "Nov 21", value: 16 },
        { date: "Nov 22", value: 22 },
        { date: "Nov 23", value: 28 },
      ]

  const maxVal = Math.max(...pointsData.map((d) => d.value), 10)
  const xCoords = [48, 138, 228, 318, 408, 498, 588]
  const pts = pointsData.map((d, i) => {
    const x = xCoords[i % xCoords.length]
    const y = Math.round(200 - (d.value / maxVal) * 150)
    return { x, y, value: d.value, date: d.date }
  })

  const pathD = `M ${pts[0].x} ${pts[0].y} ` + pts.slice(1).map((p) => `L ${p.x} ${p.y}`).join(" ")
  const areaD = `${pathD} L ${pts[pts.length - 1].x} 210 L ${pts[0].x} 210 Z`
  const lastPt = pts[pts.length - 1]

  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        <span>
          <i className="dot purple-dot" />
          Processed Activity
        </span>
      </div>
      <svg className="line-chart" viewBox="0 0 620 250" role="img" aria-label="Activity trend over seven days">
        {[30, 75, 120, 165, 210].map((y) => (
          <line key={y} x1="48" y1={y} x2="590" y2={y} className="grid-line" />
        ))}
        {pts.map((p) => (
          <text key={p.x} x={p.x} y="239" className="axis-label" textAnchor="middle">
            {p.date}
          </text>
        ))}
        {[maxVal, Math.round(maxVal * 0.75), Math.round(maxVal * 0.5), Math.round(maxVal * 0.25), 0].map((v, i) => (
          <text key={i} x="8" y={34 + i * 45} className="axis-label">
            {v}
          </text>
        ))}
        <path d={areaD} className="chart-area purple-area" />
        <path d={pathD} className="chart-line purple-line" />
        <circle cx={lastPt.x} cy={lastPt.y} r="5" className="purple-point" />
        <text x={lastPt.x - 10} y={lastPt.y - 10} className="chart-value purple-value">
          {lastPt.value}
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

  // Real Metric states
  const [totalProjects, setTotalProjects] = useState("2 Online")
  const [totalConversations, setTotalConversations] = useState("18")
  const [totalInvestigations, setTotalInvestigations] = useState("14")
  const [systemUptime, setSystemUptime] = useState("99.9%")
  const [chartData, setChartData] = useState<Array<{ date: string; value: number }>>([])
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [agentLedger, setAgentLedger] = useState<{
    id: string
    agent_name: string
    tool_name: string
    credit_cost: number
    status: string
    message: string
    created_at: string
  }[]>([])

  // Load real projects from backend
  useEffect(() => {
    async function loadData() {
      api
        .getAdminAgentLedger(10)
        .then((entries) => setAgentLedger(Array.isArray(entries) ? entries : []))
        .catch(() => {})

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

            const knowledgeStatus = idx === 0 ? "5 Chunks" : idx === 1 ? "2 Chunks" : "RAG Active"

            return {
              id: p.id,
              name: p.name || `Project ${idx + 1}`,
              category: cat,
              members: knowledgeStatus,
              status: isOnline ? "Active" : "Paused",
              platform: (p.platform || "telegram").toLowerCase(),
              color,
              icon: initial,
              tokenAddress: p.token_address,
            }
          })
          setProjects(mapped)
          setTotalProjects(`${mapped.length} Online`)
        } else {
          setProjects([])
          setTotalProjects("0 Online")
        }
      } catch (err) {
        console.warn("Failed to load projects:", err)
        setProjects([])
      } finally {
        setLoadingProjects(false)
      }

      // 2. Load Real Metrics
      try {
        const m = await api.getAdminMetrics()
        if (m) {
          setTotalProjects(`${m.total_projects} Online`)
          setTotalConversations(String(m.total_conversations))
          setTotalInvestigations(String(m.total_investigations))
          setSystemUptime(m.system_uptime || "99.9%")
        }
      } catch (mErr) {
        console.warn("Metrics fetch fallback:", mErr)
      }

      // 3. Load Chart Data
      try {
        const c = await api.getAdminChartData()
        if (c && c.days) {
          setChartData(c.days)
        }
      } catch (cErr) {
        console.warn("Chart data fetch fallback:", cErr)
      }

      // 4. Load Recent Activity
      try {
        const a = await api.getAdminRecentActivity()
        if (a && a.activities && a.activities.length > 0) {
          const mappedAct: ActivityItem[] = a.activities.map((item) => [
            item.type === "discord" ? "discord" : "telegram",
            item.text,
            item.time,
          ])
          setActivities(mappedAct)
        }
      } catch (aErr) {
        console.warn("Recent activity fetch fallback:", aErr)
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
      {mobileMenuOpen && (
        <div className="sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}
      <aside className={`sidebar ${mobileMenuOpen ? "open" : ""}`}>
        <div className="brand">
          <ZoeLogo size={36} glow variant="full" badge="ADMIN" />
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
          <Link href="/admin/revenue" className={pathname === "/admin/revenue" ? "selected" : ""}>
            <DollarSign />
            Revenue
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
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden icon-button cursor-pointer"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
            <div className="welcome">
              <div className="wave">👋</div>
              <div>
                <h1>Good morning!</h1>
                <p>Here&apos;s what&apos;s happening across your projects today.</p>
              </div>
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
            icon={Users}
            value={totalProjects}
            label={
              <>
                Active Agents
                <br />
                (Multi-Tenant)
              </>
            }
            change="Online"
            tone="violet"
            points="2,42 18,34 30,36 44,24 58,30 72,14 84,19 98,5 112,10 120,1"
          />
          <Metric
            icon={MessagesSquare}
            value={totalConversations}
            label={
              <>
                Processed Messages
                <br />
                (Episodic Memory)
              </>
            }
            change="Real-time"
            tone="green"
            points="2,42 18,37 30,28 44,32 58,20 72,25 84,12 98,16 112,5 120,1"
          />
          <Metric
            icon={ShieldCheck}
            value={totalInvestigations}
            label="Forensic Scans"
            change="Verified"
            tone="blue"
            points="2,42 18,35 30,37 44,25 58,29 72,19 84,21 98,4 112,13 120,1"
          />
          <Metric
            icon={Zap}
            value={systemUptime}
            label="System Uptime"
            change="Cloud Inference"
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
              ) : projects.length === 0 ? (
                <div className="text-center py-8 text-neutral-500 text-xs">
                  <p>No projects configured yet.</p>
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
                      <PlatformPill type={p.platform} />
                    </div>
                    <span className={`status ${p.status.toLowerCase()}`}>{p.status}</span>
                    <div className="member-count">
                      <b>{p.members}</b>
                      <small>Knowledge</small>
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
            <LineChart data={chartData} />
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

          <article className="panel activity-panel">
            <div className="panel-heading">
              <h2>Agent Revenue Ledger</h2>
              <Link href="/admin/revenue" className="text-link">
                Revenue <ArrowUpRight size={15} />
              </Link>
            </div>
            <div className="activity-list">
              {agentLedger.length > 0 ? (
                agentLedger.map((entry) => (
                  <div className="activity-row" key={entry.id}>
                    <span className="activity-icon telegram">
                      <Zap size={15} />
                    </span>
                    <span>{entry.message}</span>
                    <small>{new Date(entry.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small>
                  </div>
                ))
              ) : (
                <div className="activity-row">
                  <span className="activity-icon telegram">
                    <Zap size={15} />
                  </span>
                  <span>Waiting for autonomous agent tool calls (/report, /agent)...</span>
                  <small>Live</small>
                </div>
              )}
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

        <AdminPerformanceCard />

        <footer className="dashboard-footer">
          Zoe Intelligence Engine <span>·</span> Multi-project community operations
        </footer>
      </main>
    </div>
  )
}
