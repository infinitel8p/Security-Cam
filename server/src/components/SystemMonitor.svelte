<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface ThrottleInfo {
    raw: string;
    under_voltage_now: boolean;
    freq_capped_now: boolean;
    throttled_now: boolean;
    soft_temp_limit_now: boolean;
    under_voltage_occurred: boolean;
    freq_capped_occurred: boolean;
    throttled_occurred: boolean;
    soft_temp_limit_occurred: boolean;
  }

  interface SystemInfo {
    cpu_temp_celsius: number;
    cpu_load_percent: number;
    storage_info_gb: { total_gb: number; used_gb: number };
    ram_usage_mb: { total_mb: number; used_mb: number };
    uptime_seconds: number;
    throttle: ThrottleInfo | null;
  }

  let info = $state<SystemInfo | null>(null);
  let error = $state(false);

  async function fetchInfo() {
    try {
      const res = await fetch(`${getBackendUrl()}/system_info`);
      if (!res.ok) throw new Error();
      info = await res.json();
      error = false;
    } catch {
      error = true;
    }
  }

  onMount(fetchInfo);

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

  function formatUptime(seconds: number | undefined | null): string {
    if (seconds == null || isNaN(seconds)) return "-";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}d ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }

  function throttleActive(t: ThrottleInfo): boolean {
    return t.under_voltage_now || t.freq_capped_now || t.throttled_now || t.soft_temp_limit_now;
  }

  function throttleHistory(t: ThrottleInfo): boolean {
    return t.under_voltage_occurred || t.freq_capped_occurred || t.throttled_occurred || t.soft_temp_limit_occurred;
  }

  let loadPct = $derived(info ? Math.round(info.cpu_load_percent) : 0);
  let storagePct = $derived(info ? usagePct(info.storage_info_gb.used_gb, info.storage_info_gb.total_gb) : 0);
  let ramPct = $derived(info ? usagePct(info.ram_usage_mb.used_mb, info.ram_usage_mb.total_mb) : 0);
</script>

{#if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-4 py-8 text-center">
    <p class="text-[0.8125rem] text-text-muted">Unable to reach system monitor</p>
    <button onclick={fetchInfo} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">Retry</button>
  </div>
{:else if info}
  <div class="card divide-y divide-border-subtle">
    <!-- Row 1: Temp + CPU side by side -->
    <div class="grid grid-cols-2 divide-x divide-border-subtle">
      <!-- CPU Temp -->
      <div class="px-4 py-3">
        <div class="flex items-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Temp</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {tempColor(info.cpu_temp_celsius)}">
          {info.cpu_temp_celsius.toFixed(0)}<span class="text-[0.625rem] font-medium">&deg;C</span>
        </p>
      </div>

      <!-- CPU Load -->
      <div class="px-4 py-3">
        <div class="flex items-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" />
            <rect x="9" y="9" width="6" height="6" />
            <line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" />
            <line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" />
            <line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" />
            <line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">CPU</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none text-text-primary">
          {loadPct}<span class="text-[0.625rem] font-medium">%</span>
        </p>
        <div class="mt-1.5 h-1 rounded-full {barTrackColor(loadPct)}">
          <div class="h-full rounded-full {barColor(loadPct)} animate-bar" style="width: {loadPct}%"></div>
        </div>
      </div>
    </div>

    <!-- Row 2: Storage + RAM side by side -->
    <div class="grid grid-cols-2 divide-x divide-border-subtle">
      <!-- Storage -->
      <div class="px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="12" x2="2" y2="12" />
              <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
              <line x1="6" y1="16" x2="6.01" y2="16" /><line x1="10" y1="16" x2="10.01" y2="16" />
            </svg>
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Disk</p>
          </div>
          <p class="text-[0.625rem] tabular-nums text-text-muted">{info.storage_info_gb.used_gb.toFixed(1)}/{info.storage_info_gb.total_gb.toFixed(0)}GB</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none text-text-primary">
          {storagePct}<span class="text-[0.625rem] font-medium">%</span>
        </p>
        <div class="mt-1.5 h-1 rounded-full {barTrackColor(storagePct)}">
          <div class="h-full rounded-full {barColor(storagePct)} animate-bar" style="width: {storagePct}%"></div>
        </div>
      </div>

      <!-- RAM -->
      <div class="px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="6" width="20" height="12" rx="2" />
              <line x1="6" y1="10" x2="6" y2="14" /><line x1="10" y1="10" x2="10" y2="14" />
              <line x1="14" y1="10" x2="14" y2="14" /><line x1="18" y1="10" x2="18" y2="14" />
            </svg>
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">RAM</p>
          </div>
          <p class="text-[0.625rem] tabular-nums text-text-muted">{info.ram_usage_mb.used_mb.toFixed(0)}/{info.ram_usage_mb.total_mb.toFixed(0)}MB</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none text-text-primary">
          {ramPct}<span class="text-[0.625rem] font-medium">%</span>
        </p>
        <div class="mt-1.5 h-1 rounded-full {barTrackColor(ramPct)}">
          <div class="h-full rounded-full {barColor(ramPct)} animate-bar" style="width: {ramPct}%"></div>
        </div>
      </div>
    </div>

    <!-- Row 3: Uptime + Throttle -->
    <div class="grid grid-cols-2 divide-x divide-border-subtle">
      <!-- Uptime -->
      <div class="px-4 py-3">
        <div class="flex items-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Uptime</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {info.uptime_seconds ? 'text-text-primary' : 'text-text-muted'}">
          {formatUptime(info.uptime_seconds)}
        </p>
      </div>

      <!-- Throttle -->
      <div class="px-4 py-3">
        <div class="flex items-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Throttle</p>
        </div>
        {#if info.throttle}
          {@const active = throttleActive(info.throttle)}
          {@const history = throttleHistory(info.throttle)}
          {#if active}
            <p class="mt-1 text-lg font-bold leading-none text-status-critical">Active</p>
            <div class="mt-1 flex flex-wrap gap-1">
              {#if info.throttle.under_voltage_now}
                <span class="rounded bg-status-critical/10 px-1.5 py-0.5 text-[0.625rem] font-medium text-status-critical">Low voltage</span>
              {/if}
              {#if info.throttle.throttled_now}
                <span class="rounded bg-status-critical/10 px-1.5 py-0.5 text-[0.625rem] font-medium text-status-critical">Throttled</span>
              {/if}
              {#if info.throttle.freq_capped_now}
                <span class="rounded bg-status-warning/10 px-1.5 py-0.5 text-[0.625rem] font-medium text-status-warning">Freq cap</span>
              {/if}
              {#if info.throttle.soft_temp_limit_now}
                <span class="rounded bg-status-warning/10 px-1.5 py-0.5 text-[0.625rem] font-medium text-status-warning">Temp limit</span>
              {/if}
            </div>
          {:else if history}
            <p class="mt-1 text-lg font-bold leading-none text-status-warning">Past</p>
            <p class="mt-0.5 text-[0.625rem] text-text-muted">Since boot</p>
          {:else}
            <p class="mt-1 text-lg font-bold leading-none text-status-ok">OK</p>
          {/if}
        {:else}
          <p class="mt-1 text-xl font-bold leading-none text-text-muted">-</p>
        {/if}
      </div>
    </div>
  </div>
{:else}
  <!-- Skeleton -->
  <div class="card divide-y divide-border-subtle">
    {#each Array(3) as _}
      <div class="grid grid-cols-2 divide-x divide-border-subtle">
        <div class="px-4 py-3">
          <div class="skeleton h-2.5 w-10"></div>
          <div class="skeleton mt-2 h-5 w-12"></div>
        </div>
        <div class="px-4 py-3">
          <div class="skeleton h-2.5 w-10"></div>
          <div class="skeleton mt-2 h-5 w-12"></div>
        </div>
      </div>
    {/each}
  </div>
{/if}
