<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface SystemInfo {
    cpu_temp_celsius: number;
    cpu_load_percent: number;
    storage_info_gb: { total_gb: number; used_gb: number };
    ram_usage_mb: { total_mb: number; used_mb: number };
  }

  let info: SystemInfo | null = $state(null);
  let error = $state(false);

  onMount(async () => {
    try {
      const res = await fetch(`${getBackendUrl()}/system_info`);
      info = await res.json();
    } catch {
      error = true;
    }
  });

  function tempColor(temp: number): string {
    if (temp >= 70) return "text-status-critical";
    if (temp >= 55) return "text-status-warning";
    return "text-status-ok";
  }

  function barColor(pct: number): string {
    if (pct >= 90) return "bg-status-critical";
    if (pct >= 75) return "bg-status-warning";
    return "bg-accent";
  }

  function barTrackColor(pct: number): string {
    if (pct >= 90) return "bg-status-critical/10";
    if (pct >= 75) return "bg-status-warning/10";
    return "bg-accent/10";
  }

  function usagePct(used: number, total: number): number {
    return total > 0 ? Math.round((used / total) * 100) : 0;
  }
</script>

<div class="grid grid-cols-2 gap-2 lg:grid-cols-1 lg:gap-2.5">
  {#if error}
    <div class="card col-span-2 row-span-4 flex items-center justify-center px-4 py-8 text-center text-[0.8125rem] text-text-muted lg:col-span-1">
      Unable to reach system monitor
    </div>
  {:else if info}
    <!-- CPU Temperature -->
    <div class="card flex flex-col justify-center px-4 py-3 lg:px-5 lg:py-3.5">
      <div class="flex items-center gap-1.5">
        <svg class="h-3.5 w-3.5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
        </svg>
        <p class="text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">CPU Temp</p>
      </div>
      <p class="mt-1.5 text-2xl font-bold tabular-nums leading-none {tempColor(info.cpu_temp_celsius)}">
        {info.cpu_temp_celsius.toFixed(1)}<span class="text-xs font-medium">&deg;C</span>
      </p>
    </div>

    <!-- CPU Load -->
    {@const loadPct = Math.round(info.cpu_load_percent)}
    <div class="card flex flex-col justify-center px-4 py-3 lg:px-5 lg:py-3.5">
      <div class="flex items-center gap-1.5">
        <svg class="h-3.5 w-3.5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="4" width="16" height="16" rx="2" />
          <rect x="9" y="9" width="6" height="6" />
          <line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" />
          <line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" />
          <line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" />
          <line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" />
        </svg>
        <p class="text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">CPU Load</p>
      </div>
      <p class="mt-1.5 text-2xl font-bold tabular-nums leading-none text-text-primary">
        {loadPct}<span class="text-xs font-medium">%</span>
      </p>
      <div class="mt-2 h-1.5 rounded-full {barTrackColor(loadPct)}">
        <div
          class="h-full rounded-full {barColor(loadPct)} transition-[width] duration-500"
          style="width: {loadPct}%"
        ></div>
      </div>
    </div>

    <!-- Storage -->
    {@const storagePct = usagePct(info.storage_info_gb.used_gb, info.storage_info_gb.total_gb)}
    <div class="card flex flex-col justify-center px-4 py-3 lg:px-5 lg:py-3.5">
      <div class="flex items-center gap-1.5">
        <svg class="h-3.5 w-3.5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="12" x2="2" y2="12" />
          <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
          <line x1="6" y1="16" x2="6.01" y2="16" /><line x1="10" y1="16" x2="10.01" y2="16" />
        </svg>
        <p class="text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">Storage</p>
      </div>
      <p class="mt-1.5 text-2xl font-bold tabular-nums leading-none text-text-primary">
        {storagePct}<span class="text-xs font-medium">%</span>
      </p>
      <div class="mt-2 h-1.5 rounded-full {barTrackColor(storagePct)}">
        <div
          class="h-full rounded-full {barColor(storagePct)} transition-[width] duration-500"
          style="width: {storagePct}%"
        ></div>
      </div>
      <p class="mt-1 text-[0.6875rem] text-text-muted">
        {info.storage_info_gb.used_gb.toFixed(1)} / {info.storage_info_gb.total_gb.toFixed(1)} GB
      </p>
    </div>

    <!-- RAM -->
    {@const ramPct = usagePct(info.ram_usage_mb.used_mb, info.ram_usage_mb.total_mb)}
    <div class="card flex flex-col justify-center px-4 py-3 lg:px-5 lg:py-3.5">
      <div class="flex items-center gap-1.5">
        <svg class="h-3.5 w-3.5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="6" width="20" height="12" rx="2" />
          <line x1="6" y1="10" x2="6" y2="14" /><line x1="10" y1="10" x2="10" y2="14" />
          <line x1="14" y1="10" x2="14" y2="14" /><line x1="18" y1="10" x2="18" y2="14" />
        </svg>
        <p class="text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">RAM</p>
      </div>
      <p class="mt-1.5 text-2xl font-bold tabular-nums leading-none text-text-primary">
        {ramPct}<span class="text-xs font-medium">%</span>
      </p>
      <div class="mt-2 h-1.5 rounded-full {barTrackColor(ramPct)}">
        <div
          class="h-full rounded-full {barColor(ramPct)} transition-[width] duration-500"
          style="width: {ramPct}%"
        ></div>
      </div>
      <p class="mt-1 text-[0.6875rem] text-text-muted">
        {info.ram_usage_mb.used_mb.toFixed(0)} / {info.ram_usage_mb.total_mb.toFixed(0)} MB
      </p>
    </div>
  {:else}
    {#each Array(4) as _}
      <div class="card animate-pulse px-4 py-3">
        <div class="h-3 w-14 rounded bg-surface-elevated"></div>
        <div class="mt-2.5 h-5 w-16 rounded bg-surface-elevated"></div>
        <div class="mt-2 h-1 rounded-full bg-surface-elevated"></div>
      </div>
    {/each}
  {/if}
</div>
