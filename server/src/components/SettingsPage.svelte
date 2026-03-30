<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";
  import DeviceList from "./DeviceList.svelte";
  import CameraSettings from "./CameraSettings.svelte";
  import DirectoryPicker from "./DirectoryPicker.svelte";
  import SensorSettings from "./SensorSettings.svelte";

  interface Device {
    name: string;
    address: string;
  }

  let btDevices = $state<Device[]>([]);
  let wifiDevices = $state<Device[]>([]);
  let rotation = $state(0);
  let rotationMode = $state("display");
  let streamWidth = $state(1296);
  let streamHeight = $state(972);
  let streamFPS = $state(30);
  let saveLocation = $state("");
  let scanLinesEnabled = $state(true);
  let loading = $state(true);
  let error = $state(false);

  // Device online/offline status: { bt: { "AA:BB:...": true }, wifi: { "AA:BB:...": false } }
  let deviceStatuses = $state<{ bt: Record<string, boolean>; wifi: Record<string, boolean> }>({ bt: {}, wifi: {} });
  let statusInterval: ReturnType<typeof setInterval> | null = null;

  async function fetchDeviceStatuses() {
    try {
      const res = await fetch(`${getBackendUrl()}/devices/status`);
      if (res.ok) deviceStatuses = await res.json();
    } catch {
      // Silent fail - status is supplementary
    }
  }

  onDestroy(() => {
    if (statusInterval) clearInterval(statusInterval);
  });

  type ThemeMode = "system" | "light" | "dark";
  let theme: ThemeMode = $state("system");

  function setTheme(m: ThemeMode) {
    theme = m;
    if (m === "system") {
      localStorage.removeItem("theme");
    } else {
      localStorage.setItem("theme", m);
    }
    const isLight =
      m === "light" ||
      (m === "system" && window.matchMedia("(prefers-color-scheme: light)").matches);
    document.documentElement.classList.toggle("light", isLight);
  }

  async function fetchSettings() {
    loading = true;
    error = false;
    try {
      const res = await fetch(`${getBackendUrl()}/settings`);
      if (!res.ok) throw new Error();
      const settings = await res.json();
      btDevices = settings.TARGET_BT_ADDRESSES ?? [];
      wifiDevices = settings.TARGET_AP_MAC_ADDRESSES ?? [];
      rotation = Number(settings.RotationAngle) || 0;
      rotationMode = settings.RotationMode ?? "display";
      streamWidth = settings.StreamWidth ?? 1296;
      streamHeight = settings.StreamHeight ?? 972;
      streamFPS = settings.StreamFPS ?? 30;
      saveLocation = settings.VideoSaveLocation ?? "/home/pi/Videos";
      scanLinesEnabled = settings.ScanLines !== false;
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    const saved = localStorage.getItem("theme") as ThemeMode | null;
    theme = saved === "light" || saved === "dark" ? saved : "system";
    await fetchSettings();

    // Poll device statuses every 15 seconds (BT lookup takes ~3s per device)
    fetchDeviceStatuses();
    statusInterval = setInterval(fetchDeviceStatuses, 15_000);
  });

  async function addBtDevice(device: Device) {
    const res = await fetch(`${getBackendUrl()}/devices/bt/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(device),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || "Failed to add device");
    }
    if (!btDevices.some(d => d.address.toLowerCase() === device.address.toLowerCase())) {
      btDevices = [...btDevices, device];
    }
  }

  async function removeBtDevice(address: string) {
    await fetch(`${getBackendUrl()}/devices/bt/remove`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
    });
    btDevices = btDevices.filter(d => d.address.toLowerCase() !== address.toLowerCase());
  }

  async function addWifiDevice(device: Device) {
    const res = await fetch(`${getBackendUrl()}/devices/wifi/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(device),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || "Failed to add device");
    }
    if (!wifiDevices.some(d => d.address.toLowerCase() === device.address.toLowerCase())) {
      wifiDevices = [...wifiDevices, device];
    }
  }

  async function toggleScanLines() {
    scanLinesEnabled = !scanLinesEnabled;
    try {
      const res = await fetch(`${getBackendUrl()}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ScanLines: scanLinesEnabled }),
      });
      if (!res.ok) throw new Error();
    } catch {
      scanLinesEnabled = !scanLinesEnabled;
      toast.error("Failed to save setting");
    }
  }

  async function removeWifiDevice(address: string) {
    await fetch(`${getBackendUrl()}/devices/wifi/remove`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
    });
    wifiDevices = wifiDevices.filter(d => d.address.toLowerCase() !== address.toLowerCase());
  }
</script>

{#if loading}
  <div class="space-y-4">
    {#each Array(4) as _, i}
      <div class="card px-5 py-6 animate-in" style="animation-delay: {i * 60}ms">
        <div class="skeleton h-4 w-32"></div>
        <div class="skeleton mt-4 h-8 w-48"></div>
      </div>
    {/each}
  </div>
{:else if error}
  <div class="card flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
    <p class="text-sm text-text-muted">Unable to load settings</p>
    <button onclick={fetchSettings} class="text-[0.8125rem] font-medium text-accent hover:text-accent-hover">Retry</button>
  </div>
{:else}
  <div class="space-y-8">
    <!-- Device tracking -->
    <div class="space-y-3">
      <h2 class="section-label">Devices</h2>
      <div class="space-y-3">
        <DeviceList
          title="Bluetooth Devices"
          icon="bluetooth"
          devices={btDevices}
          onAdd={addBtDevice}
          onRemove={removeBtDevice}
          scanEndpoint="/bt/scan"
          scanResultKey="devices"
          statuses={deviceStatuses.bt}
        />
        <DeviceList
          title="WiFi Devices"
          icon="wifi"
          devices={wifiDevices}
          onAdd={addWifiDevice}
          onRemove={removeWifiDevice}
          scanEndpoint="/wifi/stations"
          scanResultKey="stations"
          statuses={deviceStatuses.wifi}
        />
      </div>
    </div>

    <!-- Camera & storage -->
    <div class="space-y-3">
      <h2 class="section-label">Camera</h2>
      <div class="space-y-3">
        <CameraSettings
          currentAngle={rotation}
          currentMode={rotationMode}
          {streamWidth}
          {streamHeight}
          {streamFPS}
        />
        <DirectoryPicker current={saveLocation} />
      </div>
    </div>

    <!-- Appearance -->
    <div class="space-y-3">
      <h2 class="section-label">Appearance</h2>
      <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
        <div class="grid grid-cols-3 gap-2">
          <button
            onclick={() => setTheme("system")}
            class="btn-press flex flex-col items-center gap-2 rounded-xl border px-3 py-3.5 transition-all duration-200
              {theme === 'system' ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            <span class="text-[0.6875rem] font-medium">System</span>
          </button>
          <button
            onclick={() => setTheme("light")}
            class="btn-press flex flex-col items-center gap-2 rounded-xl border px-3 py-3.5 transition-all duration-200
              {theme === 'light' ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
            <span class="text-[0.6875rem] font-medium">Light</span>
          </button>
          <button
            onclick={() => setTheme("dark")}
            class="btn-press flex flex-col items-center gap-2 rounded-xl border px-3 py-3.5 transition-all duration-200
              {theme === 'dark' ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
            <span class="text-[0.6875rem] font-medium">Dark</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Feed -->
    <div class="space-y-3">
      <h2 class="section-label">Feed</h2>
      <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-text-primary">Scan lines</p>
            <p class="mt-0.5 text-xs text-text-muted">Subtle CRT-style overlay on the live camera feed</p>
          </div>
          <button
            onclick={toggleScanLines}
            class="btn-press relative h-6 w-11 shrink-0 rounded-full transition-colors duration-300
              {scanLinesEnabled ? 'bg-accent shadow-[0_0_8px_rgba(77,148,255,0.25)]' : 'bg-surface-elevated'}"
          >
            <span
              class="absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-md transition-transform duration-300
                {scanLinesEnabled ? 'translate-x-5' : 'translate-x-0'}"
              style="transition-timing-function: cubic-bezier(0.25, 1, 0.5, 1);"
            ></span>
          </button>
        </div>
      </div>
    </div>

    <!-- Trigger Sensors -->
    <div class="space-y-3">
      <h2 class="section-label">Trigger Sensors</h2>
      <SensorSettings />
    </div>
  </div>
{/if}
