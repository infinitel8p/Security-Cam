<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import Icon from "./Icon.svelte";
  import shieldIcon from "../icons/shield.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";

  interface SetupState {
    hasDevices: boolean;
    hasSensor: boolean;
  }

  let setup = $state<SetupState | null>(null);
  let dismissed = $state(false);
  let loading = $state(true);

  let completedCount = $derived(
    setup ? [setup.hasDevices, setup.hasSensor].filter(Boolean).length : 0
  );
  let totalSteps = 2;

  onMount(async () => {
    if (localStorage.getItem("setup-checklist-dismissed") === "true") {
      dismissed = true;
      loading = false;
      return;
    }

    try {
      const res = await fetch(`${getBackendUrl()}/settings`);
      if (!res.ok) throw new Error();
      const settings = await res.json();

      const btDevices = settings.TARGET_BT_ADDRESSES ?? [];
      const wifiDevices = settings.TARGET_AP_MAC_ADDRESSES ?? [];
      const sensorCfg = settings.Sensor ?? {};

      setup = {
        hasDevices: btDevices.length > 0 || wifiDevices.length > 0,
        hasSensor: sensorCfg.enabled === true,
      };

      if (setup.hasDevices && setup.hasSensor) {
        dismissed = true;
        localStorage.setItem("setup-checklist-dismissed", "true");
      }
    } catch {
      dismissed = true;
    } finally {
      loading = false;
    }
  });

  function dismiss() {
    dismissed = true;
    localStorage.setItem("setup-checklist-dismissed", "true");
  }
</script>

{#if !loading && !dismissed && setup}
  <div class="animate-in card overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-border-subtle px-4 py-3 sm:px-5">
      <div class="flex items-center gap-2.5">
        <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
          <Icon icon={shieldIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
        </div>
        <div>
          <h3 class="text-sm font-semibold text-text-primary">Get your camera ready</h3>
          <p class="text-[0.6875rem] text-text-muted">{completedCount} of {totalSteps} steps done</p>
        </div>
      </div>
      <button
        onclick={dismiss}
        class="rounded-md p-1 text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
        title="Dismiss"
      >
        <Icon icon={xIcon} class="h-4 w-4" />
      </button>
    </div>

    <!-- Progress bar -->
    <div class="h-0.5 bg-surface-elevated">
      <div
        class="h-full bg-accent animate-bar transition-[width] duration-500"
        style="width: {(completedCount / totalSteps) * 100}%"
      ></div>
    </div>

    <!-- Steps -->
    <div class="divide-y divide-border-subtle">
      <!-- Step 1: Add devices -->
      <a
        href="/settings"
        class="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-overlay/40 sm:px-5"
      >
        <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full {setup.hasDevices ? 'bg-status-ok/15' : 'border border-border-default'}">
          {#if setup.hasDevices}
            <svg class="h-3 w-3 text-status-ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline class="animate-check" points="20 6 9 17 4 12" />
            </svg>
          {:else}
            <span class="text-[0.625rem] font-bold text-text-muted">1</span>
          {/if}
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-[0.8125rem] font-medium {setup.hasDevices ? 'text-text-muted line-through' : 'text-text-primary'}">
            Add your phone or laptop
          </p>
          <p class="text-[0.6875rem] text-text-muted">
            {setup.hasDevices ? "Devices configured" : "Bluetooth or WiFi device for presence detection"}
          </p>
        </div>
        {#if !setup.hasDevices}
          <Icon icon={chevronRightIcon} class="h-4 w-4 shrink-0 text-text-muted" />
        {/if}
      </a>

      <!-- Step 2: Enable sensor -->
      <a
        href="/settings"
        class="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-overlay/40 sm:px-5"
      >
        <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full {setup.hasSensor ? 'bg-status-ok/15' : 'border border-border-default'}">
          {#if setup.hasSensor}
            <svg class="h-3 w-3 text-status-ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline class="animate-check" points="20 6 9 17 4 12" />
            </svg>
          {:else}
            <span class="text-[0.625rem] font-bold text-text-muted">2</span>
          {/if}
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-[0.8125rem] font-medium {setup.hasSensor ? 'text-text-muted line-through' : 'text-text-primary'}">
            Enable a trigger sensor
          </p>
          <p class="text-[0.6875rem] text-text-muted">
            {setup.hasSensor ? "Sensor armed" : "Auto-record when motion or door activity is detected"}
          </p>
        </div>
        {#if !setup.hasSensor}
          <Icon icon={chevronRightIcon} class="h-4 w-4 shrink-0 text-text-muted" />
        {/if}
      </a>
    </div>
  </div>
{/if}
