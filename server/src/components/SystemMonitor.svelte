<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { apiFetch } from "../lib/fetch";
  import { sseClient } from "../lib/sse";
  import { animatedNumber } from "../lib/animate-number";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import temperatureIcon from "../icons/temperature.svg?raw";
  import cpuIcon from "../icons/cpu.svg?raw";
  import databaseIcon from "../icons/database.svg?raw";
  import deviceDesktopIcon from "../icons/device-desktop.svg?raw";
  import clockIcon from "../icons/clock.svg?raw";


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

  interface SdHealth {
    name?: string;
    serial?: string;
    manufacturing_date?: string;
    written_since_boot_gb?: number;
    life_time_est?: string;
  }

  interface SystemInfo {
    cpu_temp_celsius: number;
    cpu_load_percent: number;
    storage_info_gb: { total_gb: number; used_gb: number };
    ram_usage_mb: { total_mb: number; used_mb: number };
    uptime_seconds: number;
    throttle: ThrottleInfo | null;
    sd_health: SdHealth | null;
  }

  let info = $state<SystemInfo | null>(null);
  let error = $state(false);
  let retrying = $state(false);
  let unsub: (() => void) | null = null;

  // ── Animated display values (start at 0, count up on first load) ──
  let animTick = $state(0);
  const bump = () => { animTick++; };
  const aTemp = animatedNumber(0, bump);
  const aLoad = animatedNumber(0, bump);
  const aStorageUsed = animatedNumber(0, bump);
  const aRamUsed = animatedNumber(0, bump);

  // Reactive wrappers
  let dTemp = $derived((animTick, aTemp.value));
  let dLoad = $derived((animTick, aLoad.value));
  let dStorageUsed = $derived((animTick, aStorageUsed.value));
  let dRamUsed = $derived((animTick, aRamUsed.value));

  function applyInfo(d: SystemInfo) {
    info = d;
    error = false;
    aTemp.set(d.cpu_temp_celsius);
    aLoad.set(d.cpu_load_percent);
    aStorageUsed.set(d.storage_info_gb.used_gb);
    aRamUsed.set(d.ram_usage_mb.used_mb);
  }

  async function fetchInfo() {
    retrying = true;
    try {
      const res = await apiFetch(`${getBackendUrl()}/system_info`);
      if (!res.ok) throw new Error();
      applyInfo(await res.json());
    } catch {
      error = true;
    } finally {
      retrying = false;
    }
  }

  onMount(() => {
    initLocale();
    fetchInfo();

    const sse = sseClient();
    sse.registerFallback({
      event: "system_info",
      endpoint: "/system_info",
      interval: 15_000,
    });
    unsub = sse.on("system_info", (ev) => applyInfo(ev));
  });

  onDestroy(() => {
    unsub?.();
    aTemp.destroy(); aLoad.destroy(); aStorageUsed.destroy(); aRamUsed.destroy();
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

  // Derived from animated values - numbers animate smoothly, colors use real target
  let loadPct = $derived(Math.round(dLoad));
  let storagePct = $derived(info ? usagePct(dStorageUsed, info.storage_info_gb.total_gb) : 0);
  let ramPct = $derived(info ? usagePct(dRamUsed, info.ram_usage_mb.total_mb) : 0);

  // Smooth (unrounded) percentages for bar widths
  let loadBar = $derived(dLoad);
  let storageBar = $derived(info && info.storage_info_gb.total_gb > 0 ? (dStorageUsed / info.storage_info_gb.total_gb) * 100 : 0);
  let ramBar = $derived(info && info.ram_usage_mb.total_mb > 0 ? (dRamUsed / info.ram_usage_mb.total_mb) * 100 : 0);

  // Colors use real (target) values so they update immediately
  let realLoadPct = $derived(info ? Math.round(info.cpu_load_percent) : 0);
  let realStoragePct = $derived(info ? usagePct(info.storage_info_gb.used_gb, info.storage_info_gb.total_gb) : 0);
  let realRamPct = $derived(info ? usagePct(info.ram_usage_mb.used_mb, info.ram_usage_mb.total_mb) : 0);
</script>

{#if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-4 py-8 text-center">
    <p class="text-[0.8125rem] text-text-muted">{t("error.systemMonitor")}</p>
    <button onclick={fetchInfo} disabled={retrying} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover disabled:opacity-50">
      {retrying ? t("status.retrying") : t("btn.retry")}
    </button>
  </div>
{:else if info}
  <div class="card divide-y divide-border-subtle">
    <!-- Row 1: Temp (+ throttle) | CPU (+ uptime) -->
    <div class="grid grid-cols-2 divide-x divide-border-subtle">
      <!-- CPU Temp + Throttle -->
      <div class="px-3 py-2">
        <div class="flex items-center gap-1.5">
          <Icon icon={temperatureIcon} class="h-3 w-3 text-text-muted" stroke={2} />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.temperature")}</p>
        </div>
        <p class="mt-0.5 text-base font-bold tabular-nums leading-none {tempColor(info.cpu_temp_celsius)}">
          {Math.round(dTemp)}<span class="text-[0.5625rem] font-medium">&deg;C</span>
        </p>
        <!-- Throttle inline -->
        {#if info.throttle}
          {@const active = throttleActive(info.throttle)}
          {@const history = throttleHistory(info.throttle)}
          {#if active}
            <div class="mt-1.5 flex flex-wrap gap-1">
              {#if info.throttle.under_voltage_now}
                <span class="rounded bg-status-critical/10 px-1 py-0.5 text-[0.5625rem] font-medium text-status-critical">{t("throttle.lowVoltage")}</span>
              {/if}
              {#if info.throttle.throttled_now}
                <span class="rounded bg-status-critical/10 px-1 py-0.5 text-[0.5625rem] font-medium text-status-critical">{t("throttle.throttled")}</span>
              {/if}
              {#if info.throttle.freq_capped_now}
                <span class="rounded bg-status-warning/10 px-1 py-0.5 text-[0.5625rem] font-medium text-status-warning">{t("throttle.freqCapped")}</span>
              {/if}
              {#if info.throttle.soft_temp_limit_now}
                <span class="rounded bg-status-warning/10 px-1 py-0.5 text-[0.5625rem] font-medium text-status-warning">{t("throttle.tempLimit")}</span>
              {/if}
            </div>
          {:else if history}
            <p class="mt-1 text-[0.5625rem] text-status-warning">{t("throttle.pastEvent")}</p>
          {/if}
        {/if}
      </div>

      <!-- CPU Load + Uptime -->
      <div class="px-3 py-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={cpuIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.cpu")}</p>
          </div>
          <p class="flex items-center gap-1 text-[0.5625rem] tabular-nums text-text-muted">
            <Icon icon={clockIcon} class="h-2.5 w-2.5" stroke={2} />
            {formatUptime(info.uptime_seconds)}
          </p>
        </div>
        <p class="mt-0.5 text-base font-bold tabular-nums leading-none text-text-primary">
          {loadPct}<span class="text-[0.5625rem] font-medium">%</span>
        </p>
        <div class="mt-1 h-0.5 rounded-full {barTrackColor(realLoadPct)}">
          <div class="h-full rounded-full {barColor(realLoadPct)}" style="width: {loadBar}%"></div>
        </div>
      </div>
    </div>

    <!-- Row 2: Storage (+ SD card) | RAM -->
    <div class="grid grid-cols-2 divide-x divide-border-subtle">
      <!-- Storage + SD info -->
      <div class="px-3 py-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={databaseIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.disk")}</p>
          </div>
          <p class="text-[0.5625rem] tabular-nums text-text-muted">{dStorageUsed.toFixed(1)}/{info.storage_info_gb.total_gb.toFixed(0)}GB</p>
        </div>
        <p class="mt-0.5 text-base font-bold tabular-nums leading-none text-text-primary">
          {storagePct}<span class="text-[0.5625rem] font-medium">%</span>
        </p>
        <div class="mt-1 h-0.5 rounded-full {barTrackColor(realStoragePct)}">
          <div class="h-full rounded-full {barColor(realStoragePct)}" style="width: {storageBar}%"></div>
        </div>
        {#if info.sd_health}
          <p class="mt-1.5 text-[0.5625rem] tabular-nums text-text-muted">
            {info.sd_health.name ?? "SD"}{#if info.sd_health.manufacturing_date}{" "}· {info.sd_health.manufacturing_date}{/if}
          </p>
        {/if}
      </div>

      <!-- RAM -->
      <div class="px-3 py-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={deviceDesktopIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.ram")}</p>
          </div>
          <p class="text-[0.5625rem] tabular-nums text-text-muted">{Math.round(dRamUsed)}/{info.ram_usage_mb.total_mb.toFixed(0)}MB</p>
        </div>
        <p class="mt-0.5 text-base font-bold tabular-nums leading-none text-text-primary">
          {ramPct}<span class="text-[0.5625rem] font-medium">%</span>
        </p>
        <div class="mt-1 h-0.5 rounded-full {barTrackColor(realRamPct)}">
          <div class="h-full rounded-full {barColor(realRamPct)}" style="width: {ramBar}%"></div>
        </div>
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
