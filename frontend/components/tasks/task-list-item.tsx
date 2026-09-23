"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import { TaskActions } from "@/components/tasks/task-actions";
import { RiskBadge } from "@/components/shared/risk-badge";
import type { Task, TaskStatus } from "@/types";
import { MapPin, Clock } from "lucide-react";
import { formatMinutes } from "@/lib/utils";

export function TaskListItem({
  task,
  onAction,
  onOpen,
}: {
  task: Task;
  onAction: (taskId: string, nextStatus: TaskStatus) => void;
  onOpen: (task: Task) => void;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={() => onOpen(task)}
          className="flex flex-1 flex-col items-start gap-1.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-foreground">
              {task.title}
            </span>
            <TaskStatusBadge status={task.status} />
            <RiskBadge level={task.priority} />
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <MapPin className="h-3 w-3" aria-hidden="true" />
              {task.context}
            </span>
            <span>{task.category}</span>
            {task.estimatedMinutes && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" aria-hidden="true" />
                {formatMinutes(task.estimatedMinutes)}
              </span>
            )}
            {task.forgottenCount > 0 && (
              <span className="text-risk-high">
                Forgotten {task.forgottenCount}x
              </span>
            )}
          </div>
        </button>
        <TaskActions task={task} onAction={onAction} />
      </CardContent>
    </Card>
  );
}
