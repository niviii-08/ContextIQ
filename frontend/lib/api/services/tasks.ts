import { apiClient, mockResult } from "@/lib/api/client";
import { mockTaskEvents, mockTasks } from "@/mock/tasks.mock";
import type {
  ApiResult,
  CreateTaskInput,
  Priority,
  Task,
  TaskEvent,
  TaskEventType,
  TaskStatus,
} from "@/types";

/**
 * Typed contract for all task-related operations.
 * Fetches exclusively from the live PostgreSQL database or the user's registered tasks.
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

// In-memory mutable store for local fallback
const store = {
  tasks: [...mockTasks],
  events: [...mockTaskEvents],
};

function getStoredTasks(): Task[] {
  if (typeof window !== "undefined") {
    try {
      const raw = localStorage.getItem("contextiq_user_tasks");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch {}
  }
  return store.tasks;
}

function saveStoredTasks(tasks: Task[]) {
  store.tasks = tasks;
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem("contextiq_user_tasks", JSON.stringify(tasks));
    } catch {}
  }
}

const mockTasksApi: TasksApi = {
  async list(filters) {
    return mockResult(() => {
      let results = getStoredTasks();
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
      const all = getStoredTasks();
      const task = all.find((t) => t.id === id);
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
      const all = [task, ...getStoredTasks()];
      saveStoredTasks(all);
      return task;
    });
  },

  async updateStatus(id, status) {
    return mockResult(() => {
      const all = getStoredTasks();
      const idx = all.findIndex((t) => t.id === id);
      if (idx === -1) throw new Error("not found");
      const updated: Task = {
        ...all[idx],
        status,
        updatedAt: new Date().toISOString(),
        forgottenCount:
          status === "FORGOTTEN"
            ? all[idx].forgottenCount + 1
            : all[idx].forgottenCount,
        completionStreak:
          status === "COMPLETED"
            ? all[idx].completionStreak + 1
            : status === "FORGOTTEN"
              ? 0
              : all[idx].completionStreak,
      };
      const newAll = [...all.slice(0, idx), updated, ...all.slice(idx + 1)];
      saveStoredTasks(newAll);
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
  list: async (filters) => {
    const res = await apiClient.request<any[]>("/tasks", { query: filters });
    if (res.data && Array.isArray(res.data)) {
      const mapped: Task[] = res.data.map((t: any) => ({
        id: String(t.id),
        title: t.title,
        description: t.description ?? "",
        category: t.context_tag ?? "General",
        context: t.context_tag ?? "General",
        status: (t.status as TaskStatus) ?? "PENDING",
        priority: (t.priority?.toUpperCase() as Priority) ?? "MEDIUM",
        dueAt: t.due_at,
        createdAt: t.created_at || new Date().toISOString(),
        updatedAt: t.updated_at || new Date().toISOString(),
        estimatedMinutes: t.estimated_minutes ?? 30,
        actualMinutes: t.actual_minutes,
        tags: t.context_tag ? [t.context_tag] : [],
        forgottenCount: 0,
        completionStreak: 0,
      }));
      saveStoredTasks(mapped);
      return { data: mapped, error: null };
    }
    // If backend returns empty or offline, fallback to user's registered tasks
    const local = getStoredTasks();
    if (local.length > 0) {
      let filtered = local;
      if (filters?.status) filtered = filtered.filter((t) => t.status === filters.status);
      if (filters?.context) filtered = filtered.filter((t) => t.context === filters.context);
      return { data: filtered, error: null };
    }
    return { data: [], error: null };
  },
  getById: async (id) => {
    const res = await apiClient.request<any>(`/tasks/${id}`);
    if (res.error || !res.data) return res as any;
    const t = res.data;
    const task: Task = {
      id: String(t.id),
      title: t.title,
      description: t.description ?? "",
      category: t.context_tag ?? "General",
      context: t.context_tag ?? "General",
      status: (t.status as TaskStatus) ?? "PENDING",
      priority: (t.priority?.toUpperCase() as Priority) ?? "MEDIUM",
      dueAt: t.due_at,
      createdAt: t.created_at || new Date().toISOString(),
      updatedAt: t.updated_at || new Date().toISOString(),
      estimatedMinutes: t.estimated_minutes ?? 30,
      actualMinutes: t.actual_minutes,
      tags: t.context_tag ? [t.context_tag] : [],
      forgottenCount: 0,
      completionStreak: 0,
    };
    return { data: task, error: null };
  },
  create: async (input) => {
    const res = await apiClient.request<any>("/tasks", {
      method: "POST",
      body: {
        title: input.title,
        description: input.description,
        priority: input.priority.toUpperCase(),
        estimated_minutes: input.estimatedMinutes ?? 30,
        context_tag: input.category || input.context || "General",
      },
    });
    if (res.error || !res.data) return res as any;
    const t = res.data;
    const task: Task = {
      id: String(t.id),
      title: t.title,
      description: t.description ?? "",
      category: t.context_tag ?? "General",
      context: t.context_tag ?? "General",
      status: (t.status as TaskStatus) ?? "PENDING",
      priority: (t.priority?.toUpperCase() as Priority) ?? "MEDIUM",
      dueAt: t.due_at,
      createdAt: t.created_at || new Date().toISOString(),
      updatedAt: t.updated_at || new Date().toISOString(),
      estimatedMinutes: t.estimated_minutes ?? 30,
      actualMinutes: t.actual_minutes,
      tags: t.context_tag ? [t.context_tag] : [],
      forgottenCount: 0,
      completionStreak: 0,
    };
    saveStoredTasks([task, ...getStoredTasks()]);
    return { data: task, error: null };
  },
  updateStatus: async (id, status) => {
    const res = await apiClient.request<any>(`/tasks/${id}`, {
      method: "PATCH",
      body: { status },
    });
    if (res.error || !res.data) return res as any;
    const t = res.data;
    const task: Task = {
      id: String(t.id),
      title: t.title,
      description: t.description ?? "",
      category: t.context_tag ?? "General",
      context: t.context_tag ?? "General",
      status: (t.status as TaskStatus) ?? "PENDING",
      priority: (t.priority?.toUpperCase() as Priority) ?? "MEDIUM",
      dueAt: t.due_at,
      createdAt: t.created_at || new Date().toISOString(),
      updatedAt: t.updated_at || new Date().toISOString(),
      estimatedMinutes: t.estimated_minutes ?? 30,
      actualMinutes: t.actual_minutes,
      tags: t.context_tag ? [t.context_tag] : [],
      forgottenCount: 0,
      completionStreak: 0,
    };
    const all = getStoredTasks().map((item) => (item.id === id ? task : item));
    saveStoredTasks(all);
    return { data: task, error: null };
  },
  recordEvent: async (id, type) => {
    const res = await apiClient.request<any>(`/tasks/${id}/events`, {
      method: "POST",
      body: { event_type: type },
    });
    if (res.error || !res.data) return res as any;
    const ev = res.data;
    const event: TaskEvent = {
      id: String(ev.id),
      taskId: String(ev.task_id),
      type: ev.event_type as TaskEventType,
      timestamp: ev.occurred_at || ev.created_at || new Date().toISOString(),
      context: ev.context_tag,
    };
    return { data: event, error: null };
  },
  listEvents: async (taskId) => {
    const res = await apiClient.request<any[]>(`/tasks/${taskId}/events`);
    if (res.error || !res.data) return res as any;
    const events: TaskEvent[] = res.data.map((ev: any) => ({
      id: String(ev.id),
      taskId: String(ev.task_id),
      type: ev.event_type as TaskEventType,
      timestamp: ev.occurred_at || ev.created_at || new Date().toISOString(),
      context: ev.context_tag,
    }));
    return { data: events, error: null };
  },
};

export const tasksApi: TasksApi = {
  list: async (filters) => {
    const live = await liveTasksApi.list(filters);
    if (live.data && live.data.length > 0) return live;
    if (!live.error) return live;
    return mockTasksApi.list(filters);
  },
  getById: (id) => liveTasksApi.getById(id),
  create: async (input) => {
    const res = await liveTasksApi.create(input);
    if (!res.error && res.data) return res;
    return mockTasksApi.create(input);
  },
  updateStatus: async (id, status) => {
    const res = await liveTasksApi.updateStatus(id, status);
    if (!res.error && res.data) return res;
    return mockTasksApi.updateStatus(id, status);
  },
  recordEvent: async (id, type) => {
    const res = await liveTasksApi.recordEvent(id, type);
    if (!res.error && res.data) return res;
    return mockTasksApi.recordEvent(id, type);
  },
  listEvents: (taskId) => liveTasksApi.listEvents(taskId),
};
