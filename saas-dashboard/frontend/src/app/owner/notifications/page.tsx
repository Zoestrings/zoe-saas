"use client"

import React from "react"
import { Bell } from "lucide-react"
import { PerformanceAlertsPanel } from "@/components/scanner/performance-alerts-panel"

export default function OwnerNotificationsPage() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2">
        <Bell className="w-6 h-6 text-[#00ff66]" />
        <div>
          <h1 className="text-2xl font-bold text-white">Notification Centre</h1>
          <p className="text-xs text-neutral-400">
            Real-time token performance milestones, downside alerts &amp; organization monitoring feed
          </p>
        </div>
      </div>
      <PerformanceAlertsPanel />
    </div>
  )
}
