<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";
  import { initLocale, t } from "../i18n";
  import Note from "./Note.svelte";
  import WiringDiagram from "./WiringDiagram.svelte";
  import Icon from "./Icon.svelte";
  import boltIcon from "../icons/bolt.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";

  interface CalibrationParam {
    key: string;
    name: string;
    type: string;
    min: number;
    max: number;
    default: number;
    step: number;
    unit?: string;
    description: string;
    labels: { min: string; max: string };
  }

  interface SensorType {
    type: string;
    name: string;
    default_gpio: number;
    module: string;
    description: string;
    use_case: string;
    icon: string;
    wiring: { pin: string; connect: string }[];
    wiring_note: string;
    calibration: CalibrationParam[];
  }

  interface SensorConfig {
    type: string;
    gpio: number;
    enabled: boolean;
    hold_seconds: number;
    invert_logic?: boolean;
    calibration?: Record<string, number>;
  }

  interface SensorStatusData {
    enabled: boolean;
    armed: boolean;
    triggered: boolean;
    hold_seconds: number;
    config: SensorConfig;
    sensor: { type: string; name: string; gpio: number; running: boolean } | null;
  }

  // Icon map: icon key → SVG path (keeps template clean)
  const ICONS: Record<string, string> = {
    magnet: "M18 8h1a4 4 0 0 1 0 8h-1M6 8H5a4 4 0 0 0 0 8h1M6 12h12",
    eye: "M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z",
    zap: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
    rotate: "M1 4v6h6M3.51 15a9 9 0 1 0 2.13-9.36L1 10",
    hand: "M18 11V6a2 2 0 0 0-4 0v3M14 10V4a2 2 0 0 0-4 0v7M10 10.5V2a2 2 0 0 0-4 0v9M6 15v-2a2 2 0 0 0-4 0v4a8 8 0 0 0 16 0v-5a2 2 0 0 0-4 0",
  };

  let sensorTypes = $state<SensorType[]>([]);
  let status = $state<SensorStatusData | null>(null);
  let loading = $state(true);
  let loadError = $state(false);
  let saving = $state(false);
  let toggling = $state(false);
  let testingTrigger = $state(false);
  let testingRelease = $state(false);
  let message = $state("");
  let messageIsError = $state(false);
  let showWiring = $state(false);

  // GPIO test mode
  let testMode = $state(false);
  let testValue = $state<boolean | null>(null);
  let testError = $state("");
  let testInterval: ReturnType<typeof setInterval> | null = null;
  let testHistory = $state<boolean[]>([]);

  // Editable fields
  let selectedType = $state("reed_switch");
  let gpio = $state(22);
  let holdSeconds = $state(10);
  let invertLogic = $state(false);
  let calibration = $state<Record<string, number>>({});

  async function fetchAll() {
    loading = true;
    loadError = false;
    try {
      const [typesRes, statusRes] = await Promise.all([
        fetch(`${getBackendUrl()}/sensor/types`),
        fetch(`${getBackendUrl()}/sensor/status`),
      ]);
      if (!typesRes.ok || !statusRes.ok) throw new Error();
      sensorTypes = await typesRes.json();
      status = await statusRes.json();

      if (status?.config) {
        selectedType = status.config.type || "reed_switch";
        gpio = status.config.gpio ?? 22;
        holdSeconds = status.config.hold_seconds ?? 10;
        invertLogic = status.config.invert_logic ?? false;
        calibration = status.config.calibration ?? {};
      }
    } catch {
      loadError = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    initLocale();
    fetchAll();
  });

  onDestroy(() => {
    if (testInterval) clearInterval(testInterval);
  });

  function getSensorMeta(type: string): SensorType | undefined {
    return sensorTypes.find((s) => s.type === type);
  }

  function onTypeChange(type: string) {
    selectedType = type;
    const meta = getSensorMeta(type);
    if (meta) {
      gpio = meta.default_gpio;
      // Reset calibration to defaults for the new sensor type
      const defaults: Record<string, number> = {};
      for (const param of meta.calibration ?? []) {
        defaults[param.key] = param.default;
      }
      calibration = defaults;
    }
    showWiring = false;
    if (testMode) stopTest();
  }

  function showMessage(text: string, isError = false) {
    message = text;
    messageIsError = isError;
    setTimeout(() => (message = ""), 3000);
    if (isError) toast.error(text);
    else toast.success(text);
  }

  async function saveConfig() {
    saving = true;
    message = "";
    try {
      const res = await fetch(`${getBackendUrl()}/sensor/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: selectedType,
          gpio: selectedType === "mock" ? null : gpio,
          enabled: status?.enabled ?? false,
          hold_seconds: holdSeconds,
          invert_logic: invertLogic,
          calibration: Object.keys(calibration).length > 0 ? calibration : undefined,
        }),
      });
      if (res.ok) {
        const statusRes = await fetch(`${getBackendUrl()}/sensor/status`);
        status = await statusRes.json();
        showMessage(t("toast.sensorConfigured"));
      } else {
        const data = await res.json();
        showMessage(data.error || t("toast.saveFailed"), true);
      }
    } catch {
      showMessage(t("error.connectionStatus"), true);
    } finally {
      saving = false;
    }
  }

  async function toggleEnabled() {
    toggling = true;
    message = "";
    const endpoint = status?.enabled ? "/sensor/disable" : "/sensor/enable";
    try {
      const res = await fetch(`${getBackendUrl()}${endpoint}`, { method: "POST" });
      if (res.ok) {
        const statusRes = await fetch(`${getBackendUrl()}/sensor/status`);
        status = await statusRes.json();
        showMessage(status?.enabled ? t("toast.sensorEnabled") : t("toast.sensorDisabled"));
      } else {
        showMessage(t("toast.saveFailed"), true);
      }
    } catch {
      showMessage(t("error.connectionStatus"), true);
    } finally {
      toggling = false;
    }
  }

  async function mockTrigger() {
    testingTrigger = true;
    try { await fetch(`${getBackendUrl()}/sensor/mock/trigger`, { method: "POST" }); }
    catch { /* silent */ }
    finally { testingTrigger = false; }
  }

  async function mockRelease() {
    testingRelease = true;
    try { await fetch(`${getBackendUrl()}/sensor/mock/release`, { method: "POST" }); }
    catch { /* silent */ }
    finally { testingRelease = false; }
  }

  async function testRead() {
    try {
      const res = await fetch(`${getBackendUrl()}/sensor/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: selectedType, gpio }),
      });
      const data = await res.json();
      if (res.ok) {
        testValue = data.value;
        testError = "";
        testHistory = [...testHistory.slice(-19), data.value ?? false];
      } else {
        testError = data.error || t("toast.saveFailed");
        testValue = null;
      }
    } catch {
      testError = t("error.connectionStatus");
      testValue = null;
    }
  }

  function startTest() {
    testMode = true;
    testValue = null;
    testError = "";
    testHistory = [];
    testRead();
    testInterval = setInterval(testRead, 500);
  }

  function stopTest() {
    testMode = false;
    if (testInterval) {
      clearInterval(testInterval);
      testInterval = null;
    }
    testValue = null;
    testHistory = [];
  }

  let isMock = $derived(selectedType === "mock");
  let isMockActive = $derived(status?.enabled && status?.sensor?.type === "mock");
  let currentMeta = $derived(getSensorMeta(selectedType));
  let calibrationParams = $derived(currentMeta?.calibration ?? []);

  /** Try i18n key, fall back to raw string if key returns itself (not found). */
  function tOr(key: string, fallback: string): string {
    const result = t(key);
    return result === key ? fallback : result;
  }
</script>

<div class="card overflow-hidden">
  <!-- Header -->
  <div class="flex items-center gap-2.5 border-b border-border-subtle px-4 py-3 sm:px-5 sm:py-3.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <Icon icon={boltIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
    </div>
    <h3 class="text-sm font-semibold text-text-primary">{t("section.triggerSensors")}</h3>
    <div class="ml-auto flex items-center gap-2">
      {#if status}
        <span class="rounded-full px-2 py-0.5 text-[0.6875rem] font-semibold
          {status.enabled
            ? status.armed
              ? 'bg-status-ok/10 text-status-ok'
              : 'bg-surface-elevated text-text-muted'
            : 'bg-surface-elevated text-text-muted'}">
          {status.enabled ? (status.armed ? t("status.armed") : t("status.idle")) : t("status.disabled")}
        </span>
      {/if}
    </div>
  </div>

  {#if loading}
    <div class="px-4 py-6 sm:px-5">
      <div class="skeleton h-4 w-32"></div>
      <div class="skeleton mt-4 h-8 w-48"></div>
    </div>
  {:else if loadError}
    <div class="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
      <p class="text-sm text-text-muted">{t("error.sensorConfig")}</p>
      <button onclick={fetchAll} class="text-[0.8125rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
    </div>
  {:else}
    <div class="px-4 py-4 sm:px-5 sm:py-5">
      <!-- Enable/disable toggle -->
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-text-primary">{t("label.autoRecording")}</p>
          <p class="mt-0.5 text-xs text-text-muted">{t("help.autoRecording")}</p>
        </div>
        <button
          onclick={toggleEnabled}
          disabled={toggling}
          class="btn-press relative h-6 w-11 shrink-0 rounded-full transition-colors duration-300
            {status?.enabled ? 'bg-accent shadow-[0_0_8px_rgba(77,148,255,0.25)]' : 'bg-surface-elevated'}"
        >
          <span
            class="absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-md transition-transform duration-300
              {status?.enabled ? 'translate-x-5' : 'translate-x-0'}"
            style="transition-timing-function: cubic-bezier(0.25, 1, 0.5, 1);"
          ></span>
        </button>
      </div>

      <!-- ── Sensor Selection ── -->
      <div class="mt-5">
        <label class="mb-2 block text-xs font-medium text-text-secondary" for="sensor-type">{t("label.sensorType")}</label>
        <div class="grid grid-cols-3 gap-1.5 sm:grid-cols-4">
          {#each sensorTypes as st (st.type)}
            <button
              onclick={() => onTypeChange(st.type)}
              class="rounded-xl border px-2.5 py-2 text-center transition-all duration-200
                {selectedType === st.type
                  ? 'border-accent/30 bg-accent-muted text-accent shadow-[var(--shadow-glow)]'
                  : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
            >
              <div class="flex flex-col items-center gap-1">
                {#if st.icon === "gate"}
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="7" height="18" rx="1" /><rect x="14" y="3" width="7" height="18" rx="1" />
                    <line x1="10" y1="12" x2="14" y2="12" stroke-dasharray="2 2" />
                  </svg>
                {:else if st.icon === "circle"}
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
                  </svg>
                {:else if st.icon === "wrench"}
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                  </svg>
                {:else if st.icon === "eye"}
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                {:else}
                  <!-- magnet, zap, rotate, hand - all simple path icons -->
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d={ICONS[st.icon] ?? ICONS.zap} />
                  </svg>
                {/if}
                <span class="text-[0.6875rem] font-medium leading-tight">{st.name}</span>
              </div>
            </button>
          {/each}
        </div>
      </div>

      <!-- ── Selected Sensor Details ── -->
      {#if currentMeta}
        <div class="mt-4 rounded-lg border border-border-default bg-surface-base px-3.5 py-3">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-xs font-semibold text-text-primary">{currentMeta.name}
                <span class="ml-1 font-normal text-text-muted">({currentMeta.module})</span>
              </p>
              <p class="mt-0.5 text-[0.6875rem] text-text-muted">{currentMeta.description}</p>
              <p class="mt-1 text-[0.6875rem] text-text-secondary">
                <span class="font-medium">Use case:</span> {currentMeta.use_case}
              </p>
            </div>
          </div>

          <!-- Wiring guide (expandable) -->
          {#if currentMeta.wiring.length > 0}
            <button
              onclick={() => showWiring = !showWiring}
              class="mt-2.5 flex items-center gap-1 text-[0.6875rem] font-medium text-accent transition-colors hover:text-accent/80"
            >
              <Icon icon={chevronRightIcon}
                class="h-3 w-3 transition-transform duration-200 {showWiring ? 'rotate-90' : ''}"
              />
              {showWiring ? t("btn.hideWiring") : t("btn.showWiring")}
            </button>

            {#if showWiring}
              <div class="animate-slide-down mt-3 -mx-3.5 -mb-3 rounded-b-lg border-t border-border-subtle bg-surface-base/50 px-3.5 pb-3.5 pt-3.5">
                <!-- Wiring diagram -->
                <WiringDiagram
                  wiring={currentMeta.wiring}
                  sensorName={currentMeta.name}
                  module={currentMeta.module}
                />

                <!-- Wiring table (compact reference) -->
                <div class="mt-3 overflow-hidden rounded-md border border-border-subtle">
                  <table class="w-full text-[0.6875rem]">
                    <thead>
                      <tr class="bg-surface-elevated/50">
                        <th class="px-3 py-1.5 text-left font-semibold text-text-secondary">{t("label.sensorPin")}</th>
                        <th class="px-3 py-1.5 text-left font-semibold text-text-secondary">{t("label.raspberryPi")}</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-border-subtle">
                      {#each currentMeta.wiring as row}
                        <tr>
                          <td class="px-3 py-1.5 font-medium text-text-primary">{row.pin}</td>
                          <td class="px-3 py-1.5 font-mono text-text-secondary">{row.connect}</td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
                {#if currentMeta.wiring_note}
                  <p class="mt-2 text-[0.6875rem] text-text-muted">{currentMeta.wiring_note}</p>
                {/if}
              </div>
            {/if}
          {/if}
        </div>
      {/if}

      <!-- ── Configuration Controls ── -->
      {#if !isMock}
        <div class="mt-5">
          <label class="mb-1.5 block text-xs font-medium text-text-secondary" for="gpio-pin">{t("label.gpioPin")}</label>
          <input
            id="gpio-pin"
            type="number"
            min="0"
            max="27"
            bind:value={gpio}
            class="w-24 rounded-lg border border-border-default bg-surface-elevated px-3 py-1.5 text-sm font-medium tabular-nums text-text-primary outline-none focus:border-accent"
          />
          <p class="mt-1 text-[0.6875rem] text-text-muted">{t("help.gpioPin", { n: currentMeta?.default_gpio ?? "-" })}</p>
        </div>

        <!-- Wiring test panel -->
        <div class="mt-3 rounded-lg border border-border-default bg-surface-base px-3 py-3">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold text-text-secondary">{t("label.testWiring")}</p>
              <p class="mt-0.5 text-[0.6875rem] text-text-muted">
                {t("help.testWiring")}
              </p>
            </div>
            {#if testMode}
              <button
                onclick={stopTest}
                class="rounded-lg bg-status-critical/10 px-3 py-1.5 text-xs font-semibold text-status-critical transition-colors hover:bg-status-critical/15"
              >
                {t("btn.stopTest")}
              </button>
            {:else}
              <button
                onclick={startTest}
                class="rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/15"
              >
                {t("btn.startTest")}
              </button>
            {/if}
          </div>

          {#if testMode}
            <div class="animate-slide-down mt-3 space-y-2.5">
              {#if testError}
                <p class="text-xs text-status-critical">{testError}</p>
              {:else}
                <!-- Live value indicator -->
                <div class="flex items-center gap-3">
                  <div class="flex items-center gap-2">
                    <span
                      class="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold
                        {testValue
                          ? 'bg-status-ok/15 text-status-ok shadow-[0_0_12px_rgba(52,217,172,0.2)]'
                          : 'bg-surface-elevated text-text-muted'}"
                    >
                      {testValue ? "1" : "0"}
                    </span>
                    <div>
                      <p class="text-xs font-semibold {testValue ? 'text-status-ok' : 'text-text-muted'}">
                        {testValue ? t("label.high") : t("label.low")}
                      </p>
                      <p class="text-[0.625rem] text-text-muted">GPIO {gpio}</p>
                    </div>
                  </div>

                  <!-- Activity bar: last 20 readings -->
                  <div class="ml-auto flex items-end gap-px">
                    {#each testHistory as val, i}
                      <div
                        class="w-1.5 rounded-sm transition-all duration-150
                          {val ? 'bg-status-ok h-4' : 'bg-surface-elevated h-1.5'}"
                      ></div>
                    {/each}
                    {#each Array(Math.max(0, 20 - testHistory.length)) as _}
                      <div class="h-1.5 w-1.5 rounded-sm bg-surface-elevated/50"></div>
                    {/each}
                  </div>
                </div>

                <p class="text-[0.6875rem] text-text-muted">
                  {t("help.testInstructions")}
                </p>
              {/if}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Hold timeout -->
      <div class="mt-5">
        <label class="mb-1.5 block text-xs font-medium text-text-secondary" for="hold-seconds">{t("label.holdTimeout")}</label>
        <div class="flex items-center gap-2">
          <input
            id="hold-seconds"
            type="number"
            min="0"
            max="300"
            bind:value={holdSeconds}
            class="w-24 rounded-lg border border-border-default bg-surface-elevated px-3 py-1.5 text-sm font-medium tabular-nums text-text-primary outline-none focus:border-accent"
          />
          <span class="text-xs text-text-muted">{t("label.seconds")}</span>
        </div>
        <p class="mt-1 text-[0.6875rem] text-text-muted">{t("help.holdTimeout")}</p>
      </div>

      <!-- ── Calibration Controls ── -->
      {#if calibrationParams.length > 0}
        <div class="mt-5 rounded-lg border border-border-default bg-surface-base px-3.5 py-3">
          <p class="mb-3 text-xs font-semibold text-text-secondary">{t("label.calibration")}</p>
          <div class="space-y-4">
            {#each calibrationParams as param (param.key)}
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <label class="text-xs font-medium text-text-secondary" for="cal-{param.key}">
                    {tOr(`calibration.${param.key}`, param.name)}
                  </label>
                  <span class="rounded-md bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold tabular-nums text-text-primary">
                    {calibration[param.key] ?? param.default}{param.unit ? ` ${param.unit === "seconds" ? "s" : param.unit}` : ""}
                  </span>
                </div>
                <div class="flex items-center gap-2.5">
                  <span class="text-[0.625rem] text-text-muted w-12 shrink-0 text-right">
                    {tOr(`calibration.${param.key}_min`, param.labels.min)}
                  </span>
                  <input
                    id="cal-{param.key}"
                    type="range"
                    min={param.min}
                    max={param.max}
                    step={param.step}
                    value={calibration[param.key] ?? param.default}
                    oninput={(e: Event) => {
                      calibration = { ...calibration, [param.key]: Number((e.target as HTMLInputElement).value) };
                    }}
                    class="range-slider flex-1"
                  />
                  <span class="text-[0.625rem] text-text-muted w-12 shrink-0">
                    {tOr(`calibration.${param.key}_max`, param.labels.max)}
                  </span>
                </div>
                <p class="mt-1 text-[0.6875rem] text-text-muted">
                  {tOr(`calibration.${param.key}_help`, param.description)}
                </p>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Invert trigger logic -->
      {#if !isMock}
        <div class="mt-5 flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-text-primary">{t("label.invertTrigger")}</p>
            <p class="mt-0.5 text-xs text-text-muted">
              {invertLogic
                ? t("help.invertActive")
                : t("help.invertInactive")}
            </p>
          </div>
          <button
            onclick={() => { invertLogic = !invertLogic; }}
            class="btn-press relative h-6 w-11 shrink-0 rounded-full transition-colors duration-300
              {invertLogic ? 'bg-accent shadow-[0_0_8px_rgba(77,148,255,0.25)]' : 'bg-surface-elevated'}"
          >
            <span
              class="absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-md transition-transform duration-300
                {invertLogic ? 'translate-x-5' : 'translate-x-0'}"
              style="transition-timing-function: cubic-bezier(0.25, 1, 0.5, 1);"
            ></span>
          </button>
        </div>
      {/if}

      <!-- Info note -->
      <div class="mt-5">
        <Note variant="info">
          {t("help.presenceGating")}
        </Note>
      </div>

      <!-- Mock sensor testing controls -->
      {#if isMockActive}
        <div class="mt-4 rounded-lg border border-border-default bg-surface-base px-3 py-3">
          <p class="mb-2 text-xs font-semibold text-text-secondary">{t("label.mockSensorControls")}</p>
          <div class="flex gap-2">
            <button
              onclick={mockTrigger}
              disabled={testingTrigger}
              class="rounded-lg bg-status-warning/10 px-3 py-1.5 text-xs font-semibold text-status-warning transition-colors hover:bg-status-warning/15 disabled:opacity-50"
            >
              {testingTrigger ? t("btn.firing") : t("btn.simulateTrigger")}
            </button>
            <button
              onclick={mockRelease}
              disabled={testingRelease}
              class="rounded-lg bg-status-ok/10 px-3 py-1.5 text-xs font-semibold text-status-ok transition-colors hover:bg-status-ok/15 disabled:opacity-50"
            >
              {testingRelease ? t("btn.releasing") : t("btn.simulateRelease")}
            </button>
          </div>
        </div>
      {/if}

      <!-- Save button + message -->
      <div class="mt-6 flex items-center gap-3 border-t border-border-subtle pt-4">
        <button
          onclick={saveConfig}
          disabled={saving}
          class="btn-press rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50"
        >
          {saving ? t("btn.saving") : t("btn.save")}
        </button>
        {#if message}
          <span class="text-xs font-medium {messageIsError ? 'text-status-critical' : 'text-status-ok'}">{message}</span>
        {/if}
      </div>
    </div>
  {/if}
</div>
