"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import { RiskBadge } from "@/components/shared/risk-badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiData } from "@/hooks/use-api-data";
import { tasksApi } from "@/lib/api";
import type { Task } from "@/types";
import { formatMinutes } from "@/lib/utils";

export function TaskDetailDialog({
  task,
  open,
  onOpenChange,
}: {
  task: Task | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: events, status } = useApiData(
    () =>
      task
        ? tasksApi.listEvents(task.id)
        : Promise.resolve({ data: [], error: null }),
    [task?.id],
  );

  if (!task) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>{task.title}</DialogTitle>
            <TaskStatusBadge status={task.status} />
          </div>
          <DialogDescription>{task.description}</DialogDescription>
        </DialogHeader>

        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-xs text-muted-foreground">Context</dt>
            <dd className="font-medium text-foreground">{task.context}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Category</dt>
            <dd className="font-medium text-foreground">{task.category}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Priority</dt>
            <dd><RiskBadge level={task.priority} /></dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Forgotten count</dt>
            <dd className="font-mono font-medium text-foreground">
              {task.forgottenCount}
            </dd>
          </div>
          {task.estimatedMinutes && (
            <div>
              <dt className="text-xs text-muted-foreground">Estimated time</dt>
              <dd className="font-medium text-foreground">
                {formatMinutes(task.estimatedMinutes)}
              </dd>
            </div>
          )}
          <div>
            <dt className="text-xs text-muted-foreground">Completion streak</dt>
            <dd className="font-mono font-medium text-foreground">
              {task.completionStreak}
            </dd>
          </div>
        </dl>

        <Separator />

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Event history
          </p>
          {status === "loading" && (
            <div className="space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          )}
          {status === "success" && events && events.length === 0 && (
            <p className="text-xs text-muted-foreground">
              No events recorded for this task yet.
            </p>
          )}
          {status === "success" && events && events.length > 0 && (
            <ul className="space-y-1.5">
              {events.map((event) => (
                <li
                  key={event.id}
                  className="flex items-center justify-between text-xs"
                >
                  <span className="font-medium text-foreground">
                    {event.type}
                  </span>
                  <span className="font-mono text-muted-foreground">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
