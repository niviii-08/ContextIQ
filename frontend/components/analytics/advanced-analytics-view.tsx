"use client";

import { useEffect, useState } from "react";
import { analyticsApi } from "@/lib/api/services/analytics";
import type { DerivedMetrics, AllInsights, StoryAnalytics } from "@/lib/api/services/analytics";

export function AdvancedAnalyticsView({ userId }: { userId: string }) {
  const [metrics, setMetrics] = useState<DerivedMetrics | null>(null);
  const [insights, setInsights] = useState<AllInsights | null>(null);
  const [story, setStory] = useState<StoryAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError(null);

        const [metricsResult, insightsResult, storyResult] = await Promise.all([
          analyticsApi.getDerivedMetrics(userId, 30),
          analyticsApi.getAllInsights(userId, 30),
          analyticsApi.getStoryAnalytics(userId, 30),
        ]);

        if (!metricsResult.error && metricsResult.data) setMetrics(metricsResult.data);
        if (!insightsResult.error && insightsResult.data) setInsights(insightsResult.data);
        if (!storyResult.error && storyResult.data) setStory(storyResult.data);
      } catch (err) {
        setError("Failed to load analytics data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, [userId]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Story Analytics */}
      {story && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Behavioral Story</h2>
          <p className="text-gray-700 mb-4">{story.narrative}</p>

          {story.key_behaviors.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-gray-900 mb-2">Key Behaviors</h3>
              <ul className="list-disc list-inside space-y-1">
                {story.key_behaviors.map((behavior, i) => (
                  <li key={i} className="text-gray-600">{behavior}</li>
                ))}
              </ul>
            </div>
          )}

          {story.risks.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-red-900 mb-2">Risks Identified</h3>
              <ul className="list-disc list-inside space-y-1">
                {story.risks.map((risk, i) => (
                  <li key={i} className="text-red-700">{risk}</li>
                ))}
              </ul>
            </div>
          )}

          {story.recommendations.length > 0 && (
            <div>
              <h3 className="font-medium text-green-900 mb-2">Recommendations</h3>
              <ul className="list-disc list-inside space-y-1">
                {story.recommendations.map((rec, i) => (
                  <li key={i} className="text-green-700">{rec}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 pt-4 border-t text-xs text-gray-500">
            <p>Data traceability: {story.data_traceability.tasks_count} tasks, {story.data_traceability.sessions_count} sessions, {story.data_traceability.interruptions_count} interruptions</p>
          </div>
        </div>
      )}

      {/* Derived Metrics */}
      {metrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Derived Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Forget Risk */}
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="font-medium text-blue-900 mb-2">Forget Risk</h3>
              <div className="text-2xl font-bold text-blue-700">
                {(metrics.forget_risk.forget_risk * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-blue-600 mt-1">
                Based on recent patterns
              </div>
            </div>

            {/* Behavioral Friction */}
            <div className="bg-orange-50 p-4 rounded">
              <h3 className="font-medium text-orange-900 mb-2">Behavioral Friction</h3>
              <div className="text-2xl font-bold text-orange-700">
                {metrics.behavioral_friction_score.friction_score.toFixed(0)}
              </div>
              <div className="text-xs text-orange-600 mt-1">
                0-100 scale, higher = more friction
              </div>
            </div>

            {/* Context Switch Rate */}
            <div className="bg-purple-50 p-4 rounded">
              <h3 className="font-medium text-purple-900 mb-2">Context Switch Rate</h3>
              <div className="text-2xl font-bold text-purple-700">
                {metrics.context_switch_rate.context_switch_rate.toFixed(1)}/hr
              </div>
              <div className="text-xs text-purple-600 mt-1">
                {metrics.context_switch_rate.total_switches} switches total
              </div>
            </div>

            {/* Interruption Rate */}
            <div className="bg-red-50 p-4 rounded">
              <h3 className="font-medium text-red-900 mb-2">Interruption Rate</h3>
              <div className="text-2xl font-bold text-red-700">
                {metrics.interruption_rate.interruption_rate.toFixed(1)}/hr
              </div>
              <div className="text-xs text-red-600 mt-1">
                {metrics.interruption_rate.total_interruptions} interruptions
              </div>
            </div>

            {/* Completion Reliability */}
            <div className="bg-green-50 p-4 rounded">
              <h3 className="font-medium text-green-900 mb-2">Completion Reliability</h3>
              <div className="text-2xl font-bold text-green-700">
                {(metrics.completion_reliability.completion_reliability * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-green-600 mt-1">
                Consistency over time
              </div>
            </div>

            {/* Time Lost */}
            <div className="bg-gray-50 p-4 rounded">
              <h3 className="font-medium text-gray-900 mb-2">Time Lost to Interruptions</h3>
              <div className="text-2xl font-bold text-gray-700">
                {metrics.time_lost_to_interruptions.time_lost_hours.toFixed(1)}h
              </div>
              <div className="text-xs text-gray-600 mt-1">
                Per week
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Behavioral Insights */}
      {insights && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Behavioral Insights</h2>
          <div className="space-y-4">
            {insights.insights.map((insight, index) => (
              <div
                key={index}
                className={`p-4 rounded border-l-4 ${insight.risk_level === "HIGH"
                    ? "border-red-500 bg-red-50"
                    : insight.risk_level === "MEDIUM"
                      ? "border-yellow-500 bg-yellow-50"
                      : "border-green-500 bg-green-50"
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-1">
                      {insight.insight_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </h3>
                    <p className="text-gray-700 mb-2">{insight.message}</p>
                    <p className="text-sm text-gray-600 italic">
                      {insight.recommendation}
                    </p>
                  </div>
                  <span
                    className={`ml-4 px-2 py-1 text-xs font-medium rounded ${insight.risk_level === "HIGH"
                        ? "bg-red-100 text-red-800"
                        : insight.risk_level === "MEDIUM"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-green-100 text-green-800"
                      }`}
                  >
                    {insight.risk_level}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-gray-500">
            Generated at: {new Date(insights.generated_at).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}
