"use client"

import { useState, useEffect } from "react"
import { 
  Globe, 
  FileText, 
  BrainCircuit, 
  Loader2, 
  Trash2, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  Inbox,
  ArrowRight
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { api, Project, getToken } from "@/lib/api"

interface KnowledgeDoc {
  filename: string
  size_bytes: number
  char_count: number
  updated_at: string
  is_default: boolean
}

export default function OwnerKnowledgePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string>("")
  const [loadingProjects, setLoadingProjects] = useState(true)

  const [documents, setDocuments] = useState<KnowledgeDoc[]>([])
  const [loadingDocs, setLoadingDocs] = useState(false)

  const [url, setUrl] = useState("")
  const [rawText, setRawText] = useState("")

  const [isScraping, setIsScraping] = useState(false)
  const [isInjectingText, setIsInjectingText] = useState(false)
  const [deletingFile, setDeletingFile] = useState<string | null>(null)

  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" } | null>(null)

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const showNotification = (message: string, type: "success" | "error" = "success") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  const getAuthHeaders = (extra: Record<string, string> = {}) => {
    const token = getToken()
    const headers: Record<string, string> = { ...extra }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    return headers
  }

  // Load projects
  useEffect(() => {
    const load = async () => {
      setLoadingProjects(true)
      try {
        const list = await api.getProjects()
        setProjects(list || [])
        if (list && list.length > 0) {
          setSelectedProjectId(list[0].id)
        }
      } catch (err) {
        console.error("Failed to load projects:", err)
      } finally {
        setLoadingProjects(false)
      }
    }
    load()
  }, [])

  // Load documents whenever selected project changes
  const fetchDocuments = async () => {
    if (!selectedProjectId) return
    setLoadingDocs(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${selectedProjectId}/documents`, {
        headers: getAuthHeaders(),
      })
      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents || [])
      } else {
        showNotification("Failed to fetch documents.", "error")
      }
    } catch {
      showNotification("Could not reach backend service.", "error")
    } finally {
      setLoadingDocs(false)
    }
  }

  useEffect(() => {
    if (selectedProjectId) {
      fetchDocuments()
    }
  }, [selectedProjectId])

  // Scrape and inject URL
  const handleScrape = async () => {
    if (!url.trim() || !selectedProjectId) return
    setIsScraping(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${selectedProjectId}/ingest-url`, {
        method: "POST",
        headers: getAuthHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ url: url.trim() }),
      })
      const data = await res.json()
      if (res.ok) {
        showNotification(data.message || "URL successfully ingested into knowledge base.")
        setUrl("")
        fetchDocuments()
      } else {
        showNotification(data.detail || "Failed to scrape URL.", "error")
      }
    } catch {
      showNotification("Network error while scraping URL.", "error")
    } finally {
      setIsScraping(false)
    }
  }

  // Ingest raw text
  const handleInjectText = async () => {
    if (!rawText.trim() || !selectedProjectId) return
    setIsInjectingText(true)
    try {
      const res = await fetch(`${apiBase}/api/projects/${selectedProjectId}/ingest-text`, {
        method: "POST",
        headers: getAuthHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ text: rawText.trim() }),
      })
      const data = await res.json()
      if (res.ok) {
        showNotification(data.message || "Text facts successfully ingested.")
        setRawText("")
        fetchDocuments()
      } else {
        showNotification(data.detail || "Failed to inject text.", "error")
      }
    } catch {
      showNotification("Network error while injecting text.", "error")
    } finally {
      setIsInjectingText(false)
    }
  }

  // Delete document
  const handleDeleteDoc = async (filename: string) => {
    if (!selectedProjectId) return
    if (!confirm(`Are you sure you want to remove '${filename}'? This will re-index your knowledge base.`)) {
      return
    }
    setDeletingFile(filename)
    try {
      const res = await fetch(`${apiBase}/api/projects/${selectedProjectId}/documents/${encodeURIComponent(filename)}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      })
      const data = await res.json()
      if (res.ok) {
        showNotification(data.message || `Deleted ${filename}`)
        fetchDocuments()
      } else {
        showNotification(data.detail || "Failed to delete document.", "error")
      }
    } catch {
      showNotification("Network error while deleting document.", "error")
    } finally {
      setDeletingFile(null)
    }
  }

  if (loadingProjects) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-cyan-400" />
        <p className="text-xs font-medium">Loading knowledge base...</p>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="py-20 max-w-xl mx-auto text-center space-y-5">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center text-slate-500 shadow-xl">
          <Inbox className="h-8 w-8 text-slate-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-white">No Assigned Bot</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            You don&apos;t have any projects assigned yet. Please contact the Zoe platform admin to deploy your bot.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <BrainCircuit className="h-6 w-6 text-cyan-400" />
            Knowledge Base
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Feed official documents, whitepapers, and live URLs into your bot&apos;s FAISS vector brain.
          </p>
        </div>

        {projects.length > 1 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Select Bot:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-white text-xs rounded-md px-3 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Notifications */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center gap-3 text-xs backdrop-blur-md shadow-lg ${
            notification.type === "success"
              ? "bg-emerald-950/60 border-emerald-800/80 text-emerald-300"
              : "bg-rose-950/60 border-rose-800/80 text-rose-300"
          }`}
        >
          {notification.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Ingestion Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scrape URL Card */}
        <Card className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden backdrop-blur-sm shadow-xl">
          <CardHeader className="p-6 pb-4">
            <div className="flex items-center gap-2 text-cyan-400 mb-1">
              <Globe className="h-4 w-4" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Web Scraping</span>
            </div>
            <CardTitle className="text-base font-bold text-white">Ingest Public Webpage</CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Scrapes readable text from any website or blog and indexes it into FAISS.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 pt-0 space-y-4">
            <div className="space-y-2">
              <Input
                placeholder="https://docs.yourproject.io/tokenomics"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isScraping}
                className="bg-slate-950/80 border-slate-800 text-white text-xs h-9 focus:border-cyan-500"
              />
            </div>
            <Button
              onClick={handleScrape}
              disabled={isScraping || !url.trim()}
              className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-9 px-4 font-medium cursor-pointer"
            >
              {isScraping ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                  Scraping & Indexing...
                </>
              ) : (
                <>
                  <Globe className="h-3.5 w-3.5 mr-1.5" />
                  Scrape & Ingest URL
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Ingest Raw Text Card */}
        <Card className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden backdrop-blur-sm shadow-xl">
          <CardHeader className="p-6 pb-4">
            <div className="flex items-center gap-2 text-indigo-400 mb-1">
              <FileText className="h-4 w-4" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Direct Knowledge</span>
            </div>
            <CardTitle className="text-base font-bold text-white">Inject Quick Facts</CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Paste announcements, tokenomics, or FAQs to instantly update your bot&apos;s memory.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 pt-0 space-y-4">
            <Textarea
              placeholder="e.g. The staking program starts on Dec 1st. Lock tokens for 30 days to earn 15% APY..."
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              disabled={isInjectingText}
              rows={3}
              className="bg-slate-950/80 border-slate-800 text-white text-xs focus:border-indigo-500 min-h-[80px]"
            />
            <Button
              onClick={handleInjectText}
              disabled={isInjectingText || !rawText.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs h-9 px-4 font-medium cursor-pointer"
            >
              {isInjectingText ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                  Indexing Memory...
                </>
              ) : (
                <>
                  <FileText className="h-3.5 w-3.5 mr-1.5" />
                  Save to Vector Brain
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Indexed Documents Table */}
      <Card className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden backdrop-blur-sm shadow-xl">
        <CardHeader className="p-6 border-b border-slate-800/60 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold text-white">Indexed Knowledge Files</CardTitle>
            <CardDescription className="text-xs text-slate-400 mt-0.5">
              Source documents powering semantic search in FAISS.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDocuments}
            disabled={loadingDocs}
            className="border-slate-800 bg-slate-950/60 hover:bg-slate-800 text-slate-300 text-xs h-8 cursor-pointer"
          >
            <RefreshCw className={`h-3 w-3 mr-1.5 ${loadingDocs ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </CardHeader>

        <CardContent className="p-0">
          {loadingDocs ? (
            <div className="py-12 flex justify-center items-center text-slate-500 text-xs gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
              Loading documents...
            </div>
          ) : documents.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No knowledge documents indexed yet. Ingest a URL or inject facts above.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              {documents.map((doc) => (
                <div
                  key={doc.filename}
                  className="p-4 sm:px-6 flex items-center justify-between hover:bg-slate-800/20 transition-colors text-xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 shrink-0">
                      <FileText className="h-4 w-4 text-cyan-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-200">{doc.filename}</span>
                        {doc.is_default && (
                          <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700 px-1.5 py-0.2 rounded">
                            Core
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-3">
                        <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span>{doc.char_count.toLocaleString()} chars</span>
                        <span>•</span>
                        <span>{doc.updated_at}</span>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={deletingFile === doc.filename}
                    onClick={() => handleDeleteDoc(doc.filename)}
                    className="text-slate-500 hover:text-rose-400 hover:bg-rose-950/20 h-8 w-8 p-0 cursor-pointer"
                    title="Delete document and re-index"
                  >
                    {deletingFile === doc.filename ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-rose-400" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

