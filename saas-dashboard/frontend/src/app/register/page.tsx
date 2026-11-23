"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Lock, Mail, ArrowRight, AlertCircle, Loader2, CheckCircle2, ShieldCheck } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ZoeLogo } from "@/components/zoe-logo"
import { api } from "@/lib/api"

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    setLoading(true)

    try {
      const res = await api.register(email.trim(), password)
      if (res.access_token) {
        if (res.user?.role === "super_admin") {
          router.push("/admin/overview")
        } else {
          router.push("/owner/dashboard")
        }
      } else {
        router.push("/login?registered=true")
      }
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#0a0a0a] bg-[radial-gradient(ellipse_at_top,_#0a281a_0%,_#061610_35%,_#0a0a0a_75%)] relative overflow-hidden font-sans">
      {/* Background atmospheric glows */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[450px] bg-gradient-to-b from-[#00ff66]/15 via-[#00d2ff]/10 to-transparent rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-100px] left-[-100px] w-96 h-96 bg-[#00ff66]/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-1/3 right-[-150px] w-80 h-80 bg-[#00d2ff]/5 rounded-full blur-[90px] pointer-events-none" />

      {/* Atmospheric watermark */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-5">
        <ZoeLogo variant="watermark" size={700} />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand Logo & Title */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="relative mb-3 group">
            <div className="absolute -inset-2 bg-gradient-to-r from-[#00ff66] to-[#00d2ff] rounded-3xl blur-xl opacity-40 group-hover:opacity-70 transition duration-500" />
            <div className="relative h-20 w-20 rounded-2xl bg-[#0f141a] border border-[#212833] flex items-center justify-center shadow-2xl">
              <ZoeLogo size={62} glow variant="mark" />
            </div>
          </div>

          <div className="flex items-center gap-2 mt-2">
            <span className="text-3xl font-black text-white tracking-tight leading-none">
              Zoe
            </span>
            <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/30 font-bold">
              Free Tier
            </span>
          </div>
          <p className="text-xs text-[#818c99] mt-1.5 font-medium tracking-wide">
            Deploy autonomous Web3 community intelligence in seconds.
          </p>
        </div>

        {/* Glassmorphic Register Card */}
        <Card className="border border-white/10 bg-[#12161c]/85 backdrop-blur-2xl shadow-2xl shadow-black/80 rounded-3xl overflow-hidden">
          <CardHeader className="space-y-1 pb-4 pt-6 px-6 sm:px-8 border-b border-[#212833]/60">
            <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
              <span>Create your account</span>
            </CardTitle>
            <CardDescription className="text-[#818c99] text-xs">
              Manage Telegram bots, AI knowledge bases, and whale alerts
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4 pt-6 px-6 sm:px-8">
              {error && (
                <div className="flex items-start gap-2.5 p-3 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs animate-in fade-in">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5 text-rose-400" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs font-semibold text-white">
                  Email Address
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3 h-4 w-4 text-[#818c99]" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="founder@project.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="pl-10 bg-[#161b22] border-[#212833] text-white placeholder:text-[#555f6d] h-10 rounded-xl focus-visible:ring-1 focus-visible:ring-[#00ff66] focus:border-[#00ff66] text-xs transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-xs font-semibold text-white">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3 h-4 w-4 text-[#818c99]" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="At least 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="pl-10 bg-[#161b22] border-[#212833] text-white placeholder:text-[#555f6d] h-10 rounded-xl focus-visible:ring-1 focus-visible:ring-[#00ff66] focus:border-[#00ff66] text-xs transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirmPassword" className="text-xs font-semibold text-white">
                  Confirm Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3 h-4 w-4 text-[#818c99]" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Repeat password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="pl-10 bg-[#161b22] border-[#212833] text-white placeholder:text-[#555f6d] h-10 rounded-xl focus-visible:ring-1 focus-visible:ring-[#00ff66] focus:border-[#00ff66] text-xs transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-1.5 pt-2 text-[11px] text-[#818c99]">
                <div className="flex items-center gap-1.5 text-[#00ff66]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Unlimited encrypted bot connections</span>
                </div>
                <div className="flex items-center gap-1.5 text-[#00ff66]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Real-time RAG & DexScreener integrations</span>
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4 pt-4 pb-6 px-6 sm:px-8">
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-extrabold h-11 text-xs rounded-xl shadow-lg shadow-[#00ff66]/20 transition-all cursor-pointer hover:scale-[1.01]"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin text-black" />
                    Creating account...
                  </>
                ) : (
                  <>
                    Create Free Account
                    <ArrowRight className="ml-2 h-4 w-4 stroke-[3]" />
                  </>
                )}
              </Button>

              <div className="text-center text-xs text-[#818c99]">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="font-bold text-[#00ff66] hover:text-[#00ff66]/80 underline underline-offset-4"
                >
                  Sign in
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>

        {/* Security Footer Notice */}
        <div className="text-center text-[11px] text-[#818c99] mt-6 flex items-center justify-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-[#00ff66]" />
          <span>Multi-Tenant Isolation & Supabase Row-Level Security</span>
        </div>
      </div>
    </div>
  )
}
