import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useApiData } from "@/hooks/use-api-data";
import type { ApiResult } from "@/types";

describe("useApiData", () => {
  it("resolves fulfilled fetcher into success state with data", async () => {
    const payload: ApiResult<string> = {
      data: "hello",
      error: null,
    };
    const fetcher = async () => payload;

    const { result } = renderHook(() => useApiData<string>(fetcher));

    expect(result.current.status).toBe("loading");

    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });

    expect(result.current.data).toBe("hello");
    expect(result.current.error).toBeNull();
  });

  it("wraps ApiResult.error into error state (non-throwing)", async () => {
    const payload: ApiResult<string> = {
      data: null,
      error: {
        code: "VALIDATION_ERROR",
        message: "Bad input",
        status: 422,
      },
    };
    const fetcher = async () => payload;

    const { result } = renderHook(() => useApiData<string>(fetcher));

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.error?.code).toBe("VALIDATION_ERROR");
    expect(result.current.error?.message).toBe("Bad input");
    expect(result.current.data).toBeNull();
  });

  it("handles a rejected fetcher promise with NETWORK_ERROR code", async () => {
    const fetcher = async (): Promise<ApiResult<string>> => {
      throw new TypeError("Failed to fetch");
    };

    const { result } = renderHook(() => useApiData<string>(fetcher));

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.code).toBe("NETWORK_ERROR");
    expect(result.current.error?.message).toContain("Network error");
    expect(result.current.error?.message).toContain("Failed to fetch");
    expect(result.current.error?.status).toBe(0);
  });

  it("handles non-Error rejection values with NETWORK_ERROR", async () => {
    const fetcher = async (): Promise<ApiResult<string>> => {
      // eslint-disable-next-line prefer-promise-reject-errors
      return Promise.reject("plain string rejection");
    };

    const { result } = renderHook(() => useApiData<string>(fetcher));

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.error?.code).toBe("NETWORK_ERROR");
    expect(result.current.error?.message).toContain("plain string rejection");
  });
});
