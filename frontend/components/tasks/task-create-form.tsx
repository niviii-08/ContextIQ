"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { tasksApi } from "@/lib/api";
import type { CreateTaskInput, Priority } from "@/types";
import { Loader2 } from "lucide-react";

const PRIORITIES: Priority[] = ["LOW", "MEDIUM", "HIGH"];

export function TaskCreateForm({ onCreated }: { onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [context, setContext] = useState("");
  const [priority, setPriority] = useState<Priority>("MEDIUM");
  const [estimatedMinutes, setEstimatedMinutes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setCategory("");
    setContext("");
    setPriority("MEDIUM");
    setEstimatedMinutes("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!title.trim() || !category.trim() || !context.trim()) {
      setFormError("Title, category, and context are required.");
      return;
    }

    const input: CreateTaskInput = {
      title: title.trim(),
      description: description.trim() || undefined,
      category: category.trim(),
      context: context.trim(),
      priority,
      estimatedMinutes: estimatedMinutes
        ? Number(estimatedMinutes)
        : undefined,
    };

    setSubmitting(true);
    const result = await tasksApi.create(input);
    setSubmitting(false);

    if (result.error) {
      setFormError(result.error.message);
      return;
    }

    resetForm();
    onCreated();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>New task</CardTitle>
        <CardDescription>
          Tasks you create are tracked for completion, forgetting, and
          contextual association.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="task-title">Title</Label>
              <Input
                id="task-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Submit Lab Record"
                required
              />
            </div>

            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="task-description">Description</Label>
              <Textarea
                id="task-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional details about this task"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="task-category">Category</Label>
              <Input
                id="task-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. Academic"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="task-context">Context</Label>
              <Input
                id="task-context"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="e.g. Department"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="task-priority">Priority</Label>
              <Select value={priority} onValueChange={(v) => setPriority(v as Priority)}>
                <SelectTrigger id="task-priority" aria-label="Priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITIES.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="task-estimate">Estimated minutes</Label>
              <Input
                id="task-estimate"
                type="number"
                min={0}
                inputMode="numeric"
                value={estimatedMinutes}
                onChange={(e) => setEstimatedMinutes(e.target.value)}
                placeholder="e.g. 30"
              />
            </div>
          </div>

          {formError && (
            <p role="alert" className="text-xs font-medium text-destructive">
              {formError}
            </p>
          )}

          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />}
            {submitting ? "Creating…" : "Create task"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
