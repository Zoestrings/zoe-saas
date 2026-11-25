"use client"

import { RoleAwareShell } from "@/components/layout/role-aware-shell"

export default function WatchlistLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <RoleAwareShell loadingLabel="Loading Surveillance Watchlist...">
      {children}
    </RoleAwareShell>
  )
}
