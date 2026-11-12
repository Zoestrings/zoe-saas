"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Globe, FileText, BrainCircuit, Loader2, Save, ArrowLeft, CheckCircle2 } from "lucide-react"

export default function ProjectDetail({ params }: { params: Promise<{ id: string }> | { id: string } }) {
  const [projectId, setProjectId] = useState<string>("onelove")
  const [url, setUrl] = useState("")
  const [rawText, setRawText] = useState("")
  const [instructions, setInstructions] = useState("")
  
  const [isScraping, setIsScraping] = useState(false)
  const [isSavingText, setIsSavingText] = useState(false)
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" } | null>(null)

  useEffect(() => {
    Promise.resolve(params).then((p) => {
      if (p?.id) setProjectId(p.id)
    })
  }, [params])

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const showNotification = (message: string, type: "success" | "error" = "success") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 4000)
  }

  const handleScrape = async () => {
    if (!url.trim()) return
    setIsScraping(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/ingest-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to scrape URL")
      showNotification(data.message || "URL scraped and ingested into FAISS vector database successfully!")
      setUrl("")
    } catch (e: any) {
      showNotification(e.message || "Failed to scrape URL.", "error")
    } finally {
      setIsScraping(false)
    }
  }

  const handleSaveText = async () => {
    if (!rawText.trim()) return
    setIsSavingText(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/ingest-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText.trim() })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to save text")
      showNotification(data.message || "Raw text saved and indexed into FAISS vector database!")
      setRawText("")
    } catch (e: any) {
      showNotification(e.message || "Failed to save text.", "error")
    } finally {
      setIsSavingText(false)
    }
  }

  const handleSaveSettings = async () => {
    if (!instructions.trim()) return
    setIsSavingSettings(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ custom_instructions: instructions.trim() })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to update instructions")
      showNotification(data.message || "Custom bot persona instructions updated!")
    } catch (e: any) {
      showNotification(e.message || "Failed to save settings.", "error")
    } finally {
      setIsSavingSettings(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#1e1b4b] to-[#0f172a] p-6 sm:p-10 text-white">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Navigation & Header */}
        <div>
          <Link 
            href="/dashboard/projects" 
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Active Projects
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight capitalize text-white">
                {projectId} AI Configuration
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Train your bot, ingest official project knowledge, and configure bot persona rules.
              </p>
            </div>

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 backdrop-blur-md text-xs text-cyan-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Vector Engine Ready</span>
            </div>
          </div>
        </div>

        {/* Floating Notification */}
        {notification && (
          <div className={`p-4 rounded-xl border backdrop-blur-lg flex items-center gap-3 text-sm transition-all shadow-xl ${
            notification.type === "success" 
              ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-200" 
              : "bg-rose-950/80 border-rose-500/40 text-rose-200"
          }`}>
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <span>{notification.message}</span>
          </div>
        )}

        <Tabs defaultValue="knowledge" className="w-full">
          {/* Glass Tabs List */}
          <TabsList className="bg-white/5 border border-white/10 backdrop-blur-md mb-6 p-1 rounded-xl">
            <TabsTrigger 
              value="knowledge" 
              className="data-[state=active]:bg-white/20 data-[state=active]:text-white rounded-lg px-6 py-2 text-xs sm:text-sm text-slate-300 transition-colors"
            >
              Knowledge Ingestion
            </TabsTrigger>
            <TabsTrigger 
              value="instructions" 
              className="data-[state=active]:bg-white/20 data-[state=active]:text-white rounded-lg px-6 py-2 text-xs sm:text-sm text-slate-300 transition-colors"
            >
              Persona & Instructions
            </TabsTrigger>
          </TabsList>

          {/* KNOWLEDGE BASE TAB */}
          <TabsContent value="knowledge" className="space-y-6">
            
            {/* URL Scraper Card */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-300">
                  <Globe className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Ingest from Website URL</h2>
              </div>
              <p className="text-sm text-slate-300 mb-5">
                Paste your project's website link. Zoe will automatically scrape the content, remove boilerplate, and index it into her FAISS brain.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Input 
                  placeholder="https://www.onelovesailingcoin.com" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="bg-black/30 border-white/15 text-white placeholder:text-slate-500 focus-visible:ring-cyan-400 h-11 text-sm"
                />
                <Button 
                  onClick={handleScrape} 
                  disabled={isScraping || !url.trim()} 
                  className="bg-cyan-600 hover:bg-cyan-500 text-white h-11 px-6 shrink-0 font-medium transition-colors cursor-pointer"
                >
                  {isScraping ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : null}
                  {isScraping ? "Scraping..." : "Scrape & Ingest"}
                </Button>
              </div>
            </div>

            {/* Raw Text Card */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-purple-500/20 text-purple-300">
                  <FileText className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Paste Raw Text (Whitepaper, FAQs)</h2>
              </div>
              <p className="text-sm text-slate-300 mb-5">
                Copy and paste specific project facts, founder background, tokenomics, or community rules here.
              </p>
              <Textarea 
                placeholder="Paste your project details, whitepaper, or tokenomics facts here..." 
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="min-h-[160px] bg-black/30 border-white/15 text-white placeholder:text-slate-500 focus-visible:ring-purple-400 mb-4 text-sm"
              />
              <Button 
                onClick={handleSaveText} 
                disabled={isSavingText || !rawText.trim()} 
                className="bg-purple-600 hover:bg-purple-500 text-white h-11 px-6 font-medium transition-colors cursor-pointer"
              >
                {isSavingText ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : null}
                {isSavingText ? "Saving..." : "Save & Ingest Text"}
              </Button>
            </div>

          </TabsContent>

          {/* CUSTOM INSTRUCTIONS TAB */}
          <TabsContent value="instructions">
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300">
                  <BrainCircuit className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Bot Persona & Rules</h2>
              </div>
              <p className="text-sm text-slate-300 mb-5">
                Tell Zoe exactly how to behave. (e.g., "Always mention Captain Robbie when talking about the sailing boat. Never give financial advice or predict future token prices.")
              </p>
              <Textarea 
                placeholder="Enter custom persona guidelines and rules here..." 
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="min-h-[200px] bg-black/30 border-white/15 text-white placeholder:text-slate-500 focus-visible:ring-emerald-400 mb-5 text-sm"
              />
              <Button 
                onClick={handleSaveSettings} 
                disabled={isSavingSettings || !instructions.trim()} 
                className="bg-emerald-600 hover:bg-emerald-500 text-white h-11 px-6 font-medium transition-colors cursor-pointer"
              >
                {isSavingSettings ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <Save className="mr-2 h-4 w-4" />}
                {isSavingSettings ? "Updating..." : "Update Instructions"}
              </Button>
            </div>
          </TabsContent>

        </Tabs>
      </div>
    </div>
  )
}
