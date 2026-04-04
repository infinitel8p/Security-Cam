/**
 * Periodic update checker with nav badge support.
 *
 * - Checks /system/update/check on init (if 12h have passed) and every 12h
 * - Manual check via checkNow()
 * - Stores last check timestamp + result in localStorage
 * - Exposes subscribe() for nav badge reactivity
 * - Gracefully handles no-internet (returns cached or false)
 */

import { getBackendUrl } from "./api";
import { apiFetch } from "./fetch";

const STORAGE_KEY = "updateCheck";
const CHECK_INTERVAL = 12 * 60 * 60 * 1000; // 12 hours

export interface UpdateState {
  available: boolean;
  commits_behind?: number;
  summary?: string;
  error?: string;
  local_commit?: string;
  remote_commit?: string;
  lastChecked?: string; // ISO timestamp
}

let _state: UpdateState = { available: false };
let _listeners: Array<(state: UpdateState) => void> = [];
let _initialized = false;
let _intervalId: ReturnType<typeof setInterval> | null = null;
let _checking = false;

function _notify() {
  for (const fn of _listeners) fn(_state);
}

function _loadCached(): { state: UpdateState; timestamp: number } | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function _saveCache(state: UpdateState) {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      state,
      timestamp: Date.now(),
    }));
  } catch {
    // Storage full or unavailable
  }
}

async function _fetch(): Promise<UpdateState> {
  const res = await apiFetch(`${getBackendUrl()}/system/update/check`, {
    timeout: 25_000,
    retries: 0,
  });
  const data = await res.json();
  return {
    available: data.available ?? false,
    commits_behind: data.commits_behind,
    summary: data.summary,
    error: data.error,
    local_commit: data.local_commit,
    remote_commit: data.remote_commit,
    lastChecked: new Date().toISOString(),
  };
}

/** Run an update check, update state, and notify listeners. */
export async function checkNow(): Promise<UpdateState> {
  if (_checking) return _state;
  _checking = true;
  try {
    _state = await _fetch();
    _saveCache(_state);
    _notify();
    return _state;
  } catch {
    // Network error - keep previous state, don't overwrite
    return _state;
  } finally {
    _checking = false;
  }
}

export function initUpdateBadge(): void {
  if (_initialized) return;
  _initialized = true;

  // Load cached result immediately so badge shows without waiting for fetch
  const cached = _loadCached();
  if (cached) {
    _state = cached.state;
    _notify();
  }

  // Check if enough time has passed since last check
  const elapsed = cached ? Date.now() - cached.timestamp : Infinity;
  if (elapsed >= CHECK_INTERVAL) {
    checkNow();
  }

  // Schedule periodic checks
  _intervalId = setInterval(() => { checkNow(); }, CHECK_INTERVAL);
}

export function subscribe(fn: (state: UpdateState) => void): () => void {
  _listeners.push(fn);
  fn(_state);
  return () => {
    _listeners = _listeners.filter((l) => l !== fn);
  };
}

/** Clear the cached update state (e.g. after applying an update). */
export function clearUpdate(): void {
  _state = { available: false };
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(STORAGE_KEY);
  }
  _notify();
}
