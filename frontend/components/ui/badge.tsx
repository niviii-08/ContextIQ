import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wider transition-colors focus:outline-none uppercase font-mono backdrop-blur-xs",
  {
    variants: {
      variant: {
        default:
          "border-primary/30 bg-primary/15 text-primary shadow-xs shadow-primary/10",
        secondary:
          "border-border/80 bg-secondary/70 text-secondary-foreground",
        outline:
          "border-border/80 bg-card/60 text-foreground",
        high:
          "border-destructive/30 bg-destructive/15 text-destructive",
        medium:
          "border-amber-500/30 bg-amber-500/15 text-amber-500",
        low:
          "border-emerald-500/30 bg-emerald-500/15 text-emerald-500",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
