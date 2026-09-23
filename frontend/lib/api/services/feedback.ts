import { apiClient, mockResult } from "@/lib/api/client";
import type { ApiResult, Feedback, RecommendationOutcome, SubmitFeedbackInput } from "@/types";

export interface FeedbackApi {
  submit(input: SubmitFeedbackInput): Promise<ApiResult<Feedback>>;
  submitRecommendationOutcome(id: string, outcome: RecommendationOutcome, userId?: string): Promise<ApiResult<Feedback>>;
}

const mockFeedbackApi: FeedbackApi = {
  async submit(input) {
    return mockResult(() => ({
      id: `feedback-${Math.random().toString(36).slice(2, 9)}`,
      ...input,
      createdAt: new Date().toISOString(),
    }));
  },
  async submitRecommendationOutcome(id, outcome) {
    return mockFeedbackApi.submit({
      targetType: "RECOMMENDATION",
      targetId: id,
      helpful: outcome === "accepted" || outcome === "completed",
      outcome,
      comment: "Recorded from recommendation workspace",
    });
  },
};

const liveFeedbackApi: FeedbackApi = {
  submit: (input) =>
    apiClient.request<Feedback>("/feedback", { method: "POST", body: input }),
  submitRecommendationOutcome: (id, outcome, userId = "user-123") =>
    apiClient.request<Feedback>("/feedback", {
      method: "POST",
      baseUrl: "recommendation",
      body: {
        entry: {
          user_id: userId,
          target_type: "recommendation",
          target_id: id,
          feedback: outcome,
        },
      },
    }),
};

export const feedbackApi: FeedbackApi = apiClient.USE_MOCK
  ? mockFeedbackApi
  : liveFeedbackApi;
