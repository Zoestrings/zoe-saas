"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { getToken } from "@/lib/api"

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    const token = getToken()
    if (token) {
      router.replace("/dashboard/projects")
    } else {
      router.replace("/login")
    }
  }, [router])

  return (
    <div className="min-h-screen w-screen flex flex-col items-center justify-center bg-[#0b0f19] text-slate-400 gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
      <p className="text-sm font-medium">Redirecting to Zoe SaaS Dashboard...</p>
    </div>
  )
}
