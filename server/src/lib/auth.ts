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

/** Append ?token= to a URL for resources loaded via src attributes (img, video). */
export function authUrl(url: string): string {
  const token = getToken();
  if (!token) return url;
  // Avoid double-appending if already present
  if (new URL(url, location.href).searchParams.has("token")) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}token=${encodeURIComponent(token)}`;
}
