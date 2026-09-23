import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ForgetRiskPanel } from "@/components/predictions/forget-risk-panel";
import { predictionApi } from "@/lib/api";
import { mockPredictions } from "@/mock/analytics.mock";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    predictionApi: {
      listPredictions: vi.fn(),
    },
  };
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("ForgetRiskPanel", () => {
  it("renders prediction cards with risk score and reasons", async () => {
    vi.mocked(predictionApi.listPredictions).mockResolvedValue({
      data: mockPredictions,
      error: null,
    });

    render(<ForgetRiskPanel />);

    await waitFor(() => {
      expect(screen.getByText("Lab Record")).toBeInTheDocument();
    });

    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getAllByText("HIGH").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/previous forgetting frequency/i).length,
    ).toBeGreaterThan(0);
  });

  it("renders an empty state when no predictions match the filter", async () => {
    vi.mocked(predictionApi.listPredictions).mockResolvedValue({
      data: [],
      error: null,
    });

    render(<ForgetRiskPanel />);

    await waitFor(() => {
      expect(
        screen.getByText(/no predictions at this risk level/i),
      ).toBeInTheDocument();
    });
  });
});
