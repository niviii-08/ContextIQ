import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState, ErrorState } from "@/components/shared/async-states";

describe("EmptyState", () => {
  it("renders title, description, and optional action", () => {
    render(
      <EmptyState
        title="Nothing here"
        description="Try a different filter."
        action={<button>Reset</button>}
      />,
    );

    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Try a different filter.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("renders the error message with role=alert and calls onRetry when clicked", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(<ErrorState message="Something broke." onRetry={onRetry} />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Something broke.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders without a retry button when onRetry is not provided", () => {
    render(<ErrorState message="Something broke." />);
    expect(
      screen.queryByRole("button", { name: /try again/i }),
    ).not.toBeInTheDocument();
  });
});
