<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface Connections {
    bluetooth: { online: number; total: number };
    wifi: { online: number; total: number };
    ap_clients: number;
  }

  let data = $state<Connections | null>(null);
  let error = $state(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  async function fetchConnections() {
    try {
      const res = await fetch(`${getBackendUrl()}/connections`);
      if (!res.ok) throw new Error();
      data = await res.json();
      error = false;
    } catch {
      error = true;
    }
  }

  onMount(() => {
    fetchConnections();
    interval = setInterval(fetchConnections, 15_000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

{#if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-4 py-6 text-center">
    <p class="text-[0.8125rem] text-text-muted">Unable to reach connection status</p>
    <button onclick={fetchConnections} class="text-[0.75rem] font-medium text-accent hover:text-accent-hover">Retry</button>
  </div>
{:else if data}
  {@const noDevices = data.bluetooth.total === 0 && data.wifi.total === 0}
  {#if noDevices}
    <a href="/settings" class="card-interactive block px-4 py-3 text-center">
      <p class="text-[0.8125rem] font-medium text-text-secondary">No devices tracked</p>
      <p class="mt-0.5 text-[0.6875rem] text-text-muted">Add a phone or laptop in <span class="text-accent">Settings</span> for presence detection</p>
    </a>
  {:else}
  <div class="card">
    <div class="grid grid-cols-3 divide-x divide-border-subtle">
      <!-- Bluetooth -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6.5 6.5 17.5 17.5 12 23 12 1 17.5 6.5 6.5 17.5" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">BT</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.bluetooth.online > 0 ? 'text-status-ok' : 'text-text-muted'}">
          {data.bluetooth.online}<span class="text-[0.625rem] font-medium text-text-muted">/{data.bluetooth.total}</span>
        </p>
      </div>

      <!-- WiFi -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12.55a11 11 0 0 1 14.08 0" />
            <path d="M1.42 9a16 16 0 0 1 21.16 0" />
            <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
            <line x1="12" y1="20" x2="12.01" y2="20" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">WiFi</p>
        </div>
        <p class="mt-1 text-xl font-bold tabular-nums leading-none {data.wifi.online > 0 ? 'text-status-ok' : 'text-text-muted'}">
          {data.wifi.online}<span class="text-[0.625rem] font-medium text-text-muted">/{data.wifi.total}</span>
        </p>
      </div>

      <!-- AP Clients -->
      <div class="px-4 py-3 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <svg class="h-3 w-3 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">AP</p>
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
