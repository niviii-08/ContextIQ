"use client";

import { insightsApi } from "@/lib/api";
import { useApiData } from "@/hooks/use-api-data";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import { InsightCard } from "@/components/insights/insight-card";

export function InsightsPanel() {
  const { data: insights, status, error, refetch } = useApiData(() =>
    insightsApi.list(),
  );

  return (
    <section aria-labelledby="insights-heading">
      <div className="mb-4">
        <h2
          id="insights-heading"
          className="text-sm font-semibold tracking-tight text-foreground"
        >
          Behaviour Insights
        </h2>
        <p className="text-xs text-muted-foreground">
          Patterns ContextIQ has identified in how you work, forget, and get
          interrupted.
        </p>
      </div>

      {status === "loading" && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      )}

      {status === "error" && (
        <ErrorState
          message={error?.message ?? "We couldn't load behaviour insights."}
          onRetry={refetch}
        />
      )}

      {status === "success" && insights && insights.length === 0 && (
        <EmptyState
          title="No insights yet"
          description="Insights appear once ContextIQ has enough behavioural data to find patterns."
        />
      )}

      {status === "success" && insights && insights.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {insights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      )}
    </section>
  );
}
