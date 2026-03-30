<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface AccessEvent {
    ts: string;
    type: string;
    severity: string;
    detail?: string;
  }

  let events = $state<AccessEvent[]>([]);
  let loading = $state(true);
  let error = $state(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  async function fetchEvents() {
    try {
      const res = await fetch(`${getBackendUrl()}/event_history?hours=72`);
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
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  }

  function isArrival(type: string): boolean {
    return type === "device_arrived";
  }

  function deviceName(detail?: string): string {
    if (!detail) return "Unknown";
    return detail;
  }
</script>

{#if loading}
  <div class="card animate-pulse px-5 py-8">
    <div class="space-y-3">
      {#each Array(3) as _}
        <div class="flex items-center gap-4">
          <div class="h-3 w-20 rounded bg-surface-elevated"></div>
          <div class="h-3 w-32 rounded bg-surface-elevated"></div>
          <div class="h-3 w-16 rounded bg-surface-elevated"></div>
        </div>
      {/each}
    </div>
  </div>
{:else if error}
  <div class="card px-5 py-8 text-center text-[0.8125rem] text-text-muted">
    Unable to load access log
  </div>
{:else if events.length === 0}
  <div class="card px-5 py-8 text-center">
    <svg class="mx-auto h-8 w-8 text-text-muted/15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
    <p class="mt-2.5 text-[0.8125rem] text-text-muted">
      No device activity recorded yet
    </p>
  </div>
{:else}
  <!-- Mobile: stacked cards -->
  <div class="card divide-y divide-border-subtle sm:hidden">
    {#each events.slice(0, 20) as event (event.ts + event.type + event.detail)}
      <div class="flex items-center justify-between px-4 py-3">
        <div class="min-w-0">
          <p class="text-sm font-medium text-text-primary">{deviceName(event.detail)}</p>
          <p class="mt-0.5 text-[0.6875rem] tabular-nums text-text-secondary">
            {formatDate(event.ts)} &middot; {formatTime(event.ts)}
          </p>
        </div>
        {#if isArrival(event.type)}
          <span class="inline-flex shrink-0 items-center gap-1.5 text-[0.8125rem] text-status-ok">
            <span class="h-1.5 w-1.5 rounded-full bg-current"></span>Arrived
          </span>
        {:else}
          <span class="inline-flex shrink-0 items-center gap-1.5 text-[0.8125rem] text-text-muted">
            <span class="h-1.5 w-1.5 rounded-full bg-current"></span>Left
          </span>
        {/if}
      </div>
    {/each}
  </div>

  <!-- Desktop: table -->
  <div class="card hidden overflow-hidden sm:block">
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-border-default text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">
            <th class="whitespace-nowrap px-5 py-3">Device</th>
            <th class="whitespace-nowrap px-5 py-3">Date</th>
            <th class="whitespace-nowrap px-5 py-3">Time</th>
            <th class="whitespace-nowrap px-5 py-3">Event</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-subtle">
          {#each events.slice(0, 50) as event (event.ts + event.type + event.detail)}
            <tr class="transition-colors hover:bg-surface-overlay/40">
              <td class="whitespace-nowrap px-5 py-3 font-medium text-text-primary">
                {deviceName(event.detail)}
              </td>
              <td class="whitespace-nowrap px-5 py-3 tabular-nums text-text-secondary">
                {formatDate(event.ts)}
              </td>
              <td class="whitespace-nowrap px-5 py-3 tabular-nums text-text-secondary">
                {formatTime(event.ts)}
              </td>
              <td class="whitespace-nowrap px-5 py-3">
                {#if isArrival(event.type)}
                  <span class="inline-flex items-center gap-1.5 text-status-ok">
                    <span class="h-1.5 w-1.5 rounded-full bg-current"></span>Arrived
                  </span>
                {:else}
                  <span class="inline-flex items-center gap-1.5 text-text-muted">
                    <span class="h-1.5 w-1.5 rounded-full bg-current"></span>Left
                  </span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}
