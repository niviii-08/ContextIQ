import type { ApiError, ApiResult } from "@/types";

/**
 * Central API client.
 *
 * This is the ONLY place that should know about HTTP details (base URL,
 * headers, auth token, error normalization). Every service module
 * (tasksApi, analyticsApi, ...) is built on top of `apiClient.request`.
 *
 * Switching from mock data to a real backend is a ONE-LINE change:
 * set NEXT_PUBLIC_USE_MOCK=false and the base URLs in .env.
 * No component code needs to change because components only ever talk
 * to the `*Api` service objects in lib/api/services/*.
 */

export const USE_MOCK =
  (process.env.NEXT_PUBLIC_USE_MOCK ?? "true").toLowerCase() !== "false";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const ANALYTICS_API_URL =
  process.env.NEXT_PUBLIC_ANALYTICS_API_URL ?? API_BASE_URL;

export const PREDICTION_API_URL =
  process.env.NEXT_PUBLIC_PREDICTION_API_URL ?? API_BASE_URL;

export const CONTEXT_API_URL =
  process.env.NEXT_PUBLIC_CONTEXT_API_URL ?? "http://localhost:8003/api/v1";

export const INSIGHTS_API_URL =
  process.env.NEXT_PUBLIC_INSIGHTS_API_URL ?? "http://localhost:8004/api/v1";

export const RECOMMENDATION_API_URL =
  process.env.NEXT_PUBLIC_RECOMMENDATION_API_URL ?? CONTEXT_API_URL;

const DEFAULT_TIMEOUT_MS = 10_000;

export type ServiceBaseUrl =
  | "core"
  | "analytics"
  | "prediction"
  | "context"
  | "insights"
  | "recommendation";

const BASE_URLS: Record<ServiceBaseUrl, string> = {
  core: API_BASE_URL,
  analytics: ANALYTICS_API_URL,
  prediction: PREDICTION_API_URL,
  context: CONTEXT_API_URL,
  insights: INSIGHTS_API_URL,
  recommendation: RECOMMENDATION_API_URL,
};

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  baseUrl?: ServiceBaseUrl | string;
}

function resolveBaseUrl(baseUrl: RequestOptions["baseUrl"] | undefined): string {
  if (!baseUrl) return API_BASE_URL;
  if (typeof baseUrl === "string" && baseUrl in BASE_URLS) {
    return BASE_URLS[baseUrl as ServiceBaseUrl];
  }
  return baseUrl as string;
}

function buildUrl(
  path: string,
  query?: Record<string, string | number | boolean | undefined>,
  baseOverride?: RequestOptions["baseUrl"],
): string {
  const base = resolveBaseUrl(baseOverride);
  const url = new URL(
    path.startsWith("http") ? path : `${base}${path}`,
  );
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined) url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
}

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("contextiq_token");
}

function normalizeError(status: number, payload: unknown): ApiError {
  if (
    payload &&
    typeof payload === "object" &&
    "code" in payload &&
    "message" in payload
  ) {
    const p = payload as Partial<ApiError>;
    return {
      code: p.code ?? "UNKNOWN_ERROR",
      message: p.message ?? "Something went wrong.",
      status,
      details: p.details,
    };
  }
  if (typeof payload === "string" && payload.length > 0) {
    return {
      code: "UNKNOWN_ERROR",
      message: payload.slice(0, 500),
      status,
    };
  }
  return {
    code: "UNKNOWN_ERROR",
    message: "Something went wrong. Please try again.",
    status,
  };
}

function getDevUserId(): string | null {
  return process.env.NEXT_PUBLIC_DEV_USER_ID ?? null;
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResult<T>> {
  const { method = "GET", body, query, headers, signal, baseUrl } = options;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const combinedSignal = signal ?? controller.signal;

  try {
    const token = getAuthToken();
    const devUserId = getDevUserId();
    const res = await fetch(buildUrl(path, query, baseUrl), {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(devUserId && !token ? { "X-User-Id": devUserId } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: combinedSignal,
    });

    clearTimeout(timeout);

    let payload: unknown = null;
    const text = await res.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = text;
      }
    }

    if (!res.ok) {
      return { data: null, error: normalizeError(res.status, payload) };
    }

    if (res.status !== 204 && (payload === null || typeof payload === "string")) {
      return {
        data: null,
        error: {
          code: "MALFORMED_RESPONSE",
          message: "The service returned an invalid response. Please try again.",
          status: res.status,
        },
      };
    }

    return { data: payload as T, error: null };
  } catch (err) {
    clearTimeout(timeout);
    const message =
      err instanceof DOMException && err.name === "AbortError"
        ? "Request timed out. Please check your connection and try again."
        : "Network error. Please check your connection and try again.";
    return {
      data: null,
      error: { code: "NETWORK_ERROR", message, status: 0 },
    };
  }
}

/** Small helper for building consistent mock-mode results with fake latency. */
export async function mockResult<T>(
  factory: () => T,
  opts: { latencyMs?: number; failRate?: number } = {},
): Promise<ApiResult<T>> {
  const { latencyMs = 350, failRate = 0 } = opts;
  await new Promise((resolve) => setTimeout(resolve, latencyMs));

  if (failRate > 0 && Math.random() < failRate) {
    return {
      data: null,
      error: {
        code: "MOCK_SIMULATED_ERROR",
        message: "Simulated failure from mock backend.",
        status: 500,
      },
    };
  }

  try {
    return { data: factory(), error: null };
  } catch {
    return {
      data: null,
      error: {
        code: "MOCK_ERROR",
        message: "Mock data generation failed.",
        status: 500,
      },
    };
  }
}

export const apiClient = {
  request,
  USE_MOCK,
  API_BASE_URL,
  ANALYTICS_API_URL,
  PREDICTION_API_URL,
  CONTEXT_API_URL,
  INSIGHTS_API_URL,
  RECOMMENDATION_API_URL,
};
