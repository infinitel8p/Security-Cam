<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { sseClient } from "../lib/sse";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import bluetoothIcon from "../icons/bluetooth.svg?raw";
  import wifiIcon from "../icons/wifi.svg?raw";
  import usersIcon from "../icons/users.svg?raw";

  interface Connections {
    bluetooth: { online: number; total: number };
    wifi: { online: number; total: number };
    ap_clients: number;
  }

  let data = $state<Connections | null>(null);
  let error = $state(false);
  let retrying = $state(false);
  let unsub: (() => void) | null = null;

  async function fetchConnections() {
    retrying = true;
    try {
      const res = await fetch(`${getBackendUrl()}/connections`);
      if (!res.ok) throw new Error();
      data = await res.json();
      error = false;
    } catch {
      error = true;
    } finally {
      retrying = false;
    }
  }

  onMount(() => {
    initLocale();
    fetchConnections();

    const sse = sseClient();
    sse.registerFallback({
      event: "connections",
      endpoint: "/connections",
      interval: 15_000,
    });
    unsub = sse.on("connections", (ev) => {
      data = ev;
      error = false;
    });
  });

  onDestroy(() => {
    unsub?.();
  });
</script>

{#if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-4 py-6 text-center">
    <p class="text-[0.8125rem] text-text-muted">{t("error.connectionStatus")}</p>
    <button onclick={fetchConnections} disabled={retrying} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover disabled:opacity-50">
      {retrying ? t("status.retrying") : t("btn.retry")}
    </button>
  </div>
{:else if data}
  {@const noDevices = data.bluetooth.total === 0 && data.wifi.total === 0}
  {#if noDevices}
    <a href="/settings" class="card-interactive block px-4 py-3 text-center">
      <p class="text-[0.8125rem] font-medium text-text-secondary">{t("empty.noDevicesTracked")}</p>
      <p class="mt-0.5 text-[0.6875rem] text-text-muted">{t("help.addDevicesForPresence")}</p>
    </a>
  {:else}
  <div class="card">
    <div class="grid grid-cols-3 divide-x divide-border-subtle">
      <!-- Bluetooth -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <Icon icon={bluetoothIcon} class="h-3 w-3 text-text-muted" stroke={2.5} />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.bluetooth")}</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.bluetooth.online > 0 ? 'text-status-ok' : 'text-text-muted'}">
          {data.bluetooth.online}<span class="text-[0.625rem] font-medium text-text-muted">/{data.bluetooth.total}</span>
        </p>
      </div>

      <!-- WiFi -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <Icon icon={wifiIcon} class="h-3 w-3 text-text-muted" stroke={2.5} />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.wifi")}</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.wifi.online > 0 ? 'text-status-ok' : 'text-text-muted'}">
          {data.wifi.online}<span class="text-[0.625rem] font-medium text-text-muted">/{data.wifi.total}</span>
        </p>
      </div>

      <!-- AP Clients -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <Icon icon={usersIcon} class="h-3 w-3 text-text-muted" />
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">{t("label.accessPoint")}</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.ap_clients > 0 ? 'text-accent' : 'text-text-muted'}">
          {data.ap_clients}
        </p>
      </div>
    </div>
  </div>
  {/if}
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
