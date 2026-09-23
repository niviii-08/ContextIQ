"use client";

import { Button } from "@/components/ui/button";
import { Play, Pause, CheckCircle2, XCircle, RotateCw } from "lucide-react";
import type { Task, TaskStatus } from "@/types";

/**
 * Renders the valid next actions for a task's current status.
 * Every click produces a task event (see tasksApi.recordEvent) in addition
 * to updating status, so downstream analytics/ML can consume the event log.
 */
export function TaskActions({
  task,
  onAction,
  size = "sm",
}: {
  task: Task;
  onAction: (taskId: string, nextStatus: TaskStatus) => void;
  size?: "sm" | "default";
}) {
  const actions: {
    label: string;
    status: TaskStatus;
    icon: typeof Play;
    variant?: "default" | "outline" | "destructive";
  }[] = [];

  if (task.status === "PENDING") {
    actions.push({ label: "Start", status: "IN_PROGRESS", icon: Play });
  }
  if (task.status === "IN_PROGRESS") {
    actions.push({ label: "Pause", status: "PAUSED", icon: Pause, variant: "outline" });
    actions.push({ label: "Complete", status: "COMPLETED", icon: CheckCircle2 });
  }
  if (task.status === "PAUSED") {
    actions.push({ label: "Resume", status: "IN_PROGRESS", icon: RotateCw });
  }
  if (task.status === "PENDING" || task.status === "IN_PROGRESS" || task.status === "PAUSED") {
    actions.push({
      label: "Mark forgotten",
      status: "FORGOTTEN",
      icon: XCircle,
      variant: "destructive",
    });
  }

  if (actions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Button
            key={action.label}
            size={size}
            variant={action.variant ?? "default"}
            onClick={() => onAction(task.id, action.status)}
            aria-label={`${action.label} task: ${task.title}`}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {action.label}
          </Button>
        );
      })}
    </div>
  );
}
