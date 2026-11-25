"use client"

import { useEffect, useState } from "react"
import {
  Image as ImageIcon,
  Sparkles,
  Download,
  Send,
  AlertCircle,
  Loader2,
  Wand2
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"

const SAMPLE_PROMPTS = [
  "A cyberpunk pirate sailing a neon spaceship through a Solana galaxy, ultra-detailed 3D render",
  "Minimalist futuristic Web3 dragon emblem in emerald green and obsidian gold, vector NFT art",
  "Steampunk astronaut ape wearing holographic visor, studio lighting, 8k digital collectible",
]

export default function NftStudioPage() {
  const [prompt, setPrompt] = useState("")
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [credits, setCredits] = useState<number | null>(null)
  const [generatedArt, setGeneratedArt] = useState<{
    prompt: string
    image_url: string
  } | null>(null)

  useEffect(() => {
    api
      .getEntitlement()
      .then((ent) => {
        if (ent) setCredits(ent.credits ?? 0)
      })
      .catch(() => {})
  }, [])

  const handleGenerate = async () => {
    const clean = prompt.trim()
    if (!clean) {
      setError("Please describe the NFT artwork you want to generate.")
      return
    }

    setGenerating(true)
    setError(null)

    try {
      const res = await api.generateNftArtwork(clean)
      setGeneratedArt({
        prompt: res.prompt || clean,
        image_url: res.image_url,
      })
      if (typeof res.credits_remaining === "number") {
        setCredits(res.credits_remaining)
      } else {
        const ent = await api.getEntitlement().catch(() => null)
        if (ent) setCredits(ent.credits ?? 0)
      }
    } catch (err: any) {
      setError(err?.message || "Failed to generate NFT artwork. Please check your credit balance.")
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = async () => {
    if (!generatedArt?.image_url) return
    try {
      const resp = await fetch(generatedArt.image_url)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `zoe-nft-${Date.now()}.png`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      window.open(generatedArt.image_url, "_blank", "noopener,noreferrer")
    }
  }

  const handleShareTelegram = () => {
    if (!generatedArt?.image_url) return
    const shareText = encodeURIComponent(`Check out this AI NFT artwork I generated with Zoe Studio: "${generatedArt.prompt}"`)
    const shareUrl = encodeURIComponent(generatedArt.image_url)
    window.open(`https://t.me/share/url?url=${shareUrl}&text=${shareText}`, "_blank", "noopener,noreferrer")
  }

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#121212] border border-[#00ff66]/30 shadow-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="h-12 w-12 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66] shrink-0">
            <ImageIcon className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
                NFT Generation Studio
              </h1>
              <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#00ff66]/15 text-[#00ff66] border border-[#00ff66]/30">
                Pillar 2 AI
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-0.5">
              Create unique Web3 collection artwork &amp; community collectibles in seconds. 20 credits per generation.
            </p>
          </div>
        </div>

        {credits !== null && (
          <div className="px-3.5 py-2 rounded-full bg-neutral-900 border border-neutral-800 text-xs font-mono text-white flex items-center gap-2 self-start sm:self-center">
            <Sparkles className="h-3.5 w-3.5 text-[#00ff66]" />
            <span>{credits.toLocaleString()} Credits</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Prompt Input Card */}
        <Card className="lg:col-span-6 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-[#00ff66]" />
              <span>Artwork Prompt</span>
            </CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              Describe your character, style, lighting, and Web3 theme.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <Textarea
              rows={5}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your NFT collection (e.g., 'A cyberpunk pirate sailing a spaceship')"
              className="bg-neutral-950 border-neutral-800 focus:border-[#00ff66] text-white text-sm rounded-2xl resize-none p-4"
            />

            <div className="space-y-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-500">
                Quick Ideas
              </span>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_PROMPTS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setPrompt(sample)}
                    className="text-left text-[11px] px-3 py-1.5 rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-[#00ff66] transition-colors cursor-pointer line-clamp-1"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="p-3.5 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            <Button
              type="button"
              onClick={handleGenerate}
              disabled={generating}
              className="w-full h-12 rounded-2xl bg-[#00ff66] hover:bg-[#00e65c] text-black font-black text-sm tracking-wide shadow-xl shadow-[#00ff66]/15 cursor-pointer"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Generating Artwork...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Artwork (20 Credits)
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Right: Output Glassmorphism Card */}
        <Card className="lg:col-span-6 bg-[#121212] border-neutral-800 rounded-3xl shadow-2xl overflow-hidden">
          <CardHeader>
            <CardTitle className="text-base font-bold text-white">Generated Collectible</CardTitle>
            <CardDescription className="text-xs text-neutral-400">
              High-resolution 1024×1024 output ready for minting or community sharing.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="rounded-2xl bg-neutral-950/60 backdrop-blur-xl border border-neutral-800/80 p-4 space-y-4">
              {generating ? (
                <div className="aspect-square w-full rounded-2xl bg-neutral-900/90 border border-neutral-800 animate-pulse flex flex-col items-center justify-center gap-3 text-neutral-400">
                  <Loader2 className="h-8 w-8 animate-spin text-[#00ff66]" />
                  <p className="text-xs font-medium text-neutral-300">Rendering 1024×1024 NFT artwork...</p>
                </div>
              ) : generatedArt ? (
                <>
                  <div className="aspect-square w-full rounded-2xl overflow-hidden border border-neutral-800 bg-black">
                    <img
                      src={generatedArt.image_url}
                      alt={generatedArt.prompt}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <p className="text-xs text-neutral-300 italic line-clamp-2">
                    &ldquo;{generatedArt.prompt}&rdquo;
                  </p>

                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <Button
                      type="button"
                      onClick={handleDownload}
                      variant="outline"
                      className="h-10 rounded-xl border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white text-xs font-bold cursor-pointer"
                    >
                      <Download className="h-3.5 w-3.5 mr-1.5 text-[#00ff66]" />
                      Download
                    </Button>
                    <Button
                      type="button"
                      onClick={handleShareTelegram}
                      className="h-10 rounded-xl bg-[#0088cc] hover:bg-[#0077b5] text-white text-xs font-bold cursor-pointer"
                    >
                      <Send className="h-3.5 w-3.5 mr-1.5" />
                      Share to Telegram
                    </Button>
                  </div>
                </>
              ) : (
                <div className="aspect-square w-full rounded-2xl border border-dashed border-neutral-800 flex flex-col items-center justify-center text-center p-6 gap-3">
                  <div className="h-14 w-14 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-500">
                    <ImageIcon className="h-7 w-7" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-neutral-300">No artwork generated yet</p>
                    <p className="text-[11px] text-neutral-500 max-w-xs">
                      Enter a prompt on the left and click &ldquo;Generate Artwork&rdquo; to create your NFT.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
