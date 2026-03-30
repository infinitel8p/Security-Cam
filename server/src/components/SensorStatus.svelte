<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface SensorInfo {
    type: string;
    name: string;
    gpio: number;
    running: boolean;
  }

  interface SensorStatusData {
    enabled: boolean;
    armed: boolean;
    triggered: boolean;
    hold_seconds: number;
    config: {
      type: string;
      gpio: number;
      enabled: boolean;
      hold_seconds: number;
    };
    sensor: SensorInfo | null;
  }

  let data = $state<SensorStatusData | null>(null);
  let error = $state(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  async function fetchStatus() {
    try {
      const res = await fetch(`${getBackendUrl()}/sensor/status`);
      data = await res.json();
      error = false;
    } catch {
      error = true;
    }
  }

  onMount(() => {
    fetchStatus();
    interval = setInterval(fetchStatus, 5_000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });

  let statusLabel = $derived(
    !data?.enabled
      ? "Disabled"
      : data?.triggered
        ? "Triggered"
        : data?.armed
          ? "Armed"
          : "Idle"
  );

  let statusColor = $derived(
    !data?.enabled
      ? "text-text-muted"
      : data?.triggered
        ? "text-status-critical"
        : data?.armed
          ? "text-status-ok"
          : "text-text-muted"
  );

  let dotColor = $derived(
    !data?.enabled
      ? "bg-text-muted/40"
      : data?.triggered
        ? "bg-status-critical shadow-[0_0_6px_rgba(240,104,104,0.5)]"
        : data?.armed
          ? "bg-status-ok shadow-[0_0_6px_rgba(52,217,172,0.5)]"
          : "bg-text-muted/40"
  );
</script>

{#if error}
  <div class="card flex items-center justify-center px-4 py-6 text-center text-[0.8125rem] text-text-muted">
    Unable to load sensor status
  </div>
{:else if data}
  <div class="card">
    <div class="grid grid-cols-3 divide-x divide-border-subtle">
      <!-- Sensor Type -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Sensor</p>
        </div>
        <p class="mt-1 truncate text-[0.8125rem] font-bold leading-none {data.enabled ? 'text-text-primary' : 'text-text-muted'}">
          {#if data.sensor}
            {({
              reed_switch: "Reed", mini_reed: "Mini Reed", hall_digital: "Hall",
              pir: "PIR", vibration: "Shock", knock: "Knock",
              light_gate: "Gate", tilt: "Tilt", touch: "Touch",
              button: "Button", mock: "Mock",
            })[data.config.type] ?? data.config.type}
          {:else}
            Off
          {/if}
        </p>
      </div>

      <!-- Status -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <span class="h-1.5 w-1.5 rounded-full {dotColor}" class:status-live={data.armed && !data.triggered}></span>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">Status</p>
        </div>
        <p class="mt-1 text-[0.8125rem] font-bold leading-none {statusColor}">
          {statusLabel}
        </p>
      </div>

      <!-- GPIO -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
            <rect x="9" y="9" width="6" height="6" />
            <line x1="9" y1="1" x2="9" y2="4" />
            <line x1="15" y1="1" x2="15" y2="4" />
            <line x1="9" y1="20" x2="9" y2="23" />
            <line x1="15" y1="20" x2="15" y2="23" />
            <line x1="20" y1="9" x2="23" y2="9" />
            <line x1="20" y1="14" x2="23" y2="14" />
            <line x1="1" y1="9" x2="4" y2="9" />
            <line x1="1" y1="14" x2="4" y2="14" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">GPIO</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.enabled ? 'text-accent' : 'text-text-muted'}">
          {data.enabled && data.config.gpio != null ? data.config.gpio : "--"}
        </p>
      </div>
    </div>
  </div>
{:else}
  <!-- Skeleton -->
  <div class="card animate-pulse">
    <div class="grid grid-cols-3 divide-x divide-border-subtle">
      {#each Array(3) as _}
        <div class="px-4 py-3 text-center">
          <div class="mx-auto h-2.5 w-8 rounded bg-surface-elevated"></div>
          <div class="mx-auto mt-2 h-5 w-10 rounded bg-surface-elevated"></div>
        </div>
      {/each}
    </div>
  </div>
{/if}
