import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatDelta } from "@/lib/utils";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export function MetricCard({
  label,
  value,
  unit,
  icon: Icon,
  delta,
  deltaGoodDirection = "down",
  helpText,
}: {
  label: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
  delta?: number;
  /** Whether a lower value (e.g. friction) or higher value (e.g. completed) is "good". */
  deltaGoodDirection?: "up" | "down";
  helpText?: string;
}) {
  const hasDelta = typeof delta === "number" && delta !== 0;
  const isIncrease = (delta ?? 0) > 0;
  const isGood = hasDelta
    ? deltaGoodDirection === "up"
      ? isIncrease
      : !isIncrease
    : null;

  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-5">
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-1.5 font-mono text-2xl font-semibold tabular-nums tracking-tight text-foreground">
            {value}
            {unit && (
              <span className="ml-1 text-sm font-normal text-muted-foreground">
                {unit}
              </span>
            )}
          </p>
          {hasDelta ? (
            <p
              className={cn(
                "mt-1 flex items-center gap-1 text-xs font-medium",
                isGood ? "text-risk-low" : "text-risk-high",
              )}
            >
              {isIncrease ? (
                <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
              ) : (
                <ArrowDownRight className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              <span className="font-mono">{formatDelta(delta ?? 0)}</span>
              <span className="text-muted-foreground">vs yesterday</span>
            </p>
          ) : helpText ? (
            <p className="mt-1 text-xs text-muted-foreground">{helpText}</p>
          ) : null}
        </div>
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent text-accent-foreground">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
      </CardContent>
    </Card>
  );
}
