<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import boltIcon from "../icons/bolt.svg?raw";
  import cpuIcon from "../icons/cpu.svg?raw";

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
    suppressed: boolean;
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
      if (!res.ok) throw new Error();
      data = await res.json();
      error = false;
    } catch {
      error = true;
    }
  }

  onMount(() => {
    initLocale();
    fetchStatus();
    interval = setInterval(fetchStatus, 5_000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });

  let statusLabel = $derived(
    !data?.enabled
      ? t("status.disabled")
      : data?.suppressed
        ? t("status.suppressed")
        : data?.triggered
          ? t("status.triggered")
          : data?.armed
            ? t("status.armed")
            : t("status.idle")
  );

  let statusColor = $derived(
    !data?.enabled
      ? "text-text-muted"
      : data?.suppressed
        ? "text-status-warning"
        : data?.triggered
          ? "text-status-critical"
          : data?.armed
            ? "text-status-ok"
            : "text-text-muted"
  );

  let dotColor = $derived(
    !data?.enabled
      ? "bg-text-muted/40"
      : data?.suppressed
        ? "bg-status-warning shadow-[0_0_6px_rgba(234,179,8,0.4)]"
        : data?.triggered
          ? "bg-status-critical shadow-[0_0_6px_rgba(240,104,104,0.5)]"
          : data?.armed
            ? "bg-status-ok shadow-[0_0_6px_rgba(52,217,172,0.5)]"
            : "bg-text-muted/40"
  );
</script>

{#if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-4 py-6 text-center">
    <p class="text-[0.8125rem] text-text-muted">{t("error.sensorStatus")}</p>
    <button onclick={fetchStatus} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
  </div>
{:else if data}
  <div class="card">
    <div class="grid grid-cols-3 divide-x divide-border-subtle">
      <!-- Sensor Type -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <Icon icon={boltIcon} class="h-3 w-3 text-text-muted" stroke={2.5} />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.sensor")}</p>
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
            {t("status.off")}
          {/if}
        </p>
      </div>

      <!-- Status -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <span class="h-1.5 w-1.5 rounded-full {dotColor}" class:status-live={data.armed && !data.triggered}></span>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.status")}</p>
        </div>
        <p class="mt-1 text-[0.8125rem] font-bold leading-none {statusColor}">
          {statusLabel}
        </p>
      </div>

      <!-- GPIO -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <Icon icon={cpuIcon} class="h-3 w-3 text-text-muted" stroke={2.5} />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.gpio")}</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.enabled ? 'text-accent' : 'text-text-muted'}">
          {data.enabled && data.config.gpio != null ? data.config.gpio : "--"}
        </p>
      </div>
    </div>
  </div>
{:else}
  <!-- Skeleton -->
  <div class="card">
    <div class="grid grid-cols-3 divide-x divide-border-subtle">
      {#each Array(3) as _}
        <div class="px-4 py-3 text-center">
          <div class="skeleton mx-auto h-2.5 w-8"></div>
          <div class="skeleton mx-auto mt-2 h-5 w-10"></div>
        </div>
      {/each}
    </div>
  </div>
{/if}
