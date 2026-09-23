import { Badge } from "@/components/ui/badge";
import type { TaskStatus } from "@/types";

const STATUS_STYLE: Record<TaskStatus, string> = {
  PENDING: "border-border text-muted-foreground",
  IN_PROGRESS: "border-transparent bg-primary/10 text-primary",
  PAUSED: "border-transparent bg-risk-medium/15 text-risk-medium",
  COMPLETED: "border-transparent bg-risk-low/15 text-risk-low",
  FORGOTTEN: "border-transparent bg-risk-high/15 text-risk-high",
};

const STATUS_LABEL: Record<TaskStatus, string> = {
  PENDING: "Pending",
  IN_PROGRESS: "In progress",
  PAUSED: "Paused",
  COMPLETED: "Completed",
  FORGOTTEN: "Forgotten",
};

export function TaskStatusBadge({ status }: { status: TaskStatus }) {
  return (
    <Badge variant="outline" className={STATUS_STYLE[status]}>
      {STATUS_LABEL[status]}
    </Badge>
  );
}
