"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { getToken, getUser, isSuperAdmin } from "@/lib/api"

export default function AdminLayout({
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
    } else if (!isSuperAdmin()) {
      router.replace("/owner/dashboard")
    } else {
      setIsAuthenticated(true)
    }
  }, [router])

  if (isAuthenticated === null) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0b0e1c] text-neutral-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#a56cff]" />
        <p className="text-xs font-semibold text-white tracking-wide">Loading Zoe Platform...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full bg-[#0b0e1c] text-white">
      {children}
    </div>
  )
}
