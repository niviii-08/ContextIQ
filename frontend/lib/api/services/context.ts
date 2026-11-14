import { apiClient, mockResult } from "@/lib/api/client";
import { mockAssociations, mockContextMetrics } from "@/mock/analytics.mock";
import type { Association, ApiResult, ContextMetrics, ISODate } from "@/types";

export interface ContextApi {
  getMetrics(date?: ISODate): Promise<ApiResult<ContextMetrics>>;
  listAssociations(): Promise<ApiResult<Association[]>>;
}

const mockContextApi: ContextApi = {
  async getMetrics() {
    return mockResult(() => mockContextMetrics);
  },
  async listAssociations() {
    return mockResult(() => mockAssociations);
  },
};

const liveContextApi: ContextApi = {
  getMetrics: async (date) => {
    try {
      const res = await apiClient.request<ContextMetrics>("/context/metrics", {
        query: { date },
        baseUrl: "context",
      });
      if (res.data) return res;
    } catch {
      // offline fallback
    }
    return mockResult(() => mockContextMetrics);
  },
  listAssociations: async () => {
    try {
      const res = await apiClient.request<Association[]>("/context/associations", {
        baseUrl: "context",
      });
      if (res.data) return res;
    } catch {
      // offline fallback
    }
    return mockResult(() => mockAssociations);
  },
};

export const contextApi: ContextApi = apiClient.USE_MOCK
  ? mockContextApi
  : liveContextApi;
