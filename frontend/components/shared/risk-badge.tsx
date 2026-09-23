import { Badge } from "@/components/ui/badge";
import type { Priority, RiskLevel } from "@/types";
import { cn } from "@/lib/utils";

const VARIANT_MAP = {
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
} as const;

export function RiskBadge({
  level,
  className,
}: {
  level: RiskLevel | Priority;
  className?: string;
}) {
  return (
    <Badge variant={VARIANT_MAP[level]} className={cn(className)}>
      {level}
    </Badge>
  );
}
