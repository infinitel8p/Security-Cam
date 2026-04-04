/**
 * Fetch wrapper with timeout and retry for backend API calls.
 *
 * - Default 8s timeout via AbortController
 * - GET requests retry once on failure; POST/PUT/DELETE do not retry
 * - Exponential backoff between retries (1s, 2s, ...)
 * - Drop-in replacement for fetch() - same signature with optional extras
 *
 * Usage:
 *   import { apiFetch } from "../lib/fetch";
 *   const res = await apiFetch(`${getBackendUrl()}/system_info`);
 *   const res = await apiFetch(url, { method: "POST", body: ..., timeout: 15_000 });
 */

import { getToken, clearToken } from "./auth";

const DEFAULT_TIMEOUT = 8_000;

export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit & { timeout?: number; retries?: number },
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT, retries, ...fetchInit } = init ?? {};
  const method = (fetchInit.method ?? "GET").toUpperCase();
  const maxRetries = retries ?? (method === "GET" ? 1 : 0);

  // Inject auth token into every request
  const token = getToken();
  if (token) {
    const headers = new Headers(fetchInit.headers);
    if (!headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    fetchInit.headers = headers;
  }

  let lastError: unknown;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    if (attempt > 0) {
      await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt - 1)));
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(input, { ...fetchInit, signal: controller.signal });
      clearTimeout(timer);

      // Token rejected - clear and force re-login
      if (res.status === 401) {
        clearToken();
        if (typeof window !== "undefined") window.location.reload();
        return res;
      }

      return res;
    } catch (err) {
      clearTimeout(timer);
      lastError = err;
      if (attempt >= maxRetries) throw err;
    }
  }

  throw lastError;
}
