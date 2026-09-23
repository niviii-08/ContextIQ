"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import { 
  CheckCircle, 
  XCircle, 
  Lightbulb, 
  TrendingUp,
  Clock,
  AlertTriangle
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Recommendation {
  id: string;
  title: string;
  description: string;
  evidence: string[];
  expectedBenefit: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  category: string;
  dismissed?: boolean;
  accepted?: boolean;
}

interface EnhancedRecommendationsProps {
  userId: string;
  periodDays?: number;
}

export function EnhancedRecommendations({ userId, periodDays = 30 }: EnhancedRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data - in production, this would come from the API
  useEffect(() => {
    async function loadRecommendations() {
      try {
        setLoading(true);
        setError(null);

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));

        setRecommendations([
          {
            id: "1",
            title: "Schedule high-priority tasks earlier in the week",
            description: "Your forgetting risk is 50% higher on Fridays. Move important tasks to Monday-Thursday.",
            evidence: [
              "Forgetting rate on Friday: 35% vs 23% average",
              "High-risk tasks: 12 scheduled for Friday",
              "Historical pattern: 3-week trend observed"
            ],
            expectedBenefit: "Reduce forgetting risk by ~40% for high-priority tasks",
            priority: "HIGH",
            category: "Scheduling",
          },
          {
            id: "2",
            title: "Implement focus blocks during peak interruption hours",
            description: "Interruption rate peaks between 2-4 PM. Consider blocking this time for deep work.",
            evidence: [
              "Interruption rate: 8.2/hr (2-4 PM) vs 3.1/hr average",
              "Context switches: 15% higher during this window",
              "Task completion drops 25% during peak hours"
            ],
            expectedBenefit: "Increase task completion by 20-30%",
            priority: "HIGH",
            category: "Focus Management",
          },
          {
            id: "3",
            title: "Reduce context switches for Academic tasks",
            description: "Academic tasks have the highest context switch rate. Group similar tasks together.",
            evidence: [
              "Academic switch rate: 4.2/session vs 2.1/session average",
              "Recovery time: 8.3 minutes (highest category)",
              "Forgetting correlation: r=0.67 with switch rate"
            ],
            expectedBenefit: "Reduce friction score by 15-20 points",
            priority: "MEDIUM",
            category: "Task Organization",
          },
          {
            id: "4",
            title: "Optimize workspace for Work category tasks",
            description: "Work tasks show low context consistency (45%). Establish dedicated work environment.",
            evidence: [
              "Work context consistency: 45% vs 72% average",
              "Location variance: 6 different locations used",
              "Task duration: 35% longer in inconsistent contexts"
            ],
            expectedBenefit: "Improve completion reliability by 25%",
            priority: "MEDIUM",
            category: "Environment",
          },
        ]);
      } catch (err) {
        setError("Failed to load recommendations");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadRecommendations();
  }, [userId, periodDays]);

  const handleDismiss = (id: string) => {
    setRecommendations(prev => 
      prev.map(rec => 
        rec.id === id ? { ...rec, dismissed: true } : rec
      )
    );
  };

  const handleAccept = (id: string) => {
    setRecommendations(prev => 
      prev.map(rec => 
        rec.id === id ? { ...rec, accepted: true } : rec
      )
    );
  };

  const activeRecommendations = recommendations.filter(r => !r.dismissed && !r.accepted);

  if (loading) {
    return <RecommendationsSkeleton />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (activeRecommendations.length === 0) {
    return (
      <EmptyState
        title="No active recommendations"
        description="All recommendations have been addressed or dismissed. Check back after more activity."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-foreground">Recommendations</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Personalized recommendations based on your behavioral patterns
        </p>
      </div>

      <div className="space-y-4">
        {activeRecommendations.map((rec) => (
          <RecommendationCard
            key={rec.id}
            recommendation={rec}
            onDismiss={() => handleDismiss(rec.id)}
            onAccept={() => handleAccept(rec.id)}
          />
        ))}
      </div>

      {recommendations.some(r => r.accepted) && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-green-800">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">
                {recommendations.filter(r => r.accepted).length} recommendation(s) accepted
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RecommendationCard({ 
  recommendation, 
  onDismiss, 
  onAccept 
}: { 
  recommendation: Recommendation; 
  onDismiss: () => void; 
  onAccept: () => void;
}) {
  const priorityConfig = {
    HIGH: { color: "text-red-700", bg: "bg-red-50", border: "border-red-200", icon: AlertTriangle },
    MEDIUM: { color: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-200", icon: Clock },
    LOW: { color: "text-green-700", bg: "bg-green-50", border: "border-green-200", icon: TrendingUp },
  };

  const config = priorityConfig[recommendation.priority];
  const PriorityIcon = config.icon;

  return (
    <Card className={cn("border-l-4", config.border)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <PriorityIcon className={cn("h-4 w-4", config.color)} />
              <Badge 
                variant="outline" 
                className={cn(config.bg, config.color, config.border)}
              >
                {recommendation.priority}
              </Badge>
              <Badge variant="outline" className="ml-auto">
                {recommendation.category}
              </Badge>
            </div>
            <CardTitle className="text-base">{recommendation.title}</CardTitle>
            <CardDescription className="text-sm mt-1">
              {recommendation.description}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Evidence */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Evidence</span>
          </div>
          <ul className="space-y-1">
            {recommendation.evidence.map((evidence, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="text-muted-foreground mt-1">•</span>
                {evidence}
              </li>
            ))}
          </ul>
        </div>

        {/* Expected Benefit */}
        <div className="p-3 bg-blue-50 rounded-lg border-l-2 border-blue-300">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Expected Benefit</span>
          </div>
          <p className="text-sm text-blue-800">{recommendation.expectedBenefit}</p>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button 
            onClick={onAccept}
            className="flex-1"
            size="sm"
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Accept
          </Button>
          <Button 
            onClick={onDismiss}
            variant="outline"
            className="flex-1"
            size="sm"
          >
            <XCircle className="h-4 w-4 mr-2" />
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function RecommendationsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="mb-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 mt-2" />
      </div>
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton key={i} className="h-64" />
      ))}
    </div>
  );
}
