"use client";

import { useEffect, useRef, useState } from "react";
import type { ApiError, ApiResult } from "@/types";

export type AsyncStatus = "idle" | "loading" | "error" | "success";

export interface UseApiDataResult<T> {
  data: T | null;
  status: AsyncStatus;
  error: ApiError | null;
  refetch: () => void;
}

/**
 * Wraps any `() => Promise<ApiResult<T>>` service call with consistent
 * loading / error / success state so components never render a blank
 * screen while data is in flight or missing.
 *
 * `deps` controls when the fetch re-runs (e.g. a filter changing), the same
 * way a manual `useEffect` dependency array would.
 */
export function useApiData<T>(
  fetcher: () => Promise<ApiResult<T>>,
  deps: React.DependencyList = [],
): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<AsyncStatus>("idle");
  const [error, setError] = useState<ApiError | null>(null);
  const requestId = useRef(0);
  const fetcherRef = useRef(fetcher);
  const [reloadToken, setReloadToken] = useState(0);

  // This hook intentionally fetches inside an effect and updates state from
  // the async result — the standard "sync external data on mount/deps
  // change" pattern. The newer react-hooks lint rules flag this shape
  // aggressively; it's safe here because every state update is guarded by
  // the `requestId` check, which discards stale/out-of-order responses.
  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  // Status must flip to "loading" synchronously when deps change so
  // consumers never render a stale frame between the change and the fetch
  // settling; the requestId guard below discards any stale-response cascade.
  useEffect(() => {
    const id = ++requestId.current;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setStatus("loading");
    setError(null);
    fetcherRef.current().then((result) => {
      if (id !== requestId.current) return; // stale response, ignore
      if (result.error) {
        setError(result.error);
        setStatus("error");
      } else {
        setData(result.data);
        setStatus("success");
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadToken, ...deps]);

  const refetch = () => setReloadToken((t) => t + 1);

  return { data, status, error, refetch };
}
