import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BehaviourOverview } from "@/components/dashboard/behaviour-overview";
import { analyticsApi } from "@/lib/api";
import { mockDailySummary } from "@/mock/analytics.mock";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    analyticsApi: {
      getDailySummary: vi.fn(),
    },
  };
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("BehaviourOverview", () => {
  it("renders the friction score and metrics after a successful fetch", async () => {
    vi.mocked(analyticsApi.getDailySummary).mockResolvedValue({
      data: mockDailySummary,
      error: null,
    });

    render(<BehaviourOverview />);

    expect(
      screen.getByRole("heading", { name: /today's behaviour overview/i }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Friction Score")).toBeInTheDocument();
    });

    expect(screen.getByText(String(mockDailySummary.tasksCompleted))).toBeInTheDocument();
    expect(screen.getByText(String(mockDailySummary.tasksForgotten))).toBeInTheDocument();
  });

  it("renders an error state with a retry action when the fetch fails", async () => {
    vi.mocked(analyticsApi.getDailySummary).mockResolvedValue({
      data: null,
      error: { code: "NETWORK_ERROR", message: "Network error.", status: 0 },
    });

    render(<BehaviourOverview />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/network error/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });
});
