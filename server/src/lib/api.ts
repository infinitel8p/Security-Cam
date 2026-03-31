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

/**
 * Build the MediaMTX WebRTC WHEP endpoint URL.
 * Set PUBLIC_MEDIAMTX_URL in a .env file to override (e.g. http://192.168.1.50:8889).
 * Falls back to same-hostname:8889 for production on the Pi.
 */
export function getMediaMtxUrl(): string {
  const env = (import.meta as any).env?.PUBLIC_MEDIAMTX_URL;
  if (env) return env.replace(/\/$/, "");
  return `${window.location.protocol}//${window.location.hostname}:8889`;
}

/**
 * Build the MediaMTX HLS endpoint URL (fallback when WebRTC fails).
 * Set PUBLIC_HLS_URL in a .env file to override (e.g. http://192.168.1.50:8888).
 * Falls back to same-hostname:8888 for production on the Pi.
 */
export function getHlsUrl(): string {
  const env = (import.meta as any).env?.PUBLIC_HLS_URL;
  if (env) return env.replace(/\/$/, "");
  return `${window.location.protocol}//${window.location.hostname}:8888`;
}
