"use client";

import { useState } from "react";
import { MapPin, AlertTriangle, Check, X, ThumbsUp, ThumbsDown, ShieldCheck, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Recommendation, RecommendationAcceptanceStats, RecommendationOutcome } from "@/types";

export function RecommendationCard({
  recommendation,
  onAdd,
  onDismiss,
  onFeedback,
}: {
  recommendation: Recommendation;
  onAdd: (recommendation: Recommendation) => Promise<void> | void;
  onDismiss: (recommendation: Recommendation) => Promise<void> | void;
  onFeedback: (recommendation: Recommendation, outcome: RecommendationOutcome) => Promise<void> | void;
}) {
  const [pending, setPending] = useState<"add" | "dismiss" | null>(null);

  const handleAdd = async () => {
    setPending("add");
    await onAdd(recommendation);
    setPending(null);
  };

  const handleDismiss = async () => {
    setPending("dismiss");
    await onDismiss(recommendation);
    setPending(null);
  };

  const handleFeedback = async (outcome: RecommendationOutcome) => {
    setPending("dismiss");
    await onFeedback(recommendation, outcome);
    setPending(null);
  };

  return (
    <Card>
      <CardHeader className="space-y-1">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-primary">
          One more thing?
        </p>
        <div className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <MapPin className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
          {recommendation.context}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border border-border bg-muted/30 p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-foreground"><ShieldCheck className="h-3.5 w-3.5 text-primary" aria-hidden="true" /> Why this was suggested</div>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">{recommendation.triggeringBehaviour}</p>
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div><p className="text-muted-foreground">Evidence strength</p><p className="font-mono font-semibold tabular-nums">{(recommendation.evidenceStrength * 100).toFixed(0)}%</p></div>
            <div><p className="text-muted-foreground">Risk / impact</p><p className="font-mono font-semibold tabular-nums">{(recommendation.impactScore * 100).toFixed(0)}%</p></div>
          </div>
          {recommendation.evidence.length > 0 && <ul className="mt-3 space-y-1 border-t border-border pt-2">{recommendation.evidence.map((item) => <li key={`${item.source}-${item.field}`} className="text-[11px] text-muted-foreground"><span className="font-medium text-foreground">{item.field.replaceAll("_", " ")}</span>: {item.value} <span className="opacity-70">({item.source})</span></li>)}</ul>}
        </div>

        <AcceptanceBadge stats={recommendation.acceptanceStats} />

        <div>
          <p className="text-xs text-muted-foreground">
            You frequently complete these tasks here:
          </p>
          <ul className="mt-1.5 flex flex-wrap gap-1.5">
            {recommendation.reliableTasks.map((title) => (
              <li
                key={title}
                className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-foreground"
              >
                {title}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <AlertTriangle className="h-3.5 w-3.5 text-risk-medium" aria-hidden="true" />
            Deterministic action:
          </p>
          <p className="mt-1.5 text-sm font-medium">{recommendation.expectedBenefit}</p>
          <ul className="mt-2 space-y-1">
            {recommendation.suggestedTasks.map((suggestion) => (
              <li key={suggestion.title} className="text-sm">
                <span className="font-medium text-foreground">
                  {suggestion.title}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {suggestion.reason}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex gap-2 pt-1">
          <Button
            size="sm"
            onClick={handleAdd}
            disabled={pending !== null}
            aria-label={`Add suggested task for ${recommendation.context}`}
          >
            <Check className="h-3.5 w-3.5" aria-hidden="true" />
            {pending === "add" ? "Adding…" : "Add"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleDismiss}
            disabled={pending !== null}
            aria-label={`Dismiss suggestion for ${recommendation.context}`}
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
            {pending === "dismiss" ? "Dismissing…" : "Dismiss"}
          </Button>
        </div>
        <div className="flex items-center justify-between border-t border-border pt-3">
          <span className="text-[11px] text-muted-foreground">Was this useful?</span>
          <div className="flex gap-1">
            <Button size="icon" variant="ghost" onClick={() => void handleFeedback("useful")} disabled={pending !== null} aria-label="Mark recommendation useful"><ThumbsUp className="h-3.5 w-3.5" aria-hidden="true" /></Button>
            <Button size="icon" variant="ghost" onClick={() => void handleFeedback("not_useful")} disabled={pending !== null} aria-label="Mark recommendation not useful"><ThumbsDown className="h-3.5 w-3.5" aria-hidden="true" /></Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AcceptanceBadge({ stats }: { stats: RecommendationAcceptanceStats | undefined }) {
  if (!stats) return null;
  const total = stats.accepted + stats.dismissed;
  if (total <= 0) return null;
  const rate = stats.accepted / total;
  const strong = rate >= 0.8;
  return (
    <div className="flex items-center gap-2 rounded-md border border-border px-3 py-2">
      <TrendingUp
        className={strong ? "h-3.5 w-3.5 text-risk-low" : "h-3.5 w-3.5 text-muted-foreground"}
        aria-hidden="true"
      />
      <Badge
        variant={strong ? "low" : "outline"}
        className="gap-1 px-2 py-0.5 font-mono text-[10px] normal-case"
      >
        Accepted {stats.accepted}/{total} times
      </Badge>
      {strong && (
        <span className="text-[10px] font-medium text-risk-low">
          High-signal pattern
        </span>
      )}
    </div>
  );
}
