"use client"

import { RoleAwareShell } from "@/components/layout/role-aware-shell"

export default function InvestigateLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <RoleAwareShell loadingLabel="Loading Zoe Intelligence...">
      {children}
    </RoleAwareShell>
  )
}
