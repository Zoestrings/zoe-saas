"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { getToken, isSuperAdmin } from "@/lib/api"
import { AdminSidebar } from "@/components/layout/admin-sidebar"
import { AdminHeader } from "@/components/layout/admin-header"
import OwnerLayout from "@/app/owner/layout"

interface RoleAwareShellProps {
  children: React.ReactNode
  loadingLabel?: string
}

export function RoleAwareShell({
  children,
  loadingLabel = "Loading Zoe Intelligence...",
}: RoleAwareShellProps) {
  const router = useRouter()
  const [role, setRole] = useState<"super_admin" | "owner" | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      router.replace("/login")
      return
    }
    setRole(isSuperAdmin() ? "super_admin" : "owner")
  }, [router])

  if (role === null) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0a0a0a] text-neutral-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">{loadingLabel}</p>
      </div>
    )
  }

  if (role === "super_admin") {
    return (
      <div className="h-screen w-full bg-[#0a0a0a] text-white flex overflow-hidden font-sans">
        <AdminSidebar />
        <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto bg-[#0a0a0a]">
          <AdminHeader />
          <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto space-y-8">
            {children}
          </main>
        </div>
      </div>
    )
  }

  return <OwnerLayout>{children}</OwnerLayout>
}
