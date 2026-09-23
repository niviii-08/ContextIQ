import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RecommendationCard } from "@/components/recommendations/recommendation-card";
import { mockRecommendations } from "@/mock/analytics.mock";

describe("RecommendationCard", () => {
  const recommendation = mockRecommendations[0];

  it("renders reliable tasks and suggested tasks", () => {
    render(
      <RecommendationCard
        recommendation={recommendation}
        onAdd={vi.fn()}
        onDismiss={vi.fn()}
        onFeedback={vi.fn()}
      />,
    );

    expect(screen.getByText(recommendation.context)).toBeInTheDocument();
    recommendation.reliableTasks.forEach((title) => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
    expect(
      screen.getByText(recommendation.suggestedTasks[0].title),
    ).toBeInTheDocument();
  });

  it("calls onAdd when the Add button is clicked", async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn();

    render(
      <RecommendationCard
        recommendation={recommendation}
        onAdd={onAdd}
        onDismiss={vi.fn()}
        onFeedback={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /^add/i }));
    expect(onAdd).toHaveBeenCalledWith(recommendation);
  });

  it("calls onDismiss when the Dismiss button is clicked", async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();

    render(
      <RecommendationCard
        recommendation={recommendation}
        onAdd={vi.fn()}
        onDismiss={onDismiss}
        onFeedback={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /dismiss/i }));
    expect(onDismiss).toHaveBeenCalledWith(recommendation);
  });
});
