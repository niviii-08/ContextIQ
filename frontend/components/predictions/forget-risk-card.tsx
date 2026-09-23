import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { RiskBadge } from "@/components/shared/risk-badge";
import type { ForgettingPrediction } from "@/types";
import { cn } from "@/lib/utils";

const RISK_INDICATOR: Record<ForgettingPrediction["riskLevel"], string> = {
  HIGH: "bg-risk-high",
  MEDIUM: "bg-risk-medium",
  LOW: "bg-risk-low",
};

export function ForgetRiskCard({
  prediction,
}: {
  prediction: ForgettingPrediction;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <p className="text-sm font-semibold text-foreground">
            {prediction.taskTitle}
          </p>
          <p className="mt-0.5 font-mono text-2xl font-semibold tabular-nums text-foreground">
            {prediction.riskScore}%
          </p>
        </div>
        <RiskBadge level={prediction.riskLevel} />
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress
          value={prediction.riskScore}
          aria-label={`Forget risk for ${prediction.taskTitle}: ${prediction.riskScore} percent`}
          indicatorClassName={cn(RISK_INDICATOR[prediction.riskLevel])}
        />
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Reasons
          </p>
          <ul className="space-y-2">
            {prediction.reasons.map((reason) => (
              <li key={reason.label} className="text-xs">
                <span className="font-medium text-foreground">
                  {reason.label}
                </span>
                <span className="text-muted-foreground"> — {reason.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
