/**
 * Tracks the number of new recordings since the user last visited the archive.
 *
 * - Stores "lastSeenArchive" ISO timestamp in localStorage
 * - Polls /archive/new_count on init
 * - Listens to SSE "recording_state" events to increment in real-time
 * - Resets when markSeen() is called (archive page visit)
 */

import { getBackendUrl } from "./api";
import { sseClient } from "./sse";

const STORAGE_KEY = "lastSeenArchive";

let _count = 0;
let _listeners: Array<(count: number) => void> = [];
let _initialized = false;
let _unsub: (() => void) | null = null;

function _notify() {
  for (const fn of _listeners) fn(_count);
}

function _getLastSeen(): string {
  if (typeof localStorage === "undefined") return new Date().toISOString();
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) return stored;
  // First visit ever — seed with "now" so existing recordings don't all show as new
  const now = new Date().toISOString();
  localStorage.setItem(STORAGE_KEY, now);
  return now;
}

async function _fetchCount() {
  try {
    const since = _getLastSeen();
    const res = await fetch(`${getBackendUrl()}/archive/new_count?since=${encodeURIComponent(since)}`);
    if (res.ok) {
      const data = await res.json();
      _count = data.count ?? 0;
      _notify();
    }
  } catch {
    // Silently fail — badge is non-critical
  }
}

export function initArchiveBadge(): void {
  if (_initialized) return;
  _initialized = true;

  _fetchCount();

  // Listen for new recordings via SSE
  const sse = sseClient();
  _unsub = sse.on("recording_state", (data: { recording: boolean }) => {
    if (!data.recording) {
      // Recording just stopped → a new file was saved
      _count++;
      _notify();
    }
  });
}

export function getNewCount(): number {
  return _count;
}

export function subscribe(fn: (count: number) => void): () => void {
  _listeners.push(fn);
  // Deliver current value immediately
  fn(_count);
  return () => {
    _listeners = _listeners.filter((l) => l !== fn);
  };
}

export function markSeen(): void {
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(STORAGE_KEY, new Date().toISOString());
  }
  _count = 0;
  _notify();
}
