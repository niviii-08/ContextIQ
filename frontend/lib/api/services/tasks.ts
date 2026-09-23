import { apiClient, mockResult } from "@/lib/api/client";
import { mockTaskEvents, mockTasks } from "@/mock/tasks.mock";
import type {
  ApiResult,
  CreateTaskInput,
  Task,
  TaskEvent,
  TaskEventType,
  TaskStatus,
} from "@/types";

/**
 * Typed contract for all task-related operations.
 * Swap the implementation (mock vs live) without touching any component.
 */
export interface TasksApi {
  list(filters?: { status?: TaskStatus; context?: string }): Promise<
    ApiResult<Task[]>
  >;
  getById(id: string): Promise<ApiResult<Task>>;
  create(input: CreateTaskInput): Promise<ApiResult<Task>>;
  updateStatus(id: string, status: TaskStatus): Promise<ApiResult<Task>>;
  recordEvent(
    id: string,
    type: TaskEventType,
  ): Promise<ApiResult<TaskEvent>>;
  listEvents(taskId: string): Promise<ApiResult<TaskEvent[]>>;
}

// In-memory mutable store for demo/mock mode only.
const store = {
  tasks: [...mockTasks],
  events: [...mockTaskEvents],
};

const mockTasksApi: TasksApi = {
  async list(filters) {
    return mockResult(() => {
      let results = store.tasks;
      if (filters?.status) {
        results = results.filter((t) => t.status === filters.status);
      }
      if (filters?.context) {
        results = results.filter((t) => t.context === filters.context);
      }
      return results;
    });
  },

  async getById(id) {
    return mockResult(() => {
      const task = store.tasks.find((t) => t.id === id);
      if (!task) throw new Error("not found");
      return task;
    });
  },

  async create(input) {
    return mockResult(() => {
      const now = new Date().toISOString();
      const task: Task = {
        id: `task-${Math.random().toString(36).slice(2, 9)}`,
        title: input.title,
        description: input.description,
        category: input.category,
        context: input.context,
        status: "PENDING",
        priority: input.priority,
        dueAt: input.dueAt,
        createdAt: now,
        updatedAt: now,
        estimatedMinutes: input.estimatedMinutes,
        tags: input.tags ?? [],
        forgottenCount: 0,
        completionStreak: 0,
      };
      store.tasks = [task, ...store.tasks];
      return task;
    });
  },

  async updateStatus(id, status) {
    return mockResult(() => {
      const idx = store.tasks.findIndex((t) => t.id === id);
      if (idx === -1) throw new Error("not found");
      const updated: Task = {
        ...store.tasks[idx],
        status,
        updatedAt: new Date().toISOString(),
        forgottenCount:
          status === "FORGOTTEN"
            ? store.tasks[idx].forgottenCount + 1
            : store.tasks[idx].forgottenCount,
        completionStreak:
          status === "COMPLETED"
            ? store.tasks[idx].completionStreak + 1
            : status === "FORGOTTEN"
              ? 0
              : store.tasks[idx].completionStreak,
      };
      store.tasks = [
        ...store.tasks.slice(0, idx),
        updated,
        ...store.tasks.slice(idx + 1),
      ];
      return updated;
    });
  },

  async recordEvent(id, type) {
    return mockResult(() => {
      const event: TaskEvent = {
        id: `evt-${Math.random().toString(36).slice(2, 9)}`,
        taskId: id,
        type,
        timestamp: new Date().toISOString(),
      };
      store.events = [event, ...store.events];
      return event;
    });
  },

  async listEvents(taskId) {
    return mockResult(() => store.events.filter((e) => e.taskId === taskId));
  },
};

const liveTasksApi: TasksApi = {
  list: (filters) =>
    apiClient.request<Task[]>("/tasks", { query: filters }),
  getById: (id) => apiClient.request<Task>(`/tasks/${id}`),
  create: (input) =>
    apiClient.request<Task>("/tasks", { method: "POST", body: input }),
  updateStatus: (id, status) =>
    apiClient.request<Task>(`/tasks/${id}/status`, {
      method: "PATCH",
      body: { status },
    }),
  recordEvent: (id, type) =>
    apiClient.request<TaskEvent>(`/tasks/${id}/events`, {
      method: "POST",
      body: { type },
    }),
  listEvents: (taskId) =>
    apiClient.request<TaskEvent[]>(`/tasks/${taskId}/events`),
};

export const tasksApi: TasksApi = apiClient.USE_MOCK
  ? mockTasksApi
  : liveTasksApi;
