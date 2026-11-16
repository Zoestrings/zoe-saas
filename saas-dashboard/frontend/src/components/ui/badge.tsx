import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-1 focus:ring-[#00ff66]",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[#00ff66] text-black font-bold",
        secondary:
          "border border-[#212833] bg-[#181d24] text-white",
        success:
          "border border-[#00ff66]/30 bg-[#00ff66]/10 text-[#00ff66] font-semibold",
        destructive:
          "border border-rose-500/30 bg-rose-500/10 text-rose-400 font-semibold",
        outline: "border border-[#212833] text-white",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
