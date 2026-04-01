<script lang="ts">
  import { onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";
  import { t } from "../i18n";
  import Icon from "./Icon.svelte";
  import bluetoothIcon from "../icons/bluetooth.svg?raw";
  import wifiIcon from "../icons/wifi.svg?raw";
  import searchIcon from "../icons/search.svg?raw";
  import plusIcon from "../icons/plus.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import loader2Icon from "../icons/loader-2.svg?raw";

  interface Device {
    name: string;
    address: string;
  }

  interface Props {
    title: string;
    icon: "bluetooth" | "wifi";
    devices: Device[];
    onAdd: (device: Device) => Promise<void>;
    onRemove: (address: string) => Promise<void>;
    scanEndpoint: string;
    scanResultKey: string;
    scanDuration?: number;
    statuses?: Record<string, boolean>;
  }

  const DISCOVERABLE_TIMEOUT = 90;

  let { title, icon, devices, onAdd, onRemove, scanEndpoint, scanResultKey, scanDuration = 10, statuses = {} }: Props = $props();

  function isOnline(address: string): boolean | undefined {
    const key = address.toUpperCase();
    return key in statuses ? statuses[key] : undefined;
  }

  let scanning = $state(false);
  let scanResults = $state<Device[]>([]);
  let scanError = $state("");
  let showScanPanel = $state(false);
  let addingAddress = $state<string | null>(null);
  let removingAddress = $state<string | null>(null);

  // Manual add
  let showManualAdd = $state(false);
  let manualMac = $state("");
  let manualName = $state("");
  let manualAdding = $state(false);

  // Inline name editing for scan results
  let editingNames = $state<Record<string, string>>({});

  // Discoverable mode (BT only)
  // Restore state if mobile browser reloaded the tab while user was in phone BT settings
  const DISCO_KEY = "bt-discoverable-until";
  const savedUntil = typeof sessionStorage !== "undefined" ? Number(sessionStorage.getItem(DISCO_KEY) || 0) : 0;
  const restoredDiscoverable = savedUntil > Date.now();

  let discoverable = $state(restoredDiscoverable);
  let discoverableError = $state("");

  if (restoredDiscoverable) {
    // The backend request is still running (or already timed out).
    // Show the animation and clear it when the timestamp expires.
    showScanPanel = true;
    const remainingMs = savedUntil - Date.now();
    startCountdown(Math.max(0, Math.ceil(remainingMs / 1000)));
    setTimeout(() => {
      if (discoverable) {
        discoverable = false;
        discoverableError = "";
        stopTimer();
        sessionStorage.removeItem(DISCO_KEY);
      }
    }, remainingMs);
  }

  // Countdown / elapsed timer for scanning / discoverable states
  let remaining = $state(0);
  let timerInterval: ReturnType<typeof setInterval> | undefined;

  function startCountdown(seconds: number) {
    remaining = seconds;
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      remaining = Math.max(0, remaining - 1);
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = undefined;
  }

  onDestroy(() => stopTimer());

  function formatTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}:${String(sec).padStart(2, "0")}` : `0:${String(sec).padStart(2, "0")}`;
  }

  // Abort controller for cancellable requests
  let abortController: AbortController | undefined;

  function isAlreadyAdded(address: string): boolean {
    return devices.some(d => d.address.toLowerCase() === address.toLowerCase());
  }

  async function startScan() {
    showScanPanel = true;
    showManualAdd = false;
    scanning = true;
    scanError = "";
    scanResults = [];
    abortController = new AbortController();
    startCountdown(scanDuration);

    try {
      const res = await fetch(`${getBackendUrl()}${scanEndpoint}`, {
        method: scanEndpoint.includes("scan") ? "POST" : "GET",
        signal: abortController?.signal,
      });
      const data = await res.json();

      if (!res.ok) {
        scanError = data.error || data.message || "Scan failed";
        return;
      }

      scanResults = data[scanResultKey] ?? [];
      if (scanResults.length === 0) {
        scanError = t("status.noData");
      }
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError")) {
        scanError = t("error.connectionStatus");
      }
    } finally {
      scanning = false;
      stopTimer();
      abortController = undefined;
    }
  }

  function handleAdd(device: Device) {
    addingAddress = device.address;
    const customName = editingNames[device.address]?.trim();
    const finalDevice = customName
      ? { ...device, name: customName }
      : { ...device, name: device.name || device.address };

    toast.promise(
      (async () => {
        await onAdd(finalDevice);
        scanResults = scanResults.filter(d => d.address !== device.address);
        delete editingNames[device.address];
      })(),
      {
        loading: t("status.saving"),
        success: t("toast.deviceAdded", { name: finalDevice.name }),
        error: (e) => e instanceof Error ? e.message : t("toast.addDeviceFailed"),
      },
    ).finally(() => { addingAddress = null; });
  }

  function handleRemove(address: string) {
    removingAddress = address;

    toast.promise(onRemove(address), {
      loading: t("status.removing"),
      success: t("toast.deviceRemoved"),
      error: (e) => e instanceof Error ? e.message : t("toast.removeDeviceFailed"),
    }).finally(() => { removingAddress = null; });
  }

  function handleManualAdd() {
    const address = manualMac.trim();
    if (!address) return;

    manualAdding = true;
    const name = manualName.trim() || address;

    toast.promise(
      (async () => {
        await onAdd({ address, name });
        manualMac = "";
        manualName = "";
        showManualAdd = false;
      })(),
      {
        loading: t("status.saving"),
        success: t("toast.deviceAdded", { name }),
        error: (e) => e instanceof Error ? e.message : t("toast.addDeviceFailed"),
      },
    ).finally(() => { manualAdding = false; });
  }

  async function startDiscoverable() {
    discoverable = true;
    discoverableError = "";
    showManualAdd = false;
    showScanPanel = true;
    abortController = new AbortController();
    startCountdown(DISCOVERABLE_TIMEOUT);
    sessionStorage.setItem(DISCO_KEY, String(Date.now() + DISCOVERABLE_TIMEOUT * 1000));

    try {
      const res = await fetch(`${getBackendUrl()}/bt/discoverable`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timeout: DISCOVERABLE_TIMEOUT }),
        signal: abortController?.signal,
      });
      const data = await res.json();

      if (!res.ok) {
        discoverableError = data.error || t("error.connectionStatus");
        return;
      }

      // Device was paired and auto-registered by the backend
      const device = data.device;
      if (device && !isAlreadyAdded(device.address)) {
        // Refresh the device list from parent (it was already saved server-side)
        devices = [...devices, device];
      }
      toast.success(t("toast.deviceAdded", { name: device?.name || "device" }));
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError")) {
        discoverableError = t("error.connectionStatus");
      }
    } finally {
      stopTimer();
      discoverable = false;
      abortController = undefined;
      sessionStorage.removeItem(DISCO_KEY);
    }
  }

  function closeScanPanel() {
    abortController?.abort();
    abortController = undefined;
    stopTimer();
    scanning = false;
    discoverable = false;
    showScanPanel = false;
    showManualAdd = false;
    scanResults = [];
    scanError = "";
    discoverableError = "";
  }
</script>

<div class="card overflow-hidden">
  <!-- Header -->
  <div class="flex items-center gap-2.5 border-b border-border-subtle px-4 py-3 sm:px-5 sm:py-3.5">
    {#if icon === "bluetooth"}
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <Icon icon={bluetoothIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
      </div>
    {:else}
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <Icon icon={wifiIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
      </div>
    {/if}
    <h3 class="text-sm font-semibold text-text-primary">{title}</h3>
    <span class="ml-auto rounded-full bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold text-text-muted">
      {devices.length}
    </span>
  </div>

  <!-- Device list -->
  {#if devices.length === 0 && !showScanPanel}
    <div class="px-4 py-6 text-center sm:px-5 sm:py-8">
      <p class="text-sm text-text-muted">{t("empty.noDevicesConfigured")}</p>
      <div class="mt-3 flex flex-wrap items-center justify-center gap-2">
        <button
          onclick={startScan}
          class="inline-flex items-center gap-1.5 rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/15"
        >
          <Icon icon={searchIcon} class="h-3 w-3" />
          {t("btn.scanForDevices")}
        </button>
        {#if icon === "bluetooth"}
          <button
            onclick={startDiscoverable}
            class="inline-flex items-center gap-1.5 rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/15"
          >
            <Icon icon={bluetoothIcon} class="h-3 w-3" />
            {t("btn.makeDiscoverable")}
          </button>
        {/if}
      </div>
    </div>
  {:else if devices.length > 0}
    <ul class="divide-y divide-border-subtle">
      {#each devices as device (device.address)}
        {@const online = isOnline(device.address)}
        <li class="group flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-surface-overlay/50 sm:px-5 sm:py-3">
          {#if online === undefined}
            <span class="h-2 w-2 shrink-0 rounded-full bg-text-muted/40"></span>
          {:else if online}
            <span class="h-2 w-2 shrink-0 rounded-full bg-status-ok shadow-[0_0_6px_rgba(0,230,118,0.4)]"></span>
          {:else}
            <span class="h-2 w-2 shrink-0 rounded-full bg-text-muted/30"></span>
          {/if}
          <div class="flex min-w-0 flex-1 items-baseline gap-3">
            <span class="truncate text-sm font-medium text-text-primary">{device.name}</span>
            {#if device.name.toLowerCase() !== device.address.toLowerCase()}
              <code class="shrink-0 font-mono text-xs font-medium text-text-muted">{device.address}</code>
            {/if}
          </div>
          <button
            onclick={() => handleRemove(device.address)}
            disabled={removingAddress === device.address}
            class="shrink-0 rounded-md p-2 text-text-muted transition-all hover:bg-status-critical/10 hover:text-status-critical sm:opacity-0 sm:group-hover:opacity-100 disabled:opacity-50"
            title={t("btn.removeDevice")}
            aria-label={t("btn.removeDevice")}
          >
            {#if removingAddress === device.address}
              <Icon icon={loader2Icon} class="h-3.5 w-3.5 animate-spin" />
            {:else}
              <Icon icon={xIcon} class="h-3.5 w-3.5" />
            {/if}
          </button>
        </li>
      {/each}
    </ul>
  {/if}

  <!-- Actions bar -->
  {#if devices.length > 0 && !showScanPanel}
    <div class="flex items-center gap-3 border-t border-border-subtle px-4 py-2.5 sm:px-5">
      <button
        onclick={startScan}
        class="inline-flex items-center gap-1.5 rounded-lg text-xs font-medium text-text-muted transition-colors hover:text-accent"
      >
        <Icon icon={searchIcon} class="h-3 w-3" />
        {t("btn.scanForDevices")}
      </button>
      {#if icon === "bluetooth"}
        <button
          onclick={startDiscoverable}
          class="inline-flex items-center gap-1.5 rounded-lg text-xs font-medium text-text-muted transition-colors hover:text-accent"
        >
          <Icon icon={bluetoothIcon} class="h-3 w-3" />
          {t("btn.makeDiscoverable")}
        </button>
      {/if}
    </div>
  {/if}

  <!-- Scan / discovery panel -->
  {#if showScanPanel}
    <div class="animate-slide-down border-t border-border-subtle bg-surface-base/50">
      <!-- Panel header -->
      <div class="flex items-center justify-between px-4 py-2.5 sm:px-5">
        <span class="text-xs font-semibold text-text-secondary">
          {scanning ? t("status.scanning") : discoverable ? t("status.discoverable") : t("label.discoveredDevices")}
        </span>
        <div class="flex items-center gap-2">
          {#if !scanning && !discoverable}
            <button
              onclick={() => { showManualAdd = !showManualAdd; }}
              class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-accent"
            >
              {t("btn.enterManually")}
            </button>
            <span class="text-border-default">|</span>
            <button
              onclick={startScan}
              class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-accent"
            >
              {t("btn.rescan")}
            </button>
            <span class="text-border-default">|</span>
          {/if}
          <button
            onclick={closeScanPanel}
            class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-text-primary"
          >
            {t("btn.close")}
          </button>
        </div>
      </div>

      <!-- Scanning indicator -->
      {#if scanning}
        <div class="flex flex-col items-center gap-3 px-4 py-6 sm:px-5">
          <div class="relative flex h-10 w-10 items-center justify-center">
            <div class="absolute inset-0 animate-ping rounded-full bg-accent/20"></div>
            <div class="absolute inset-1 animate-ping rounded-full bg-accent/15" style="animation-delay: 0.3s;"></div>
            {#if icon === "bluetooth"}
              <Icon icon={bluetoothIcon} class="relative h-5 w-5 text-accent" />
            {:else}
              <Icon icon={wifiIcon} class="relative h-5 w-5 text-accent" />
            {/if}
          </div>
          <p class="text-xs text-text-muted">
            {icon === "bluetooth" ? t("help.searchingBluetooth") : t("help.checkingWiFi")}
            <span class="ml-1 tabular-nums text-text-muted/60">{formatTime(remaining)}</span>
          </p>
        </div>
      {/if}

      <!-- Discoverable waiting state (BT only) -->
      {#if discoverable}
        <div class="flex flex-col items-center gap-3 px-4 py-6 sm:px-5">
          <div class="relative flex h-10 w-10 items-center justify-center">
            <div class="absolute inset-0 animate-ping rounded-full bg-accent/20" style="animation-duration: 2s;"></div>
            <div class="absolute inset-1 animate-ping rounded-full bg-accent/15" style="animation-duration: 2s; animation-delay: 0.5s;"></div>
            <Icon icon={bluetoothIcon} class="relative h-5 w-5 text-accent" />
          </div>
          <div class="text-center">
            <p class="text-xs font-medium text-text-secondary">
              {t("help.discoverableWaiting")}
              <span class="ml-1 tabular-nums text-text-muted/60">{formatTime(remaining)}</span>
            </p>
            <p class="mt-1 text-[0.6875rem] text-text-muted">{t("help.discoverableHint")}</p>
          </div>
          {#if discoverableError}
            <p class="text-xs text-status-critical">{discoverableError}</p>
          {/if}
        </div>
      {/if}

      <!-- Make discoverable button (BT only, shown when not scanning/discoverable and scan results are showing) -->
      {#if icon === "bluetooth" && !scanning && !discoverable && showScanPanel}
        <div class="border-t border-border-subtle px-4 py-2.5 sm:px-5">
          <button
            onclick={startDiscoverable}
            class="btn-press flex w-full items-center gap-2.5 rounded-xl border border-accent/20 bg-accent/5 px-3 py-2.5 text-left transition-colors hover:border-accent/30 hover:bg-accent/10"
          >
            <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent/10">
              <Icon icon={bluetoothIcon} class="h-3.5 w-3.5 text-accent" />
            </div>
            <div class="min-w-0">
              <p class="text-xs font-semibold text-accent">{t("btn.makeDiscoverable")}</p>
              <p class="text-[0.6875rem] text-text-muted">{t("help.makeDiscoverable")}</p>
            </div>
          </button>
        </div>
      {/if}

      <!-- Manual add form -->
      {#if showManualAdd && !scanning && !discoverable}
        <div class="space-y-2 px-4 pb-3 sm:px-5">
          <div class="grid grid-cols-2 gap-2">
            <input
              type="text"
              bind:value={manualMac}
              placeholder={t("input.macAddress")}
              maxlength="17"
              autocomplete="off"
              spellcheck="false"
              aria-label={t("input.macAddress")}
              class="rounded-lg border border-border-default bg-surface-elevated px-3 py-1.5 text-xs font-medium text-text-primary placeholder:text-text-muted/50 outline-none focus:border-accent"
            />
            <input
              type="text"
              bind:value={manualName}
              placeholder={t("input.nameOptional")}
              maxlength="64"
              aria-label={t("input.nameOptional")}
              class="rounded-lg border border-border-default bg-surface-elevated px-3 py-1.5 text-xs font-medium text-text-primary placeholder:text-text-muted/50 outline-none focus:border-accent"
            />
          </div>
          <div class="flex justify-end">
          <button
            onclick={handleManualAdd}
            disabled={!manualMac.trim() || manualAdding}
            class="rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-40"
          >
            {manualAdding ? t("btn.adding") : t("btn.add")}
          </button>
          </div>
        </div>
      {/if}

      <!-- Scan results -->
      {#if !scanning && scanResults.length > 0}
        <ul class="divide-y divide-border-subtle">
          {#each scanResults as device (device.address)}
            {@const alreadyAdded = isAlreadyAdded(device.address)}
            <li class="flex items-center gap-3 px-4 py-2.5 sm:px-5">
              <div class="flex min-w-0 flex-1 items-center gap-3">
                <div class="flex min-w-0 flex-1 flex-col gap-0.5">
                  {#if device.name}
                    <span class="truncate text-sm font-medium text-text-primary">{device.name}</span>
                  {/if}
                  <code class="shrink-0 font-mono text-[0.6875rem] font-medium text-text-muted">{device.address}</code>
                </div>
                {#if !device.name}
                  <input
                    type="text"
                    placeholder={t("input.nameOptional")}
                    value={editingNames[device.address] ?? ""}
                    oninput={(e) => { editingNames[device.address] = e.currentTarget.value; }}
                    class="w-28 shrink-0 rounded-lg border border-border-default bg-surface-elevated px-2.5 py-1 text-xs font-medium text-text-primary placeholder:text-text-muted/50 outline-none focus:border-accent"
                  />
                {/if}
              </div>
              {#if alreadyAdded}
                <span class="shrink-0 text-[0.6875rem] font-medium text-status-ok">{t("status.added")}</span>
              {:else}
                <div class="flex shrink-0 flex-col items-end gap-1">
                  <button
                    onclick={() => handleAdd(device)}
                    disabled={addingAddress === device.address}
                    class="rounded-lg bg-accent/10 px-2.5 py-1 text-[0.6875rem] font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-50"
                  >
                    {addingAddress === device.address ? t("btn.adding") : t("btn.add")}
                  </button>
                  {#if addingAddress === device.address && icon === "bluetooth"}
                    <span class="text-[0.625rem] text-text-muted">{t("help.pairingCheckPhone")}</span>
                  {/if}
                </div>
              {/if}
            </li>
          {/each}
        </ul>
      {/if}

      <!-- Error / empty state -->
      {#if !scanning && scanError && scanResults.length === 0}
        <p class="px-4 pb-4 text-center text-xs text-text-muted sm:px-5">{scanError}</p>
      {/if}
    </div>
  {/if}
</div>
