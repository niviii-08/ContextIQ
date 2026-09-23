"use client";

import { useEffect, useState } from "react";
import { analyticsApi } from "@/lib/api/services/analytics";
import type { DerivedMetrics } from "@/lib/api/services/analytics";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import {
  Shuffle,
  RotateCcw,
  MapPin,
  Network,
  Info,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface EnhancedContextIntelligenceProps {
  userId: string;
  periodDays?: number;
}

export function EnhancedContextIntelligence({ userId, periodDays = 30 }: EnhancedContextIntelligenceProps) {
  const [metrics, setMetrics] = useState<DerivedMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);

        const result = await analyticsApi.getDerivedMetrics(userId, periodDays);
        if (!result.error && result.data) {
          setMetrics(result.data);
        }
      } catch (err) {
        setError("Failed to load context intelligence data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, [userId, periodDays]);

  if (loading) {
    return <ContextIntelligenceSkeleton />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (!metrics) {
    return (
      <EmptyState
        title="No context data yet"
        description="Once tasks and interruptions are logged, context metrics will appear here."
      />
    );
  }

  return (
    <div className="space-y-7">
      <header className="flex flex-col justify-between gap-4 border-b border-border pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-primary">Context layer</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">Context intelligence</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">Understand the environments, repetitions, and recovery costs shaping task performance.</p>
        </div>
        <Badge variant="outline" className="w-fit font-mono normal-case">{periodDays}-day window</Badge>
      </header>

      {/* Context Metrics */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <ContextMetricCard
          label="Recovery Time"
          value={`${metrics.recovery_time.recovery_time_minutes.toFixed(1)}min`}
          icon={RotateCcw}
          description="Average time to return to paused tasks"
          color="purple"
        />
        <ContextMetricCard
          label="Context Consistency"
          value={`${(metrics.context_consistency.context_consistency * 100).toFixed(0)}%`}
          icon={MapPin}
          description="How consistently tasks use typical contexts"
          color="blue"
        />
        <ContextMetricCard
          label="Repetition Strength"
          value={`${(metrics.repetition_strength.repetition_strength * 100).toFixed(0)}%`}
          icon={Network}
          description="Strength of repeating task patterns"
          color="green"
        />
        <ContextMetricCard
          label="Context Switch Rate"
          value={`${metrics.context_switch_rate.context_switch_rate.toFixed(1)}/hr`}
          icon={Shuffle}
          description="Frequency of context switching"
          color="orange"
        />
      </div>

      {/* Context Patterns */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ContextPatternCard
          title="Context Consistency by Category"
          description="How consistently each task category uses its typical locations"
          data={metrics.context_consistency.category_scores}
          icon={MapPin}
          color="blue"
        />
        <ContextPatternCard
          title="Repetition Strength by Category"
          description="How strongly each category shows repeating patterns"
          data={metrics.repetition_strength.category_strengths}
          icon={Network}
          color="green"
        />
      </div>

      {/* Context Switching Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shuffle className="h-5 w-5 text-orange-500" />
            Context Switching Analysis
          </CardTitle>
          <CardDescription>
            Switching patterns and recovery behavior
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">Switch Rate</div>
                <div className="text-2xl font-bold text-orange-700">
                  {metrics.context_switch_rate.context_switch_rate.toFixed(1)}/hr
                </div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">Total Switches</div>
                <div className="text-2xl font-bold text-orange-700">
                  {metrics.context_switch_rate.total_switches}
                </div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">Active Hours</div>
                <div className="text-2xl font-bold text-orange-700">
                  {metrics.context_switch_rate.active_hours.toFixed(1)}h
                </div>
              </div>
            </div>

            <div className="mt-4 rounded-md border border-dashed border-border bg-muted/30 p-4">
              <div className="flex items-start gap-3">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                <p className="text-xs leading-5 text-muted-foreground">A timestamped switch series is not included in the current analytics response. The summary above uses the observed switch count and active-hour sample only.</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recovery Time Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5 text-purple-500" />
            Recovery Time Analysis
          </CardTitle>
          <CardDescription>
            Time to regain focus after interruptions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-md border border-border bg-muted/40 p-4">
              <div>
                <div className="text-sm text-muted-foreground">Average Recovery Time</div>
                <div className="font-mono text-3xl font-semibold tabular-nums text-chart-4">
                  {metrics.recovery_time.recovery_time_minutes.toFixed(1)} min
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-muted-foreground">Sample Size</div>
                <div className="font-mono text-lg font-semibold tabular-nums text-chart-4">
                  {metrics.recovery_time.sample_size}
                </div>
              </div>
            </div>

            <div className="text-sm leading-6 text-muted-foreground">
              Recovery time measures how long it takes to return to a paused task after an interruption.
              Lower values indicate better focus recovery and less cognitive switching cost.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ContextMetricCard({
  label,
  value,
  icon: Icon,
  description,
  color
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  description: string;
  color: string;
}) {
  const colorClasses = {
    purple: "text-chart-4 bg-accent border-border",
    blue: "text-chart-1 bg-accent border-border",
    green: "text-risk-low bg-muted border-border",
    orange: "text-risk-medium bg-muted border-border",
  };

  const classes = colorClasses[color as keyof typeof colorClasses] || colorClasses.blue;

  return (
    <Card className={cn("border-l-4", classes)}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
          <Icon className={cn("h-4 w-4", classes.split(" ")[0])} />
        </div>
        <div className="font-mono text-2xl font-semibold tabular-nums text-foreground">
          {value}
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {description}
        </div>
      </CardContent>
    </Card>
  );
}

function ContextPatternCard({
  title,
  description,
  data,
  icon: Icon,
  color
}: {
  title: string;
  description: string;
  data: Record<string, number>;
  icon: LucideIcon;
  color: string;
}) {
  const colorClasses = {
    blue: "bg-chart-1",
    green: "bg-risk-low",
    purple: "bg-chart-4",
    orange: "bg-risk-medium",
  };

  const bgColor = colorClasses[color as keyof typeof colorClasses] || colorClasses.blue;

  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className="h-4 w-4" />
          {title}
        </CardTitle>
        <CardDescription className="text-xs">
          {description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.map(([category, value]) => (
            <div key={category} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="font-medium">{category}</span>
                <span className="text-muted-foreground">{(value * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className={cn("h-full transition-all", bgColor)}
                  style={{ width: `${value * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ContextIntelligenceSkeleton() {
  return (
    <div className="space-y-6">
      <div className="mb-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 mt-2" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
      <Skeleton className="h-48" />
      <Skeleton className="h-48" />
    </div>
  );
}
