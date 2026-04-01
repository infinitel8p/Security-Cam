<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import temperatureIcon from "../icons/temperature.svg?raw";
  import cpuIcon from "../icons/cpu.svg?raw";
  import databaseIcon from "../icons/database.svg?raw";
  import deviceDesktopIcon from "../icons/device-desktop.svg?raw";
  import clockIcon from "../icons/clock.svg?raw";
  import boltIcon from "../icons/bolt.svg?raw";
  import activityIcon from "../icons/activity.svg?raw";
  import wifiIcon from "../icons/wifi.svg?raw";
  import videoIcon from "../icons/video.svg?raw";
  import cameraIcon from "../icons/camera.svg?raw";
  import shieldIcon from "../icons/shield.svg?raw";
  import bluetoothIcon from "../icons/bluetooth.svg?raw";

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
    oemid?: string;
    manufacturing_date?: string;
    hw_revision?: string;
    fw_revision?: string;
    written_since_boot_gb?: number;
    life_time_est?: string;
    preferred_erase_size_mb?: number;
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

  interface ExtendedStats {
    process_count?: number;
    cpu_count?: number;
    cpu_per_core?: number[];
    boot_time?: string;
    hostname?: string;
    network?: { bytes_sent: number; bytes_recv: number; packets_sent: number; packets_recv: number };
    swap?: { total_mb: number; used_mb: number; percent: number };
    load_avg?: { "1min": number; "5min": number; "15min": number };
    python_version?: string;
    os_info?: string;
    arch?: string;
  }

  interface ConnectionInfo {
    bluetooth: { online: number; total: number };
    wifi: { online: number; total: number };
    ap_clients?: number;
  }

  interface StreamSettings {
    width: number;
    height: number;
    fps: number;
  }

  interface SensorInfo {
    enabled: boolean;
    armed: boolean;
    triggered: boolean;
    suppressed: boolean;
    recording_from_sensor: boolean;
    config?: { type?: string; gpio?: number };
  }

  interface TimelapseInfo {
    enabled: boolean;
    interval_minutes: number;
    today_frame_count: number;
    last_capture: string | null;
  }

  let info = $state<SystemInfo | null>(null);
  let extended = $state<ExtendedStats | null>(null);
  let connections = $state<ConnectionInfo | null>(null);
  let stream = $state<StreamSettings | null>(null);
  let sensor = $state<SensorInfo | null>(null);
  let timelapse = $state<TimelapseInfo | null>(null);
  let archiveCount = $state<number | null>(null);
  let recording = $state(false);
  let error = $state(false);
  let retrying = $state(false);
  let pollTimer: ReturnType<typeof setTimeout> | null = null;
  let consecutiveErrors = 0;
  let destroyed = false;
  let pulseKey = $state(0);

  // History for sparklines
  const HISTORY_LEN = 60;
  const POLL_INTERVAL = 10_000; // 10s — gentler on the Pi's CPU
  let cpuHistory = $state<number[]>([]);
  let tempHistory = $state<number[]>([]);
  let ramHistory = $state<number[]>([]);

  async function fetchInfo() {
    // Skip fetch when tab is hidden — no point updating invisible UI
    if (typeof document !== "undefined" && document.hidden) return;

    retrying = true;
    try {
      const res = await fetch(`${getBackendUrl()}/system_info?extended=1`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      info = data;
      if (data.extended) extended = data.extended;
      error = false;
      consecutiveErrors = 0;
      pulseKey++;

      if (info) {
        const load = info.cpu_load_percent ?? 0;
        const temp = info.cpu_temp_celsius ?? 0;
        const ram = usagePct(info.ram_usage_mb?.used_mb ?? 0, info.ram_usage_mb?.total_mb ?? 1);
        cpuHistory = [...cpuHistory.slice(-(HISTORY_LEN - 1)), Math.round(load)];
        tempHistory = [...tempHistory.slice(-(HISTORY_LEN - 1)), temp];
        ramHistory = [...ramHistory.slice(-(HISTORY_LEN - 1)), ram];
      }

      // Fetch secondary data (non-blocking)
      fetchSecondary();
    } catch {
      consecutiveErrors++;
      // Only show error state if we never loaded successfully
      if (!info) error = true;
    } finally {
      retrying = false;
    }
  }

  function schedulePoll() {
    if (destroyed) return;
    // Back off on consecutive errors: 10s → 20s → 40s, capped at 60s
    const delay = Math.min(POLL_INTERVAL * Math.pow(2, consecutiveErrors), 60_000);
    pollTimer = setTimeout(() => {
      if (destroyed) return;
      fetchInfo().then(schedulePoll);
    }, delay);
  }

  async function fetchSecondary() {
    const base = getBackendUrl();
    const fetches = [
      fetch(`${base}/connections`).then(r => r.ok ? r.json() : null).then(d => { if (d) connections = d; }).catch(() => {}),
      fetch(`${base}/stream_settings`).then(r => r.ok ? r.json() : null).then(d => { if (d) stream = d; }).catch(() => {}),
      fetch(`${base}/sensor/status`).then(r => r.ok ? r.json() : null).then(d => { if (d) sensor = d; }).catch(() => {}),
      fetch(`${base}/timelapse/status`).then(r => r.ok ? r.json() : null).then(d => { if (d) timelapse = d; }).catch(() => {}),
      fetch(`${base}/recording_status`).then(r => r.ok ? r.json() : null).then(d => { if (d) recording = d.recording ?? false; }).catch(() => {}),
      fetch(`${base}/archive`).then(r => r.ok ? r.json() : null).then(d => { if (Array.isArray(d)) archiveCount = d.length; }).catch(() => {}),
    ];
    await Promise.allSettled(fetches);
  }

  async function loadHistory() {
    try {
      const res = await fetch(`${getBackendUrl()}/health_history?hours=1`);
      if (!res.ok) return;
      const entries: { temp: number | null; load: number | null }[] = await res.json();
      if (entries.length > 0) {
        cpuHistory = entries.filter((e) => e.load != null).map((e) => Math.round(e.load!)).slice(-HISTORY_LEN);
        tempHistory = entries.filter((e) => e.temp != null).map((e) => e.temp!).slice(-HISTORY_LEN);
      }
    } catch {
      // non-critical
    }
  }

  onMount(() => {
    initLocale();
    loadHistory().then(() => fetchInfo()).then(schedulePoll);
  });

  onDestroy(() => {
    destroyed = true;
    if (pollTimer) clearTimeout(pollTimer);
  });

  function usagePct(used: number, total: number): number {
    return total > 0 ? Math.round((used / total) * 100) : 0;
  }

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

  function statusDotColor(pct: number): string {
    if (pct >= 90) return "bg-status-critical";
    if (pct >= 75) return "bg-status-warning";
    return "bg-status-ok";
  }

  /** Subtle card glow keyed to status — "calm until it matters" */
  function cardGlow(pct: number): string {
    if (pct >= 90) return "shadow-[inset_0_1px_0_0_rgba(240,104,104,0.15),0_0_20px_-6px_rgba(240,104,104,0.1)]";
    if (pct >= 75) return "shadow-[inset_0_1px_0_0_rgba(240,185,58,0.12),0_0_16px_-6px_rgba(240,185,58,0.08)]";
    return "";
  }

  /** Animated border sweep class for warning/critical cards */
  function cardSweepClass(pct: number): string {
    if (pct >= 90) return "card-sweep-critical";
    if (pct >= 75) return "card-sweep-warn";
    return "";
  }

  /** Sparkline stroke color keyed to status */
  function sparklineColor(pct: number): string {
    if (pct >= 90) return "text-status-critical/50";
    if (pct >= 75) return "text-status-warning/50";
    return "text-accent/50";
  }

  function formatUptimeLong(seconds: number | undefined | null): string {
    if (seconds == null || isNaN(seconds)) return "-";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const parts: string[] = [];
    if (d > 0) parts.push(`${d}d`);
    if (h > 0) parts.push(`${h}h`);
    parts.push(`${m}m`);
    return parts.join(" ");
  }

  function throttleActive(t: ThrottleInfo): boolean {
    return t.under_voltage_now || t.freq_capped_now || t.throttled_now || t.soft_temp_limit_now;
  }

  function throttleHistory(t: ThrottleInfo): boolean {
    return t.under_voltage_occurred || t.freq_capped_occurred || t.throttled_occurred || t.soft_temp_limit_occurred;
  }

  /** Build SVG polyline points — always fills full width */
  function sparklinePoints(data: number[], max: number): string {
    if (data.length < 2) return "";
    const safeMax = max > 0 ? max : 1;
    const w = 100;
    const h = 24;
    const step = w / (data.length - 1);
    return data
      .map((v, i) => {
        const x = i * step;
        const y = h - (Math.min(v, safeMax) / safeMax) * h;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }

  function formatBytes(bytes: number | null | undefined): string {
    if (bytes == null || !isFinite(bytes) || bytes < 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
    return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
  }

  function formatBootTime(iso: string | undefined): string {
    if (!iso) return "-";
    try {
      const d = new Date(iso);
      return d.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return iso;
    }
  }

  /** Safe numeric access — returns 0 for null/undefined/NaN */
  function num(v: number | null | undefined): number {
    return v != null && isFinite(v) ? v : 0;
  }

  let cpuTemp = $derived(info ? num(info.cpu_temp_celsius) : 0);
  let tempPctLevel = $derived(cpuTemp >= 70 ? 90 : cpuTemp >= 55 ? 80 : 0);
  let loadPct = $derived(info ? Math.round(num(info.cpu_load_percent)) : 0);
  let storagePct = $derived(info ? usagePct(num(info.storage_info_gb?.used_gb), num(info.storage_info_gb?.total_gb)) : 0);
  let ramPct = $derived(info ? usagePct(num(info.ram_usage_mb?.used_mb), num(info.ram_usage_mb?.total_mb)) : 0);
  let storageFreeGb = $derived(info ? num(info.storage_info_gb?.total_gb) - num(info.storage_info_gb?.used_gb) : 0);
</script>

{#if error}
  <div class="card mt-6 flex flex-col items-center justify-center gap-2 px-4 py-8 text-center">
    <p class="text-[0.8125rem] text-text-muted">{t("error.systemMonitor")}</p>
    <button onclick={fetchInfo} disabled={retrying} class="text-[0.75rem] font-medium text-accent transition-colors hover:text-accent-hover disabled:opacity-50">
      {retrying ? t("status.retrying") : t("btn.retry")}
    </button>
  </div>
{:else if info}
  <div class="mt-6 animate-in">
    <!-- Uptime + Host + Boot — compact inline row -->
    <div class="card flex flex-wrap items-center gap-x-6 gap-y-1 px-4 py-3 min-w-0">
      <div class="flex items-center gap-2">
        <Icon icon={clockIcon} class="h-3.5 w-3.5 text-accent" stroke={2} />
        <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.uptime")}</p>
        <p class="text-sm font-bold tabular-nums text-text-primary">{formatUptimeLong(info.uptime_seconds)}</p>
      </div>
      {#if extended?.hostname}
        <div class="flex items-center gap-2">
          <Icon icon={deviceDesktopIcon} class="h-3.5 w-3.5 text-text-muted" stroke={2} />
          <p class="text-sm font-medium text-text-secondary truncate">{extended.hostname}</p>
        </div>
      {/if}
      {#if extended?.boot_time}
        <div class="flex items-center gap-2">
          <Icon icon={activityIcon} class="h-3.5 w-3.5 text-text-muted" stroke={2} />
          <p class="text-sm tabular-nums text-text-secondary">{formatBootTime(extended.boot_time)}</p>
        </div>
      {/if}
    </div>

    <!-- CPU + Temp row -->
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      <!-- CPU Load -->
      <div class="card px-4 py-4 transition-shadow duration-700 {cardGlow(loadPct)} {cardSweepClass(loadPct)}">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={cpuIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.cpu")}</p>
          </div>
          <span class="h-2 w-2 rounded-full {statusDotColor(loadPct)}"></span>
        </div>
        <p class="mt-2 text-4xl font-bold tabular-nums leading-none text-text-primary">
          {loadPct}<span class="ml-0.5 text-xs font-medium text-text-muted/60">%</span>
        </p>
        <div class="mt-3 h-1 rounded-full {barTrackColor(loadPct)}">
          <div class="h-full rounded-full {barColor(loadPct)} transition-all duration-500" style="width: {loadPct}%"></div>
        </div>
        {#if cpuHistory.length > 1}
          <svg class="mt-3 h-8 w-full" viewBox="0 0 100 24" preserveAspectRatio="none">
            <defs>
              <linearGradient id="cpu-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="currentColor" stop-opacity="0.12" />
                <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
              </linearGradient>
            </defs>
            {#key pulseKey}
              <polygon
                points="{sparklinePoints(cpuHistory, 100)} 100,24 0,24"
                fill="url(#cpu-fill)"
                class="{sparklineColor(loadPct)} animate-sparkline-pulse"
              />
            {/key}
            <polyline
              points={sparklinePoints(cpuHistory, 100)}
              fill="none"
              stroke="currentColor"
              stroke-width="1.2"
              stroke-linejoin="round"
              class="{sparklineColor(loadPct)}"
            />
          </svg>
        {/if}
        <!-- Per-core bars -->
        {#if extended?.cpu_per_core && extended.cpu_per_core.length > 1}
          <div class="mt-3 space-y-1">
            {#each extended.cpu_per_core as core, i}
              <div class="flex items-center gap-2">
                <span class="w-5 text-[0.625rem] tabular-nums text-text-muted text-right">{i}</span>
                <div class="flex-1 h-1 rounded-full {barTrackColor(core)}">
                  <div class="h-full rounded-full {barColor(core)} transition-all duration-500" style="width: {core}%"></div>
                </div>
                <span class="w-7 text-[0.625rem] tabular-nums text-text-muted text-right">{core}%</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- CPU Temp -->
      <div class="card px-4 py-4 transition-shadow duration-700 {cardGlow(tempPctLevel)} {cardSweepClass(tempPctLevel)}">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={temperatureIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.temperature")}</p>
          </div>
          <span class="h-2 w-2 rounded-full {statusDotColor(tempPctLevel)}"></span>
        </div>
        <p class="mt-2 text-4xl font-bold tabular-nums leading-none {tempColor(cpuTemp)}">
          {cpuTemp.toFixed(0)}<span class="ml-0.5 text-xs font-medium text-text-muted/60">&deg;C</span>
        </p>
        <div class="mt-3 h-1 rounded-full {barTrackColor(tempPctLevel)}">
          <div class="h-full rounded-full {barColor(tempPctLevel)} transition-all duration-500" style="width: {Math.min(cpuTemp / 85 * 100, 100)}%"></div>
        </div>
        {#if tempHistory.length > 1}
          <svg class="mt-3 h-8 w-full" viewBox="0 0 100 24" preserveAspectRatio="none">
            <defs>
              <linearGradient id="temp-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="currentColor" stop-opacity="0.12" />
                <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
              </linearGradient>
            </defs>
            {#key pulseKey}
              <polygon
                points="{sparklinePoints(tempHistory, 85)} 100,24 0,24"
                fill="url(#temp-fill)"
                class="{sparklineColor(tempPctLevel)} animate-sparkline-pulse"
              />
            {/key}
            <polyline
              points={sparklinePoints(tempHistory, 85)}
              fill="none"
              stroke="currentColor"
              stroke-width="1.2"
              stroke-linejoin="round"
              class="{sparklineColor(tempPctLevel)}"
            />
          </svg>
        {/if}
      </div>
    </div>

    <!-- RAM + Storage row -->
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      <!-- RAM -->
      <div class="card px-4 py-4 transition-shadow duration-700 {cardGlow(ramPct)} {cardSweepClass(ramPct)}">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={deviceDesktopIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.ram")}</p>
          </div>
          <p class="text-[0.6875rem] tabular-nums text-text-muted">{num(info.ram_usage_mb?.used_mb).toFixed(0)} / {num(info.ram_usage_mb?.total_mb).toFixed(0)} MB</p>
        </div>
        <p class="mt-2 text-4xl font-bold tabular-nums leading-none text-text-primary">
          {ramPct}<span class="ml-0.5 text-xs font-medium text-text-muted/60">%</span>
        </p>
        <div class="mt-3 h-1 rounded-full {barTrackColor(ramPct)}">
          <div class="h-full rounded-full {barColor(ramPct)} transition-all duration-500" style="width: {ramPct}%"></div>
        </div>
        {#if ramHistory.length > 1}
          <svg class="mt-3 h-8 w-full" viewBox="0 0 100 24" preserveAspectRatio="none">
            <defs>
              <linearGradient id="ram-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="currentColor" stop-opacity="0.12" />
                <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
              </linearGradient>
            </defs>
            {#key pulseKey}
              <polygon
                points="{sparklinePoints(ramHistory, 100)} 100,24 0,24"
                fill="url(#ram-fill)"
                class="{sparklineColor(ramPct)} animate-sparkline-pulse"
              />
            {/key}
            <polyline
              points={sparklinePoints(ramHistory, 100)}
              fill="none"
              stroke="currentColor"
              stroke-width="1.2"
              stroke-linejoin="round"
              class="{sparklineColor(ramPct)}"
            />
          </svg>
        {/if}
        <!-- Swap -->
        {#if extended?.swap && extended.swap.total_mb > 0}
          <div class="mt-3">
            <div class="flex items-center justify-between">
              <p class="text-[0.625rem] uppercase text-text-muted">{t("stats.swap")}</p>
              <p class="text-[0.625rem] tabular-nums text-text-muted">{extended.swap.used_mb} / {extended.swap.total_mb} MB</p>
            </div>
            <div class="mt-1 h-0.5 rounded-full {barTrackColor(extended.swap.percent)}">
              <div class="h-full rounded-full {barColor(extended.swap.percent)} transition-all duration-500" style="width: {extended.swap.percent}%"></div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Storage -->
      <div class="card px-4 py-4 transition-shadow duration-700 {cardGlow(storagePct)} {cardSweepClass(storagePct)}">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={databaseIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.disk")}</p>
          </div>
          <p class="text-[0.6875rem] tabular-nums text-text-muted">{num(info.storage_info_gb?.used_gb).toFixed(1)} / {num(info.storage_info_gb?.total_gb).toFixed(0)} GB</p>
        </div>
        <p class="mt-2 text-4xl font-bold tabular-nums leading-none text-text-primary">
          {storagePct}<span class="ml-0.5 text-xs font-medium text-text-muted/60">%</span>
        </p>
        <div class="mt-3 h-1 rounded-full {barTrackColor(storagePct)}">
          <div class="h-full rounded-full {barColor(storagePct)} transition-all duration-500" style="width: {storagePct}%"></div>
        </div>
        <p class="mt-3 text-[0.6875rem] tabular-nums text-text-muted">
          {storageFreeGb.toFixed(1)} GB {t("stats.free")}
        </p>
      </div>
    </div>

    <!-- Hardware & Network details — wider gap from metric cards above -->
    <div class="mt-6 grid gap-4 sm:grid-cols-2">
      <!-- Throttle + System (combined) -->
      <div class="card px-4 py-4">
        <!-- Throttle -->
        {#if info.throttle}
          {@const active = throttleActive(info.throttle)}
          {@const history = throttleHistory(info.throttle)}
          <div class="flex items-center gap-1.5">
            <Icon icon={boltIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.throttle")}</p>
          </div>

          {#if active}
            <div class="mt-2 flex flex-wrap gap-1.5">
              {#if info.throttle.under_voltage_now}
                <span class="rounded-lg bg-status-critical/10 px-2 py-0.5 text-xs font-medium text-status-critical">{t("throttle.lowVoltage")}</span>
              {/if}
              {#if info.throttle.throttled_now}
                <span class="rounded-lg bg-status-critical/10 px-2 py-0.5 text-xs font-medium text-status-critical">{t("throttle.throttled")}</span>
              {/if}
              {#if info.throttle.freq_capped_now}
                <span class="rounded-lg bg-status-warning/10 px-2 py-0.5 text-xs font-medium text-status-warning">{t("throttle.freqCapped")}</span>
              {/if}
              {#if info.throttle.soft_temp_limit_now}
                <span class="rounded-lg bg-status-warning/10 px-2 py-0.5 text-xs font-medium text-status-warning">{t("throttle.tempLimit")}</span>
              {/if}
            </div>
          {:else if history}
            <p class="mt-1.5 text-xs text-status-warning">{t("throttle.pastEvent")}</p>
          {:else}
            <p class="mt-1.5 text-xs text-status-ok">{t("status.ok")}</p>
          {/if}

          {#if history && !active}
            <div class="mt-2 flex flex-wrap gap-1.5">
              {#if info.throttle.under_voltage_occurred}
                <span class="rounded-lg bg-surface-overlay px-2 py-0.5 text-[0.6875rem] text-text-muted">{t("throttle.lowVoltage")} ({t("status.past").toLowerCase()})</span>
              {/if}
              {#if info.throttle.throttled_occurred}
                <span class="rounded-lg bg-surface-overlay px-2 py-0.5 text-[0.6875rem] text-text-muted">{t("throttle.throttled")} ({t("status.past").toLowerCase()})</span>
              {/if}
              {#if info.throttle.freq_capped_occurred}
                <span class="rounded-lg bg-surface-overlay px-2 py-0.5 text-[0.6875rem] text-text-muted">{t("throttle.freqCapped")} ({t("status.past").toLowerCase()})</span>
              {/if}
              {#if info.throttle.soft_temp_limit_occurred}
                <span class="rounded-lg bg-surface-overlay px-2 py-0.5 text-[0.6875rem] text-text-muted">{t("throttle.tempLimit")} ({t("status.past").toLowerCase()})</span>
              {/if}
            </div>
          {/if}

          {#if info.throttle.raw}
            <p class="mt-2 text-[0.625rem] font-mono tabular-nums text-text-muted">
              {t("stats.rawFlags")}: {info.throttle.raw}
            </p>
          {/if}
        {/if}

        <!-- System — separated by border from throttle -->
        {#if extended}
          <div class="mt-3 border-t border-border-subtle pt-3">
            <div class="grid grid-cols-2 gap-x-6 gap-y-2">
              {#if extended.process_count != null}
                <div>
                  <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.processes")}</p>
                  <p class="text-sm font-semibold tabular-nums text-text-primary">{extended.process_count}</p>
                </div>
              {/if}
              {#if extended.cpu_count != null}
                <div>
                  <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.cpuCores")}</p>
                  <p class="text-sm font-semibold tabular-nums text-text-primary">{extended.cpu_count}</p>
                </div>
              {/if}
              {#if extended.load_avg}
                <div>
                  <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.loadAvg")} 1/5/15m</p>
                  <p class="text-sm font-semibold tabular-nums text-text-primary">{extended.load_avg["1min"]} / {extended.load_avg["5min"]} / {extended.load_avg["15min"]}</p>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <!-- Network I/O -->
      {#if extended?.network}
        <div class="card px-4 py-4">
          <div class="flex items-center gap-1.5">
            <Icon icon={wifiIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("stats.network")}</p>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-x-6 gap-y-2">
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.sent")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{formatBytes(extended.network.bytes_sent)}</p>
            </div>
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.received")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{formatBytes(extended.network.bytes_recv)}</p>
            </div>
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.packetsSent")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{extended.network.packets_sent.toLocaleString()}</p>
            </div>
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.packetsRecv")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{extended.network.packets_recv.toLocaleString()}</p>
            </div>
          </div>
          <p class="mt-2 text-[0.625rem] uppercase tracking-wider text-text-muted">{t("label.sinceBoot")}</p>
        </div>
      {/if}
    </div>

    <!-- SD Card details -->
    {#if info.sd_health}
      <div class="mt-4 card px-4 py-4">
        <div class="flex items-center gap-1.5">
          <Icon icon={databaseIcon} class="h-3 w-3 text-text-muted" stroke={2} />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.sdCard")}</p>
        </div>

        <div class="mt-3 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
          {#if info.sd_health.name}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.cardName")}</p>
              <p class="text-sm font-medium text-text-primary">{info.sd_health.name}</p>
            </div>
          {/if}
          {#if info.sd_health.manufacturing_date}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.mfgDate")}</p>
              <p class="text-sm font-medium text-text-primary">{info.sd_health.manufacturing_date}</p>
            </div>
          {/if}
          {#if info.sd_health.serial}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.serial")}</p>
              <p class="text-sm font-medium font-mono text-text-primary truncate" title={info.sd_health.serial}>{info.sd_health.serial}</p>
            </div>
          {/if}
          {#if info.sd_health.oemid}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.oemId")}</p>
              <p class="text-sm font-medium font-mono text-text-primary">{info.sd_health.oemid}</p>
            </div>
          {/if}
          {#if info.sd_health.hw_revision}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.hwRevision")}</p>
              <p class="text-sm font-medium font-mono text-text-primary">{info.sd_health.hw_revision}</p>
            </div>
          {/if}
          {#if info.sd_health.fw_revision}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.fwRevision")}</p>
              <p class="text-sm font-medium font-mono text-text-primary">{info.sd_health.fw_revision}</p>
            </div>
          {/if}
          {#if info.sd_health.written_since_boot_gb != null}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("label.writtenSinceBoot")}</p>
              <p class="text-sm font-medium tabular-nums text-text-primary">{info.sd_health.written_since_boot_gb.toFixed(2)} GB</p>
            </div>
          {/if}
          {#if info.sd_health.life_time_est}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("label.lifeEst")}</p>
              <p class="text-sm font-medium text-text-primary">{info.sd_health.life_time_est}</p>
            </div>
          {/if}
          {#if info.sd_health.preferred_erase_size_mb}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.eraseBlock")}</p>
              <p class="text-sm font-medium tabular-nums text-text-primary">{info.sd_health.preferred_erase_size_mb} MB</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Camera, Recording & Connectivity -->
    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <!-- Camera / Stream -->
      {#if stream}
        <div class="card px-4 py-4">
          <div class="flex items-center gap-1.5">
            <Icon icon={cameraIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("stats.camera")}</p>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-x-6 gap-y-2">
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.resolution")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{stream.width}&times;{stream.height}</p>
            </div>
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("label.fps")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{stream.fps}</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Recordings -->
      <div class="card px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Icon icon={videoIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("stats.recordings")}</p>
          </div>
          {#if recording}
            <span class="flex items-center gap-1">
              <span class="h-1.5 w-1.5 rounded-full bg-status-critical animate-pulse"></span>
              <span class="text-[0.625rem] font-semibold uppercase text-status-critical">{t("badge.rec")}</span>
            </span>
          {/if}
        </div>
        <div class="mt-3 grid grid-cols-2 gap-x-6 gap-y-2">
          <div>
            <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.totalRecordings")}</p>
            <p class="text-sm font-semibold tabular-nums text-text-primary">{archiveCount ?? "-"}</p>
          </div>
          {#if timelapse}
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("stats.framesToday")}</p>
              <p class="text-sm font-semibold tabular-nums text-text-primary">{timelapse.today_frame_count}</p>
            </div>
          {/if}
        </div>
        {#if timelapse?.enabled}
          <p class="mt-2 text-[0.625rem] uppercase tracking-wider text-text-muted">
            {t("stats.timelapseActive")}
          </p>
        {/if}
      </div>

      <!-- Connectivity -->
      {#if connections}
        <div class="card px-4 py-4">
          <div class="flex items-center gap-1.5">
            <Icon icon={bluetoothIcon} class="h-3 w-3 text-text-muted" stroke={2} />
            <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("stats.connectivity")}</p>
          </div>
          <div class="mt-2 grid grid-cols-2 gap-x-6 gap-y-2">
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("label.bluetooth")}</p>
              <p class="text-xl font-bold tabular-nums leading-none {connections.bluetooth.online > 0 ? 'text-status-ok' : 'text-text-muted'}">
                {connections.bluetooth.online}<span class="text-[0.625rem] font-medium text-text-muted">/{connections.bluetooth.total}</span>
              </p>
            </div>
            <div>
              <p class="text-[0.625rem] uppercase tracking-wider text-text-muted">{t("label.wifi")}</p>
              <p class="text-xl font-bold tabular-nums leading-none {connections.wifi.online > 0 ? 'text-status-ok' : 'text-text-muted'}">
                {connections.wifi.online}<span class="text-[0.625rem] font-medium text-text-muted">/{connections.wifi.total}</span>
              </p>
            </div>
          </div>
          {#if sensor}
            <div class="mt-3 border-t border-border-subtle pt-3">
              <div class="flex items-center gap-1.5">
                <Icon icon={shieldIcon} class="h-3 w-3 text-text-muted" stroke={2} />
                <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.sensor")}</p>
                {#if sensor.armed}
                  <span class="rounded-lg bg-status-ok/10 px-2 py-0.5 text-[0.625rem] font-medium text-status-ok">{t("status.armed")}</span>
                {:else if sensor.enabled}
                  <span class="rounded-lg bg-surface-overlay px-2 py-0.5 text-[0.625rem] font-medium text-text-muted">{t("status.idle")}</span>
                {:else}
                  <span class="rounded-lg bg-surface-overlay px-2 py-0.5 text-[0.625rem] font-medium text-text-muted">{t("status.off")}</span>
                {/if}
              </div>
              {#if sensor.config?.type}
                <p class="mt-1 text-[0.625rem] text-text-muted">{sensor.config.type}{#if sensor.config.gpio != null} · GPIO {sensor.config.gpio}{/if}</p>
              {/if}
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Platform info -->
    {#if extended?.os_info || extended?.python_version}
      <div class="mt-4 card px-4 py-3">
        <div class="flex flex-wrap items-center gap-x-6 gap-y-1 min-w-0 text-[0.625rem] tabular-nums text-text-muted">
          {#if extended.os_info}
            <span class="truncate">{extended.os_info}</span>
          {/if}
          {#if extended.python_version}
            <span>Python {extended.python_version}</span>
          {/if}
          {#if extended.arch}
            <span>{extended.arch}</span>
          {/if}
        </div>
      </div>
    {/if}
  </div>
{:else}
  <!-- Skeleton -->
  <div class="mt-6">
    <!-- Uptime bar skeleton -->
    <div class="card flex items-center gap-4 px-4 py-3">
      <div class="skeleton h-3.5 w-3.5 rounded"></div>
      <div class="skeleton h-4 w-20"></div>
      <div class="skeleton h-4 w-28"></div>
    </div>
    <!-- Metric cards skeleton -->
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      {#each Array(2) as _}
        <div class="card px-4 py-4">
          <div class="skeleton h-2.5 w-12"></div>
          <div class="skeleton mt-3 h-9 w-16"></div>
          <div class="skeleton mt-3 h-1 w-full"></div>
          <div class="skeleton mt-3 h-8 w-full"></div>
        </div>
      {/each}
    </div>
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      {#each Array(2) as _}
        <div class="card px-4 py-4">
          <div class="skeleton h-2.5 w-12"></div>
          <div class="skeleton mt-3 h-9 w-16"></div>
          <div class="skeleton mt-3 h-1 w-full"></div>
        </div>
      {/each}
    </div>
    <!-- Info cards skeleton -->
    <div class="mt-6 grid gap-4 sm:grid-cols-2">
      {#each Array(2) as _}
        <div class="card px-4 py-4">
          <div class="skeleton h-2.5 w-16"></div>
          <div class="mt-3 grid grid-cols-2 gap-3">
            <div class="skeleton h-8 w-full"></div>
            <div class="skeleton h-8 w-full"></div>
          </div>
        </div>
      {/each}
    </div>
    <!-- Status cards skeleton -->
    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each Array(3) as _}
        <div class="card px-4 py-4">
          <div class="skeleton h-2.5 w-14"></div>
          <div class="mt-3 grid grid-cols-2 gap-3">
            <div class="skeleton h-6 w-full"></div>
            <div class="skeleton h-6 w-full"></div>
          </div>
        </div>
      {/each}
    </div>
    <!-- Platform skeleton -->
    <div class="mt-4 card px-4 py-3">
      <div class="skeleton h-3 w-64"></div>
    </div>
  </div>
{/if}
