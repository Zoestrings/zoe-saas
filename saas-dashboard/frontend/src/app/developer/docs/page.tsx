"use client"

import Link from "next/link"
import { ArrowLeft, BookOpen, Code2, Terminal } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function DeveloperDocsPage() {
  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      <div className="p-5 sm:p-6 rounded-3xl bg-[#121212] border border-[#00ff66]/30 shadow-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="h-12 w-12 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shrink-0">
            <BookOpen className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
              Zoe Developer API v1 Documentation
            </h1>
            <p className="text-xs text-neutral-400 mt-0.5">
              REST endpoints for Web3 AI chat, token security scanning, and smart contract auditing.
            </p>
          </div>
        </div>

        <Link href="/developer">
          <Button
            variant="outline"
            size="sm"
            className="border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-9 px-4 rounded-full cursor-pointer"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
            Back to API Keys
          </Button>
        </Link>
      </div>

      {/* Pricing & Auth */}
      <Card className="bg-[#121212] border-neutral-800 rounded-3xl shadow-xl">
        <CardHeader>
          <CardTitle className="text-base font-bold text-white flex items-center gap-2">
            <Code2 className="h-4 w-4 text-[#00ff66]" />
            <span>Authentication &amp; Credit Pricing</span>
          </CardTitle>
          <CardDescription className="text-xs text-neutral-400">
            Pass your secret key in the <code className="text-neutral-200">Authorization</code> header on every request.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-800">
            <span className="font-mono text-[#00ff66] font-bold">POST /api/v1/chat</span>
            <p className="text-neutral-400 mt-1">Web3 intelligence Q&amp;A routed through Zoe Engine.</p>
            <span className="inline-block mt-2 px-2 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-white font-mono text-[10px]">
              2 Credits / call
            </span>
          </div>
          <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-800">
            <span className="font-mono text-[#00ff66] font-bold">POST /api/v1/scan</span>
            <p className="text-neutral-400 mt-1">Solana &amp; EVM token risk, liquidity, and holder scan.</p>
            <span className="inline-block mt-2 px-2 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-white font-mono text-[10px]">
              15 Credits / call
            </span>
          </div>
          <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-800">
            <span className="font-mono text-[#00ff66] font-bold">POST /api/v1/audit</span>
            <p className="text-neutral-400 mt-1">Static + AI smart contract security vulnerability audit.</p>
            <span className="inline-block mt-2 px-2 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-white font-mono text-[10px]">
              50 Credits / call
            </span>
          </div>
        </CardContent>
      </Card>

      {/* cURL Example */}
      <Card className="bg-[#121212] border-neutral-800 rounded-3xl shadow-xl">
        <CardHeader>
          <CardTitle className="text-base font-bold text-white flex items-center gap-2">
            <Terminal className="h-4 w-4 text-[#00ff66]" />
            <span>cURL Example</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="p-4 rounded-2xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-[#00ff66] overflow-x-auto">
{`curl -X POST https://your-zoe-backend.up.railway.app/api/v1/scan \\
  -H "Authorization: Bearer zoe_sk_YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"contract_address": "So11111111111111111111111111111111111111112"}'`}
          </pre>
        </CardContent>
      </Card>

      {/* Python Example */}
      <Card className="bg-[#121212] border-neutral-800 rounded-3xl shadow-xl">
        <CardHeader>
          <CardTitle className="text-base font-bold text-white flex items-center gap-2">
            <Code2 className="h-4 w-4 text-[#00ff66]" />
            <span>Python Example</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="p-4 rounded-2xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-neutral-200 overflow-x-auto">
{`import requests

API_KEY = "zoe_sk_YOUR_API_KEY"
BASE_URL = "https://your-zoe-backend.up.railway.app"

resp = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"prompt": "What is SOL price and liquidity?", "project_id": "default"},
    timeout=30,
)
print(resp.json())`}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}
