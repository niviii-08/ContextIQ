import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskCreateForm } from "@/components/tasks/task-create-form";
import { tasksApi } from "@/lib/api";
import type { Task } from "@/types";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    tasksApi: {
      create: vi.fn(),
    },
  };
});

afterEach(() => {
  vi.clearAllMocks();
});

const buildTask = (): Task => ({
  id: "task-new",
  title: "Submit Timesheet",
  category: "Admin",
  context: "Department",
  status: "PENDING",
  priority: "MEDIUM",
  createdAt: "2026-08-18T00:00:00Z",
  updatedAt: "2026-08-18T00:00:00Z",
  tags: [],
  forgottenCount: 0,
  completionStreak: 0,
});

describe("TaskCreateForm", () => {
  it("submits a new task with the entered values", async () => {
    const user = userEvent.setup();
    vi.mocked(tasksApi.create).mockResolvedValue({
      data: buildTask(),
      error: null,
    });
    const onCreated = vi.fn();

    render(<TaskCreateForm onCreated={onCreated} />);

    await user.type(screen.getByLabelText(/title/i), "Submit Timesheet");
    await user.type(screen.getByLabelText(/category/i), "Admin");
    await user.type(screen.getByLabelText(/context/i), "Department");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => {
      expect(tasksApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Submit Timesheet",
          category: "Admin",
          context: "Department",
          priority: "MEDIUM",
        }),
      );
    });

    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
  });

  it("shows a validation error and does not submit when required fields are empty", async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();

    render(<TaskCreateForm onCreated={onCreated} />);
    await user.click(screen.getByRole("button", { name: /create task/i }));

    expect(
      await screen.findByText(/title, category, and context are required/i),
    ).toBeInTheDocument();
    expect(tasksApi.create).not.toHaveBeenCalled();
    expect(onCreated).not.toHaveBeenCalled();
  });
});
