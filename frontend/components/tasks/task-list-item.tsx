"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import { TaskActions } from "@/components/tasks/task-actions";
import { RiskBadge } from "@/components/shared/risk-badge";
import type { Task, TaskStatus } from "@/types";
import { MapPin, Clock, Utensils, Shirt, AlertCircle, Laptop, CheckCircle2 } from "lucide-react";
import { formatMinutes, cn } from "@/lib/utils";

export function TaskListItem({
  task,
  onAction,
  onOpen,
}: {
  task: Task;
  onAction: (taskId: string, nextStatus: TaskStatus) => void;
  onOpen: (task: Task) => void;
}) {
  const isChore =
    task.category?.toLowerCase().includes("daily chore") ||
    task.title?.toLowerCase().includes("daily chore");
  const isWeekendChore =
    task.category?.toLowerCase().includes("weekend chore") ||
    task.title?.toLowerCase().includes("weekend chore");
  const isAnchor =
    task.category?.toLowerCase().includes("memory anchor") ||
    task.title?.toLowerCase().includes("anti-forget") ||
    task.title?.toLowerCase().includes("anchor");

  const CategoryIcon = isChore
    ? Utensils
    : isWeekendChore
      ? Shirt
      : isAnchor
        ? AlertCircle
        : Laptop;

  const categoryColorClass = isChore
    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
    : isWeekendChore
      ? "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20"
      : isAnchor
        ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
        : "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20";

  return (
    <Card className="glass-card card-hover-lift border-border/80 group transition-all duration-200">
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={() => onOpen(task)}
          className="flex flex-1 flex-col items-start gap-1.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg p-1 -m-1 transition-colors"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1.5 text-sm font-bold text-foreground group-hover:text-primary transition-colors">
              <CategoryIcon className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
              {task.title}
            </span>
            <TaskStatusBadge status={task.status} />
            <RiskBadge level={task.priority} />
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-mono font-semibold border",
                categoryColorClass,
              )}
            >
              {task.category || "General"}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            {task.context && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
                <span>{task.context}</span>
              </span>
            )}
            {task.estimatedMinutes && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
                <span>{formatMinutes(task.estimatedMinutes)}</span>
              </span>
            )}
            {task.forgottenCount > 0 && (
              <span className="text-risk-high font-semibold flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
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
