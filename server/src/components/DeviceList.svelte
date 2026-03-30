<script lang="ts">
  import { getBackendUrl } from "../lib/api";

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
    statuses?: Record<string, boolean>;
  }

  let { title, icon, devices, onAdd, onRemove, scanEndpoint, scanResultKey, statuses = {} }: Props = $props();

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

  function isAlreadyAdded(address: string): boolean {
    return devices.some(d => d.address.toLowerCase() === address.toLowerCase());
  }

  async function startScan() {
    showScanPanel = true;
    showManualAdd = false;
    scanning = true;
    scanError = "";
    scanResults = [];

    try {
      const res = await fetch(`${getBackendUrl()}${scanEndpoint}`, {
        method: scanEndpoint.includes("scan") ? "POST" : "GET",
      });
      const data = await res.json();

      if (!res.ok) {
        scanError = data.error || data.message || "Scan failed";
        return;
      }

      scanResults = data[scanResultKey] ?? [];
      if (scanResults.length === 0) {
        scanError = "No devices found";
      }
    } catch {
      scanError = "Could not reach the camera service";
    } finally {
      scanning = false;
    }
  }

  async function handleAdd(device: Device) {
    addingAddress = device.address;
    try {
      // Use the edited name if one was entered, otherwise use what we have
      const customName = editingNames[device.address]?.trim();
      const finalDevice = customName
        ? { ...device, name: customName }
        : { ...device, name: device.name || device.address };
      await onAdd(finalDevice);
      // Remove from scan results after adding
      scanResults = scanResults.filter(d => d.address !== device.address);
      delete editingNames[device.address];
    } finally {
      addingAddress = null;
    }
  }

  async function handleRemove(address: string) {
    removingAddress = address;
    try {
      await onRemove(address);
    } finally {
      removingAddress = null;
    }
  }

  async function handleManualAdd() {
    const address = manualMac.trim();
    if (!address) return;

    manualAdding = true;
    try {
      await onAdd({ address, name: manualName.trim() || address });
      manualMac = "";
      manualName = "";
      showManualAdd = false;
    } finally {
      manualAdding = false;
    }
  }

  function closeScanPanel() {
    showScanPanel = false;
    showManualAdd = false;
    scanResults = [];
    scanError = "";
  }
</script>

<div class="card overflow-hidden">
  <!-- Header -->
  <div class="flex items-center gap-2.5 border-b border-border-subtle px-4 py-3 sm:px-5 sm:py-3.5">
    {#if icon === "bluetooth"}
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6.5 6.5 17.5 17.5 12 23 12 1 17.5 6.5 6.5 17.5" />
        </svg>
      </div>
    {:else}
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0" />
          <path d="M1.42 9a16 16 0 0 1 21.16 0" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <line x1="12" y1="20" x2="12.01" y2="20" />
        </svg>
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
      <p class="text-sm text-text-muted">No devices configured</p>
      <button
        onclick={startScan}
        class="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/15"
      >
        <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        Scan for devices
      </button>
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
          <div class="flex min-w-0 flex-1 items-center gap-3">
            <span class="truncate text-sm font-medium text-text-primary">{device.name}</span>
            {#if device.name.toLowerCase() !== device.address.toLowerCase()}
              <code class="shrink-0 text-[0.6875rem] font-medium text-text-muted">{device.address}</code>
            {/if}
          </div>
          <button
            onclick={() => handleRemove(device.address)}
            disabled={removingAddress === device.address}
            class="shrink-0 rounded-md p-1 text-text-muted opacity-0 transition-all hover:bg-status-critical/10 hover:text-status-critical group-hover:opacity-100 disabled:opacity-50"
            title="Remove device"
          >
            {#if removingAddress === device.address}
              <svg class="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 2a10 10 0 0 1 10 10" />
              </svg>
            {:else}
              <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            {/if}
          </button>
        </li>
      {/each}
    </ul>
  {/if}

  <!-- Actions bar -->
  {#if devices.length > 0 && !showScanPanel}
    <div class="border-t border-border-subtle px-4 py-2.5 sm:px-5">
      <button
        onclick={startScan}
        class="inline-flex items-center gap-1.5 rounded-lg text-xs font-medium text-text-muted transition-colors hover:text-accent"
      >
        <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Add device
      </button>
    </div>
  {/if}

  <!-- Scan / discovery panel -->
  {#if showScanPanel}
    <div class="border-t border-border-subtle bg-surface-base/50">
      <!-- Panel header -->
      <div class="flex items-center justify-between px-4 py-2.5 sm:px-5">
        <span class="text-xs font-semibold text-text-secondary">
          {scanning ? "Scanning..." : "Discovered devices"}
        </span>
        <div class="flex items-center gap-2">
          {#if !scanning}
            <button
              onclick={() => { showManualAdd = !showManualAdd; }}
              class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-accent"
            >
              Enter manually
            </button>
            <span class="text-border-default">|</span>
            <button
              onclick={startScan}
              class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-accent"
            >
              Rescan
            </button>
            <span class="text-border-default">|</span>
          {/if}
          <button
            onclick={closeScanPanel}
            disabled={scanning}
            class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-text-primary disabled:opacity-50"
          >
            Close
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
              <svg class="relative h-5 w-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6.5 6.5 17.5 17.5 12 23 12 1 17.5 6.5 6.5 17.5" />
              </svg>
            {:else}
              <svg class="relative h-5 w-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12.55a11 11 0 0 1 14.08 0" /><path d="M1.42 9a16 16 0 0 1 21.16 0" />
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0" /><line x1="12" y1="20" x2="12.01" y2="20" />
              </svg>
            {/if}
          </div>
          <p class="text-xs text-text-muted">
            {icon === "bluetooth" ? "Searching for nearby Bluetooth devices..." : "Checking connected WiFi clients..."}
          </p>
        </div>
      {/if}

      <!-- Manual add form -->
      {#if showManualAdd && !scanning}
        <div class="space-y-2 px-4 pb-3 sm:px-5">
          <div class="grid grid-cols-2 gap-2">
            <input
              type="text"
              bind:value={manualMac}
              placeholder="MAC address"
              class="rounded-lg border border-border-default bg-surface-elevated px-3 py-1.5 text-xs font-medium text-text-primary placeholder:text-text-muted/50 outline-none focus:border-accent"
            />
            <input
              type="text"
              bind:value={manualName}
              placeholder="Name (optional)"
              class="rounded-lg border border-border-default bg-surface-elevated px-3 py-1.5 text-xs font-medium text-text-primary placeholder:text-text-muted/50 outline-none focus:border-accent"
            />
          </div>
          <button
            onclick={handleManualAdd}
            disabled={!manualMac.trim() || manualAdding}
            class="rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-40"
          >
            {manualAdding ? "Adding..." : "Add"}
          </button>
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
                  <code class="shrink-0 text-[0.6875rem] font-medium text-text-muted">{device.address}</code>
                </div>
                {#if !device.name}
                  <input
                    type="text"
                    placeholder="Name (optional)"
                    value={editingNames[device.address] ?? ""}
                    oninput={(e) => { editingNames[device.address] = e.currentTarget.value; }}
                    class="w-28 shrink-0 rounded-lg border border-border-default bg-surface-elevated px-2.5 py-1 text-xs font-medium text-text-primary placeholder:text-text-muted/50 outline-none focus:border-accent"
                  />
                {/if}
              </div>
              {#if alreadyAdded}
                <span class="shrink-0 text-[0.6875rem] font-medium text-status-ok">Added</span>
              {:else}
                <button
                  onclick={() => handleAdd(device)}
                  disabled={addingAddress === device.address}
                  class="shrink-0 rounded-lg bg-accent/10 px-2.5 py-1 text-[0.6875rem] font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-50"
                >
                  {addingAddress === device.address ? "Adding..." : "Add"}
                </button>
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
