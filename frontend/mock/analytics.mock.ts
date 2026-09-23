import type {
  Association,
  BehaviourInsight,
  ContextMetrics,
  DailySummary,
  ForgettingPrediction,
  Recommendation,
} from "@/types";

export const mockDailySummary: DailySummary = {
  date: "2026-08-18",
  frictionScore: 64,
  tasksCompleted: 5,
  tasksForgotten: 2,
  contextSwitches: 14,
  interruptionMinutes: 87,
  recoveryCostMinutes: 39,
  comparedToYesterday: {
    frictionScoreDelta: 6,
    tasksCompletedDelta: -1,
  },
};

export const mockContextMetrics: ContextMetrics = {
  date: "2026-08-18",
  focusMinutes: 214,
  interruptionMinutes: 87,
  contextSwitches: 14,
  recoveryCostMinutes: 39,
  topInterruptionCategory: "Notifications",
  mostAffectedTaskCategory: "Academic",
  byHour: [
    { hour: 8, focusMinutes: 22, interruptionMinutes: 8 },
    { hour: 9, focusMinutes: 35, interruptionMinutes: 10 },
    { hour: 10, focusMinutes: 18, interruptionMinutes: 15 },
    { hour: 11, focusMinutes: 40, interruptionMinutes: 5 },
    { hour: 12, focusMinutes: 12, interruptionMinutes: 20 },
    { hour: 13, focusMinutes: 10, interruptionMinutes: 6 },
    { hour: 14, focusMinutes: 30, interruptionMinutes: 9 },
    { hour: 15, focusMinutes: 25, interruptionMinutes: 7 },
    { hour: 16, focusMinutes: 22, interruptionMinutes: 7 },
  ],
  byCategory: [
    { category: "Notifications", minutes: 34, count: 21 },
    { category: "Conversations", minutes: 22, count: 6 },
    { category: "Environment", minutes: 16, count: 9 },
    { category: "Context Switch", minutes: 15, count: 14 },
  ],
};

export const mockAssociations: Association[] = [
  {
    id: "assoc-001",
    context: "Department",
    reliableTasks: ["Collect Form", "Submit Record"],
    atRiskTasks: ["Internship Document"],
    confidence: 0.82,
  },
  {
    id: "assoc-002",
    context: "Home",
    reliableTasks: ["Water Plants"],
    atRiskTasks: ["Pay Hostel Fee", "Reply to Advisor Email"],
    confidence: 0.71,
  },
  {
    id: "assoc-003",
    context: "Library",
    reliableTasks: ["Prepare Seminar Slides"],
    atRiskTasks: [],
    confidence: 0.6,
  },
];

export const mockPredictions: ForgettingPrediction[] = [
  {
    id: "pred-001",
    taskId: "task-001",
    taskTitle: "Lab Record",
    riskScore: 82,
    riskLevel: "HIGH",
    reasons: [
      {
        label: "Previous forgetting frequency",
        detail: "Forgotten 6 out of the last 10 weeks.",
        weight: 0.45,
      },
      {
        label: "Historical completion rate",
        detail: "Only 40% completion rate for this task type.",
        weight: 0.35,
      },
      {
        label: "Weekday pattern",
        detail: "Tasks due on Wednesdays are forgotten 2x more often.",
        weight: 0.2,
      },
    ],
    generatedAt: "2026-08-18T06:00:00Z",
    modelVersion: "forgetting-model-v1.3.0",
  },
  {
    id: "pred-002",
    taskId: "task-006",
    taskTitle: "Pay Hostel Fee",
    riskScore: 71,
    riskLevel: "HIGH",
    reasons: [
      {
        label: "Previous forgetting frequency",
        detail: "Forgotten 4 out of the last 6 billing cycles.",
        weight: 0.5,
      },
      {
        label: "Low task salience",
        detail: "No reminder context associated with 'Home'.",
        weight: 0.3,
      },
      {
        label: "Weekday pattern",
        detail: "Deadline falls on weekends 3 out of 4 times.",
        weight: 0.2,
      },
    ],
    generatedAt: "2026-08-18T06:00:00Z",
    modelVersion: "forgetting-model-v1.3.0",
  },
  {
    id: "pred-003",
    taskId: "task-002",
    taskTitle: "Submit Internship Document",
    riskScore: 54,
    riskLevel: "MEDIUM",
    reasons: [
      {
        label: "Context mismatch",
        detail: "Task requires 'Department' context but often planned at 'Home'.",
        weight: 0.4,
      },
      {
        label: "Historical completion rate",
        detail: "62% completion rate for admin document tasks.",
        weight: 0.35,
      },
      {
        label: "Recency",
        detail: "First occurrence of this specific task.",
        weight: 0.25,
      },
    ],
    generatedAt: "2026-08-18T06:00:00Z",
    modelVersion: "forgetting-model-v1.3.0",
  },
  {
    id: "pred-004",
    taskId: "task-005",
    taskTitle: "Reply to Advisor Email",
    riskScore: 28,
    riskLevel: "LOW",
    reasons: [
      {
        label: "Historical completion rate",
        detail: "85% completion rate for communication tasks.",
        weight: 0.6,
      },
      {
        label: "Short duration",
        detail: "Low-effort tasks are rarely forgotten.",
        weight: 0.4,
      },
    ],
    generatedAt: "2026-08-18T06:00:00Z",
    modelVersion: "forgetting-model-v1.3.0",
  },
];

export const mockRecommendations: Recommendation[] = [
  {
    id: "rec-001",
    recommendationType: "context_based_reminder",
    triggeringBehaviour: "Internship Document is associated with the Department context.",
    evidence: [
      { field: "association_confidence", value: "0.82", source: "Association:Department->Internship Document" },
      { field: "association_support", value: "0.40", source: "Association:Department->Internship Document" },
    ],
    evidenceStrength: 0.82,
    impactScore: 0.82,
    riskLevel: "MEDIUM",
    expectedBenefit: "Use a reliably observed context-task association when planning the next action.",
    feedback: [],
    context: "Department",
    reliableTasks: ["Collect Form", "Submit Record"],
    suggestedTasks: [
      {
        taskId: "task-002",
        title: "Internship Document",
        reason: "Often needed alongside admin visits to this context.",
      },
    ],
    generatedAt: "2026-08-18T08:00:00Z",
    status: "PENDING",
  },
  {
    id: "rec-002",
    recommendationType: "recurring_forgotten_task_prevention",
    triggeringBehaviour: "Pay Hostel Fee is associated with Home and has observed forgetting exposure.",
    evidence: [
      { field: "association_confidence", value: "0.71", source: "Association:Home->Pay Hostel Fee" },
      { field: "forgetting_probability", value: "0.71", source: "ForgettingPrediction:Pay Hostel Fee" },
    ],
    evidenceStrength: 0.71,
    impactScore: 0.71,
    riskLevel: "MEDIUM",
    expectedBenefit: "Reduce exposure to the observed forgetting risk by prompting this task in its associated context.",
    feedback: [],
    context: "Home",
    reliableTasks: ["Water Plants"],
    suggestedTasks: [
      {
        taskId: "task-006",
        title: "Pay Hostel Fee",
        reason: "Frequently forgotten during evening hours at home.",
      },
    ],
    generatedAt: "2026-08-18T18:00:00Z",
    status: "PENDING",
  },
];

export const mockInsights: BehaviourInsight[] = [
  {
    id: "insight-001",
    type: "FRICTION_SOURCE",
    title: "Your biggest friction source",
    description:
      "Notification interruptions between 12–1 PM cost you the most recovery time this week.",
    priority: "HIGH",
    metricLabel: "Avg. recovery cost",
    metricValue: "6.2 min/interruption",
    generatedAt: "2026-08-18T06:00:00Z",
  },
  {
    id: "insight-002",
    type: "FREQUENTLY_FORGOTTEN",
    title: "Your most frequently forgotten task",
    description:
      "\"Water Plants\" has been forgotten 8 times in the last 30 days, usually before 9 AM.",
    priority: "MEDIUM",
    metricLabel: "Forgotten",
    metricValue: "8 times / 30 days",
    generatedAt: "2026-08-18T06:00:00Z",
  },
  {
    id: "insight-003",
    type: "HIGH_INTERRUPTION_CONTEXT",
    title: "Your highest-interruption context",
    description:
      "The 'Library' context shows 2.3x more context switches than your daily average.",
    priority: "HIGH",
    metricLabel: "Context switches",
    metricValue: "2.3x average",
    generatedAt: "2026-08-18T06:00:00Z",
  },
  {
    id: "insight-004",
    type: "STRONGEST_ASSOCIATION",
    title: "Your strongest contextual association",
    description:
      "'Department' + 'Collect Form' has an 82% same-visit completion association.",
    priority: "LOW",
    metricLabel: "Confidence",
    metricValue: "82%",
    generatedAt: "2026-08-18T06:00:00Z",
  },
];
