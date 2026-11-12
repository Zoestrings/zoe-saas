"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { 
  Globe, 
  FileText, 
  BrainCircuit, 
  Loader2, 
  Save, 
  ArrowLeft, 
  Trash2, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  FileCode,
  Calendar,
  Sparkles,
  Database
} from "lucide-react"

interface KnowledgeDoc {
  filename: string
  size_bytes: number
  char_count: number
  updated_at: string
  is_default: boolean
}

export default function ProjectDetail({ params }: { params: Promise<{ id: string }> | { id: string } }) {
  const [projectId, setProjectId] = useState<string>("onelove")
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([])
  const [loadingDocs, setLoadingDocs] = useState<boolean>(true)
  
  const [url, setUrl] = useState("")
  const [rawText, setRawText] = useState("")
  const [instructions, setInstructions] = useState("")
  
  const [isScraping, setIsScraping] = useState(false)
  const [isInjectingText, setIsInjectingText] = useState(false)
  const [isSavingSettings, setIsSavingSettings] = useState(false)
  const [deletingFile, setDeletingFile] = useState<string | null>(null)

  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" } | null>(null)

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const showNotification = (message: string, type: "success" | "error" = "success") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  // Resolve Next.js 15/16 dynamic route params
  useEffect(() => {
    Promise.resolve(params).then((p) => {
      if (p?.id) setProjectId(p.id)
    })
  }, [params])

  // Fetch document list & existing settings
  const fetchDocuments = async () => {
    setLoadingDocs(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/documents`)
      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents || [])
      }
    } catch {
      // Backend offline fallback
    } finally {
      setLoadingDocs(false)
    }
  }

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/settings`)
      if (res.ok) {
        const data = await res.json()
        if (data.custom_instructions) {
          setInstructions(data.custom_instructions)
        }
      }
    } catch {}
  }

  useEffect(() => {
    if (projectId) {
      fetchDocuments()
      fetchSettings()
    }
  }, [projectId])

  // Scrape and inject URL
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
      showNotification(data.message || `Scraped and indexed into FAISS successfully!`)
      setUrl("")
      await fetchDocuments()
    } catch (e: any) {
      showNotification(e.message || "Failed to scrape URL.", "error")
    } finally {
      setIsScraping(false)
    }
  }

  // Inject raw text
  const handleInjectText = async () => {
    if (!rawText.trim()) return
    setIsInjectingText(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/ingest-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText.trim() })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to inject text")
      showNotification(data.message || `Injected facts and rebuilt FAISS vector index!`)
      setRawText("")
      await fetchDocuments()
    } catch (e: any) {
      showNotification(e.message || "Failed to inject knowledge.", "error")
    } finally {
      setIsInjectingText(false)
    }
  }

  // Delete document
  const handleDeleteDoc = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}? The FAISS index will be rebuilt immediately.`)) {
      return
    }
    setDeletingFile(filename)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/documents/${encodeURIComponent(filename)}`, {
        method: "DELETE"
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to delete document")
      showNotification(data.message || `Deleted ${filename} and rebuilt index.`)
      await fetchDocuments()
    } catch (e: any) {
      showNotification(e.message || "Failed to delete document.", "error")
    } finally {
      setDeletingFile(null)
    }
  }

  // Update persona instructions
  const handleSaveSettings = async () => {
    setIsSavingSettings(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${projectId}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ custom_instructions: instructions.trim() })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to update instructions")
      showNotification(data.message || "Custom bot persona instructions updated and active!")
    } catch (e: any) {
      showNotification(e.message || "Failed to save instructions.", "error")
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
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-4 cursor-pointer"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Active Projects
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight capitalize text-white">
                {projectId} AI Knowledge & Brain
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Direct Knowledge Injection · Instant FAISS Vector Rebuilding · No Server Restart Required
              </p>
            </div>

            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/15 backdrop-blur-md text-xs text-cyan-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live FAISS Engine Connected</span>
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
            {notification.type === "success" ? (
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
            )}
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
              Knowledge Base & Documents
            </TabsTrigger>
            <TabsTrigger 
              value="instructions" 
              className="data-[state=active]:bg-white/20 data-[state=active]:text-white rounded-lg px-6 py-2 text-xs sm:text-sm text-slate-300 transition-colors"
            >
              Custom Persona Instructions
            </TabsTrigger>
          </TabsList>

          {/* KNOWLEDGE BASE TAB */}
          <TabsContent value="knowledge" className="space-y-6">
            
            {/* 1. Active Documents Table */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-300">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-white">Active Knowledge Documents</h2>
                    <p className="text-xs text-slate-400 mt-0.5">Documents indexed in the FAISS vector database for this bot.</p>
                  </div>
                </div>

                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={fetchDocuments}
                  disabled={loadingDocs}
                  className="bg-white/5 border-white/15 text-slate-300 hover:text-white hover:bg-white/10 text-xs h-8 cursor-pointer"
                >
                  <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loadingDocs ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>

              {loadingDocs ? (
                <div className="py-8 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                  <span>Loading knowledge documents...</span>
                </div>
              ) : documents.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs border border-dashed border-white/10 rounded-xl">
                  No documents found for this project. Inject facts below to train the bot.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider text-[11px]">
                        <th className="pb-3 font-semibold">Document Name</th>
                        <th className="pb-3 font-semibold">Characters</th>
                        <th className="pb-3 font-semibold">Last Ingested</th>
                        <th className="pb-3 font-semibold text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {documents.map((doc) => (
                        <tr key={doc.filename} className="hover:bg-white/5 transition-colors">
                          <td className="py-3 font-mono font-medium text-slate-200">
                            <div className="flex items-center gap-2">
                              <FileCode className="h-4 w-4 text-cyan-400 shrink-0" />
                              <span>{doc.filename}</span>
                              {doc.is_default && (
                                <span className="text-[10px] uppercase font-sans font-semibold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                  Default
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 text-slate-300">{doc.char_count.toLocaleString()} chars</td>
                          <td className="py-3 text-slate-400">{doc.updated_at}</td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDeleteDoc(doc.filename)}
                              disabled={deletingFile === doc.filename}
                              className="p-1.5 rounded-md hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                              title="Delete document and rebuild index"
                            >
                              {deletingFile === doc.filename ? (
                                <Loader2 className="h-4 w-4 animate-spin text-rose-400" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* 2. Direct Raw Text Injection Card */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-purple-500/20 text-purple-300">
                  <FileText className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Direct Knowledge Injection (Text / FAQs)</h2>
              </div>
              <p className="text-sm text-slate-300 mb-5">
                Paste new announcements, tokenomics facts, partnership updates, or team details. Clicking <strong>"Inject Knowledge"</strong> instantly vectorizes and loads them into the live bot's memory within 2 seconds.
              </p>
              <Textarea 
                placeholder="e.g. 'Hummingbird just partnered with Raydium. Contract address is 0x1b44f3514812d835eb1bdb0acb33d3ff3351655c. All stakers earn 15% APY.'" 
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="min-h-[160px] bg-black/30 border-white/15 text-white placeholder:text-slate-500 focus-visible:ring-purple-400 mb-4 text-sm"
              />
              <Button 
                onClick={handleInjectText} 
                disabled={isInjectingText || !rawText.trim()} 
                className="bg-purple-600 hover:bg-purple-500 text-white h-11 px-6 font-medium transition-colors cursor-pointer"
              >
                {isInjectingText ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <Sparkles className="mr-2 h-4 w-4" />}
                {isInjectingText ? "Vectorizing & Injecting..." : "Inject Knowledge"}
              </Button>
            </div>

            {/* 3. URL Web Scraper Card */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-300">
                  <Globe className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Ingest & Scrape from Website URL</h2>
              </div>
              <p className="text-sm text-slate-300 mb-5">
                Paste any live URL. Zoe will automatically crawl the page, remove HTML tags, extract clean paragraphs, and rebuild the FAISS vector index.
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
                  {isScraping ? "Scraping & Indexing..." : "Scrape & Inject"}
                </Button>
              </div>
            </div>

          </TabsContent>

          {/* CUSTOM INSTRUCTIONS TAB */}
          <TabsContent value="instructions">
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl p-6 sm:p-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300">
                  <BrainCircuit className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Bot Persona & Community Rules</h2>
              </div>
              <p className="text-sm text-slate-300 mb-5">
                Dictate exactly how the AI behaves in your Telegram group. Changes are applied instantly to the bot's system prompt without a restart.
              </p>
              <Textarea 
                placeholder="e.g. 'Always mention Captain Robbie Olson when asked about the team. Keep replies concise, enthusiastic, and under 3 sentences. Never give financial advice or predict future token prices.'" 
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="min-h-[220px] bg-black/30 border-white/15 text-white placeholder:text-slate-500 focus-visible:ring-emerald-400 mb-5 text-sm"
              />
              <Button 
                onClick={handleSaveSettings} 
                disabled={isSavingSettings} 
                className="bg-emerald-600 hover:bg-emerald-500 text-white h-11 px-6 font-medium transition-colors cursor-pointer"
              >
                {isSavingSettings ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <Save className="mr-2 h-4 w-4" />}
                {isSavingSettings ? "Saving Rules..." : "Update Instructions"}
              </Button>
            </div>
          </TabsContent>

        </Tabs>
      </div>
    </div>
  )
}
