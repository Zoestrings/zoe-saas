import React from "react"

interface ZoeLogoProps {
  className?: string
  size?: number | string
  variant?: "mark" | "full" | "watermark"
  withSparkle?: boolean
  glow?: boolean
  badge?: string
}

export function ZoeLogo({
  className = "",
  size = 40,
  variant = "mark",
  withSparkle = true,
  glow = false,
  badge,
}: ZoeLogoProps) {
  const numericSize = typeof size === "number" ? size : parseInt(size as string, 10) || 40

  if (variant === "watermark") {
    return (
      <svg
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        style={{ width: size, height: size }}
      >
        <defs>
          <linearGradient id="zoeWatermarkGrad" x1="20" y1="20" x2="180" y2="180" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#00ff66" />
            <stop offset="50%" stopColor="#00d2ff" />
            <stop offset="100%" stopColor="#0066ff" />
          </linearGradient>
          <filter id="zoeWatermarkGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <g filter="url(#zoeWatermarkGlow)">
          {/* Top curve ribbon */}
          <path
            d="M 35 55 C 35 38, 55 30, 85 30 L 145 30 C 165 30, 175 42, 160 58 L 75 140 C 65 150, 72 165, 95 165 L 155 165 C 175 165, 175 178, 155 178 L 70 178 C 45 178, 35 160, 52 144 L 135 62 C 145 52, 138 42, 120 42 L 55 42 C 40 42, 35 48, 35 55 Z"
            fill="url(#zoeWatermarkGrad)"
          />
          {/* 4-point Sparkle */}
          <path
            d="M 165 45 C 165 52, 170 57, 177 57 C 170 57, 165 62, 165 69 C 165 62, 160 57, 153 57 C 160 57, 165 52, 165 45 Z"
            fill="#00ffc8"
          />
        </g>
      </svg>
    )
  }

  if (variant === "full") {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        {/* Stylized Logo Mark */}
        <div
          className="relative flex items-center justify-center shrink-0"
          style={{ width: numericSize, height: numericSize }}
        >
          <svg
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-full"
          >
            <defs>
              <linearGradient id="zoeRibbonGradFull" x1="10" y1="10" x2="90" y2="90" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#00ff66" />
                <stop offset="55%" stopColor="#00d2ff" />
                <stop offset="100%" stopColor="#0055ff" />
              </linearGradient>
              <linearGradient id="zoeRibbonFoldFull" x1="30" y1="50" x2="70" y2="90" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#00bb55" />
                <stop offset="50%" stopColor="#0088cc" />
                <stop offset="100%" stopColor="#0044aa" />
              </linearGradient>
              <filter id="zoeGlowFull" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            <g filter={glow ? "url(#zoeGlowFull)" : undefined}>
              {/* Main 3D Ribbon 'Z' */}
              <path
                d="M 18 28 C 18 19, 28 15, 45 15 L 75 15 C 86 15, 91 22, 82 31 L 38 73 C 32 79, 36 86, 48 86 L 80 86 C 90 86, 90 93, 80 93 L 36 93 C 23 93, 18 83, 27 74 L 69 32 C 75 26, 71 21, 62 21 L 28 21 C 20 21, 18 24, 18 28 Z"
                fill="url(#zoeRibbonGradFull)"
              />
              {/* Fold Depth Shadow */}
              <path
                d="M 38 73 L 52 59 C 56 65, 52 74, 40 78 Z"
                fill="url(#zoeRibbonFoldFull)"
                opacity="0.6"
              />
              {/* Sparkle */}
              {withSparkle && (
                <path
                  d="M 85 24 C 85 28, 88 31, 92 31 C 88 31, 85 34, 85 38 C 85 34, 82 31, 78 31 C 82 31, 85 28, 85 24 Z"
                  fill="#00ffc8"
                />
              )}
            </g>
          </svg>
        </div>

        {/* Brand Text Typography */}
        <div className="flex flex-col select-none">
          <div className="flex items-center gap-2 leading-none">
            <span className="font-extrabold text-white tracking-tight" style={{ fontSize: numericSize * 0.58 }}>
              Zoe
            </span>
            {badge && (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-md bg-[#00ff66]/10 text-[#00ff66] border border-[#00ff66]/40 font-bold leading-none">
                {badge}
              </span>
            )}
          </div>
          <span
            className="font-bold tracking-[0.22em] text-[#00ff66] uppercase leading-tight mt-1"
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
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: numericSize, height: numericSize }}
    >
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full drop-shadow-[0_0_15px_rgba(0,255,102,0.35)]"
      >
        <defs>
          <linearGradient id="zoeRibbonGradMark" x1="12" y1="12" x2="88" y2="88" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#00ff66" />
            <stop offset="55%" stopColor="#00d2ff" />
            <stop offset="100%" stopColor="#0055ff" />
          </linearGradient>
          <filter id="zoeGlowMark" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <g filter={glow ? "url(#zoeGlowMark)" : undefined}>
          <path
            d="M 18 28 C 18 19, 28 15, 45 15 L 75 15 C 86 15, 91 22, 82 31 L 38 73 C 32 79, 36 86, 48 86 L 80 86 C 90 86, 90 93, 80 93 L 36 93 C 23 93, 18 83, 27 74 L 69 32 C 75 26, 71 21, 62 21 L 28 21 C 20 21, 18 24, 18 28 Z"
            fill="url(#zoeRibbonGradMark)"
          />
          {withSparkle && (
            <path
              d="M 85 24 C 85 28, 88 31, 92 31 C 88 31, 85 34, 85 38 C 85 34, 82 31, 78 31 C 82 31, 85 28, 85 24 Z"
              fill="#00ffc8"
            />
          )}
        </g>
      </svg>
    </div>
  )
}
