"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import { 
  User as UserIcon, 
  Shield, 
  CreditCard, 
  Key, 
  Check, 
  Copy, 
  ExternalLink, 
  Loader2, 
  Crown, 
  Sparkles, 
  AlertCircle,
  Clock,
  RefreshCw,
  Lock
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { 
  api, 
  getUser, 
  User, 
  EntitlementResponse, 
  BillingHistoryItem 
} from "@/lib/api"

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [entitlement, setEntitlement] = useState<EntitlementResponse | null>(null)
  const [invoices, setInvoices] = useState<BillingHistoryItem[]>([])
  const [loadingBilling, setLoadingBilling] = useState(false)

  // Profile Form State
  const [displayName, setDisplayName] = useState("")
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)

  // Security Form State
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [savingPassword, setSavingPassword] = useState(false)
  const [passwordSuccessMsg, setPasswordSuccessMsg] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)

  // Copy helper
  const [copiedTx, setCopiedTx] = useState<string | null>(null)
  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedTx(id)
    setTimeout(() => setCopiedTx(null), 2000)
  }

  useEffect(() => {
    const curUser = getUser()
    if (curUser) {
      setUser(curUser)
      setDisplayName(curUser.display_name || curUser.email.split("@")[0] || "")
    }
    loadEntitlementAndInvoices()
  }, [])

  const loadEntitlementAndInvoices = async () => {
    setLoadingBilling(true)
    try {
      const [entData, invData] = await Promise.all([
        api.getEntitlement().catch(() => null),
        api.getBillingHistory().catch(() => []),
      ])
      if (entData) setEntitlement(entData)
      setInvoices(invData || [])
    } catch (err) {
      console.debug("Failed to load billing settings:", err)
    } finally {
      setLoadingBilling(false)
    }
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleanName = displayName.trim()
    if (!cleanName) {
      setProfileError("Display name cannot be empty.")
      return
    }

    setSavingProfile(true)
    setProfileError(null)
    setProfileSuccessMsg(null)

    try {
      const res = await api.updateProfile(cleanName)
      setProfileSuccessMsg(res.message || "Profile updated successfully.")
      const updated = getUser()
      if (updated) setUser(updated)
      setTimeout(() => setProfileSuccessMsg(null), 4000)
    } catch (err: any) {
      setProfileError(err.message || "Failed to update profile.")
    } finally {
      setSavingProfile(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPassword || newPassword.length < 6) {
      setPasswordError("Password must be at least 6 characters long.")
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords do not match.")
      return
    }

    setSavingPassword(true)
    setPasswordError(null)
    setPasswordSuccessMsg(null)

    try {
      const res = await api.updatePassword(newPassword)
      setPasswordSuccessMsg(res.message || "Password changed successfully.")
      setNewPassword("")
      setConfirmPassword("")
      setTimeout(() => setPasswordSuccessMsg(null), 4000)
    } catch (err: any) {
      setPasswordError(err.message || "Failed to update password.")
    } finally {
      setSavingPassword(false)
    }
  }

  const email = user?.email || "user@zoe.community"
  const initials = (displayName || email.split("@")[0]).slice(0, 2).toUpperCase() || "ZA"
  const isPro = entitlement?.is_pro || user?.role === "super_admin"

  const formatDate = (isoStr?: string | null) => {
    if (!isoStr) return "--"
    try {
      const d = new Date(isoStr)
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    } catch {
      return isoStr
    }
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="space-y-1 pb-4 border-b border-neutral-800">
        <div className="inline-flex items-center gap-2 bg-[#00ff66]/10 border border-[#00ff66]/30 px-3 py-1 rounded-full text-xs font-bold text-[#00ff66]">
          <Sparkles className="h-3.5 w-3.5" />
          User Account Center
        </div>
        <h1 className="text-3xl font-black tracking-tight text-white mt-2">
          Account Settings
        </h1>
        <p className="text-xs text-neutral-400">
          Manage your personal profile, credentials, security policies, and subscription invoice history.
        </p>
      </div>

      {/* Main Tabbed Interface */}
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="bg-[#121212] border border-neutral-800 p-1.5 rounded-2xl flex flex-wrap gap-2 w-full sm:w-auto h-auto">
          <TabsTrigger
            value="profile"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all data-[state=active]:bg-[#00ff66] data-[state=active]:text-black text-neutral-400 hover:text-white"
          >
            <UserIcon className="h-4 w-4" />
            <span>Profile</span>
          </TabsTrigger>

          <TabsTrigger
            value="security"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all data-[state=active]:bg-[#00ff66] data-[state=active]:text-black text-neutral-400 hover:text-white"
          >
            <Shield className="h-4 w-4" />
            <span>Security</span>
          </TabsTrigger>

          <TabsTrigger
            value="billing"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all data-[state=active]:bg-[#00ff66] data-[state=active]:text-black text-neutral-400 hover:text-white"
          >
            <CreditCard className="h-4 w-4" />
            <span>Billing &amp; Invoices</span>
          </TabsTrigger>
        </TabsList>

        {/* 1. Profile Tab */}
        <TabsContent value="profile" className="space-y-6 focus-visible:outline-none">
          <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden p-6 sm:p-8">
            <CardHeader className="p-0 pb-6 border-b border-neutral-800 flex flex-row items-center gap-4">
              <Avatar className="h-16 w-16 border-2 border-[#00ff66]/40 bg-neutral-900 text-white shadow-lg">
                <AvatarFallback className="text-lg font-black text-[#00ff66]">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white tracking-tight">
                    {displayName || "User Profile"}
                  </h2>
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                    user?.role === "super_admin"
                      ? "bg-[#00ff66]/20 text-[#00ff66] border-[#00ff66]/40"
                      : isPro
                        ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                        : "bg-neutral-800 text-neutral-400 border-neutral-700"
                  }`}>
                    {user?.role === "super_admin" ? "Super Admin" : isPro ? "Pro Plan" : "Free Plan"}
                  </span>
                </div>
                <p className="text-xs text-neutral-500 font-mono truncate max-w-md">{email}</p>
              </div>
            </CardHeader>

            <CardContent className="p-0 pt-6">
              <form onSubmit={handleSaveProfile} className="space-y-6 max-w-xl">
                {profileSuccessMsg && (
                  <div className="p-3.5 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
                    <Check className="h-4 w-4 shrink-0" />
                    <span>{profileSuccessMsg}</span>
                  </div>
                )}

                {profileError && (
                  <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{profileError}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="display-name" className="text-xs font-bold text-neutral-300">
                    Display Name
                  </Label>
                  <Input
                    id="display-name"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Captain Robbie"
                    className="h-11 bg-neutral-900 border-neutral-700 rounded-xl text-xs text-white focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66]"
                  />
                  <p className="text-[11px] text-neutral-500">
                    This name will appear on reports, receipts, and internal system logs.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="user-email" className="text-xs font-bold text-neutral-300">
                    Email Address
                  </Label>
                  <Input
                    id="user-email"
                    type="email"
                    value={email}
                    disabled
                    className="h-11 bg-neutral-950 border-neutral-800 rounded-xl text-xs text-neutral-400 cursor-not-allowed font-mono"
                  />
                  <p className="text-[11px] text-neutral-600">
                    Email is linked to your primary authentication provider.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs font-bold text-neutral-300">Account ID</Label>
                  <div className="h-11 px-3.5 bg-neutral-950 border border-neutral-800 rounded-xl flex items-center justify-between text-xs font-mono text-neutral-500">
                    <span>{user?.id || "anon-user-session"}</span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(user?.id || "", "account-id")}
                      className="text-neutral-500 hover:text-white transition-colors cursor-pointer"
                      title="Copy User ID"
                    >
                      {copiedTx === "account-id" ? <Check className="h-3.5 w-3.5 text-[#00ff66]" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={savingProfile}
                  className="h-11 px-6 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 transition-all flex items-center gap-2"
                >
                  {savingProfile ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Saving Changes...</span>
                    </>
                  ) : (
                    <span>Save Profile</span>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 2. Security Tab */}
        <TabsContent value="security" className="space-y-6 focus-visible:outline-none">
          <Card className="bg-[#121212] border border-neutral-800 rounded-3xl shadow-xl overflow-hidden p-6 sm:p-8">
            <CardHeader className="p-0 pb-6 border-b border-neutral-800">
              <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
                <Key className="h-5 w-5 text-[#00ff66]" />
                <span>Password &amp; Authentication</span>
              </CardTitle>
              <CardDescription className="text-xs text-neutral-400 mt-1">
                Update your login password to secure your account across the Zoe dashboard and Telegram bots.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-0 pt-6">
              <form onSubmit={handleChangePassword} className="space-y-6 max-w-xl">
                {passwordSuccessMsg && (
                  <div className="p-3.5 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-xs flex items-center gap-2">
                    <Check className="h-4 w-4 shrink-0" />
                    <span>{passwordSuccessMsg}</span>
                  </div>
                )}

                {passwordError && (
                  <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{passwordError}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="new-password" className="text-xs font-bold text-neutral-300">
                    New Password
                  </Label>
                  <Input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter at least 6 characters..."
                    className="h-11 bg-neutral-900 border-neutral-700 rounded-xl text-xs text-white focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password" className="text-xs font-bold text-neutral-300">
                    Confirm New Password
                  </Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your new password..."
                    className="h-11 bg-neutral-900 border-neutral-700 rounded-xl text-xs text-white focus:border-[#00ff66] focus:ring-1 focus:ring-[#00ff66]"
                  />
                </div>

                <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 text-xs space-y-2">
                  <span className="font-bold text-white block">Security Guidelines:</span>
                  <ul className="space-y-1 text-neutral-400 text-[11px] list-disc list-inside">
                    <li>Minimum 6 alphanumeric characters</li>
                    <li>Password changes are applied immediately across all active sessions</li>
                  </ul>
                </div>

                <Button
                  type="submit"
                  disabled={savingPassword}
                  className="h-11 px-6 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs cursor-pointer shadow-lg shadow-[#00ff66]/20 transition-all flex items-center gap-2"
                >
                  {savingPassword ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Updating Password...</span>
                    </>
                  ) : (
                    <span>Change Password</span>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 3. Billing & Invoices Tab */}
        <TabsContent value="billing" className="space-y-6 focus-visible:outline-none">
          {/* Plan Summary Banner */}
          <div className="bg-[#121212] border border-neutral-800 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2.5">
                <div className="h-10 w-10 rounded-2xl bg-[#00ff66]/10 border border-[#00ff66]/30 flex items-center justify-center text-[#00ff66]">
                  <Crown className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-white">
                      {isPro ? "Pro Intelligence Plan" : "Free Tier"}
                    </h2>
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                      isPro
                        ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                        : "bg-neutral-800 text-neutral-400 border-neutral-700"
                    }`}>
                      {isPro ? "Active Plan" : "Limited Access"}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-400 mt-0.5">
                    {isPro
                      ? `Full access to AI Analyst, Deep Wallet Tracing, and Paper Trading.`
                      : `Upgrade to unlock AI Analyst summaries, automated continuous alerts, and paper trading.`}
                  </p>
                </div>
              </div>

              {entitlement?.expires_at && (
                <div className="flex items-center gap-2 pt-2 text-xs text-neutral-400">
                  <Clock className="h-3.5 w-3.5 text-[#00ff66]" />
                  <span>Renews / Expires: <strong className="text-white font-mono">{formatDate(entitlement.expires_at)}</strong></span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3 self-start sm:self-center">
              {!isPro ? (
                <Link href="/billing">
                  <Button className="h-11 px-6 rounded-full bg-[#00ff66] hover:bg-[#00e65c] text-black font-bold text-xs shadow-lg shadow-[#00ff66]/20 cursor-pointer">
                    Upgrade to Pro ($20/mo)
                  </Button>
                </Link>
              ) : (
                <Link href="/billing">
                  <Button variant="outline" className="h-11 px-5 rounded-full border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-white text-xs font-bold cursor-pointer">
                    Manage Subscription
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Past Invoices Table */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-[#00ff66]" />
                <h3 className="text-base font-bold text-white tracking-tight">Invoice &amp; Payment History</h3>
                <span className="text-xs bg-neutral-900 text-neutral-400 px-2.5 py-0.5 rounded-full border border-neutral-800 font-mono">
                  {invoices.length} Receipts
                </span>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={loadEntitlementAndInvoices}
                disabled={loadingBilling}
                className="border-neutral-800 bg-neutral-900 hover:bg-neutral-800 text-white text-xs h-8 px-3 rounded-full cursor-pointer"
              >
                <RefreshCw className={`h-3 w-3 mr-1.5 ${loadingBilling ? "animate-spin text-[#00ff66]" : ""}`} />
                Refresh
              </Button>
            </div>

            <div className="rounded-3xl border border-neutral-800 bg-[#121212] overflow-hidden shadow-2xl">
              <Table>
                <TableHeader>
                  <TableRow className="border-b border-neutral-800 hover:bg-transparent">
                    <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                      Invoice Date
                    </TableHead>
                    <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                      Plan / Description
                    </TableHead>
                    <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                      Amount
                    </TableHead>
                    <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                      Status
                    </TableHead>
                    <TableHead className="text-neutral-400 text-xs py-3.5 px-5 font-bold uppercase tracking-wider">
                      On-Chain Tx
                    </TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {loadingBilling && invoices.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-28 text-center text-neutral-500">
                        <div className="flex items-center justify-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin text-[#00ff66]" />
                          <span className="text-xs">Loading billing receipts...</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : invoices.length > 0 ? (
                    invoices.map((inv) => {
                      const isPaid = inv.status.toLowerCase() === "paid"

                      return (
                        <TableRow
                          key={inv.id}
                          className="border-b border-neutral-800/60 hover:bg-neutral-900/60 transition-colors"
                        >
                          {/* Date */}
                          <TableCell className="py-4 px-5 text-xs text-white font-mono">
                            {formatDate(inv.date || inv.created_at)}
                          </TableCell>

                          {/* Description */}
                          <TableCell className="py-4 px-5 text-xs">
                            <span className="font-bold text-white block">
                              {inv.plan || "Pro Subscription (30 Days)"}
                            </span>
                            <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-mono">
                              Solana USDT · Monthly
                            </span>
                          </TableCell>

                          {/* Amount */}
                          <TableCell className="py-4 px-5 text-xs font-mono font-bold text-white">
                            ${(inv.amount || inv.amount_usdt || 20.0).toFixed(2)} USDT
                          </TableCell>

                          {/* Status */}
                          <TableCell className="py-4 px-5 text-xs">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                              isPaid
                                ? "bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30"
                                : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                            }`}>
                              {isPaid ? <Check className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                              <span className="capitalize">{inv.status}</span>
                            </span>
                          </TableCell>

                          {/* Tx Hash */}
                          <TableCell className="py-4 px-5 text-xs font-mono">
                            {inv.tx_hash ? (
                              <div className="inline-flex items-center gap-1.5 bg-neutral-900 border border-neutral-800 px-2.5 py-1 rounded-full text-neutral-300">
                                <a
                                  href={`https://solscan.io/tx/${inv.tx_hash}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[#00ff66] hover:underline flex items-center gap-1"
                                >
                                  <span>{inv.tx_hash.slice(0, 4)}...{inv.tx_hash.slice(-4)}</span>
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              </div>
                            ) : (
                              <span className="text-neutral-500 italic text-[11px]">Direct activation</span>
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="h-28 text-center text-neutral-500 text-xs">
                        <div className="space-y-1">
                          <p className="font-semibold text-neutral-400">No past invoices found</p>
                          <p className="text-[11px] text-neutral-600">
                            When you subscribe or renew your monthly Pro plan, receipts will appear here automatically.
                          </p>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
