<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { initLocale, t } from "../i18n";
  import { getBackendUrl } from "../lib/api";
  import { sseClient } from "../lib/sse";
  import Icon from "./Icon.svelte";
  import usersIcon from "../icons/users.svg?raw";
  import chevronDownIcon from "../icons/chevron-down.svg?raw";
  import chevronUpIcon from "../icons/chevron-up.svg?raw";
  import chevronLeftIcon from "../icons/chevron-left.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";

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
  let unsub: (() => void) | null = null;

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
    initLocale();
    fetchEvents();

    const sse = sseClient();
    sse.registerFallback({
      event: "event_logged",
      endpoint: "/event_history?hours=72",
      interval: 30_000,
    });
    // When a new event arrives via SSE, prepend if it's an access event
    unsub = sse.on("event_logged", (ev) => {
      if (ev.type === "device_arrived" || ev.type === "device_left") {
        events = [ev, ...events];
      }
    });
  });

  onDestroy(() => {
    unsub?.();
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
    <p class="text-[0.8125rem] text-text-muted">{t("error.accessLog")}</p>
    <button onclick={fetchEvents} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
  </div>
{:else if events.length === 0}
  <div class="card px-5 py-8 text-center">
    <Icon icon={usersIcon} class="animate-float mx-auto h-8 w-8 text-text-muted/20" stroke={1.5} />
    <p class="mt-2.5 text-[0.8125rem] text-text-muted">
      {t("empty.accessLog")}
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
          {isArrival(event.type) ? t("device.arrived") : t("device.left")}
        </span>
      </div>
    {/each}

    <!-- Collapsed: show expand button if there are more -->
    {#if !expanded && events.length > COLLAPSED_COUNT}
      <button
        onclick={() => { expanded = true; page = 0; }}
        class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-surface-overlay/40"
      >
        {t("btn.showMore")} ({events.length - COLLAPSED_COUNT})
        <Icon icon={chevronDownIcon} class="h-3 w-3" />
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
            <Icon icon={chevronLeftIcon} class="h-3 w-3" />
            {t("btn.newer")}
          </button>
          <span class="text-[0.6875rem] tabular-nums text-text-muted">{page + 1} / {totalPages}</span>
          <button
            onclick={() => page++}
            disabled={page >= totalPages - 1}
            class="flex items-center gap-1 text-[0.75rem] font-medium transition-colors {page >= totalPages - 1 ? 'text-text-muted/30 cursor-not-allowed' : 'text-accent hover:text-accent-hover'}"
          >
            {t("btn.older")}
            <Icon icon={chevronRightIcon} class="h-3 w-3" />
          </button>
        {:else}
          <span></span><span></span><span></span>
        {/if}
      </div>
      <button
        onclick={() => { expanded = false; page = 0; }}
        class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-surface-overlay/40"
      >
        {t("btn.showLess")}
        <Icon icon={chevronUpIcon} class="h-3 w-3" />
      </button>
    {/if}
  </div>
{/if}
