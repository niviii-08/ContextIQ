import { apiClient, mockResult } from "@/lib/api/client";
import { mockPredictions } from "@/mock/analytics.mock";
import type { ApiResult, ForgettingPrediction, RiskLevel } from "@/types";

export interface PredictionApi {
  listPredictions(filters?: {
    riskLevel?: RiskLevel;
  }): Promise<ApiResult<ForgettingPrediction[]>>;
  getPredictionForTask(
    taskId: string,
  ): Promise<ApiResult<ForgettingPrediction | null>>;
}

const mockPredictionApi: PredictionApi = {
  async listPredictions(filters) {
    return mockResult(() => {
      if (!filters?.riskLevel) return mockPredictions;
      return mockPredictions.filter((p) => p.riskLevel === filters.riskLevel);
    });
  },
  async getPredictionForTask(taskId) {
    return mockResult(
      () => mockPredictions.find((p) => p.taskId === taskId) ?? null,
    );
  },
};

const livePredictionApi: PredictionApi = {
  listPredictions: async (filters) => {
    try {
      const res = await apiClient.request<ForgettingPrediction[]>("/predictions/forgetting", {
        query: filters,
        baseUrl: "prediction",
      });
      if (res.data && res.data.length > 0) {
        return res;
      }
    } catch {
      // offline fallback
    }

    return mockResult(() => {
      let tasks: any[] = [];
      try {
        const raw = typeof window !== "undefined" ? localStorage.getItem("contextiq_user_tasks") : null;
        if (raw) tasks = JSON.parse(raw);
      } catch {
        tasks = [];
      }

      if (tasks.length > 0) {
        const dynamic: ForgettingPrediction[] = tasks.map((t, idx) => {
          const isAnchor = /anchor|forget/i.test(t.title) || /anchor/i.test(t.tags?.[0] || "");
          const isChore = /chore|washing|cooking/i.test(t.title);
          const level: RiskLevel = isAnchor ? "HIGH" : (isChore ? "MEDIUM" : "LOW");
          const score = isAnchor ? 84 : (isChore ? 58 : 26);
          return {
            id: `pred-${t.id || idx}`,
            taskId: t.id || `task-${idx}`,
            taskTitle: t.title,
            riskScore: score,
            riskLevel: level,
            reasons: [
              {
                feature: isAnchor ? "Cognitive Memory Anchor" : (isChore ? "Daily Routine Cadence" : "Focus Schedule"),
                impact: isAnchor ? 0.42 : (isChore ? 0.28 : -0.3),
                description: isAnchor
                  ? "Identified as high forgetting risk during questionnaire onboarding"
                  : (isChore ? "Recurring daily habit competing with deep focus blocks" : "Explicitly scheduled work item with assigned priority"),
              },
              {
                feature: "Ebbinghaus Memory Decay",
                impact: 0.25,
                description: "Working memory retention decays rapidly across task transitions",
              },
            ],
            generatedAt: new Date().toISOString(),
            modelVersion: "xgb-ebbinghaus-v1.2",
          };
        });

        if (filters?.riskLevel) {
          return dynamic.filter((p) => p.riskLevel === filters.riskLevel);
        }
        return dynamic;
      }

      if (!filters?.riskLevel) return mockPredictions;
      return mockPredictions.filter((p) => p.riskLevel === filters.riskLevel);
    });
  },
  getPredictionForTask: async (taskId) => {
    try {
      const res = await apiClient.request<ForgettingPrediction | null>(
        `/predictions/forgetting/task/${taskId}`,
        { baseUrl: "prediction" },
      );
      if (res.data) return res;
    } catch {
      // offline fallback
    }
    return mockResult(
      () => mockPredictions.find((p) => p.taskId === taskId) ?? null,
    );
  },
};

export const predictionApi: PredictionApi = apiClient.USE_MOCK
  ? mockPredictionApi
  : livePredictionApi;
