/**
 * SSE client with automatic reconnection and polling fallback.
 *
 * Usage:
 *   import { sseClient } from "../lib/sse";
 *
 *   const sse = sseClient();
 *
 *   // Subscribe to a specific event type:
 *   const unsub = sse.on("sensor_state", (data) => {
 *     // data is the parsed JSON payload
 *   });
 *
 *   // Check connection state:
 *   sse.connected  // true when SSE is active
 *   sse.degraded   // true when fallen back to polling
 *
 *   // Clean up:
 *   unsub();          // remove one listener
 *   sse.destroy();    // close everything
 */

import { getBackendUrl } from "./api";

type Listener = (data: any) => void;

interface FallbackConfig {
  /** Event type to listen for */
  event: string;
  /** Endpoint to poll (relative to backend URL) */
  endpoint: string;
  /** Polling interval in ms */
  interval: number;
  /** Transform fetch response JSON before dispatching */
  transform?: (json: any) => any;
}

interface SSEClient {
  /** Subscribe to an SSE event type. Returns an unsubscribe function. */
  on: (event: string, listener: Listener) => () => void;
  /** Register a polling fallback for an event type. */
  registerFallback: (config: FallbackConfig) => void;
  /** True when EventSource is connected */
  readonly connected: boolean;
  /** True when SSE failed and we're polling instead */
  readonly degraded: boolean;
  /** Subscribe to connection state changes */
  onStateChange: (listener: (state: { connected: boolean; degraded: boolean }) => void) => () => void;
  /** Tear down all connections and listeners */
  destroy: () => void;
}

const MAX_SSE_FAILURES = 3;
const SSE_RETRY_DELAY = 3000;

/** Singleton SSE client — shared across all components. */
let instance: SSEClient | null = null;

export function sseClient(): SSEClient {
  if (instance) return instance;

  const listeners = new Map<string, Set<Listener>>();
  const stateListeners = new Set<(state: { connected: boolean; degraded: boolean }) => void>();
  const fallbacks = new Map<string, FallbackConfig>();
  const pollTimers = new Map<string, ReturnType<typeof setInterval>>();

  let es: EventSource | null = null;
  let _connected = false;
  let _degraded = false;
  let failCount = 0;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let destroyed = false;

  function notifyState() {
    const state = { connected: _connected, degraded: _degraded };
    for (const fn of stateListeners) {
      try { fn(state); } catch { /* ignore */ }
    }
  }

  function dispatch(event: string, data: any) {
    const set = listeners.get(event);
    if (set) {
      for (const fn of set) {
        try { fn(data); } catch { /* ignore */ }
      }
    }
  }

  function startPolling() {
    // Start polling for all registered fallbacks
    for (const [event, config] of fallbacks) {
      if (pollTimers.has(event)) continue;
      const timer = setInterval(async () => {
        try {
          const res = await fetch(`${getBackendUrl()}${config.endpoint}`);
          if (!res.ok) return;
          let json = await res.json();
          if (config.transform) json = config.transform(json);
          dispatch(config.event, json);
        } catch { /* silent */ }
      }, config.interval);
      pollTimers.set(event, timer);
    }
  }

  function stopPolling() {
    for (const timer of pollTimers.values()) {
      clearInterval(timer);
    }
    pollTimers.clear();
  }

  function connect() {
    if (destroyed) return;

    const url = `${getBackendUrl()}/events`;
    es = new EventSource(url);

    es.onopen = () => {
      failCount = 0;
      _connected = true;
      if (_degraded) {
        _degraded = false;
        stopPolling();
      }
      notifyState();
    };

    es.onerror = () => {
      _connected = false;
      notifyState();

      if (es) {
        es.close();
        es = null;
      }

      failCount++;
      if (failCount >= MAX_SSE_FAILURES && !_degraded) {
        _degraded = true;
        notifyState();
        startPolling();
      }

      // Always retry SSE (even when polling) so we recover
      retryTimer = setTimeout(connect, SSE_RETRY_DELAY);
    };

    // Listen for all named events we have subscribers for
    // SSE sends named events like: event: sensor_state\ndata: {...}
    // We use the generic "message" handler + named event listeners.
    // Since our backend sends named events, we need addEventListener per type.
    // But we don't know all types upfront, so we use onmessage as catch-all
    // and also register specific listeners.

    // The backend sends: event: <name>\ndata: <json>
    // EventSource only fires named events on addEventListener, not onmessage.
    // We register listeners for known event types.
    const knownEvents = [
      "sensor_state",
      "recording_state",
      "connections",
      "presence_change",
      "event_logged",
    ];

    for (const eventName of knownEvents) {
      es.addEventListener(eventName, ((e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          dispatch(eventName, data);
        } catch { /* ignore malformed */ }
      }) as EventListener);
    }
  }

  // Start immediately
  connect();

  instance = {
    on(event: string, listener: Listener) {
      if (!listeners.has(event)) listeners.set(event, new Set());
      listeners.get(event)!.add(listener);

      return () => {
        listeners.get(event)?.delete(listener);
        if (listeners.get(event)?.size === 0) listeners.delete(event);
      };
    },

    registerFallback(config: FallbackConfig) {
      fallbacks.set(config.event, config);
      // If already degraded, start polling for this fallback immediately
      if (_degraded && !pollTimers.has(config.event)) {
        const timer = setInterval(async () => {
          try {
            const res = await fetch(`${getBackendUrl()}${config.endpoint}`);
            if (!res.ok) return;
            let json = await res.json();
            if (config.transform) json = config.transform(json);
            dispatch(config.event, json);
          } catch { /* silent */ }
        }, config.interval);
        pollTimers.set(config.event, timer);
      }
    },

    get connected() { return _connected; },
    get degraded() { return _degraded; },

    onStateChange(listener) {
      stateListeners.add(listener);
      return () => { stateListeners.delete(listener); };
    },

    destroy() {
      destroyed = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (es) { es.close(); es = null; }
      stopPolling();
      listeners.clear();
      stateListeners.clear();
      instance = null;
    },
  };

  return instance;
}
