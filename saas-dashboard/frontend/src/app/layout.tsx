import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Zoe | Autonomous Community Intelligence Engine",
  description: "Enterprise SaaS dashboard for managing autonomous Web3 community agents and live Telegram bots.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className="h-full bg-[#0b0f19] text-slate-100 font-sans antialiased">
        {children}
      </body>
    </html>
  )
}
