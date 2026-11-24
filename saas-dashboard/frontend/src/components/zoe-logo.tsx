import React from "react"
import Image from "next/image"

interface ZoeLogoProps {
  className?: string
  size?: number | string
  variant?: "mark" | "full" | "app-icon" | "watermark" | "horizontal" | "monochrome"
  withSparkle?: boolean
  glow?: boolean
  badge?: string
}

export function ZoeLogo({
  className = "",
  size = 40,
  variant = "mark",
  glow = false,
  badge,
}: ZoeLogoProps) {
  const numericSize = typeof size === "number" ? size : parseInt(size as string, 10) || 40

  if (variant === "watermark") {
    return (
      <div
        className={`pointer-events-none select-none ${className}`}
        style={{ width: size, height: size }}
      >
        <Image
          src="/zoe-mark.png"
          alt="Zoe Watermark"
          width={numericSize}
          height={numericSize}
          className="w-full h-full object-contain opacity-5 filter drop-shadow-[0_0_20px_rgba(0,229,153,0.2)]"
        />
      </div>
    )
  }

  if (variant === "app-icon") {
    return (
      <div
        className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
        style={{ width: numericSize, height: numericSize }}
      >
        <Image
          src="/zoe-app-icon.png"
          alt="Zoe App Icon"
          width={numericSize}
          height={numericSize}
          className="w-full h-full object-contain rounded-2xl shadow-lg shadow-[#00e599]/15"
        />
      </div>
    )
  }

  if (variant === "monochrome") {
    return (
      <div
        className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
        style={{ width: numericSize, height: numericSize }}
      >
        <Image
          src="/zoe-monochrome.png"
          alt="Zoe Monochrome"
          width={numericSize}
          height={numericSize}
          className="w-full h-full object-contain"
          priority
        />
      </div>
    )
  }

  if (variant === "horizontal") {
    return (
      <div className={`relative inline-flex items-center ${className}`}>
        <Image
          src="/zoe-brand-full.png"
          alt="Zoe Intelligence"
          width={numericSize * 3.5}
          height={numericSize}
          className="h-auto max-h-[48px] w-auto object-contain"
          priority
        />
      </div>
    )
  }

  if (variant === "full") {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        {/* 3D Ribbon 'Z' Brand Mark with Green-Cyan Gradient and Mint Sparkle */}
        <div
          className={`relative flex items-center justify-center shrink-0 ${
            glow ? "drop-shadow-[0_0_12px_rgba(0,229,153,0.35)]" : ""
          }`}
          style={{ width: numericSize, height: numericSize }}
        >
          <Image
            src="/zoe-mark.png"
            alt="Zoe Mark"
            width={numericSize}
            height={numericSize}
            className="w-full h-full object-contain"
            priority
          />
        </div>

        {/* Brand Text Typography Matching Official Brand Kit */}
        <div className="flex flex-col select-none leading-none">
          <div className="flex items-center gap-2">
            <span
              className="font-extrabold text-white tracking-tight font-sans"
              style={{ fontSize: Math.max(16, numericSize * 0.58) }}
            >
              Zoe
            </span>
            {badge && (
              <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-[#00e599] border border-emerald-500/30 font-bold tracking-wider leading-none shadow-sm shadow-[#00e599]/10">
                {badge}
              </span>
            )}
          </div>
          <span
            className="font-bold tracking-[0.24em] text-[#00f0ff] uppercase mt-1 leading-none font-sans"
            style={{ fontSize: Math.max(9, numericSize * 0.22) }}
          >
            Intelligence
          </span>
        </div>
      </div>
    )
  }

  // Default 'mark' variant
  return (
    <div
      className={`relative inline-flex items-center justify-center shrink-0 ${
        glow ? "drop-shadow-[0_0_15px_rgba(0,229,153,0.35)]" : ""
      } ${className}`}
      style={{ width: numericSize, height: numericSize }}
    >
      <Image
        src="/zoe-mark.png"
        alt="Zoe Mark"
        width={numericSize}
        height={numericSize}
        className="w-full h-full object-contain"
        priority
      />
    </div>
  )
}
