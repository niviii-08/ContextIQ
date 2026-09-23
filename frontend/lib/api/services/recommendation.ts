import { apiClient, mockResult } from "@/lib/api/client";
import { mockRecommendations } from "@/mock/analytics.mock";
import type {
  ApiResult,
  Recommendation,
  RecommendationAcceptanceStats,
} from "@/types";

type BackendRecommendation = Partial<Recommendation> & {
  associated_task?: string;
  association_confidence?: number;
  forgetting_probability?: number | null;
  recommendation_type?: string;
  triggering_behaviour?: string;
  evidence_strength?: number;
  impact_score?: number;
  risk_level?: "HIGH" | "MEDIUM" | "LOW";
  expected_benefit?: string;
  explanation?: string;
  generated_at?: string;
  acceptance_stats?: { accepted: number; dismissed: number; deferred: number };
};

type FeedbackResponse = {
  feedback: BackendRecommendation;
  created_task_id?: string | null;
};

function normalizeAcceptanceStats(
  raw?: BackendRecommendation["acceptance_stats"] | RecommendationAcceptanceStats,
): RecommendationAcceptanceStats | undefined {
  if (!raw) return undefined;
  return {
    accepted: Number(raw.accepted) || 0,
    dismissed: Number(raw.dismissed) || 0,
    deferred: Number(raw.deferred) || 0,
  };
}

function normalizeRecommendation(raw: BackendRecommendation): Recommendation {
  const taskTitle = raw.associated_task ?? raw.suggestedTasks?.[0]?.title ?? "Observed task";
  const status = (raw.status === "ACCEPTED" ? "ADDED" : raw.status) as Recommendation["status"];
  return {
    id: raw.id ?? `recommendation-${taskTitle.toLowerCase().replaceAll(" ", "-")}`,
    recommendationType: raw.recommendationType ?? raw.recommendation_type ?? "context_based_reminder",
    triggeringBehaviour: raw.triggeringBehaviour ?? raw.triggering_behaviour ?? raw.explanation ?? "Derived from observed behavioural data.",
    evidence: raw.evidence ?? [],
    evidenceStrength: raw.evidenceStrength ?? raw.evidence_strength ?? raw.association_confidence ?? 0,
    impactScore: raw.impactScore ?? raw.impact_score ?? raw.forgetting_probability ?? 0,
    riskLevel: raw.riskLevel ?? raw.risk_level ?? "LOW",
    expectedBenefit: raw.expectedBenefit ?? raw.expected_benefit ?? "Use the observed pattern when planning the next action.",
    feedback: raw.feedback ?? [],
    context: raw.context ?? "Observed context",
    reliableTasks: raw.reliableTasks ?? [],
    suggestedTasks: raw.suggestedTasks ?? [{ title: taskTitle, reason: raw.explanation ?? "Observed association", taskId: undefined }],
    generatedAt: raw.generatedAt ?? raw.generated_at ?? new Date().toISOString(),
    status: status ?? "PENDING",
    acceptanceStats: normalizeAcceptanceStats(raw.acceptance_stats ?? raw.acceptanceStats),
  };
}

export interface RecommendationApi {
  list(): Promise<ApiResult<Recommendation[]>>;
  accept(id: string, taskTitle: string): Promise<ApiResult<Recommendation>>;
  dismiss(id: string): Promise<ApiResult<Recommendation>>;
}

const store = { recommendations: [...mockRecommendations] };

const mockRecommendationApi: RecommendationApi = {
  async list() {
    return mockResult(() =>
      store.recommendations.filter((r) => r.status === "PENDING"),
    );
  },
  async accept(id) {
    return mockResult(() => {
      const idx = store.recommendations.findIndex((r) => r.id === id);
      if (idx === -1) throw new Error("not found");
      const updated: Recommendation = {
        ...store.recommendations[idx],
        status: "ADDED",
      };
      store.recommendations = [
        ...store.recommendations.slice(0, idx),
        updated,
        ...store.recommendations.slice(idx + 1),
      ];
      return updated;
    });
  },
  async dismiss(id) {
    return mockResult(() => {
      const idx = store.recommendations.findIndex((r) => r.id === id);
      if (idx === -1) throw new Error("not found");
      const updated: Recommendation = {
        ...store.recommendations[idx],
        status: "DISMISSED",
      };
      store.recommendations = [
        ...store.recommendations.slice(0, idx),
        updated,
        ...store.recommendations.slice(idx + 1),
      ];
      return updated;
    });
  },
};

const liveRecommendationApi: RecommendationApi = {
  async list() {
    const result = await apiClient.request<BackendRecommendation[]>("/recommendations", { baseUrl: "core" });
    return result.data ? { data: result.data.map(normalizeRecommendation), error: null } : { data: null, error: result.error };
  },
  async accept(id, taskTitle) {
    const result = await apiClient.request<FeedbackResponse>(`/recommendations/${id}/feedback`, {
      method: "POST",
      baseUrl: "core",
      body: { action: "ACCEPTED", prefill_context_tag: taskTitle?.slice(0, 64) || undefined },
    });
    if (result.error || !result.data) return { data: null, error: result.error ?? { code: "NO_DATA", message: "No response from feedback endpoint", status: 0 } };
    const accepted: BackendRecommendation = {
      ...(result.data.feedback as unknown as BackendRecommendation),
      status: "ACCEPTED",
    };
    return { data: normalizeRecommendation(accepted), error: null };
  },
  async dismiss(id) {
    const result = await apiClient.request<FeedbackResponse>(`/recommendations/${id}/feedback`, {
      method: "POST",
      baseUrl: "core",
      body: { action: "DISMISSED" },
    });
    if (result.error || !result.data) return { data: null, error: result.error ?? { code: "NO_DATA", message: "No response from feedback endpoint", status: 0 } };
    const dismissed: BackendRecommendation = {
      ...(result.data.feedback as unknown as BackendRecommendation),
      status: "DISMISSED",
    };
    return { data: normalizeRecommendation(dismissed), error: null };
  },
};

export const recommendationApi: RecommendationApi = apiClient.USE_MOCK
  ? mockRecommendationApi
  : liveRecommendationApi;
