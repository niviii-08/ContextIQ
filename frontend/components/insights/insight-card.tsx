import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/shared/risk-badge";
import type { BehaviourInsight } from "@/types";
import { Flame, Repeat2, Radar, Link2, Sparkles, Activity } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const ICONS: Record<BehaviourInsight["type"], LucideIcon> = {
  FRICTION_SOURCE: Flame,
  FREQUENTLY_FORGOTTEN: Repeat2,
  HIGH_INTERRUPTION_CONTEXT: Radar,
  STRONGEST_ASSOCIATION: Link2,
  GENERAL: Sparkles,
};

export function InsightCard({ insight }: { insight: BehaviourInsight }) {
  const Icon = ICONS[insight.type] || Sparkles;

  return (
    <Card className="glass-card hover:border-indigo-500/40 transition-all duration-300 rounded-2xl p-1 shadow-2xs hover:shadow-md animate-slide-up group">
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/70 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-800 shadow-2xs transition-transform duration-300 group-hover:scale-110">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-xs font-bold text-foreground transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
              {insight.title}
            </p>
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
              {insight.type.replace(/_/g, " ")}
            </span>
          </div>
        </div>
        <RiskBadge level={insight.priority} />
      </CardHeader>
      <CardContent className="space-y-3 pt-1">
        <p className="text-xs text-muted-foreground leading-relaxed">{insight.description}</p>
        {insight.metricLabel && insight.metricValue && (
          <div className="flex items-center justify-between border-t border-border/60 pt-2.5 text-xs">
            <span className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
              <Activity className="h-3 w-3 text-indigo-500" />
              {insight.metricLabel}
            </span>
            <span className="font-mono text-xs font-bold text-foreground px-2 py-0.5 rounded-md bg-muted/60 border border-border/50">
              {insight.metricValue}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
