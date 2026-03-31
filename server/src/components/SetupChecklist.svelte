<script lang="ts">
  import { onMount } from "svelte";
  import { initLocale, t } from "../i18n";
  import { getBackendUrl } from "../lib/api";
  import Icon from "./Icon.svelte";
  import shieldIcon from "../icons/shield.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";

  interface SetupState {
    hasDevices: boolean;
    hasSensor: boolean;
    hasRecording: boolean;
    hasStorage: boolean;
  }

  let setup = $state<SetupState | null>(null);
  let dismissed = $state(false);
  let loading = $state(true);

  const steps = $derived(
    setup ? [setup.hasDevices, setup.hasSensor, setup.hasRecording, setup.hasStorage] : []
  );
  let completedCount = $derived(steps.filter(Boolean).length);
  let totalSteps = 4;

  onMount(async () => {
    initLocale();
    if (localStorage.getItem("setup-checklist-dismissed") === "true") {
      dismissed = true;
      loading = false;
      return;
    }

    try {
      const [settingsRes, archiveRes] = await Promise.all([
        fetch(`${getBackendUrl()}/settings`),
        fetch(`${getBackendUrl()}/archive`),
      ]);
      if (!settingsRes.ok) throw new Error();
      const settings = await settingsRes.json();

      const btDevices = settings.TARGET_BT_ADDRESSES ?? [];
      const wifiDevices = settings.TARGET_AP_MAC_ADDRESSES ?? [];
      const sensorCfg = settings.Sensor ?? {};
      const storageCfg = settings.StorageLimit ?? {};

      let hasRecording = false;
      if (archiveRes.ok) {
        const archive = await archiveRes.json();
        hasRecording = Array.isArray(archive) ? archive.length > 0 : false;
      }

      setup = {
        hasDevices: btDevices.length > 0 || wifiDevices.length > 0,
        hasSensor: sensorCfg.enabled === true,
        hasRecording,
        hasStorage: storageCfg.enabled === true,
      };

      if (setup.hasDevices && setup.hasSensor && setup.hasRecording && setup.hasStorage) {
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

{#snippet step(num: number, done: boolean, href: string, title: string, desc: string)}
  <a
    {href}
    class="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-overlay/40 sm:px-5"
  >
    <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full {done ? 'bg-status-ok/15' : 'border border-border-default'}">
      {#if done}
        <svg class="h-3 w-3 text-status-ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <polyline class="animate-check" points="20 6 9 17 4 12" />
        </svg>
      {:else}
        <span class="text-[0.625rem] font-bold text-text-muted">{num}</span>
      {/if}
    </div>
    <div class="min-w-0 flex-1">
      <p class="text-[0.8125rem] font-medium {done ? 'text-text-muted line-through' : 'text-text-primary'}">
        {title}
      </p>
      <p class="text-[0.6875rem] text-text-muted">{desc}</p>
    </div>
    {#if !done}
      <Icon icon={chevronRightIcon} class="h-4 w-4 shrink-0 text-text-muted" />
    {/if}
  </a>
{/snippet}

{#if !loading && !dismissed && setup}
  <div class="animate-in card overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-border-subtle px-4 py-3 sm:px-5">
      <div class="flex items-center gap-2.5">
        <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
          <Icon icon={shieldIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
        </div>
        <div>
          <h3 class="text-sm font-semibold text-text-primary">{t("setup.title")}</h3>
          <p class="text-[0.6875rem] text-text-muted">{t("setup.stepProgress", { n: completedCount, total: totalSteps })}</p>
        </div>
      </div>
      <button
        onclick={dismiss}
        class="rounded-md p-1 text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
        title={t("btn.dismiss")}
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
      {@render step(1, setup.hasDevices, "/settings#devices", t("setup.addDevices"), setup.hasDevices ? t("setup.addDevicesDone") : t("setup.addDevicesDesc"))}
      {@render step(2, setup.hasSensor, "/settings#sensors", t("setup.enableSensor"), setup.hasSensor ? t("setup.enableSensorDone") : t("setup.enableSensorDesc"))}
      {@render step(3, setup.hasRecording, "/archive", t("setup.testRecording"), setup.hasRecording ? t("setup.testRecordingDone") : t("setup.testRecordingDesc"))}
      {@render step(4, setup.hasStorage, "/settings#storage", t("setup.setupStorage"), setup.hasStorage ? t("setup.setupStorageDone") : t("setup.setupStorageDesc"))}
    </div>
  </div>
{/if}
