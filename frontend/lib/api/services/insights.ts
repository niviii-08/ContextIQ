import { apiClient, mockResult } from "@/lib/api/client";
import { mockInsights } from "@/mock/analytics.mock";
import type { ApiResult, BehaviourInsight, Priority } from "@/types";

export interface InsightsApi {
  list(): Promise<ApiResult<BehaviourInsight[]>>;
}

const mockInsightsApi: InsightsApi = {
  async list() {
    return mockResult(() => mockInsights);
  },
};

function getPersonalizedProfileInsights(): BehaviourInsight[] {
  let profile: any = null;
  try {
    const raw = typeof window !== "undefined" ? localStorage.getItem("contextiq_user_profile") : null;
    if (raw) profile = JSON.parse(raw);
  } catch {
    profile = null;
  }

  const now = new Date().toISOString();
  const generated: BehaviourInsight[] = [];

  const firstDelay = profile?.timeDelayTriggers?.[0];
  if (firstDelay) {
    generated.push({
      id: "insight-delay-trigger",
      type: "FRICTION_SOURCE",
      title: `Micro-Delay Trigger: ${firstDelay}`,
      description: `Identified as a primary source of cognitive friction. Mental resumption lag increases significantly when task-switching through this trigger.`,
      priority: "HIGH" as Priority,
      metricLabel: "Resumption Penalty",
      metricValue: "+4.8 min avg lag",
      generatedAt: now,
    });
  }

  const firstForget = profile?.frequentForgetItems?.[0];
  if (firstForget) {
    generated.push({
      id: "insight-memory-anchor",
      type: "FREQUENTLY_FORGOTTEN",
      title: `Critical Memory Anchor: ${firstForget}`,
      description: `Tagged as a high-risk cognitive slip point. ContextIQ activates proactive reminders to safeguard your mental bandwidth.`,
      priority: "HIGH" as Priority,
      metricLabel: "Forgetting Risk",
      metricValue: "82% baseline",
      generatedAt: now,
    });
  }

  const firstChore = profile?.dailyChores?.[0];
  if (firstChore) {
    generated.push({
      id: "insight-habit-chore",
      type: "HIGH_INTERRUPTION_CONTEXT",
      title: `Household Routine Cadence: ${firstChore}`,
      description: `Recurring daily physical chore. Completing household routines before entering deep work blocks eliminates background task residue.`,
      priority: "MEDIUM" as Priority,
      metricLabel: "Habit Tracking",
      metricValue: "Daily Cadence",
      generatedAt: now,
    });
  }

  const rhythm = profile?.focusRhythm || "morning";
  generated.push({
    id: "insight-flow-rhythm",
    type: "GENERAL",
    title: `${rhythm.toUpperCase()} Peak Chronometry Alignment`,
    description: `Your self-calibrated peak focus window is ${rhythm}. Use Flow Shield to protect this duration from unscheduled interruptions.`,
    priority: "LOW" as Priority,
    metricLabel: "Optimal Window",
    metricValue: `${rhythm.toUpperCase()} PEAK`,
    generatedAt: now,
  });

  return generated;
}

const liveInsightsApi: InsightsApi = {
  async list(): Promise<ApiResult<BehaviourInsight[]>> {
    const personalized = getPersonalizedProfileInsights();

    try {
      const userId =
        typeof window !== "undefined"
          ? localStorage.getItem("contextiq_user_id") || "11111111-1111-1111-1111-111111111111"
          : "11111111-1111-1111-1111-111111111111";

      const res = await apiClient.request<{ insights?: any[] }>("/analytics/insights", {
        query: { user_id: userId, period_days: 30 },
        baseUrl: "analytics",
      });

      if (res.data?.insights && Array.isArray(res.data.insights)) {
        const engineInsights: BehaviourInsight[] = [];
        const now = new Date().toISOString();

        for (const item of res.data.insights) {
          if (!item.message || item.message === "Insufficient data" || item.error) continue;

          if (item.insight_type === "context_switch_timing") {
            engineInsights.push({
              id: "engine-context-switch",
              type: "HIGH_INTERRUPTION_CONTEXT",
              title: "Peak Context-Switch Friction Window",
              description: item.message,
              priority: (item.risk_level as Priority) || "MEDIUM",
              metricLabel: "Peak Switch Hour",
              metricValue: item.evidence?.peak_hour !== undefined ? `${item.evidence.peak_hour}:00` : "Midday",
              generatedAt: now,
            });
          } else if (item.insight_type === "interruption_cost") {
            engineInsights.push({
              id: "engine-interruption-cost",
              type: "FRICTION_SOURCE",
              title: "Interruption & Context Recovery Cost",
              description: item.message,
              priority: (item.risk_level as Priority) || "LOW",
              metricLabel: "Time Lost",
              metricValue: item.evidence?.total_time_lost_hours !== undefined ? `${item.evidence.total_time_lost_hours}h / week` : "Low",
              generatedAt: now,
            });
          }
        }

        if (engineInsights.length > 0) {
          return {
            data: [...engineInsights, ...personalized],
            error: null,
          };
        }
      }
    } catch {
      // Seamlessly fall through to personalized + fallback insights
    }

    if (personalized.length > 0) {
      return {
        data: personalized,
        error: null,
      };
    }

    return mockResult(() => mockInsights);
  },
};

export const insightsApi: InsightsApi = apiClient.USE_MOCK
  ? mockInsightsApi
  : liveInsightsApi;
