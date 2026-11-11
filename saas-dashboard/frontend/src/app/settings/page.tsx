import { Settings, Shield, Sliders, Database, Key } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Engine Settings
        </h2>
        <p className="text-sm text-slate-400">
          Global LLM router failover, Supabase auth keys, and safety policy parameters.
        </p>
      </div>

      <Card className="border-slate-800">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="h-4 w-4 text-cyan-400" />
            LLM Provider Configuration
          </CardTitle>
          <CardDescription>Primary and failover inference providers.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Primary LLM Provider</Label>
            <Input value="Groq (Llama-3.3-70b-versatile)" disabled className="bg-slate-950 font-mono text-xs" />
          </div>
          <div className="space-y-2">
            <Label>Failover LLM Provider</Label>
            <Input value="Anthropic (Claude 3.5 Sonnet)" disabled className="bg-slate-950 font-mono text-xs" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
