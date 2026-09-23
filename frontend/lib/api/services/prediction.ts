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
  listPredictions: (filters) =>
    apiClient.request<ForgettingPrediction[]>("/predictions/forgetting", {
      query: filters,
      baseUrl: "prediction",
    }),
  getPredictionForTask: (taskId) =>
    apiClient.request<ForgettingPrediction | null>(
      `/predictions/forgetting/task/${taskId}`,
      { baseUrl: "prediction" },
    ),
};

export const predictionApi: PredictionApi = apiClient.USE_MOCK
  ? mockPredictionApi
  : livePredictionApi;
