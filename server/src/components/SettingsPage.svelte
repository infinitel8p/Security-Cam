<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import DeviceList from "./DeviceList.svelte";
  import CameraRotation from "./CameraRotation.svelte";
  import DirectoryPicker from "./DirectoryPicker.svelte";

  interface Device {
    name: string;
    address: string;
  }

  let btDevices: Device[] = $state([]);
  let wifiDevices: Device[] = $state([]);
  let rotation = $state(0);
  let saveLocation = $state("");
  let loading = $state(true);
  let error = $state(false);

  onMount(async () => {
    try {
      const res = await fetch(`${getBackendUrl()}/settings`);
      const settings = await res.json();
      btDevices = settings.TARGET_BT_ADDRESSES ?? [];
      wifiDevices = settings.TARGET_AP_MAC_ADDRESSES ?? [];
      rotation = settings.RotationAngle ?? 0;
      saveLocation = settings.VideoSaveLocation ?? "/home/pi/Videos";
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div class="space-y-4">
    {#each Array(4) as _}
      <div class="card animate-pulse px-5 py-6">
        <div class="h-4 w-32 rounded bg-surface-elevated"></div>
        <div class="mt-4 h-8 w-48 rounded bg-surface-elevated"></div>
      </div>
    {/each}
  </div>
{:else if error}
  <div class="card px-6 py-12 text-center text-sm text-text-muted">
    Unable to load settings
  </div>
{:else}
  <div class="space-y-4">
    <DeviceList title="Bluetooth Devices" icon="bluetooth" devices={btDevices} />
    <DeviceList title="WiFi Devices" icon="wifi" devices={wifiDevices} />
    <CameraRotation current={rotation} />
    <DirectoryPicker current={saveLocation} />

    <!-- Modular Trigger Sensors (placeholder) -->
    <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
      <div class="flex items-center gap-2.5">
        <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
          <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
        </div>
        <h3 class="text-sm font-semibold text-text-primary">Modular Trigger Sensors</h3>
      </div>
      <p class="mt-3 text-sm text-text-muted">Coming soon</p>
    </div>
  </div>
{/if}
