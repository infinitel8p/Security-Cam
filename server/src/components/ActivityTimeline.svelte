<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import Icon from "./Icon.svelte";
  import activityIcon from "../icons/activity.svg?raw";
  import chevronDownIcon from "../icons/chevron-down.svg?raw";
  import chevronLeftIcon from "../icons/chevron-left.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";
  import chevronUpIcon from "../icons/chevron-up.svg?raw";

  interface TimelineEvent {
    ts: string;
    type: string;
    severity: "ok" | "warn" | "critical";
    detail?: string;
  }

  const COLLAPSED_COUNT = 5;
  const EXPANDED_COUNT = 15;
  const PAGE_SIZE = 15;

  let events = $state<TimelineEvent[]>([]);
  let expanded = $state(false);
  let page = $state(0);
  let loading = $state(true);
  let error = $state(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  const EVENT_META: Record<string, { label: string; icon: string; color: string }> = {
    recording_started: {
      label: "Recording started",
      icon: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1 14V8l6 4-6 4z",
      color: "text-status-warning",
    },
    recording_stopped: {
      label: "Recording stopped",
      icon: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-2 14V8h1.5v8H10zm3.5 0V8H15v8h-1.5z",
      color: "text-text-secondary",
    },
    motion_detected: {
      label: "Motion detected",
      icon: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
      color: "text-status-warning",
    },
    stream_disconnected: {
      label: "Stream disconnected",
      icon: "M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.17-2.39M10.71 5.05A16 16 0 0 1 22.56 9M1.42 9a15.91 15.91 0 0 1 4.7-2.88M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01",
      color: "text-status-critical",
    },
    stream_reconnected: {
      label: "Stream reconnected",
      icon: "M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01",
      color: "text-status-ok",
    },
    unauthorized_access: {
      label: "Unauthorized access",
      icon: "M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
      color: "text-status-critical",
    },
    system_boot: {
      label: "System boot",
      icon: "M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10",
      color: "text-accent",
    },
    device_arrived: {
      label: "Device arrived",
      icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
      color: "text-status-ok",
    },
    device_left: {
      label: "Device left",
      icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
      color: "text-text-muted",
    },
  };

  // Exclude device events - those belong in Access Log
  const EXCLUDED_TYPES = new Set(["device_arrived", "device_left"]);

  async function fetchEvents() {
    try {
      const res = await fetch(`${getBackendUrl()}/event_history?hours=168`);
      if (!res.ok) throw new Error();
      const all: TimelineEvent[] = await res.json();
      events = all
        .filter(e => !EXCLUDED_TYPES.has(e.type))
        .reverse(); // newest first
      error = false;
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchEvents();
    interval = setInterval(fetchEvents, 30_000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });

  function getMeta(type: string) {
    return EVENT_META[type] ?? {
      label: type.replace(/_/g, " "),
      icon: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
      color: "text-text-secondary",
    };
  }

  function formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit" });
  }

  function formatTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function relativeTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  }

  function severityDot(severity: string): string {
    if (severity === "critical") return "bg-status-critical shadow-[0_0_6px_rgba(240,104,104,0.4)]";
    if (severity === "warn") return "bg-status-warning shadow-[0_0_6px_rgba(240,185,58,0.3)]";
    return "bg-status-ok";
  }
</script>

{#if loading}
  <div class="card px-5 py-8">
    <div class="space-y-4">
      {#each Array(4) as _, i}
        <div class="flex items-center gap-3 animate-in" style="animation-delay: {i * 60}ms">
          <div class="skeleton h-7 w-7 rounded-full"></div>
          <div class="flex-1 space-y-1.5">
            <div class="skeleton h-3 w-28"></div>
            <div class="skeleton h-2.5 w-20"></div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{:else if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-5 py-8 text-center">
    <p class="text-[0.8125rem] text-text-muted">Unable to load activity timeline</p>
    <button onclick={fetchEvents} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">Retry</button>
  </div>
{:else if events.length === 0}
  <div class="card px-5 py-8 text-center">
    <Icon icon={activityIcon} class="animate-float mx-auto h-8 w-8 text-text-muted/20" stroke={1.5} />
    <p class="mt-2.5 text-[0.8125rem] text-text-muted">
      System is running smoothly — no events to report
    </p>
  </div>
{:else}
  {@const totalPages = Math.ceil(events.length / PAGE_SIZE)}
  {@const visibleEvents = expanded
    ? events.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
    : events.slice(0, COLLAPSED_COUNT)}
  <div class="card divide-y divide-border-subtle">
    {#each visibleEvents as event (event.ts + event.type + (event.detail ?? ''))}
      {@const meta = getMeta(event.type)}
      <div class="flex items-start gap-3 px-4 py-3">
        <!-- Icon -->
        <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-elevated">
          <svg class="h-3.5 w-3.5 {meta.color}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d={meta.icon} />
          </svg>
        </div>

        <!-- Content -->
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="text-[0.8125rem] font-medium text-text-primary">{meta.label}</span>
            <span class="h-1.5 w-1.5 shrink-0 rounded-full {severityDot(event.severity)}"></span>
          </div>
          {#if event.detail}
            <p class="mt-0.5 text-[0.75rem] text-text-secondary">{event.detail}</p>
          {/if}
          <p class="mt-0.5 text-[0.6875rem] tabular-nums text-text-muted">
            {formatDate(event.ts)} &middot; {formatTime(event.ts)}
            <span class="ml-1 text-text-muted/60">{relativeTime(event.ts)}</span>
          </p>
        </div>
      </div>
    {/each}

    <!-- Collapsed: show expand button if there are more than 5 -->
    {#if !expanded && events.length > COLLAPSED_COUNT}
      <button
        onclick={() => { expanded = true; page = 0; }}
        class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-surface-overlay/40"
      >
        Show more
        <Icon icon={chevronDownIcon} class="h-3 w-3" />
      </button>
    {/if}

    <!-- Expanded: pagination + collapse -->
    {#if expanded}
      <div class="flex items-center justify-between px-4 py-2.5">
        {#if totalPages > 1}
          <button
            onclick={() => page--}
            disabled={page === 0}
            class="flex items-center gap-1 text-[0.75rem] font-medium transition-colors {page === 0 ? 'text-text-muted/30 cursor-not-allowed' : 'text-accent hover:text-accent-hover'}"
          >
            <Icon icon={chevronLeftIcon} class="h-3 w-3" />
            Newer
          </button>
          <span class="text-[0.6875rem] tabular-nums text-text-muted">{page + 1} / {totalPages}</span>
          <button
            onclick={() => page++}
            disabled={page >= totalPages - 1}
            class="flex items-center gap-1 text-[0.75rem] font-medium transition-colors {page >= totalPages - 1 ? 'text-text-muted/30 cursor-not-allowed' : 'text-accent hover:text-accent-hover'}"
          >
            Older
            <Icon icon={chevronRightIcon} class="h-3 w-3" />
          </button>
        {:else}
          <span></span>
          <span></span>
          <span></span>
        {/if}
      </div>
      <button
        onclick={() => { expanded = false; page = 0; }}
        class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-surface-overlay/40"
      >
        Show less
        <Icon icon={chevronUpIcon} class="h-3 w-3" />
      </button>
    {/if}
  </div>
{/if}
