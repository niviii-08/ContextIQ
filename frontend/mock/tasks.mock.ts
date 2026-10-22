import type { Task, TaskEvent } from "@/types";

/**
 * Clean Task Store — no hardcoded fake tasks.
 * Real tasks are populated exclusively from user onboarding and the PostgreSQL database.
 */
export const mockTasks: Task[] = [];
export const mockTaskEvents: TaskEvent[] = [];
