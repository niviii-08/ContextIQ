"use client";

import { feedbackApi, recommendationApi } from "@/lib/api";
import { useApiData } from "@/hooks/use-api-data";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import { RecommendationCard } from "@/components/recommendations/recommendation-card";
import type { Recommendation, RecommendationOutcome } from "@/types";
import { useState } from "react";

export function RecommendationsPanel() {
  const { data: recommendations, status, error, refetch } = useApiData(() =>
    recommendationApi.list(),
  );
  const [toast, setToast] = useState<string | null>(null);

  const handleAdd = async (recommendation: Recommendation) => {
    const result = await recommendationApi.accept(
      recommendation.id,
      recommendation.suggestedTasks[0]?.title ?? "",
    );
    if (!result.error) {
      await feedbackApi.submitRecommendationOutcome(recommendation.id, "accepted");
      setToast(
        `Added "${recommendation.suggestedTasks[0]?.title}" to your tasks.`,
      );
      refetch();
    }
  };

  const handleDismiss = async (recommendation: Recommendation) => {
    const result = await recommendationApi.dismiss(recommendation.id);
    if (!result.error) {
      await feedbackApi.submitRecommendationOutcome(recommendation.id, "dismissed");
      setToast(`Dismissed suggestion for ${recommendation.context}.`);
      refetch();
    }
  };

  const handleFeedback = async (recommendation: Recommendation, outcome: RecommendationOutcome) => {
    const result = await feedbackApi.submitRecommendationOutcome(recommendation.id, outcome);
    if (!result.error) setToast(outcome === "not_useful" ? "Feedback recorded for future recommendations." : "Feedback recorded.");
  };

  return (
    <section aria-labelledby="recommendations-heading">
      <div className="mb-4">
        <h2
          id="recommendations-heading"
          className="text-sm font-semibold tracking-tight text-foreground"
        >
          One More Thing
        </h2>
        <p className="text-xs text-muted-foreground">Deterministic suggestions derived from observed behaviour, with traceable evidence and feedback capture.</p>
      </div>

      <div aria-live="polite" className="sr-only">
        {toast}
      </div>
      {toast && (
        <p className="mb-4 rounded-md border border-border bg-accent px-3 py-2 text-xs text-accent-foreground">
          {toast}
        </p>
      )}

      {status === "loading" && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      )}

      {status === "error" && (
        <ErrorState
          message={error?.message ?? "We couldn't load recommendations."}
          onRetry={refetch}
        />
      )}

      {status === "success" &&
        recommendations &&
        recommendations.length === 0 && (
          <EmptyState
            title="No suggestions right now"
            description="ContextIQ will surface suggestions here as it learns your context patterns."
          />
        )}

      {status === "success" &&
        recommendations &&
        recommendations.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {recommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onAdd={handleAdd}
                onDismiss={handleDismiss}
                onFeedback={handleFeedback}
              />
            ))}
          </div>
        )}
    </section>
  );
}
