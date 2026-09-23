"use client";

import { contextApi } from "@/lib/api";
import { useApiData } from "@/hooks/use-api-data";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import { MetricCard } from "@/components/dashboard/metric-card";
import { FocusInterruptionChart } from "@/components/analytics/focus-interruption-chart";
import { InterruptionCategoryChart } from "@/components/analytics/interruption-category-chart";
import { formatMinutes } from "@/lib/utils";
import { Clock, BellRing, Shuffle, RotateCcw } from "lucide-react";

export function ContextIntelligenceView() {
  const { data: metrics, status, error, refetch } = useApiData(() =>
    contextApi.getMetrics(),
  );

  if (status === "loading") {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[104px] w-full" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <ErrorState
        message={error?.message ?? "We couldn't load context intelligence data."}
        onRetry={refetch}
      />
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
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Focus time"
          value={formatMinutes(metrics.focusMinutes)}
          icon={Clock}
          helpText="Uninterrupted working time today"
        />
        <MetricCard
          label="Interruption time"
          value={formatMinutes(metrics.interruptionMinutes)}
          icon={BellRing}
          helpText="Total time lost to interruptions"
        />
        <MetricCard
          label="Context switches"
          value={metrics.contextSwitches}
          icon={Shuffle}
          helpText="Shifts between task contexts today"
        />
        <MetricCard
          label="Recovery cost"
          value={formatMinutes(metrics.recoveryCostMinutes)}
          icon={RotateCcw}
          helpText="Time to regain focus after switching"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Focus vs. interruption, by hour</CardTitle>
            <CardDescription>
              Where in the day focus is gained and lost.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FocusInterruptionChart data={metrics.byHour} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Interruption categories</CardTitle>
            <CardDescription>
              Top category: <span className="font-medium text-foreground">{metrics.topInterruptionCategory}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <InterruptionCategoryChart data={metrics.byCategory} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Most affected task category</CardTitle>
          <CardDescription>
            The task category most disrupted by interruptions and context
            switching today.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="font-mono text-lg font-semibold text-foreground">
            {metrics.mostAffectedTaskCategory}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
