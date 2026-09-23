"use client";

import { useState } from "react";
import { predictionApi } from "@/lib/api";
import { useApiData } from "@/hooks/use-api-data";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import { ForgetRiskCard } from "@/components/predictions/forget-risk-card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { RiskLevel } from "@/types";

const FILTERS: { label: string; value: RiskLevel | "ALL" }[] = [
  { label: "All", value: "ALL" },
  { label: "High", value: "HIGH" },
  { label: "Medium", value: "MEDIUM" },
  { label: "Low", value: "LOW" },
];

export function ForgetRiskPanel() {
  const [filter, setFilter] = useState<RiskLevel | "ALL">("ALL");

  const { data: predictions, status, error, refetch } = useApiData(
    () =>
      predictionApi.listPredictions(
        filter === "ALL" ? undefined : { riskLevel: filter },
      ),
    [filter],
  );

  return (
    <section aria-labelledby="forget-risk-heading">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2
            id="forget-risk-heading"
            className="text-sm font-semibold tracking-tight text-foreground"
          >
            Forget Risk
          </h2>
          <p className="text-xs text-muted-foreground">
            Tasks ranked by likelihood of being forgotten, with the model&apos;s
            reasoning.
          </p>
        </div>
        <Tabs value={filter} onValueChange={(v) => setFilter(v as RiskLevel | "ALL")}>
          <TabsList aria-label="Filter by risk level">
            {FILTERS.map((f) => (
              <TabsTrigger key={f.value} value={f.value}>
                {f.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {status === "loading" && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full" />
          ))}
        </div>
      )}

      {status === "error" && (
        <ErrorState
          message={error?.message ?? "We couldn't load forget risk predictions."}
          onRetry={refetch}
        />
      )}

      {status === "success" && predictions && predictions.length === 0 && (
        <EmptyState
          title="No predictions at this risk level"
          description="Try a different filter, or check back after more task activity."
        />
      )}

      {status === "success" && predictions && predictions.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {predictions.map((prediction) => (
            <ForgetRiskCard key={prediction.id} prediction={prediction} />
          ))}
        </div>
      )}
    </section>
  );
}
