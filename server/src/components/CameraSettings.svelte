<script lang="ts">

  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";
  import { t } from "../i18n";
  import Note from "./Note.svelte";
  import Icon from "./Icon.svelte";
  import rotateIcon from "../icons/rotate.svg?raw";
  import deviceDesktopIcon from "../icons/device-desktop.svg?raw";

  interface Props {
    currentAngle: number;
    currentMode: string;
    streamWidth: number;
    streamHeight: number;
    streamFPS: number;
  }

  let {
    currentAngle,
    currentMode,
    streamWidth,
    streamHeight,
    streamFPS,
  }: Props = $props();

  // Rotation state
  let angle = $state(currentAngle);
  let mode = $state(currentMode);
  let rotationSaving = $state(false);
  let rotationError = $state("");

  // Stream params state
  let width = $state(streamWidth);
  let height = $state(streamHeight);
  let fps = $state(streamFPS);
  let streamSaving = $state(false);
  let streamError = $state("");

  // Quality presets covering common Pi camera modules:
  // OV5647 (v1): 640×480, 1296×972, 1920×1080, 2592×1944
  // IMX219 (v2): 640×480, 1640×1232, 1920×1080, 3280×2464
  // IMX477 (HQ):  640×480, 1332×990, 1920×1080, 2028×1520, 4056×3040
  // IMX708 (v3): 640×480, 1536×864, 2304×1296, 4608×2592
  interface Preset {
    label: string;
    w: number;
    h: number;
    fps: number;
    note: string;
    recommended?: boolean;
    warn?: boolean;
  }

  interface PresetGroup {
    label: string;
    presets: Preset[];
  }

  const presetGroups: PresetGroup[] = [
    {
      label: "Common",
      presets: [
        { label: "SD 640×360 · 30 fps", w: 640, h: 360, fps: 30, note: "Lightweight 16:9 widescreen" },
        { label: "SD 640×480 · 15 fps", w: 640, h: 480, fps: 15, note: "Lowest resource usage" },
        { label: "SD 640×480 · 30 fps", w: 640, h: 480, fps: 30, note: "Minimal CPU load, works with all cameras" },
        { label: "HD 1280×720 · 15 fps", w: 1280, h: 720, fps: 15, note: "720p, lower CPU" },
        { label: "HD 1280×720 · 30 fps", w: 1280, h: 720, fps: 30, note: "720p, smooth playback" },
        { label: "Full HD 1920×1080 · 15 fps", w: 1920, h: 1080, fps: 15, note: "1080p, lower CPU" },
        { label: "Full HD 1920×1080 · 30 fps", w: 1920, h: 1080, fps: 30, note: "1080p — native on all modules" },
      ],
    },
    {
      label: "OV5647 (Camera v1 — 5 MP)",
      presets: [
        { label: "1296×972 · 15 fps", w: 1296, h: 972, fps: 15, note: "Sharp 4:3, relaxed CPU" },
        { label: "★ 1296×972 · 30 fps", w: 1296, h: 972, fps: 30, note: "Best balance for Pi Zero 2 W", recommended: true },
        { label: "2592×1944 · 15 fps", w: 2592, h: 1944, fps: 15, note: "Max resolution — 5 MP, exceeds H.264 encoder limit on Pi Zero 2 W", warn: true },
      ],
    },
    {
      label: "IMX219 (Camera v2 — 8 MP)",
      presets: [
        { label: "1640×1232 · 15 fps", w: 1640, h: 1232, fps: 15, note: "Full sensor binned, lower CPU" },
        { label: "★ 1640×1232 · 30 fps", w: 1640, h: 1232, fps: 30, note: "Full sensor binned — best balance", recommended: true },
        { label: "3280×2464 · 15 fps", w: 3280, h: 2464, fps: 15, note: "Max resolution — 8 MP, exceeds H.264 encoder limit on Pi Zero 2 W", warn: true },
      ],
    },
    {
      label: "IMX477 (HQ Camera — 12.3 MP)",
      presets: [
        { label: "1332×990 · 30 fps", w: 1332, h: 990, fps: 30, note: "2×2 binned, lightweight" },
        { label: "★ 2028×1520 · 30 fps", w: 2028, h: 1520, fps: 30, note: "Half-resolution — best balance, may exceed encoder limit on Pi Zero 2 W", recommended: true, warn: true },
        { label: "4056×3040 · 10 fps", w: 4056, h: 3040, fps: 10, note: "Max resolution — 12.3 MP, exceeds H.264 encoder limit on Pi Zero 2 W", warn: true },
      ],
    },
    {
      label: "IMX708 (Camera v3 — 12 MP)",
      presets: [
        { label: "1536×864 · 30 fps", w: 1536, h: 864, fps: 30, note: "Binned 16:9, lightweight" },
        { label: "★ 2304×1296 · 30 fps", w: 2304, h: 1296, fps: 30, note: "Native 16:9 — best balance, may exceed encoder limit on Pi Zero 2 W", recommended: true, warn: true },
        { label: "4608×2592 · 14 fps", w: 4608, h: 2592, fps: 14, note: "Max resolution — 12 MP, exceeds H.264 encoder limit on Pi Zero 2 W", warn: true },
      ],
    },
  ];

  // Flat list for index-based lookup
  const allPresets = presetGroups.flatMap(g => g.presets);

  let selectedPreset = $state(-1); // -1 = custom

  // Sync preset selection on mount
  $effect(() => {
    const idx = allPresets.findIndex(p => p.w === width && p.h === height && p.fps === fps);
    selectedPreset = idx;
  });

  function applyPreset(idx: number) {
    selectedPreset = idx;
    if (idx >= 0) {
      width = allPresets[idx].w;
      height = allPresets[idx].h;
      fps = allPresets[idx].fps;
    }
  }

  // Derived warnings
  let hardwareUnsupported = $derived(mode === "stream" && (angle === 90 || angle === 270));
  let streamParamsChanged = $derived(
    width !== streamWidth || height !== streamHeight || fps !== streamFPS
  );
  let presetNote = $derived(selectedPreset >= 0 ? allPresets[selectedPreset].note : null);
  let presetRecommended = $derived(selectedPreset >= 0 ? allPresets[selectedPreset].recommended : false);
  let presetWarn = $derived(selectedPreset >= 0 ? allPresets[selectedPreset].warn : false);

  function clearFeedback(which: "rotation" | "stream") {
    if (which === "rotation") {
      rotationError = "";
    } else {
      streamError = "";
    }
  }

  async function doSaveRotation() {
    // Always save angle + mode to settings.json
    await fetch(`${getBackendUrl()}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ RotationAngle: angle, RotationMode: mode }),
    });

    // If stream mode, also apply to MediaMTX (only 0/180 allowed)
    if (mode === "stream") {
      const effectiveAngle = (angle === 90 || angle === 270) ? 0 : angle;
      const res = await fetch(`${getBackendUrl()}/stream_settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rotation_angle: effectiveAngle }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || t("toast.rotationFailed"));
      }
    }

    currentAngle = angle;
    currentMode = mode;
  }

  function saveRotation() {
    clearFeedback("rotation");
    rotationSaving = true;

    toast.promise(doSaveRotation(), {
      loading: t("status.saving"),
      success: t("toast.rotationSaved"),
      error: (err) => {
        rotationError = err.message || t("toast.rotationFailed");
        angle = currentAngle;
        mode = currentMode;
        return rotationError;
      },
    }).finally(() => { rotationSaving = false; });
  }

  async function saveStreamParams() {
    clearFeedback("stream");
    streamSaving = true;

    toast.promise(doSaveStreamParams(), {
      loading: t("status.saving"),
      success: t("toast.streamSettingsApplied"),
      error: (err: Error) => {
        streamError = err.message || t("toast.streamSettingsFailed");
        width = streamWidth;
        height = streamHeight;
        fps = streamFPS;
        return streamError;
      },
    }).finally(() => { streamSaving = false; });
  }

  async function doSaveStreamParams() {
    // Save to settings.json
    await fetch(`${getBackendUrl()}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        StreamWidth: width,
        StreamHeight: height,
        StreamFPS: fps,
      }),
    });

    // Apply to MediaMTX
    const res = await fetch(`${getBackendUrl()}/stream_settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ width, height, fps }),
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.message || t("toast.streamSettingsFailed"));
    }

    streamWidth = width;
    streamHeight = height;
    streamFPS = fps;
  }
</script>

<!-- Rotation -->
<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <Icon icon={rotateIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
    </div>
    <h3 class="text-sm font-semibold text-text-primary">{t("section.cameraRotation")}</h3>
  </div>
    
  <div class="mt-3 space-y-3">
    <!-- Info/warnings -->
    {#if mode === "display"}
      <p class="text-xs leading-relaxed text-text-muted">
        {t("help.displayRotation")}
      </p>
    {:else if hardwareUnsupported}
      <Note variant="warning">
        {t("help.hardwareRotationLimited", { angle })}
      </Note>
    {:else}
      <p class="text-xs leading-relaxed text-text-muted">
        {t("help.hardwareRotation")}
      </p>
    {/if}
  </div>

  <div class="mt-3 space-y-3">
    <!-- Angle selector -->
    <select
      bind:value={angle}
      onchange={saveRotation}
      disabled={rotationSaving}
      class="rounded-xl border border-border-default w-full bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-(--shadow-glow) disabled:opacity-50"
    >
      <option value={0}>{t("rotation.default")}</option>
      <option value={90}>{t("rotation.clockwise")}</option>
      <option value={180}>{t("rotation.flipped")}</option>
      <option value={270}>{t("rotation.counterClockwise")}</option>
    </select>

    <!-- Mode toggle -->
    <div class="flex items-center gap-2">
      <div class="flex gap-2">
        <button
          onclick={() => { mode = "display"; saveRotation(); }}
          disabled={rotationSaving}
          class="rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors
            {mode === 'display'
              ? 'border-accent bg-accent/10 text-accent'
              : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}
            disabled:opacity-50"
        >
          {t("btn.displayOnly")}
        </button>
        <button
          onclick={() => { mode = "stream"; saveRotation(); }}
          disabled={rotationSaving}
          class="rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors
            {mode === 'stream'
              ? 'border-accent bg-accent/10 text-accent'
              : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}
            disabled:opacity-50"
        >
          {t("btn.applyToStream")}
        </button>
      </div>
    </div>

    {#if rotationError}
      <p class="mt-2 rounded-lg border border-status-critical/20 bg-status-critical/5 px-3 py-2 text-xs font-medium text-status-critical">{rotationError}</p>
    {/if}
  </div>
</div>

<!-- Stream Parameters -->
<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <Icon icon={deviceDesktopIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
    </div>
    <h3 class="text-sm font-semibold text-text-primary">{t("section.streamQuality")}</h3>
  </div>

  <div class="mt-3 space-y-3">
    <!-- Preset selector -->
    <div>
      <label for="stream-preset" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">{t("label.preset")}</label>
      <select
        id="stream-preset"
        value={selectedPreset}
        onchange={(e) => applyPreset(Number((e.target as HTMLSelectElement).value))}
        disabled={streamSaving}
        class="w-full rounded-xl border border-border-default bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50"
      >
        {#each presetGroups as group}
          {@const groupStartIdx = allPresets.indexOf(group.presets[0])}
          <optgroup label={group.label}>
            {#each group.presets as preset, i}
              <option value={groupStartIdx + i}>{preset.label}</option>
            {/each}
          </optgroup>
        {/each}
        <option value={-1}>{t("label.custom")}</option>
      </select>
    </div>

    {#if presetNote}
      <div class="flex flex-wrap items-center gap-1.5 {presetWarn ? 'text-status-warning' : 'text-text-muted'}">
        {#if presetWarn}
          <span class="flex shrink-0 items-center rounded-md bg-status-warning/10 border border-status-warning/20 px-1.5 py-0.5 text-[0.625rem] font-semibold text-status-warning">
            <svg class="mr-1 h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 9v4" /><path d="M12 17h.01" />
              <path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" />
            </svg>
            {t("label.encoderWarning")}
          </span>
        {/if}
        <span class="text-xs">{presetNote}</span>
        {#if presetRecommended}
          <span class="flex shrink-0 items-center rounded-md bg-accent/10 px-1.5 py-0.5 text-[0.625rem] font-semibold text-accent">{t("label.recommended")}</span>
        {/if}
      </div>
    {/if}

    <!-- Custom fields (always visible but muted when a preset is active) -->
    <div class="grid grid-cols-3 gap-3">
      <div>
        <label for="stream-width" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">{t("label.width")}</label>
        <input
          id="stream-width"
          type="number"
          bind:value={width}
          oninput={() => { selectedPreset = -1; }}
          min="320"
          max="4056"
          step="1"
          disabled={streamSaving}
          class="w-full rounded-xl border border-border-default bg-surface-elevated px-3 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50"
        />
      </div>
      <div>
        <label for="stream-height" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">{t("label.height")}</label>
        <input
          id="stream-height"
          type="number"
          bind:value={height}
          oninput={() => { selectedPreset = -1; }}
          min="240"
          max="3040"
          step="1"
          disabled={streamSaving}
          class="w-full rounded-xl border border-border-default bg-surface-elevated px-3 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50"
        />
      </div>
      <div>
        <label for="stream-fps" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">{t("label.fps")}</label>
        <input
          id="stream-fps"
          type="number"
          bind:value={fps}
          oninput={() => { selectedPreset = -1; }}
          min="1"
          max="120"
          step="1"
          disabled={streamSaving}
          class="w-full rounded-xl border border-border-default bg-surface-elevated px-3 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50"
        />
      </div>
    </div>

    {#if streamError}
      <p class="rounded-lg border border-status-critical/20 bg-status-critical/5 px-3 py-2 text-xs font-medium text-status-critical">{streamError}</p>
    {/if}

    <div class="flex items-center justify-end">
      <button
        onclick={saveStreamParams}
        disabled={streamSaving || !streamParamsChanged}
        class="btn-press rounded-xl bg-accent/10 px-4 py-2 text-xs font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-40"
      >
        {streamSaving ? t("btn.applying") : t("btn.apply")}
      </button>
    </div>

    <Note>
      {t("help.streamInterrupt")}
    </Note>
  </div>
</div>
