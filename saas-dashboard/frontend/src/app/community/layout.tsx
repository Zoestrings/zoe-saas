"use client"

import { RoleAwareShell } from "@/components/layout/role-aware-shell"

export default function CommunityLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <RoleAwareShell loadingLabel="Loading Community Intelligence...">
      {children}
    </RoleAwareShell>
  )
}
