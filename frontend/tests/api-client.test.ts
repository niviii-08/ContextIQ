import { describe, it, expect } from "vitest";
import { mockResult, apiClient } from "@/lib/api/client";

describe("apiClient / mockResult", () => {
  it("resolves with data when the factory succeeds", async () => {
    const result = await mockResult(() => ({ value: 42 }), { latencyMs: 0 });
    expect(result.error).toBeNull();
    expect(result.data).toEqual({ value: 42 });
  });

  it("resolves with a normalized error when failRate forces a failure", async () => {
    const result = await mockResult(() => ({ value: 42 }), {
      latencyMs: 0,
      failRate: 1,
    });
    expect(result.data).toBeNull();
    expect(result.error).not.toBeNull();
    expect(result.error?.code).toBe("MOCK_SIMULATED_ERROR");
    expect(result.error?.status).toBe(500);
  });

  it("resolves with an error when the factory throws", async () => {
    const result = await mockResult<{ value: number }>(
      () => {
        throw new Error("boom");
      },
      { latencyMs: 0 },
    );
    expect(result.data).toBeNull();
    expect(result.error?.code).toBe("MOCK_ERROR");
  });

  it("defaults to mock mode unless NEXT_PUBLIC_USE_MOCK is explicitly false", () => {
    expect(apiClient.USE_MOCK).toBe(true);
  });
});
