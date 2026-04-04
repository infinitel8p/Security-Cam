/**
 * Client-side API token management.
 *
 * - Stores the token in localStorage
 * - Used by fetch.ts (Authorization header) and sse.ts (?token= param)
 */

const STORAGE_KEY = "api-token";

export function getToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(STORAGE_KEY);
}
