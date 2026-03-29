/**
 * Build the Flask backend base URL.
 * Set PUBLIC_BACKEND_URL in a .env file to override (e.g. http://192.168.1.50:5005).
 * Falls back to same-hostname:5005 for production on the Pi.
 */
export function getBackendUrl(): string {
  const env = (import.meta as any).env?.PUBLIC_BACKEND_URL;
  if (env) return env.replace(/\/$/, "");
  return `${window.location.protocol}//${window.location.hostname}:5005`;
}
