"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { getToken, getUser, isSuperAdmin } from "@/lib/api"
import { ZoeLogo } from "@/components/zoe-logo"

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
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0a0a0a] text-neutral-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
        <p className="text-xs font-semibold text-white tracking-wide">Loading Zoe Platform...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full bg-[#0a0a0a] text-white relative overflow-x-hidden">
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
    </div>
  )
}
