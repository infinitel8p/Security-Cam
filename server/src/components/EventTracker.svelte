<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface EventEntry {
    ts: string;
    type: string;
    severity: "ok" | "warn" | "critical";
    detail?: string;
  }

  let events: EventEntry[] = $state([]);
  let slots: { severity: string; label: string; events: EventEntry[] }[] = $state([]);
  let loading = $state(true);
  let error = $state(false);
  let hoveredIndex = $state(-1);

  const HOURS = 168; // 7 days
  const TOTAL_SLOTS = 56; // 3h per bucket
  const BUCKET_MS = (HOURS / TOTAL_SLOTS) * 60 * 60 * 1000;

  const severityColors: Record<string, string> = {
    ok: "bg-status-ok",
    warn: "bg-status-warning",
    critical: "bg-status-critical",
    empty: "bg-surface-elevated",
  };

  const typeLabels: Record<string, string> = {
    device_arrived: "Arrived",
    device_left: "Left",
    recording_started: "Rec start",
    recording_stopped: "Rec stop",
    motion_detected: "Motion",
    stream_disconnected: "Stream lost",
    stream_reconnected: "Stream ok",
    unauthorized_access: "Unauthorized",
    system_boot: "Boot",
  };

  function buildSlots(data: EventEntry[]) {
    const now = Date.now();
    const result: { severity: string; label: string; events: EventEntry[] }[] = [];

    for (let i = 0; i < TOTAL_SLOTS; i++) {
      const bucketStart = now - (TOTAL_SLOTS - i) * BUCKET_MS;
      const bucketEnd = bucketStart + BUCKET_MS;

      const bucketEvents = data.filter((e) => {
        const t = new Date(e.ts).getTime();
        return t >= bucketStart && t < bucketEnd;
      });

      let severity = "empty";
      if (bucketEvents.length > 0) {
        if (bucketEvents.some((e) => e.severity === "critical")) severity = "critical";
        else if (bucketEvents.some((e) => e.severity === "warn")) severity = "warn";
        else severity = "ok";
      }

      const time = new Date(bucketStart);
      const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      const h = time.getHours().toString().padStart(2, "0");
      const label = `${days[time.getDay()]} ${h}:00`;
      result.push({ severity, label, events: bucketEvents });
    }

    return result;
  }

  function hoveredSummary(slot: { severity: string; events: EventEntry[] }): string {
    if (slot.events.length === 0) return "No events";
    const types = slot.events.map((e) => typeLabels[e.type] ?? e.type);
    // Deduplicate
    const unique = [...new Set(types)];
    return unique.join(", ");
  }

  onMount(async () => {
    try {
      const res = await fetch(`${getBackendUrl()}/event_history?hours=${HOURS}`);
      events = await res.json();
    } catch {
      error = true;
    } finally {
      if (!error) slots = buildSlots(events);
      loading = false;
    }
  });
</script>

<div class="card px-4 py-3 sm:px-5 sm:py-3.5">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-1.5">
      <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
      <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Events - Last 7 days</p>
    </div>
    {#if hoveredIndex >= 0 && slots[hoveredIndex]}
      <span class="text-[0.625rem] tabular-nums text-text-muted">
        {slots[hoveredIndex].label} · <span class="{slots[hoveredIndex].severity === 'critical' ? 'text-status-critical' : slots[hoveredIndex].severity === 'warn' ? 'text-status-warning' : slots[hoveredIndex].severity === 'ok' ? 'text-status-ok' : 'text-text-muted'}">{hoveredSummary(slots[hoveredIndex])}</span>
      </span>
    {/if}
  </div>

  {#if loading}
    <div class="mt-2.5 flex gap-[2px]">
      {#each Array(TOTAL_SLOTS) as _}
        <div class="h-5 flex-1 animate-pulse rounded-[2px] bg-surface-elevated"></div>
      {/each}
    </div>
  {:else if error}
    <p class="mt-2.5 text-center text-[0.6875rem] text-text-muted">Unable to load event data</p>
  {:else}
    <div
      class="mt-2.5 flex gap-[2px]"
      role="img"
      aria-label="Security events over the last 7 days"
      onmouseleave={() => (hoveredIndex = -1)}
    >
      {#each slots as slot, i}
        <div
          class="h-5 flex-1 rounded-[2px] transition-opacity duration-100 {severityColors[slot.severity]} {hoveredIndex >= 0 && hoveredIndex !== i ? 'opacity-40' : ''}"
          role="presentation"
          onmouseenter={() => (hoveredIndex = i)}
        ></div>
      {/each}
    </div>
    <!-- Time labels -->
    <div class="mt-1 flex justify-between text-[0.5625rem] tabular-nums text-text-muted">
      <span>{slots[0]?.label ?? ""}</span>
      <span>{slots[Math.floor(TOTAL_SLOTS / 2)]?.label ?? ""}</span>
      <span>Now</span>
    </div>
  {/if}
</div>
