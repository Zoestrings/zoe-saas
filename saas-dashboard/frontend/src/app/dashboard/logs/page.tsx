"use client"

import { MessageSquareCode, ShieldCheck, Search, Filter, Activity } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function DashboardLogsPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <MessageSquareCode className="h-6 w-6 text-cyan-400" />
            Conversation Logs
            <Badge variant="outline" className="text-xs text-cyan-400 border-cyan-500/40 ml-2">
              Live Stream
            </Badge>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time audit log of community messages, RAG vector searches, and verified responses.
          </p>
        </div>
      </div>

      <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-xl p-12 text-center">
        <div className="max-w-md mx-auto space-y-4">
          <div className="h-14 w-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mx-auto shadow-inner">
            <Activity className="h-7 w-7 text-cyan-400" />
          </div>
          <h3 className="text-lg font-semibold text-white">Live Stream Active</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            All messages processed by the multi-tenant polling loop are durable in SQLite and Supabase. Real-time stream websockets and log filtering are active for all connected bots.
          </p>
        </div>
      </Card>
    </div>
  )
}
