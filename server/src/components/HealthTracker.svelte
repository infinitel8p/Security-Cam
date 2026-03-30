<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface HealthEntry {
    ts: string;
    status: "ok" | "warn" | "critical" | "unknown";
    temp: number | null;
    load: number | null;
  }

  let entries: HealthEntry[] = $state([]);
  let slots: { status: string; label: string }[] = $state([]);
  let loading = $state(true);
  let error = $state(false);
  let hoveredIndex = $state(-1);

  const HOURS = 72; // 3 days
  const TOTAL_SLOTS = 48; // 1.5h per bucket
  const BUCKET_MS = (HOURS / TOTAL_SLOTS) * 60 * 60 * 1000;

  const statusColors: Record<string, string> = {
    ok: "bg-status-ok",
    warn: "bg-status-warning",
    critical: "bg-status-critical",
    unknown: "bg-surface-elevated",
  };

  function buildSlots(data: HealthEntry[]) {
    const now = Date.now();
    const result: { status: string; label: string }[] = [];

    for (let i = 0; i < TOTAL_SLOTS; i++) {
      const bucketStart = now - (TOTAL_SLOTS - i) * BUCKET_MS;
      const bucketEnd = bucketStart + BUCKET_MS;

      const bucketEntries = data.filter((e) => {
        const t = new Date(e.ts).getTime();
        return t >= bucketStart && t < bucketEnd;
      });

      let status = "unknown";
      if (bucketEntries.length > 0) {
        if (bucketEntries.some((e) => e.status === "critical")) status = "critical";
        else if (bucketEntries.some((e) => e.status === "warn")) status = "warn";
        else status = "ok";
      }

      const time = new Date(bucketStart);
      const h = time.getHours().toString().padStart(2, "0");
      const m = time.getMinutes().toString().padStart(2, "0");
      result.push({ status, label: `${h}:${m}` });
    }

    return result;
  }

  onMount(async () => {
    try {
      const res = await fetch(`${getBackendUrl()}/health_history?hours=${HOURS}`);
      entries = await res.json();
    } catch {
      error = true;
    } finally {
      if (!error) slots = buildSlots(entries);
      loading = false;
    }
  });
</script>

<div class="card px-4 py-3 sm:px-5 sm:py-3.5">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-1.5">
      <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
      <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Health - Last 72h</p>
    </div>
    {#if hoveredIndex >= 0 && slots[hoveredIndex]}
      <span class="text-[0.625rem] tabular-nums text-text-muted">
        {slots[hoveredIndex].label} · <span class="capitalize {slots[hoveredIndex].status === 'critical' ? 'text-status-critical' : slots[hoveredIndex].status === 'warn' ? 'text-status-warning' : slots[hoveredIndex].status === 'ok' ? 'text-status-ok' : 'text-text-muted'}">{slots[hoveredIndex].status === 'unknown' ? 'No data' : slots[hoveredIndex].status}</span>
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
    <p class="mt-2.5 text-center text-[0.6875rem] text-text-muted">Unable to load health data</p>
  {:else}
    <div
      class="mt-2.5 flex gap-[2px]"
      role="img"
      aria-label="System health over the last 72 hours"
      onmouseleave={() => (hoveredIndex = -1)}
    >
      {#each slots as slot, i}
        <div
          class="h-5 flex-1 rounded-[2px] transition-opacity duration-100 {statusColors[slot.status]} {hoveredIndex >= 0 && hoveredIndex !== i ? 'opacity-40' : ''}"
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
