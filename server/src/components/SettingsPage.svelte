<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";
  import DeviceList from "./DeviceList.svelte";
  import CameraSettings from "./CameraSettings.svelte";
  import DirectoryPicker from "./DirectoryPicker.svelte";
  import SensorSettings from "./SensorSettings.svelte";
  import Icon from "./Icon.svelte";
  import deviceDesktopIcon from "../icons/device-desktop.svg?raw";
  import sunIcon from "../icons/sun.svg?raw";
  import moonIcon from "../icons/moon.svg?raw";
  import { initLocale, getLocale, setLocale, type Locale } from "../i18n";
  import { t } from "../i18n";

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
  let activeSection = $state("appearance");

  // Device online/offline status: { bt: { "AA:BB:...": true }, wifi: { "AA:BB:...": false } }
  let deviceStatuses = $state<{ bt: Record<string, boolean>; wifi: Record<string, boolean> }>({ bt: {}, wifi: {} });
  let statusInterval: ReturnType<typeof setInterval> | null = null;

  const sectionIds = ["appearance", "camera", "storage", "devices", "sensors"];

  function scrollToSection(id: string) {
    const el = document.getElementById(`settings-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      activeSection = id;
      history.replaceState(null, "", `#${id}`);
    }
  }

  let observer: IntersectionObserver | null = null;

  function setupObserver() {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const id = entry.target.id.replace("settings-", "");
            activeSection = id;
            history.replaceState(null, "", `#${id}`);
          }
        }
      },
      { rootMargin: "-20% 0px -60% 0px" }
    );
    for (const id of sectionIds) {
      const el = document.getElementById(`settings-${id}`);
      if (el) observer.observe(el);
    }
  }

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
    if (observer) observer.disconnect();
  });

  type ThemeMode = "system" | "light" | "dark";
  let theme: ThemeMode = $state("system");
  let locale: Locale = $state("en");

  function changeLocale(l: Locale) {
    locale = l;
    setLocale(l);
    document.documentElement.lang = l;
    // Reload to apply translations everywhere
    location.reload();
  }

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
    initLocale();
    locale = getLocale();
    const saved = localStorage.getItem("theme") as ThemeMode | null;
    theme = saved === "light" || saved === "dark" ? saved : "system";
    await fetchSettings();

    // Poll device statuses every 15 seconds (BT lookup takes ~3s per device)
    fetchDeviceStatuses();
    statusInterval = setInterval(fetchDeviceStatuses, 15_000);

    // Track which section is visible for nav highlighting
    requestAnimationFrame(() => {
      setupObserver();

      // Scroll to section if URL has a hash (e.g. /settings#camera)
      const hash = window.location.hash.replace("#", "");
      if (hash && sectionIds.includes(hash)) {
        scrollToSection(hash);
      }
    });
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
      toast.error(t("toast.saveFailed"));
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

{#snippet navItem(id: string, label: string)}
  <button
    onclick={() => scrollToSection(id)}
    class="w-full text-left rounded-lg px-3 py-2 text-[0.8125rem] font-medium transition-colors
      {activeSection === id
        ? 'bg-accent/10 text-accent'
        : 'text-text-muted hover:bg-surface-elevated hover:text-text-secondary'}"
  >
    {label}
  </button>
{/snippet}

{#if loading}
  <div class="mt-5 space-y-4">
    {#each Array(4) as _, i}
      <div class="card px-5 py-6 animate-in" style="animation-delay: {i * 60}ms">
        <div class="skeleton h-4 w-32"></div>
        <div class="skeleton mt-4 h-8 w-48"></div>
      </div>
    {/each}
  </div>
{:else if error}
  <div class="mt-5 card flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
    <p class="text-sm text-text-muted">{t("error.settings")}</p>
    <button onclick={fetchSettings} class="text-[0.8125rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
  </div>
{:else}
  <div class="mt-5 flex gap-6 lg:gap-8 items-start">
    <!-- Sidebar nav -->
    <nav class="hidden lg:block sticky top-6 w-48 shrink-0">
      <div class="flex flex-col gap-0.5">
        {@render navItem("appearance", t("section.appearance"))}
        {@render navItem("camera", t("section.camera"))}
        {@render navItem("storage", t("section.storage"))}
        {@render navItem("devices", t("section.devices"))}
        {@render navItem("sensors", t("section.triggerSensors"))}
      </div>
    </nav>

    <!-- Content -->
    <div class="min-w-0 flex-1 space-y-8">
      <!-- Appearance -->
      <section id="settings-appearance" class="scroll-mt-6 space-y-3">
        <h2 class="section-label">{t("section.appearance")}</h2>
        <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
          <div class="grid grid-cols-3 gap-2">
            <button
              onclick={() => setTheme("system")}
              class="btn-press flex flex-col items-center gap-2 rounded-xl border px-3 py-3.5 transition-all duration-200
                {theme === 'system' ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
            >
              <Icon icon={deviceDesktopIcon} class="h-5 w-5" />
              <span class="text-[0.6875rem] font-medium">{t("theme.system")}</span>
            </button>
            <button
              onclick={() => setTheme("light")}
              class="btn-press flex flex-col items-center gap-2 rounded-xl border px-3 py-3.5 transition-all duration-200
                {theme === 'light' ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
            >
              <Icon icon={sunIcon} class="h-5 w-5" />
              <span class="text-[0.6875rem] font-medium">{t("theme.light")}</span>
            </button>
            <button
              onclick={() => setTheme("dark")}
              class="btn-press flex flex-col items-center gap-2 rounded-xl border px-3 py-3.5 transition-all duration-200
                {theme === 'dark' ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
            >
              <Icon icon={moonIcon} class="h-5 w-5" />
              <span class="text-[0.6875rem] font-medium">{t("theme.dark")}</span>
            </button>
          </div>
        </div>
        <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-text-primary">{t("language.label")}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              {#each ["en", "de", "fr", "es", "it"] as lang}
                <button
                  onclick={() => changeLocale(lang as import("../i18n").Locale)}
                  class="rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors
                    {locale === lang
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
                >
                  {t(`language.${lang}`)}
                </button>
              {/each}
            </div>
          </div>
        </div>
      </section>

      <!-- Camera -->
      <section id="settings-camera" class="scroll-mt-6 space-y-3">
        <h2 class="section-label">{t("section.camera")}</h2>
        <CameraSettings
          currentAngle={rotation}
          currentMode={rotationMode}
          {streamWidth}
          {streamHeight}
          {streamFPS}
        />
        <div class="card px-4 py-3.5 sm:px-5 sm:py-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-text-primary">{t("label.scanLines")}</p>
              <p class="mt-0.5 text-xs text-text-muted">{t("help.scanLines")}</p>
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
      </section>

      <!-- Storage -->
      <section id="settings-storage" class="scroll-mt-6 space-y-3">
        <h2 class="section-label">{t("section.storage")}</h2>
        <DirectoryPicker current={saveLocation} />
      </section>

      <!-- Devices -->
      <section id="settings-devices" class="scroll-mt-6 space-y-3">
        <h2 class="section-label">{t("section.devices")}</h2>
        <div class="space-y-3">
          <DeviceList
            title={t("label.bluetoothDevices")}
            icon="bluetooth"
            devices={btDevices}
            onAdd={addBtDevice}
            onRemove={removeBtDevice}
            scanEndpoint="/bt/scan"
            scanResultKey="devices"
            statuses={deviceStatuses.bt}
          />
          <DeviceList
            title={t("label.wifiDevices")}
            icon="wifi"
            devices={wifiDevices}
            onAdd={addWifiDevice}
            onRemove={removeWifiDevice}
            scanEndpoint="/wifi/stations"
            scanResultKey="stations"
            statuses={deviceStatuses.wifi}
          />
        </div>
      </section>

      <!-- Trigger Sensors -->
      <section id="settings-sensors" class="scroll-mt-6 space-y-3">
        <h2 class="section-label">{t("section.triggerSensors")}</h2>
        <SensorSettings />
      </section>
    </div>
  </div>
{/if}
