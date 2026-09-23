"use client";

import { useState } from "react";
import { tasksApi } from "@/lib/api";
import { useApiData } from "@/hooks/use-api-data";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/async-states";
import { TaskListItem } from "@/components/tasks/task-list-item";
import { TaskCreateForm } from "@/components/tasks/task-create-form";
import { TaskDetailDialog } from "@/components/tasks/task-detail-dialog";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Task, TaskStatus } from "@/types";

const STATUS_FILTERS: { label: string; value: TaskStatus | "ALL" }[] = [
  { label: "All", value: "ALL" },
  { label: "Pending", value: "PENDING" },
  { label: "In progress", value: "IN_PROGRESS" },
  { label: "Paused", value: "PAUSED" },
  { label: "Completed", value: "COMPLETED" },
  { label: "Forgotten", value: "FORGOTTEN" },
];

export function TaskManager() {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "ALL">("ALL");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: tasks, status, error, refetch } = useApiData(
    () =>
      tasksApi.list(
        statusFilter === "ALL" ? undefined : { status: statusFilter },
      ),
    [statusFilter],
  );

  const handleAction = async (taskId: string, nextStatus: TaskStatus) => {
    const eventType =
      nextStatus === "IN_PROGRESS"
        ? "STARTED"
        : nextStatus === "PAUSED"
          ? "PAUSED"
          : nextStatus === "COMPLETED"
            ? "COMPLETED"
            : "FORGOTTEN";

    await tasksApi.updateStatus(taskId, nextStatus);
    await tasksApi.recordEvent(taskId, eventType);
    refetch();
  };

  const handleOpen = (task: Task) => {
    setSelectedTask(task);
    setDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <TaskCreateForm onCreated={refetch} />

      <section aria-labelledby="task-list-heading">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2
            id="task-list-heading"
            className="text-sm font-semibold tracking-tight text-foreground"
          >
            Tasks
          </h2>
          <Tabs
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as TaskStatus | "ALL")}
          >
            <TabsList aria-label="Filter tasks by status" className="flex-wrap">
              {STATUS_FILTERS.map((f) => (
                <TabsTrigger key={f.value} value={f.value}>
                  {f.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {status === "loading" && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        )}

        {status === "error" && (
          <ErrorState
            message={error?.message ?? "We couldn't load your tasks."}
            onRetry={refetch}
          />
        )}

        {status === "success" && tasks && tasks.length === 0 && (
          <EmptyState
            title="No tasks in this view"
            description="Create a task above, or choose a different status filter."
          />
        )}

        {status === "success" && tasks && tasks.length > 0 && (
          <div className="space-y-3">
            {tasks.map((task) => (
              <TaskListItem
                key={task.id}
                task={task}
                onAction={handleAction}
                onOpen={handleOpen}
              />
            ))}
          </div>
        )}
      </section>

      <TaskDetailDialog
        task={selectedTask}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </div>
  );
}
