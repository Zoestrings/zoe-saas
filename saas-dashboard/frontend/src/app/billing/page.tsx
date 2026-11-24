"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { getToken, isSuperAdmin } from "@/lib/api"

export default function BillingRedirectPage() {
  const router = useRouter()

  useEffect(() => {
    const token = getToken()
    if (!token) {
      router.replace("/login")
    } else if (isSuperAdmin()) {
      router.replace("/admin/billing")
    } else {
      router.replace("/owner/billing")
    }
  }, [router])

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0a0a0a] text-neutral-400 gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
      <p className="text-xs font-semibold text-white tracking-wide">Redirecting to Billing & Invoices...</p>
    </div>
  )
}
