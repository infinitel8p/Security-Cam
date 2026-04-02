/**
 * Fetch wrapper with timeout and retry for backend API calls.
 *
 * - Default 8s timeout via AbortController
 * - GET requests retry once on failure; POST/PUT/DELETE do not retry
 * - Exponential backoff between retries (1s, 2s, ...)
 * - Drop-in replacement for fetch() — same signature with optional extras
 *
 * Usage:
 *   import { apiFetch } from "../lib/fetch";
 *   const res = await apiFetch(`${getBackendUrl()}/system_info`);
 *   const res = await apiFetch(url, { method: "POST", body: ..., timeout: 15_000 });
 */

const DEFAULT_TIMEOUT = 8_000;

export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit & { timeout?: number; retries?: number },
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT, retries, ...fetchInit } = init ?? {};
  const method = (fetchInit.method ?? "GET").toUpperCase();
  const maxRetries = retries ?? (method === "GET" ? 1 : 0);

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
      return res;
    } catch (err) {
      clearTimeout(timer);
      lastError = err;
      if (attempt >= maxRetries) throw err;
    }
  }

  throw lastError;
}
