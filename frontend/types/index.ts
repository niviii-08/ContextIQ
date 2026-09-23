/**
 * ContextIQ — Integration Contracts
 * ---------------------------------
 * These interfaces define the conceptual contract between this frontend
 * and the (independently developed) ContextIQ backend / ML services.
 *
 * Any backend implementation MUST return payloads shaped like these
 * interfaces. See docs/INTEGRATION_BLUEPRINT.md for endpoint-by-endpoint
 * request/response schemas.
 */

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

export type ISODateTime = string; // e.g. "2026-08-18T09:30:00Z"
export type ISODate = string; // e.g. "2026-08-18"

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type Priority = "LOW" | "MEDIUM" | "HIGH";
export type TaskStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "PAUSED"
  | "COMPLETED"
  | "FORGOTTEN";

export type Weekday =
  | "MONDAY"
  | "TUESDAY"
  | "WEDNESDAY"
  | "THURSDAY"
  | "FRIDAY"
  | "SATURDAY"
  | "SUNDAY";

/** Generic envelope every API service function resolves to. */
export interface ApiResult<T> {
  data: T | null;
  error: ApiError | null;
}

/** Canonical error shape returned by every backend endpoint on failure. */
export interface ApiError {
  code: string; // e.g. "TASK_NOT_FOUND", "VALIDATION_ERROR"
  message: string; // human readable, safe to display
  status: number; // HTTP status
  details?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Task
// ---------------------------------------------------------------------------

export interface Task {
  id: string;
  title: string;
  description?: string;
  category: string; // e.g. "Academic", "Admin", "Personal"
  context: string; // location / situational tag, e.g. "Department"
  status: TaskStatus;
  priority: Priority;
  dueAt?: ISODateTime;
  createdAt: ISODateTime;
  updatedAt: ISODateTime;
  estimatedMinutes?: number;
  actualMinutes?: number;
  tags: string[];
  forgottenCount: number;
  completionStreak: number;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  category: string;
  context: string;
  priority: Priority;
  dueAt?: ISODateTime;
  estimatedMinutes?: number;
  tags?: string[];
}

export type TaskEventType =
  | "STARTED"
  | "PAUSED"
  | "RESUMED"
  | "COMPLETED"
  | "FORGOTTEN"
  | "CREATED"
  | "EDITED";

export interface TaskEvent {
  id: string;
  taskId: string;
  type: TaskEventType;
  timestamp: ISODateTime;
  context?: string;
  metadata?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Interruption / Context Intelligence
// ---------------------------------------------------------------------------

export interface Interruption {
  id: string;
  taskId?: string;
  category: string; // e.g. "Notification", "Conversation", "Environment"
  context: string;
  startedAt: ISODateTime;
  durationSeconds: number;
  recoveryCostSeconds: number;
}

export interface ContextMetrics {
  date: ISODate;
  focusMinutes: number;
  interruptionMinutes: number;
  contextSwitches: number;
  recoveryCostMinutes: number;
  topInterruptionCategory: string;
  mostAffectedTaskCategory: string;
  byHour: ContextHourBucket[];
  byCategory: ContextCategoryBucket[];
}

export interface ContextHourBucket {
  hour: number; // 0-23
  focusMinutes: number;
  interruptionMinutes: number;
}

export interface ContextCategoryBucket {
  category: string;
  minutes: number;
  count: number;
}

export interface Association {
  id: string;
  context: string; // e.g. "Department"
  reliableTasks: string[]; // task titles frequently completed here
  atRiskTasks: string[]; // task titles often forgotten in/near this context
  confidence: number; // 0-1
}

// ---------------------------------------------------------------------------
// Forgetting Prediction (ML)
// ---------------------------------------------------------------------------

export interface ForgettingPrediction {
  id: string;
  taskId: string;
  taskTitle: string;
  riskScore: number; // 0-100
  riskLevel: RiskLevel;
  reasons: PredictionReason[];
  generatedAt: ISODateTime;
  modelVersion: string;
}

export interface PredictionReason {
  label: string; // e.g. "Previous forgetting frequency"
  detail: string;
  weight: number; // 0-1 contribution to score
}

// ---------------------------------------------------------------------------
// Recommendations ("One More Thing")
// ---------------------------------------------------------------------------

export interface RecommendationAcceptanceStats {
  accepted: number;
  dismissed: number;
  deferred: number;
}

export interface Recommendation {
  id: string;
  recommendationType: string;
  triggeringBehaviour: string;
  evidence: RecommendationEvidence[];
  evidenceStrength: number;
  impactScore: number;
  riskLevel: Priority;
  expectedBenefit: string;
  feedback: RecommendationOutcome[];
  context: string;
  reliableTasks: string[]; // "You frequently complete these tasks here"
  suggestedTasks: RecommendedTask[]; // "You may also want to check"
  generatedAt: ISODateTime;
  status: "PENDING" | "ADDED" | "DISMISSED" | "ACCEPTED";
  acceptanceStats?: RecommendationAcceptanceStats;
}

export interface RecommendationEvidence {
  field: string;
  value: string;
  source: string;
}

export type RecommendationOutcome = "accepted" | "dismissed" | "useful" | "not_useful" | "completed";

export interface RecommendedTask {
  taskId?: string; // present if it maps to an existing task
  title: string;
  reason: string;
}

// ---------------------------------------------------------------------------
// Behaviour Insights
// ---------------------------------------------------------------------------

export type InsightType =
  | "FRICTION_SOURCE"
  | "FREQUENTLY_FORGOTTEN"
  | "HIGH_INTERRUPTION_CONTEXT"
  | "STRONGEST_ASSOCIATION"
  | "GENERAL";

export interface BehaviourInsight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  priority: Priority;
  metricLabel?: string;
  metricValue?: string;
  generatedAt: ISODateTime;
}

// ---------------------------------------------------------------------------
// Daily Summary
// ---------------------------------------------------------------------------

export interface DailySummary {
  date: ISODate;
  frictionScore: number; // 0-100, higher = more friction
  tasksCompleted: number;
  tasksForgotten: number;
  contextSwitches: number;
  interruptionMinutes: number;
  recoveryCostMinutes: number;
  comparedToYesterday: {
    frictionScoreDelta: number;
    tasksCompletedDelta: number;
  };
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export type FeedbackTargetType =
  | "PREDICTION"
  | "RECOMMENDATION"
  | "INSIGHT"
  | "GENERAL";

export interface Feedback {
  id: string;
  targetType: FeedbackTargetType;
  targetId: string;
  helpful: boolean;
  comment?: string;
  createdAt: ISODateTime;
}

export interface SubmitFeedbackInput {
  targetType: FeedbackTargetType;
  targetId: string;
  helpful: boolean;
  outcome?: RecommendationOutcome;
  comment?: string;
}
