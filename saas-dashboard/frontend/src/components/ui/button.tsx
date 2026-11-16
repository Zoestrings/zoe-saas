import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-full text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#00ff66] disabled:pointer-events-none disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        default:
          "bg-[#00ff66] text-black font-bold hover:bg-[#00e65c] shadow-lg shadow-[#00ff66]/20",
        destructive:
          "bg-rose-950/40 text-rose-400 border border-rose-800/60 hover:bg-rose-900/60",
        outline:
          "border border-[#212833] bg-[#12161c] text-white hover:bg-[#181d24] hover:border-[#2e3744]",
        secondary:
          "bg-[#181d24] text-white hover:bg-[#212833] border border-[#212833]",
        ghost: "hover:bg-[#181d24] hover:text-[#00ff66] text-[#818c99]",
        link: "text-[#00ff66] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-5 py-2",
        sm: "h-8 px-3.5 text-xs",
        lg: "h-11 px-8 text-sm",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
