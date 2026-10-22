import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/shared/risk-badge";
import type { BehaviourInsight } from "@/types";
import { Flame, Repeat2, Radar, Link2, Sparkle } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const ICONS: Record<BehaviourInsight["type"], LucideIcon> = {
  FRICTION_SOURCE: Flame,
  FREQUENTLY_FORGOTTEN: Repeat2,
  HIGH_INTERRUPTION_CONTEXT: Radar,
  STRONGEST_ASSOCIATION: Link2,
  GENERAL: Sparkle,
};

export function InsightCard({ insight }: { insight: BehaviourInsight }) {
  const Icon = ICONS[insight.type];

  return (
    <Card className="card-hover-lift group hover:border-primary/40 transition-all duration-300 animate-slide-up">
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent text-accent-foreground shadow-xs transition-transform duration-300 group-hover:scale-110 group-hover:bg-primary group-hover:text-primary-foreground">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
          <p className="text-sm font-semibold text-foreground transition-colors group-hover:text-primary">
            {insight.title}
          </p>
        </div>
        <RiskBadge level={insight.priority} />
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground leading-relaxed">{insight.description}</p>
        {insight.metricLabel && insight.metricValue && (
          <p className="mt-3 flex items-baseline gap-2 border-t border-border pt-3">
            <span className="text-xs text-muted-foreground">
              {insight.metricLabel}
            </span>
            <span className="font-mono text-sm font-semibold text-foreground transition-transform group-hover:translate-x-0.5">
              {insight.metricValue}
            </span>
          </p>
        )}
      </CardContent>
    </Card>
  );
}
