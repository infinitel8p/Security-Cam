/**
 * Tracks system health alert state and fires toast notifications on transitions.
 *
 * - Fetches initial state from /system_alert_state on init
 * - Listens to SSE "system_alert" events for real-time transitions
 * - Exposes subscribe() for Navbar/MobileNav badge reactivity
 */

import { getBackendUrl } from "./api";
import { apiFetch } from "./fetch";
import { sseClient } from "./sse";
import toast from "svelte-5-french-toast";
import { t } from "../i18n";

export type AlertLevel = "ok" | "warn" | "critical";

export interface AlertState {
  overall: AlertLevel;
  alerts: Record<string, AlertLevel>;
  values: Record<string, number | null>;
}

interface Transition {
  metric: string;
  from: AlertLevel;
  to: AlertLevel;
}

interface AlertEvent extends AlertState {
  transitions: Transition[];
  ts: string;
}

let _state: AlertState = { overall: "ok", alerts: {}, values: {} };
let _listeners: Array<(state: AlertState) => void> = [];
let _initialized = false;
// Kept for potential cleanup in future; SSE subscription is app-lifetime
let _unsub: (() => void) | null = null; // eslint-disable-line @typescript-eslint/no-unused-vars

function _notify() {
  for (const fn of _listeners) fn(_state);
}

function _handleTransitions(transitions: Transition[], values: Record<string, number | null>) {
  for (const tr of transitions) {
    if (tr.to === "critical") {
      const msg = _alertMessage(tr.metric, tr.to, values);
      toast.error(msg, { duration: Infinity });
    } else if (tr.to === "warn") {
      const msg = _alertMessage(tr.metric, tr.to, values);
      toast.error(msg, { duration: 8000 });
    } else if (tr.to === "ok" && tr.from !== "ok") {
      toast.success(t(`alert.${tr.metric}.resolved`), { duration: 5000 });
    }
  }
}

function _alertMessage(metric: string, level: string, values: Record<string, number | null>): string {
  const msg = t(`alert.${metric}.${level}`);
  // Replace placeholders like {temp} and {pct} with actual values
  return msg
    .replace("{temp}", String(values.temp ?? "?"))
    .replace("{pct}", String(values.storage_pct ?? "?"));
}

async function _fetchState() {
  try {
    const res = await apiFetch(`${getBackendUrl()}/system_alert_state`);
    if (res.ok) {
      const data = await res.json();
      _state = {
        overall: data.overall ?? "ok",
        alerts: data.alerts ?? {},
        values: data.values ?? {},
      };
      _notify();
    }
  } catch {
    // Non-critical - badge just stays "ok" until first SSE event
  }
}

export function initSystemAlerts(): void {
  if (_initialized) return;
  _initialized = true;

  _fetchState();

  const sse = sseClient();
  _unsub = sse.on("system_alert", (data: AlertEvent) => {
    _state = {
      overall: data.overall ?? "ok",
      alerts: data.alerts ?? {},
      values: data.values ?? {},
    };
    _notify();

    if (data.transitions?.length) {
      _handleTransitions(data.transitions, data.values ?? {});
    }
  });

  // Fallback polling when SSE is degraded
  sse.registerFallback({
    event: "system_alert",
    endpoint: "/system_alert_state",
    interval: 60_000,
    transform: (json) => json,
  });
}

export function getAlertState(): AlertState {
  return _state;
}

export function subscribe(fn: (state: AlertState) => void): () => void {
  _listeners.push(fn);
  fn(_state);
  return () => {
    _listeners = _listeners.filter((l) => l !== fn);
  };
}
