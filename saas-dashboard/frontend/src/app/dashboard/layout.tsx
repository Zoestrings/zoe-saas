"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { getToken, getUser, isSuperAdmin } from "@/lib/api"
import { AdminSidebar } from "@/components/layout/admin-sidebar"
import { AdminHeader } from "@/components/layout/admin-header"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    const token = getToken()
    const user = getUser()
    if (!token) {
      router.replace("/login")
    } else if (user && user.role !== "super_admin") {
      router.replace("/owner/dashboard")
    } else {
      setIsAuthenticated(true)
    }
  }, [router])

  if (isAuthenticated === null) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-background text-muted-foreground gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-foreground" />
        <p className="text-sm font-medium">Verifying session...</p>
      </div>
    )
  }

  return (
    <div className="h-screen w-full bg-background text-foreground flex overflow-hidden font-sans">
      <AdminSidebar />
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto bg-slate-50/60">
        <AdminHeader />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
