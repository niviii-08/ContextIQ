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
  getMetrics: (date) =>
    apiClient.request<ContextMetrics>("/context/metrics", {
      query: { date },
      baseUrl: "context",
    }),
  listAssociations: () =>
    apiClient.request<Association[]>("/context/associations", {
      baseUrl: "context",
    }),
};

export const contextApi: ContextApi = apiClient.USE_MOCK
  ? mockContextApi
  : liveContextApi;
