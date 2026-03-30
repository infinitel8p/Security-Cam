<script lang="ts">
  import { onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import Note from "./Note.svelte";

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
  let rotationSaved = $state(false);
  let rotationError = $state("");
  let rotationTimer: ReturnType<typeof setTimeout> | undefined;

  // Stream params state
  let width = $state(streamWidth);
  let height = $state(streamHeight);
  let fps = $state(streamFPS);
  let streamSaving = $state(false);
  let streamSaved = $state(false);
  let streamError = $state("");
  let streamTimer: ReturnType<typeof setTimeout> | undefined;

  // Quality presets (Pi Camera v2 sensor modes, tuned for Pi Zero 2 W)
  interface Preset {
    label: string;
    w: number;
    h: number;
    fps: number;
    note: string;
    recommended?: boolean;
  }

  interface PresetGroup {
    label: string;
    presets: Preset[];
  }

  const presetGroups: PresetGroup[] = [
    {
      label: "4:3 - Full field of view",
      presets: [
        { label: "SD 640×480 · 30 fps", w: 640, h: 480, fps: 30, note: "Minimal CPU load, great for monitoring" },
        { label: "SD 640×480 · 15 fps", w: 640, h: 480, fps: 15, note: "Lowest resource usage" },
        { label: "HD 1296×972 · 30 fps", w: 1296, h: 972, fps: 30, note: "Best balance for Pi Zero 2 W", recommended: true },
        { label: "HD 1296×972 · 15 fps", w: 1296, h: 972, fps: 15, note: "Sharp image, relaxed CPU" },
        { label: "Full 1640×1232 · 15 fps", w: 1640, h: 1232, fps: 15, note: "Max 4:3 resolution - may strain Pi Zero 2 W" },
      ],
    },
    {
      label: "16:9 - Wide",
      presets: [
        { label: "SD 640×360 · 30 fps", w: 640, h: 360, fps: 30, note: "Lightweight widescreen" },
        { label: "HD 1280×720 · 30 fps", w: 1280, h: 720, fps: 30, note: "720p, smooth playback" },
        { label: "HD 1280×720 · 15 fps", w: 1280, h: 720, fps: 15, note: "720p, lower CPU" },
        { label: "Full HD 1920×1080 · 15 fps", w: 1920, h: 1080, fps: 15, note: "1080p at comfortable framerate" },
        { label: "Full HD 1920×1080 · 30 fps", w: 1920, h: 1080, fps: 30, note: "Max quality - will strain Pi Zero 2 W" },
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

  function clearFeedback(which: "rotation" | "stream") {
    if (which === "rotation") {
      rotationSaved = false;
      rotationError = "";
    } else {
      streamSaved = false;
      streamError = "";
    }
  }

  async function saveRotation() {
    rotationSaving = true;
    clearFeedback("rotation");

    try {
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
          rotationError = data.message || "Failed to apply stream rotation";
          return;
        }
      }

      currentAngle = angle;
      currentMode = mode;
      rotationSaved = true;
      clearTimeout(rotationTimer);
      rotationTimer = setTimeout(() => (rotationSaved = false), 2000);
    } catch {
      rotationError = "Failed to save rotation settings";
      angle = currentAngle;
      mode = currentMode;
    } finally {
      rotationSaving = false;
    }
  }

  async function saveStreamParams() {
    streamSaving = true;
    clearFeedback("stream");

    try {
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
        streamError = data.message || "Failed to apply stream settings";
        return;
      }

      streamWidth = width;
      streamHeight = height;
      streamFPS = fps;
      streamSaved = true;
      clearTimeout(streamTimer);
      streamTimer = setTimeout(() => (streamSaved = false), 2000);
    } catch {
      streamError = "Failed to save stream settings";
      width = streamWidth;
      height = streamHeight;
      fps = streamFPS;
    } finally {
      streamSaving = false;
    }
  }

  onDestroy(() => {
    clearTimeout(rotationTimer);
    clearTimeout(streamTimer);
  });
</script>

<!-- Rotation -->
<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="1 4 1 10 7 10" />
        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
      </svg>
    </div>
    <h3 class="text-sm font-semibold text-text-primary">Camera Rotation</h3>
  </div>
    
  <div class="mt-3 space-y-3">
    <!-- Info/warnings -->
    {#if mode === "display"}
      <p class="text-xs leading-relaxed text-text-muted">
        Rotates the video on the dashboard only. Recordings are not affected. No performance cost.
      </p>
    {:else if hardwareUnsupported}
      <Note variant="warning">
        Hardware rotation only supports 0° and 180°. The {angle}° rotation will be applied as display-only instead.
      </Note>
    {:else}
      <p class="text-xs leading-relaxed text-text-muted">
        Applies rotation at the hardware level via MediaMTX. No performance cost for 0°/180°. Recordings will also be rotated.
      </p>
    {/if}
  </div>

  <div class="mt-3 space-y-3">
    <!-- Angle selector -->
    <div class="flex items-center gap-3">
      <select
        bind:value={angle}
        onchange={saveRotation}
        disabled={rotationSaving}
        class="rounded-xl border border-border-default bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50"
      >
        <option value={0}>0° - Default</option>
        <option value={90}>90° - Clockwise</option>
        <option value={180}>180° - Flipped</option>
        <option value={270}>270° - Counter-clockwise</option>
      </select>

      {#if rotationSaving}
        <span class="text-xs font-medium text-text-muted">Saving...</span>
      {/if}
      {#if rotationSaved}
        <span class="flex items-center gap-1 text-xs font-medium text-status-ok">
          <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Saved
        </span>
      {/if}
      {#if rotationError}
        <span class="text-xs font-medium text-status-critical">{rotationError}</span>
      {/if}
    </div>

    <!-- Mode toggle -->
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
        Display only
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
        Apply to stream
      </button>
    </div>
  </div>
</div>

<!-- Stream Parameters -->
<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    </div>
    <h3 class="text-sm font-semibold text-text-primary">Stream Quality</h3>
  </div>

  <div class="mt-3 space-y-3">
    <!-- Preset selector -->
    <div>
      <label for="stream-preset" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">Preset</label>
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
        <option value={-1}>Custom</option>
      </select>
    </div>

    {#if presetNote}
      <p class="text-xs leading-relaxed text-text-muted">
        {presetNote}
        {#if presetRecommended}
          <span class="ml-1 inline-flex items-center rounded-md bg-accent/10 px-1.5 py-0.5 text-[0.625rem] font-semibold text-accent">Recommended</span>
        {/if}
      </p>
    {/if}

    <!-- Custom fields (always visible but muted when a preset is active) -->
    <div class="grid grid-cols-3 gap-3">
      <div>
        <label for="stream-width" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">Width</label>
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
        <label for="stream-height" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">Height</label>
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
        <label for="stream-fps" class="mb-1 block text-[0.6875rem] font-medium text-text-muted">FPS</label>
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

    <div class="flex items-center gap-3">
      <button
        onclick={saveStreamParams}
        disabled={streamSaving || !streamParamsChanged}
        class="rounded-xl bg-accent/10 px-4 py-2 text-xs font-semibold text-accent transition-colors hover:bg-accent/15 disabled:opacity-40"
      >
        {streamSaving ? "Applying..." : "Apply"}
      </button>

      {#if streamSaved}
        <span class="flex items-center gap-1 text-xs font-medium text-status-ok">
          <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Applied
        </span>
      {/if}
      {#if streamError}
        <span class="text-xs font-medium text-status-critical">{streamError}</span>
      {/if}
    </div>

    <Note>
      Changing stream settings will briefly interrupt the live feed while MediaMTX restarts.
    </Note>
  </div>
</div>
