import { MessageSquareCode, ShieldCheck, Search, Filter } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function LogsPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Conversation Logs
            <Badge variant="outline" className="text-xs text-cyan-400 border-cyan-500/40">
              Live Stream
            </Badge>
          </h2>
          <p className="text-sm text-slate-400">
            Inspect raw update IDs, user pseudonym hashes, RAG similarity scores, and safety validation logs.
          </p>
        </div>
      </div>

      <Card className="border-slate-800 bg-slate-900/40 p-8 text-center">
        <div className="max-w-md mx-auto space-y-4">
          <div className="h-12 w-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mx-auto">
            <MessageSquareCode className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-semibold text-white">Full Stream Connected</h3>
          <p className="text-sm text-slate-400">
            All messages persisted in <code className="text-cyan-400 bg-slate-950 px-1.5 py-0.5 rounded">data/operational/operational.db</code> are streamed in real time. Full pagination and export will be enabled in Phase 2.
          </p>
        </div>
      </Card>
    </div>
  )
}
