"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle, CheckCircle, Clock, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ForgettingPrediction } from "@/types";

interface EnhancedPredictionCardProps {
  prediction: ForgettingPrediction;
}

export function EnhancedPredictionCard({ prediction }: EnhancedPredictionCardProps) {
  const riskConfig = {
    HIGH: { color: "text-red-700", bg: "bg-red-50", border: "border-red-200", icon: AlertTriangle },
    MEDIUM: { color: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-200", icon: Clock },
    LOW: { color: "text-green-700", bg: "bg-green-50", border: "border-green-200", icon: CheckCircle },
  };

  const config = riskConfig[prediction.riskLevel];
  const RiskIcon = config.icon;

  return (
    <Card className={cn("border-l-4", config.border)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base mb-1">{prediction.taskTitle}</CardTitle>
            <CardDescription className="text-xs">
              Model v{prediction.modelVersion}
            </CardDescription>
          </div>
          <Badge
            variant="outline"
            className={cn("ml-2", config.bg, config.color, config.border)}
          >
            {prediction.riskLevel}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Probability Visualization */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Forget Probability</span>
            <span className={cn("text-lg font-bold", config.color)}>
              {prediction.riskScore.toFixed(1)}%
            </span>
          </div>
          <Progress
            value={prediction.riskScore}
            className="h-2"
          />
        </div>

        {/* Risk Category */}
        <div className={cn("flex items-center gap-2 p-3 rounded-lg", config.bg)}>
          <RiskIcon className={cn("h-5 w-5", config.color)} />
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-900">
              {prediction.riskLevel} Risk
            </p>
            <p className="text-xs text-gray-600">
              {getRiskDescription(prediction.riskLevel)}
            </p>
          </div>
        </div>

        {/* SHAP/Explanation Factors */}
        {prediction.reasons.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Info className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Key Factors</span>
            </div>
            <div className="space-y-2">
              {prediction.reasons.map((reason) => (
                <div
                  key={reason.label}
                  className="text-xs p-2 bg-gray-50 rounded border-l-2 border-gray-300"
                >
                  <span className="font-medium">{reason.label}</span><span className="ml-1 text-muted-foreground">{reason.detail}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence/Sample Information */}
        <div className="border-t pt-3 text-xs text-muted-foreground">
          <div className="flex justify-between"><span>Generated</span><span className="font-medium">{new Date(prediction.generatedAt).toLocaleDateString()}</span></div>
        </div>
      </CardContent>
    </Card>
  );
}

function getRiskDescription(riskLevel: string): string {
  switch (riskLevel) {
    case "HIGH":
      return "High probability of forgetting - immediate attention recommended";
    case "MEDIUM":
      return "Moderate risk - consider proactive measures";
    case "LOW":
      return "Low risk - normal monitoring sufficient";
    default:
      return "";
  }
}
