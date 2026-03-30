<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface AccessEvent {
    ts: string;
    type: string;
    severity: string;
    detail?: string;
  }

  const COLLAPSED_COUNT = 5;
  const PAGE_SIZE = 15;

  let events = $state<AccessEvent[]>([]);
  let expanded = $state(false);
  let page = $state(0);
  let loading = $state(true);
  let error = $state(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  async function fetchEvents() {
    try {
      const res = await fetch(`${getBackendUrl()}/event_history?hours=72`);
      if (!res.ok) throw new Error();
      const all: AccessEvent[] = await res.json();
      events = all
        .filter(e => e.type === "device_arrived" || e.type === "device_left")
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

  function formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit" });
  }

  function formatTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function isArrival(type: string): boolean {
    return type === "device_arrived";
  }

  function deviceName(detail?: string): string {
    if (!detail) return "Unknown";
    return detail;
  }

  let totalPages = $derived(Math.ceil(events.length / PAGE_SIZE));
  let visibleEvents = $derived(
    expanded
      ? events.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
      : events.slice(0, COLLAPSED_COUNT)
  );
</script>

{#if loading}
  <div class="card px-5 py-8">
    <div class="space-y-3">
      {#each Array(3) as _, i}
        <div class="flex items-center gap-4 animate-in" style="animation-delay: {i * 60}ms">
          <div class="skeleton h-3 w-20"></div>
          <div class="skeleton h-3 w-32"></div>
          <div class="skeleton h-3 w-16"></div>
        </div>
      {/each}
    </div>
  </div>
{:else if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-5 py-8 text-center">
    <p class="text-[0.8125rem] text-text-muted">Unable to load access log</p>
    <button onclick={fetchEvents} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">Retry</button>
  </div>
{:else if events.length === 0}
  <div class="card px-5 py-8 text-center">
    <svg class="animate-float mx-auto h-8 w-8 text-text-muted/20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
    <p class="mt-2.5 text-[0.8125rem] text-text-muted">
      No devices have come or gone — all quiet
    </p>
  </div>
{:else}
  <div class="card divide-y divide-border-subtle">
    {#each visibleEvents as event (event.ts + event.type + event.detail)}
      <div class="flex items-center justify-between px-4 py-3 sm:px-5">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            {#if isArrival(event.type)}
              <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-status-ok shadow-[0_0_6px_rgba(52,217,172,0.3)]"></span>
            {:else}
              <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-text-muted/30"></span>
            {/if}
            <span class="truncate text-sm font-medium text-text-primary">{deviceName(event.detail)}</span>
          </div>
          <p class="mt-0.5 ml-3.5 text-[0.6875rem] tabular-nums text-text-muted">
            {formatDate(event.ts)} &middot; {formatTime(event.ts)}
          </p>
        </div>
        <span class="shrink-0 text-[0.8125rem] {isArrival(event.type) ? 'text-status-ok' : 'text-text-muted'}">
          {isArrival(event.type) ? "Arrived" : "Left"}
        </span>
      </div>
    {/each}

    <!-- Collapsed: show expand button if there are more -->
    {#if !expanded && events.length > COLLAPSED_COUNT}
      <button
        onclick={() => { expanded = true; page = 0; }}
        class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-surface-overlay/40"
      >
        Show more ({events.length - COLLAPSED_COUNT} more)
        <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
      </button>
    {/if}

    <!-- Expanded: pagination + collapse -->
    {#if expanded}
      <div class="flex items-center justify-between px-4 py-2.5 sm:px-5">
        {#if totalPages > 1}
          <button
            onclick={() => page--}
            disabled={page === 0}
            class="flex items-center gap-1 text-[0.75rem] font-medium transition-colors {page === 0 ? 'text-text-muted/30 cursor-not-allowed' : 'text-accent hover:text-accent-hover'}"
          >
            <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
            Newer
          </button>
          <span class="text-[0.6875rem] tabular-nums text-text-muted">{page + 1} / {totalPages}</span>
          <button
            onclick={() => page++}
            disabled={page >= totalPages - 1}
            class="flex items-center gap-1 text-[0.75rem] font-medium transition-colors {page >= totalPages - 1 ? 'text-text-muted/30 cursor-not-allowed' : 'text-accent hover:text-accent-hover'}"
          >
            Older
            <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
        {:else}
          <span></span><span></span><span></span>
        {/if}
      </div>
      <button
        onclick={() => { expanded = false; page = 0; }}
        class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-surface-overlay/40"
      >
        Show less
        <svg class="h-3 w-3 rotate-180" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
      </button>
    {/if}
  </div>
{/if}
