<script lang="ts">
  import { getBackendUrl } from "../lib/api";
  import { apiFetch } from "../lib/fetch";
  import { t } from "../i18n";
  import toast from "svelte-5-french-toast";
  import Icon from "./Icon.svelte";
  import Note from "./Note.svelte";
  import StreamPreview from "./StreamPreview.svelte";
  import cameraIcon from "../icons/camera.svg?raw";

  interface ISP {
    brightness: number;
    contrast: number;
    saturation: number;
    sharpness: number;
    ev: number;
    awb: string;
    exposure: string;
    denoise: string;
    metering: string;
  }

  const DEFAULTS: ISP = {
    brightness: 0, contrast: 1, saturation: 1, sharpness: 1,
    ev: 0, awb: "auto", exposure: "normal", denoise: "off", metering: "centre",
  };

  let {
    brightness = 0, contrast = 1, saturation = 1, sharpness = 1,
    ev = 0, awb = "auto", exposure = "normal", denoise = "off", metering = "centre",
  }: ISP = $props();

  // Local mutable state
  let b = $state(brightness);
  let c = $state(contrast);
  let sat = $state(saturation);
  let sh = $state(sharpness);
  let evVal = $state(ev);
  let awbVal = $state(awb);
  let expVal = $state(exposure);
  let denoiseVal = $state(denoise);
  let meterVal = $state(metering);

  let saving = $state(false);
  let preview: StreamPreview;
  let showPreview = $state(false);

  // Track last-applied values to detect changes
  let applied: ISP = $state({ brightness, contrast, saturation, sharpness, ev, awb, exposure, denoise, metering });

  let hasChanges = $derived(
    b !== applied.brightness || c !== applied.contrast || sat !== applied.saturation ||
    sh !== applied.sharpness || evVal !== applied.ev || awbVal !== applied.awb ||
    expVal !== applied.exposure || denoiseVal !== applied.denoise || meterVal !== applied.metering
  );

  let isDefault = $derived(
    b === DEFAULTS.brightness && c === DEFAULTS.contrast && sat === DEFAULTS.saturation &&
    sh === DEFAULTS.sharpness && evVal === DEFAULTS.ev && awbVal === DEFAULTS.awb &&
    expVal === DEFAULTS.exposure && denoiseVal === DEFAULTS.denoise && meterVal === DEFAULTS.metering
  );

  function currentValues(): ISP {
    return {
      brightness: b, contrast: c, saturation: sat, sharpness: sh,
      ev: evVal, awb: awbVal, exposure: expVal, denoise: denoiseVal, metering: meterVal,
    };
  }

  async function apply() {
    saving = true;
    try {
      const res = await apiFetch(`${getBackendUrl()}/isp_settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentValues()),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || `${res.status}`);
      }
      applied = currentValues();
      toast.success(t("toast.ispApplied"), { duration: 4000 });
      preview?.reconnect();
    } catch (e) {
      toast.error((e as Error).message || t("toast.ispFailed"), { duration: 5000 });
    } finally {
      saving = false;
    }
  }

  function resetDefaults() {
    b = DEFAULTS.brightness;
    c = DEFAULTS.contrast;
    sat = DEFAULTS.saturation;
    sh = DEFAULTS.sharpness;
    evVal = DEFAULTS.ev;
    awbVal = DEFAULTS.awb;
    expVal = DEFAULTS.exposure;
    denoiseVal = DEFAULTS.denoise;
    meterVal = DEFAULTS.metering;
  }

  const selectClass = "w-full rounded-xl border border-border-default bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50";
  const labelClass = "text-[0.6875rem] font-semibold text-text-muted";
  const badgeClass = "rounded bg-surface-elevated px-1.5 py-0.5 text-[0.625rem] font-semibold tabular-nums transition-colors duration-200";

  // Derived fill percentages for slider tracks (cached, only recompute on value change)
  let fillB = $derived(((b - (-1)) / (1 - (-1))) * 100);
  let fillC = $derived(((c - 0) / (16 - 0)) * 100);
  let fillSat = $derived(((sat - 0) / (16 - 0)) * 100);
  let fillSh = $derived(((sh - 0) / (16 - 0)) * 100);
  let fillEv = $derived(((evVal - (-10)) / (10 - (-10))) * 100);

  const AWB_OPTIONS = ["auto", "daylight", "cloudy", "tungsten", "fluorescent", "indoor", "incandescent"] as const;
  const EXPOSURE_OPTIONS = ["normal", "short", "long"] as const;
  const DENOISE_OPTIONS = ["off", "cdn_fast", "cdn_hq"] as const;
  const METERING_OPTIONS = ["centre", "spot", "matrix"] as const;
</script>

<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2.5">
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <Icon icon={cameraIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
      </div>
      <h3 class="text-sm font-semibold text-text-primary">{t("section.imageQuality")}</h3>
    </div>
    <button
      class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-accent"
      onclick={() => showPreview = !showPreview}
    >
      {showPreview ? t("btn.hidePreview") : t("btn.showPreview")}
    </button>
  </div>

  <div class="mt-3 space-y-3">
    <!-- Live preview -->
    {#if showPreview}
      <div class="animate-slide-down">
        <StreamPreview bind:this={preview} />
      </div>
    {/if}

    <!-- Sliders -->
    <div class="space-y-3">
      <!-- Brightness -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label for="isp-brightness" class={labelClass}>
            {t("label.brightness")}
            {#if b !== DEFAULTS.brightness}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
          </label>
          <span class="{badgeClass} {b !== DEFAULTS.brightness ? 'text-accent' : 'text-text-primary'}">{b.toFixed(1)}</span>
        </div>
        <input id="isp-brightness" type="range" class="range-slider range-fill w-full" min="-1" max="1" step="0.1" bind:value={b} disabled={saving}
          style="--fill: {fillB}%" />
      </div>

      <!-- Contrast -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label for="isp-contrast" class={labelClass}>
            {t("label.contrast")}
            {#if c !== DEFAULTS.contrast}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
          </label>
          <span class="{badgeClass} {c !== DEFAULTS.contrast ? 'text-accent' : 'text-text-primary'}">{c.toFixed(1)}</span>
        </div>
        <input id="isp-contrast" type="range" class="range-slider range-fill w-full" min="0" max="16" step="0.5" bind:value={c} disabled={saving}
          style="--fill: {fillC}%" />
      </div>

      <!-- Saturation -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label for="isp-saturation" class={labelClass}>
            {t("label.saturation")}
            {#if sat !== DEFAULTS.saturation}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
          </label>
          <span class="{badgeClass} {sat !== DEFAULTS.saturation ? 'text-accent' : 'text-text-primary'}">{sat.toFixed(1)}</span>
        </div>
        <input id="isp-saturation" type="range" class="range-slider range-fill w-full" min="0" max="16" step="0.5" bind:value={sat} disabled={saving}
          style="--fill: {fillSat}%" />
      </div>

      <!-- Sharpness -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label for="isp-sharpness" class={labelClass}>
            {t("label.sharpness")}
            {#if sh !== DEFAULTS.sharpness}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
          </label>
          <span class="{badgeClass} {sh !== DEFAULTS.sharpness ? 'text-accent' : 'text-text-primary'}">{sh.toFixed(1)}</span>
        </div>
        <input id="isp-sharpness" type="range" class="range-slider range-fill w-full" min="0" max="16" step="0.5" bind:value={sh} disabled={saving}
          style="--fill: {fillSh}%" />
      </div>

      <!-- EV -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label for="isp-ev" class={labelClass}>
            {t("label.ev")}
            {#if evVal !== DEFAULTS.ev}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
          </label>
          <span class="{badgeClass} {evVal !== DEFAULTS.ev ? 'text-accent' : 'text-text-primary'}">{evVal > 0 ? "+" : ""}{evVal}</span>
        </div>
        <input id="isp-ev" type="range" class="range-slider range-fill w-full" min="-10" max="10" step="1" bind:value={evVal} disabled={saving}
          style="--fill: {fillEv}%" />
      </div>
    </div>

    <!-- Dropdowns -->
    <div class="grid gap-3 sm:grid-cols-2">
      <!-- White Balance -->
      <div>
        <label for="isp-awb" class="mb-1 block {labelClass}">
          {t("label.awb")}
          {#if awbVal !== DEFAULTS.awb}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
        </label>
        <select id="isp-awb" class={selectClass} bind:value={awbVal} disabled={saving}>
          {#each AWB_OPTIONS as opt}
            <option value={opt}>{t(`isp.awb_${opt}`)}</option>
          {/each}
        </select>
      </div>

      <!-- Exposure Mode -->
      <div>
        <label for="isp-exposure" class="mb-1 block {labelClass}">
          {t("label.exposureMode")}
          {#if expVal !== DEFAULTS.exposure}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
        </label>
        <select id="isp-exposure" class={selectClass} bind:value={expVal} disabled={saving}>
          {#each EXPOSURE_OPTIONS as opt}
            <option value={opt}>{t(`isp.exposure_${opt}`)}</option>
          {/each}
        </select>
      </div>

      <!-- Denoise -->
      <div>
        <label for="isp-denoise" class="mb-1 block {labelClass}">
          {t("label.denoise")}
          {#if denoiseVal !== DEFAULTS.denoise}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
        </label>
        <select id="isp-denoise" class={selectClass} bind:value={denoiseVal} disabled={saving}>
          {#each DENOISE_OPTIONS as opt}
            <option value={opt}>{t(`isp.denoise_${opt}`)}</option>
          {/each}
        </select>
      </div>

      <!-- Metering -->
      <div>
        <label for="isp-metering" class="mb-1 block {labelClass}">
          {t("label.metering")}
          {#if meterVal !== DEFAULTS.metering}<span class="ml-1 inline-block h-1 w-1 rounded-full bg-accent animate-pop"></span>{/if}
        </label>
        <select id="isp-metering" class={selectClass} bind:value={meterVal} disabled={saving}>
          {#each METERING_OPTIONS as opt}
            <option value={opt}>{t(`isp.metering_${opt}`)}</option>
          {/each}
        </select>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-between">
      <button
        onclick={resetDefaults}
        disabled={saving || isDefault}
        class="text-[0.6875rem] font-medium text-text-muted transition-colors hover:text-accent disabled:opacity-40"
      >
        {t("btn.resetDefaults")}
      </button>
      <button
        onclick={apply}
        disabled={saving || !hasChanges}
        class="btn-press rounded-xl bg-accent/10 px-4 py-2 text-xs font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-40"
      >
        {saving ? t("btn.applying") : t("btn.apply")}
      </button>
    </div>

    <Note>
      {t("help.imageQuality")} <a href="/docs/basics/image-quality" target="_blank" class="font-semibold underline underline-offset-2 hover:text-accent">{t("help.ispDocsLink")}</a>
    </Note>

    {#if denoiseVal === "cdn_hq"}
      <div class="animate-slide-down">
        <Note variant="warning">
          {t("help.ispPerformance")}
        </Note>
      </div>
    {/if}
  </div>
</div>
