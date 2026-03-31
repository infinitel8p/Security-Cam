<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { initLocale, t } from "../i18n";
  import { getBackendUrl } from "../lib/api";
  import Icon from "./Icon.svelte";
  import activityIcon from "../icons/activity.svg?raw";
  import chevronDownIcon from "../icons/chevron-down.svg?raw";
  import chevronLeftIcon from "../icons/chevron-left.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";
  import chevronUpIcon from "../icons/chevron-up.svg?raw";
  import playerRecordIcon from "../icons/player-record.svg?raw";
  import playerStopIcon from "../icons/player-stop.svg?raw";
  import boltIcon from "../icons/bolt.svg?raw";
  import shieldIcon from "../icons/shield.svg?raw";
  import wifiOffIcon from "../icons/wifi-off.svg?raw";
  import wifiIcon from "../icons/wifi.svg?raw";
  import alertTriangleIcon from "../icons/alert-triangle.svg?raw";
  import powerIcon from "../icons/power.svg?raw";
  import usersIcon from "../icons/users.svg?raw";

  interface TimelineEvent {
    ts: string;
    type: string;
    severity: "ok" | "warn" | "critical";
    detail?: string;
  }

  const COLLAPSED_COUNT = 5;
  const EXPANDED_COUNT = 15;
  const PAGE_SIZE = 15;

  let events = $state<DisplayEvent[]>([]);
  let expanded = $state(false);
  let page = $state(0);
  let loading = $state(true);
  let error = $state(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  const EVENT_META: Record<string, { icon: string; color: string; bgColor: string }> = {
    recording_started:   { icon: playerRecordIcon,   color: "text-status-critical", bgColor: "bg-status-critical/10" },
    recording_stopped:   { icon: playerStopIcon,     color: "text-text-muted",      bgColor: "bg-surface-elevated" },
    motion_detected:     { icon: boltIcon,           color: "text-status-warning",  bgColor: "bg-status-warning/10" },
    sensor_triggered:    { icon: boltIcon,           color: "text-status-warning",  bgColor: "bg-status-warning/10" },
    sensor_released:     { icon: boltIcon,           color: "text-text-muted",      bgColor: "bg-surface-elevated" },
    sensor_armed:        { icon: shieldIcon,         color: "text-status-ok",       bgColor: "bg-status-ok/10" },
    sensor_disarmed:     { icon: shieldIcon,         color: "text-text-muted",      bgColor: "bg-surface-elevated" },
    stream_disconnected: { icon: wifiOffIcon,        color: "text-status-critical", bgColor: "bg-status-critical/10" },
    stream_reconnected:  { icon: wifiIcon,           color: "text-status-ok",       bgColor: "bg-status-ok/10" },
    unauthorized_access: { icon: alertTriangleIcon,  color: "text-status-critical", bgColor: "bg-status-critical/10" },
    system_boot:         { icon: powerIcon,          color: "text-accent",          bgColor: "bg-accent/10" },
    device_arrived:      { icon: usersIcon,          color: "text-status-ok",       bgColor: "bg-status-ok/10" },
    device_left:         { icon: usersIcon,          color: "text-text-muted",      bgColor: "bg-surface-elevated" },
  };

  // Exclude device events (belong in Access Log) and sensor_released (noise - grouped with trigger)
  const EXCLUDED_TYPES = new Set(["device_arrived", "device_left"]);

  // Types that are low-priority and should be collapsed when repeated
  const COLLAPSIBLE_TYPES = new Set(["sensor_triggered", "sensor_released"]);

  interface DisplayEvent extends TimelineEvent {
    count?: number; // how many consecutive events were collapsed
  }

  /**
   * Collapse rapid-fire sensor trigger/release pairs into single entries.
   * Events within 5 minutes of the same type+detail get grouped.
   */
  function collapseEvents(raw: TimelineEvent[]): DisplayEvent[] {
    const result: DisplayEvent[] = [];
    for (const event of raw) {
      const prev = result[result.length - 1];
      if (
        prev &&
        COLLAPSIBLE_TYPES.has(event.type) &&
        prev.type === event.type &&
        prev.detail === event.detail
      ) {
        const gap = new Date(prev.ts).getTime() - new Date(event.ts).getTime();
        if (gap < 5 * 60 * 1000) {
          prev.count = (prev.count ?? 1) + 1;
          continue;
        }
      }
      result.push({ ...event });
    }
    return result;
  }

  async function fetchEvents() {
    try {
      const res = await fetch(`${getBackendUrl()}/event_history?hours=168`);
      if (!res.ok) throw new Error();
      const all: TimelineEvent[] = await res.json();
      const filtered = all
        .filter(e => !EXCLUDED_TYPES.has(e.type))
        .reverse(); // newest first
      events = collapseEvents(filtered);
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
    interval = setInterval(fetchEvents, 30_000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });

  function getMeta(type: string) {
    return EVENT_META[type] ?? {
      icon: activityIcon,
      color: "text-text-secondary",
      bgColor: "bg-surface-elevated",
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

  function eventLabel(type: string): string {
    const key = "event." + type.replace(/_([a-z])/g, (_: string, c: string) => c.toUpperCase());
    const result = t(key);
    return result !== key ? result : type.replace(/_/g, " ");
  }

  function relativeTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return t("time.justNow");
    if (mins < 60) return t("time.minutesAgo", { n: mins });
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return t("time.hoursAgo", { n: hrs });
    const days = Math.floor(hrs / 24);
    return t("time.daysAgo", { n: days });
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
    <p class="text-[0.8125rem] text-text-muted">{t("error.activityTimeline")}</p>
    <button onclick={fetchEvents} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
  </div>
{:else if events.length === 0}
  <div class="card px-5 py-8 text-center">
    <Icon icon={activityIcon} class="animate-float mx-auto h-8 w-8 text-text-muted/20" stroke={1.5} />
    <p class="mt-2.5 text-[0.8125rem] text-text-muted">
      {t("empty.activityTimeline")}
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
        <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full {meta.bgColor}">
          <Icon icon={meta.icon} class="h-3.5 w-3.5 {meta.color}" />
        </div>

        <!-- Content -->
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="text-[0.8125rem] font-medium {meta.color === 'text-status-critical' ? 'text-status-critical' : 'text-text-primary'}">{eventLabel(event.type)}</span>
            {#if event.count && event.count > 1}
              <span class="rounded-full bg-surface-elevated px-1.5 py-0.5 text-[0.625rem] tabular-nums font-medium text-text-muted">&times;{event.count}</span>
            {/if}
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
        {t("btn.showMore")}
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
          <span></span>
          <span></span>
          <span></span>
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
