<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { apiFetch } from "../lib/fetch";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import activityIcon from "../icons/activity.svg?raw";

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

  async function fetchHealth() {
    loading = true;
    error = false;
    try {
      const res = await apiFetch(`${getBackendUrl()}/health_history?hours=${HOURS}`);
      if (!res.ok) throw new Error();
      entries = await res.json();
      slots = buildSlots(entries);
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    initLocale();
    fetchHealth();
  });
</script>

<div class="card px-4 py-3 sm:px-5 sm:py-3.5">
  <div class="flex min-h-[1.25rem] items-center justify-between gap-2">
    <div class="flex shrink-0 items-center gap-1.5">
      <Icon icon={activityIcon} class="h-3 w-3 text-text-muted" />
      <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.healthLast72h")}</p>
    </div>
    {#if hoveredIndex >= 0 && slots[hoveredIndex]}
      <span class="truncate text-[0.625rem] tabular-nums text-text-muted">
        {slots[hoveredIndex].label} · <span class="capitalize {slots[hoveredIndex].status === 'critical' ? 'text-status-critical' : slots[hoveredIndex].status === 'warn' ? 'text-status-warning' : slots[hoveredIndex].status === 'ok' ? 'text-status-ok' : 'text-text-muted'}">{slots[hoveredIndex].status === 'unknown' ? t('status.noData') : slots[hoveredIndex].status}</span>
      </span>
    {/if}
  </div>

  {#if loading}
    <div class="mt-2.5 flex gap-[2px]">
      {#each Array(TOTAL_SLOTS) as _}
        <div class="skeleton h-5 flex-1 rounded-[2px]"></div>
      {/each}
    </div>
  {:else if error}
    <div class="mt-2.5 flex items-center justify-center gap-2">
      <p class="text-[0.6875rem] text-text-muted">{t("error.healthData")}</p>
      <button onclick={fetchHealth} class="text-[0.6875rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
    </div>
  {:else}
    <div
      class="mt-2.5 flex gap-[2px]"
      role="img"
      aria-label={t("label.healthLast72h")}
      onmouseleave={() => (hoveredIndex = -1)}
    >
      {#each slots as slot, i}
        <div
          class="h-5 flex-1 rounded-[2px] transition-opacity duration-100 animate-bar-grow {statusColors[slot.status]} {hoveredIndex >= 0 && hoveredIndex !== i ? 'opacity-40' : ''}"
          style="animation-delay: {i * 15}ms"
          role="presentation"
          onmouseenter={() => (hoveredIndex = i)}
        ></div>
      {/each}
    </div>
    <!-- Time labels -->
    <div class="mt-1 flex justify-between text-[0.625rem] tabular-nums text-text-muted">
      <span>{slots[0]?.label ?? ""}</span>
      <span>{slots[Math.floor(TOTAL_SLOTS / 2)]?.label ?? ""}</span>
      <span>{t("label.now")}</span>
    </div>
  {/if}
</div>
