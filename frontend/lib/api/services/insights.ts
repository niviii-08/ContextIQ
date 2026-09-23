import { apiClient, mockResult } from "@/lib/api/client";
import { mockInsights } from "@/mock/analytics.mock";
import type { ApiResult, BehaviourInsight } from "@/types";

export interface InsightsApi {
  list(): Promise<ApiResult<BehaviourInsight[]>>;
}

const mockInsightsApi: InsightsApi = {
  async list() {
    return mockResult(() => mockInsights);
  },
};

const liveInsightsApi: InsightsApi = {
  list: () =>
    apiClient.request<BehaviourInsight[]>("/insights/generate", {
      baseUrl: "insights",
    }),
};

export const insightsApi: InsightsApi = apiClient.USE_MOCK
  ? mockInsightsApi
  : liveInsightsApi;
