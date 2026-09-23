"use client";

import { analyticsApi } from "@/lib/api";
import { useApiData } from "@/hooks/use-api-data";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/shared/async-states";
import { MetricCard } from "@/components/dashboard/metric-card";
import { FrictionScoreGauge } from "@/components/dashboard/friction-score-gauge";
import { formatMinutes } from "@/lib/utils";
import {
  CheckCircle2,
  XCircle,
  Shuffle,
  BellRing,
  RotateCcw,
} from "lucide-react";

export function BehaviourOverview() {
  const { data: summary, status, error, refetch } = useApiData(() =>
    analyticsApi.getDailySummary(),
  );

  return (
    <section aria-labelledby="behaviour-overview-heading">
      <div className="mb-4 flex items-baseline justify-between">
        <h2
          id="behaviour-overview-heading"
          className="text-sm font-semibold tracking-tight text-foreground"
        >
          Today&apos;s Behaviour Overview
        </h2>
      </div>

      {status === "loading" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className="sm:col-span-2 lg:col-span-1 lg:row-span-2">
            <CardContent className="flex items-center justify-center p-8">
              <Skeleton className="h-40 w-40 rounded-full" />
            </CardContent>
          </Card>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-[104px] w-full" />
          ))}
        </div>
      )}

      {status === "error" && (
        <ErrorState
          message={
            error?.message ??
            "We couldn't load today's behaviour overview."
          }
          onRetry={refetch}
        />
      )}

      {status === "success" && summary && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className="flex items-center justify-center sm:col-span-2 lg:col-span-1 lg:row-span-2">
            <CardHeader className="items-center text-center">
              <CardTitle>Friction Score</CardTitle>
              <CardDescription>
                Composite measure of forgetting, switching, and interruption
                cost today.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FrictionScoreGauge score={summary.frictionScore} />
            </CardContent>
          </Card>

          <MetricCard
            label="Tasks completed"
            value={summary.tasksCompleted}
            icon={CheckCircle2}
            delta={summary.comparedToYesterday.tasksCompletedDelta}
            deltaGoodDirection="up"
          />
          <MetricCard
            label="Tasks forgotten"
            value={summary.tasksForgotten}
            icon={XCircle}
            deltaGoodDirection="down"
            helpText="Tasks marked forgotten today"
          />
          <MetricCard
            label="Context switches"
            value={summary.contextSwitches}
            icon={Shuffle}
            deltaGoodDirection="down"
            helpText="Shifts between task contexts"
          />
          <MetricCard
            label="Interruption time"
            value={formatMinutes(summary.interruptionMinutes)}
            icon={BellRing}
            deltaGoodDirection="down"
            helpText="Time lost to interruptions"
          />
          <MetricCard
            label="Recovery cost"
            value={formatMinutes(summary.recoveryCostMinutes)}
            icon={RotateCcw}
            deltaGoodDirection="down"
            helpText="Time to regain focus after switching"
          />
        </div>
      )}
    </section>
  );
}
