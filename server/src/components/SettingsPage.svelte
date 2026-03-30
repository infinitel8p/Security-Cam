<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import DeviceList from "./DeviceList.svelte";
  import CameraSettings from "./CameraSettings.svelte";
  import DirectoryPicker from "./DirectoryPicker.svelte";

  interface Device {
    name: string;
    address: string;
  }

  let btDevices: Device[] = $state([]);
  let wifiDevices: Device[] = $state([]);
  let rotation = $state(0);
  let rotationMode = $state("display");
  let streamWidth = $state(1296);
  let streamHeight = $state(972);
  let streamFPS = $state(30);
  let saveLocation = $state("");
  let loading = $state(true);
  let error = $state(false);

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

  onMount(async () => {
    const saved = localStorage.getItem("theme") as ThemeMode | null;
    theme = saved === "light" || saved === "dark" ? saved : "system";
    try {
      const res = await fetch(`${getBackendUrl()}/settings`);
      const settings = await res.json();
      btDevices = settings.TARGET_BT_ADDRESSES ?? [];
      wifiDevices = settings.TARGET_AP_MAC_ADDRESSES ?? [];
      rotation = Number(settings.RotationAngle) || 0;
      rotationMode = settings.RotationMode ?? "display";
      streamWidth = settings.StreamWidth ?? 1296;
      streamHeight = settings.StreamHeight ?? 972;
      streamFPS = settings.StreamFPS ?? 30;
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
  <div class="space-y-8">
    <!-- Device tracking -->
    <div class="space-y-3">
      <h2 class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">Devices</h2>
      <div class="space-y-3">
        <DeviceList title="Bluetooth Devices" icon="bluetooth" devices={btDevices} />
        <DeviceList title="WiFi Devices" icon="wifi" devices={wifiDevices} />
      </div>
    </div>

    <!-- Camera & storage -->
    <div class="space-y-3">
      <h2 class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">Camera</h2>
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
      <h2 class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">Appearance</h2>
      <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
        <div class="grid grid-cols-3 gap-2">
          <button
            onclick={() => setTheme("system")}
            class="flex flex-col items-center gap-1.5 rounded-xl border px-3 py-3 transition-colors
              {theme === 'system' ? 'border-accent bg-accent/8 text-accent' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
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
            class="flex flex-col items-center gap-1.5 rounded-xl border px-3 py-3 transition-colors
              {theme === 'light' ? 'border-accent bg-accent/8 text-accent' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
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
            class="flex flex-col items-center gap-1.5 rounded-xl border px-3 py-3 transition-colors
              {theme === 'dark' ? 'border-accent bg-accent/8 text-accent' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
            <span class="text-[0.6875rem] font-medium">Dark</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Advanced -->
    <div class="space-y-3">
      <h2 class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">Advanced</h2>
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
  </div>
{/if}
