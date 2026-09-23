import { apiClient, mockResult } from "@/lib/api/client";
import { mockDailySummary } from "@/mock/analytics.mock";
import type { ApiResult, DailySummary, ISODate } from "@/types";

// Enhanced analytics types
export interface DerivedMetrics {
  forget_risk: {
    forget_risk: number;
    components: {
      recent_forgetting_rate: number;
      interruption_density: number;
      context_switch_frequency: number;
      deadline_pressure_ratio: number;
    };
  };
  context_switch_rate: {
    context_switch_rate: number;
    total_switches: number;
    active_hours: number;
  };
  interruption_rate: {
    interruption_rate: number;
    total_interruptions: number;
    active_hours: number;
  };
  recovery_time: {
    recovery_time_seconds: number;
    recovery_time_minutes: number;
    sample_size: number;
  };
  behavioral_friction_score: {
    friction_score: number;
    components: {
      forgetting_component: number;
      interruption_component: number;
      context_switch_component: number;
      recovery_component: number;
    };
  };
  completion_reliability: {
    completion_reliability: number;
    mean_daily_rate: number;
    std_daily_rate: number;
    sample_days: number;
  };
  context_consistency: {
    context_consistency: number;
    category_scores: Record<string, number>;
  };
  repetition_strength: {
    repetition_strength: number;
    category_strengths: Record<string, number>;
  };
  time_lost_to_interruptions: {
    time_lost_hours: number;
    interruption_hours: number;
    switch_overhead_hours: number;
    total_switches: number;
  };
}

export interface Insight {
  insight_type: string;
  message: string;
  evidence: Record<string, unknown>;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  recommendation: string;
  error?: string;
}

export interface AllInsights {
  user_id: string;
  period_days: number;
  insights: Insight[];
  generated_at: string;
}

export interface TrendAnalysis {
  user_id: string;
  period_days: number;
  metric_name: string;
  slope: number;
  r_squared: number;
  trend_direction: "INCREASING" | "DECREASING" | "STABLE";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  sample_size: number;
}

export interface DistributionStats {
  metric_name: string;
  statistics: {
    count: number;
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
    q25: number;
    q75: number;
    iqr: number;
    sample_confidence: "HIGH" | "MEDIUM" | "LOW";
  };
  sample_confidence: string;
}

export interface CorrelationData {
  correlations: Record<string, { correlation: number; sample_size: number }>;
  sample_size: number;
  sample_confidence: string;
  method: string;
}

export interface StoryAnalytics {
  user_id: string;
  period_days: number;
  narrative: string;
  key_behaviors: string[];
  patterns: string[];
  evidence: Array<{ insight_type: string; evidence: Record<string, unknown> }>;
  risks: string[];
  recommendations: string[];
  data_traceability: {
    tasks_count: number;
    sessions_count: number;
    interruptions_count: number;
    period_days: number;
    data_source: string;
  };
}

export interface TimelineEntry {
  timestamp: string;
  taskId: string;
  taskTitle: string;
  locationId: string | null;
  locationLabel: string | null;
  contextTag: string | null;
  eventType: string;
  isInterruption: boolean;
}

export interface HeatmapData {
  rows: string[];
  columns: string[];
  cells: (number | null)[][];
  sampleSizes: number[][];
  metric: string;
}

export interface AnalyticsApi {
  getDailySummary(date?: ISODate): Promise<ApiResult<DailySummary>>;
  getDerivedMetrics(userId: string, periodDays?: number): Promise<ApiResult<DerivedMetrics>>;
  getAllInsights(userId: string, periodDays?: number): Promise<ApiResult<AllInsights>>;
  getTrendAnalysis(userId: string, metricName: string, periodDays?: number): Promise<ApiResult<TrendAnalysis>>;
  getDistribution(userId: string, metricName: string, periodDays?: number): Promise<ApiResult<DistributionStats>>;
  getCorrelations(userId: string, periodDays?: number): Promise<ApiResult<CorrelationData>>;
  getStoryAnalytics(userId: string, periodDays?: number): Promise<ApiResult<StoryAnalytics>>;
  getContextSwitchTimeline(userId: string, periodDays: number): Promise<ApiResult<TimelineEntry[]>>;
  getTaskContextHeatmap(
    userId: string,
    periodDays: number,
    metric?: "completion_rate" | "forget_rate",
  ): Promise<ApiResult<HeatmapData>>;
}

const mockAnalyticsApi: AnalyticsApi = {
  async getDailySummary() {
    return mockResult(() => mockDailySummary);
  },
  async getDerivedMetrics() {
    return mockResult(() => ({
      forget_risk: { forget_risk: 0.3, components: { recent_forgetting_rate: 0.2, interruption_density: 0.5, context_switch_frequency: 0.4, deadline_pressure_ratio: 0.1 } },
      context_switch_rate: { context_switch_rate: 2.5, total_switches: 15, active_hours: 6 },
      interruption_rate: { interruption_rate: 3.0, total_interruptions: 18, active_hours: 6 },
      recovery_time: { recovery_time_seconds: 120, recovery_time_minutes: 2, sample_size: 10 },
      behavioral_friction_score: { friction_score: 45, components: { forgetting_component: 30, interruption_component: 50, context_switch_component: 40, recovery_component: 20 } },
      completion_reliability: { completion_reliability: 0.85, mean_daily_rate: 0.9, std_daily_rate: 0.1, sample_days: 30 },
      context_consistency: { context_consistency: 0.7, category_scores: { Work: 0.8, Personal: 0.6 } },
      repetition_strength: { repetition_strength: 0.5, category_strengths: { Work: 0.6, Personal: 0.4 } },
      time_lost_to_interruptions: { time_lost_hours: 2.5, interruption_hours: 1.5, switch_overhead_hours: 1, total_switches: 12 },
    }));
  },
  async getAllInsights() {
    return mockResult(() => ({
      user_id: "mock-user-id",
      period_days: 30,
      insights: [
        {
          insight_type: "forgetting_timing",
          message: "You're 50% more likely to forget tasks on Friday.",
          evidence: { overall_forgetting_rate: 0.2, high_risk_weekdays: ["Friday"] },
          risk_level: "MEDIUM",
          recommendation: "Schedule important tasks earlier in the week.",
        },
      ],
      generated_at: new Date().toISOString(),
    }));
  },
  async getTrendAnalysis() {
    return mockResult(() => ({
      user_id: "mock-user-id",
      period_days: 30,
      metric_name: "forgetting_rate",
      slope: -0.001,
      r_squared: 0.45,
      trend_direction: "DECREASING",
      confidence: "MEDIUM",
      sample_size: 30,
    }));
  },
  async getDistribution() {
    return mockResult(() => ({
      metric_name: "task_duration",
      statistics: {
        count: 100,
        mean: 45,
        median: 40,
        std: 20,
        min: 5,
        max: 120,
        q25: 30,
        q75: 60,
        iqr: 30,
        sample_confidence: "HIGH",
      },
      sample_confidence: "HIGH",
    }));
  },
  async getCorrelations() {
    return mockResult(() => ({
      correlations: {
        "focused_time_seconds_vs_interruption_time_seconds": { correlation: -0.3, sample_size: 50 },
      },
      sample_size: 50,
      sample_confidence: "MEDIUM",
      method: "pearson",
    }));
  },
  async getStoryAnalytics() {
    return mockResult(() => ({
      user_id: "mock-user-id",
      period_days: 30,
      narrative: "Your behavior analysis reveals 2 high-risk patterns requiring attention.",
      key_behaviors: ["You're 50% more likely to forget tasks on Friday."],
      patterns: ["forgetting_timing", "context_forgetting"],
      evidence: [],
      risks: ["High forgetting rate on Fridays"],
      recommendations: ["Schedule important tasks earlier in the week."],
      data_traceability: {
        tasks_count: 100,
        sessions_count: 50,
        interruptions_count: 30,
        period_days: 30,
        data_source: "tasks, sessions, interruptions tables",
      },
    }));
  },
  async getContextSwitchTimeline() {
    const now = new Date();
    const day1 = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const day2 = new Date(now.getTime() - 0 * 60 * 60 * 1000);
    return mockResult(() => [
      {
        timestamp: new Date(day1.getTime() + 9 * 60 * 60 * 1000).toISOString(),
        taskId: "task-001",
        taskTitle: "Review project proposal",
        locationId: "loc-office",
        locationLabel: "Office",
        contextTag: "Work",
        eventType: "started",
        isInterruption: false,
      },
      {
        timestamp: new Date(day1.getTime() + 9 * 60 * 60 * 1000 + 25 * 60 * 1000).toISOString(),
        taskId: "task-001",
        taskTitle: "Review project proposal",
        locationId: "loc-office",
        locationLabel: "Office",
        contextTag: "Work",
        eventType: "paused",
        isInterruption: true,
      },
      {
        timestamp: new Date(day2.getTime() + 14 * 60 * 60 * 1000).toISOString(),
        taskId: "task-002",
        taskTitle: "Write weekly report",
        locationId: "loc-home",
        locationLabel: "Home",
        contextTag: "Work",
        eventType: "started",
        isInterruption: false,
      },
      {
        timestamp: new Date(day2.getTime() + 15 * 60 * 60 * 1000 + 10 * 60 * 1000).toISOString(),
        taskId: "task-003",
        taskTitle: "Grocery shopping list",
        locationId: null,
        locationLabel: null,
        contextTag: "Personal",
        eventType: "created",
        isInterruption: false,
      },
    ]);
  },
  async getTaskContextHeatmap() {
    return mockResult(() => ({
      rows: ["Work", "Personal", "Study"],
      columns: ["00-03", "04-07", "08-11", "12-15", "16-19", "20-23"],
      cells: [
        [null, null, 0.85, 0.72, 0.78, 0.65],
        [null, null, null, 0.5, 0.6, 0.4],
        [null, 0.9, 0.88, null, 0.82, null],
      ],
      sampleSizes: [
        [0, 2, 15, 18, 12, 6],
        [1, 0, 2, 8, 10, 5],
        [0, 5, 7, 2, 11, 1],
      ],
      metric: "completion_rate",
    }));
  },
};

const liveAnalyticsApi: AnalyticsApi = {
  getDailySummary: (date) =>
    apiClient.request<DailySummary>("/analytics/daily-summary", {
      query: { date },
      baseUrl: "analytics",
    }),
  getDerivedMetrics: (userId, periodDays = 30) =>
    apiClient.request<DerivedMetrics>("/analytics/derived-metrics", {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "analytics",
    }),
  getAllInsights: (userId, periodDays = 30) =>
    apiClient.request<AllInsights>("/analytics/insights", {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "analytics",
    }),
  getTrendAnalysis: (userId, metricName, periodDays = 30) =>
    apiClient.request<TrendAnalysis>(`/analytics/trends/${metricName}`, {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "analytics",
    }),
  getDistribution: (userId, metricName, periodDays = 30) =>
    apiClient.request<DistributionStats>(`/analytics/distributions/${metricName}`, {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "analytics",
    }),
  getCorrelations: (userId, periodDays = 30) =>
    apiClient.request<CorrelationData>("/analytics/correlations", {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "analytics",
    }),
  getStoryAnalytics: (userId, periodDays = 30) =>
    apiClient.request<StoryAnalytics>("/analytics/story", {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "analytics",
    }),
  getContextSwitchTimeline: (userId, periodDays = 30) =>
    apiClient.request<TimelineEntry[]>("/analytics/context-switch-timeline", {
      query: { user_id: userId, period_days: periodDays },
      baseUrl: "core",
    }),
  getTaskContextHeatmap: (userId, periodDays = 30, metric) =>
    apiClient.request<HeatmapData>("/analytics/task-context-heatmap", {
      query: { user_id: userId, period_days: periodDays, value_metric: metric },
      baseUrl: "core",
    }),
};

export const analyticsApi: AnalyticsApi = apiClient.USE_MOCK
  ? mockAnalyticsApi
  : liveAnalyticsApi;
