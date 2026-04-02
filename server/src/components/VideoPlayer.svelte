<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl, getMediaMtxUrl, getHlsUrl } from "../lib/api";
  import { sseClient } from "../lib/sse";
  import toast from "svelte-5-french-toast";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import cameraIcon from "../icons/camera.svg?raw";
  import cameraBoltIcon from "../icons/camera-bolt.svg?raw";
  import alertCircleIcon from "../icons/alert-circle.svg?raw";
  import maximizeIcon from "../icons/maximize.svg?raw";
  import minimizeIcon from "../icons/minimize.svg?raw";

  let containerEl: HTMLDivElement;
  let videoEl: HTMLVideoElement;
  let pc: RTCPeerConnection | null = null;
  let connected = $state(false);
  let error = $state("");
  let recording = $state(false);
  let recordingStartedAt: string | null = $state(null);
  let toggling = $state(false);
  let snapping = $state(false);
  let isFullscreen = $state(false);
  let recSeconds = $state(0);
  let recTimer: ReturnType<typeof setInterval> | undefined;
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let unsubRecording: (() => void) | undefined;
  let destroyed = false;
  let webrtcFailCount = $state(0);
  let hlsFailCount = $state(0);
  let streamMode: "webrtc" | "hls" = $state("webrtc");
  const MAX_FAILURES = 3;

  let rotationAngle = $state(0);
  let rotationMode = $state("display");
  let scanLines = $state(true);
  let cssRotation = $derived(
    rotationMode === "display" && rotationAngle !== 0 ? rotationAngle : 0
  );
  let isSideways = $derived(cssRotation === 90 || cssRotation === 270);

  const STREAM_PATH = "cam";

  function startStream() {
    if (streamMode === "hls") {
      startHLS();
    } else {
      startWebRTC();
    }
  }

  async function startWebRTC() {
    if (destroyed) return;
    error = "";

    const whepUrl = `${getMediaMtxUrl()}/${STREAM_PATH}/whep`;

    pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });

    pc.addTransceiver("video", { direction: "recvonly" });

    pc.ontrack = (ev) => {
      videoEl.srcObject = ev.streams[0];
      connected = true;
      webrtcFailCount = 0;
      hlsFailCount = 0;
    };

    pc.onconnectionstatechange = () => {
      if (pc?.connectionState === "failed" || pc?.connectionState === "disconnected") {
        connected = false;
        error = t("error.streamDisconnected");
        webrtcFailCount++;
        cleanup();
        scheduleRetry();
      }
    };

    try {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const res = await fetch(whepUrl, {
        method: "POST",
        headers: { "Content-Type": "application/sdp" },
        body: offer.sdp,
      });

      if (!res.ok) {
        throw new Error(`WHEP request failed: ${res.status}`);
      }

      const answerSdp = await res.text();
      await pc.setRemoteDescription({
        type: "answer",
        sdp: answerSdp,
      });
    } catch (e) {
      console.error("WebRTC connection failed:", e);
      webrtcFailCount++;
      error = t("error.connectFailed");
      cleanup();
      scheduleRetry();
    }
  }

  function startHLS() {
    if (destroyed) return;
    error = "";

    const hlsSrc = `${getHlsUrl()}/${STREAM_PATH}/index.m3u8`;

    // Clear any WebRTC source
    videoEl.srcObject = null;
    videoEl.src = hlsSrc;
    videoEl.load();

    videoEl.onloadeddata = () => {
      connected = true;
      hlsFailCount = 0;
      webrtcFailCount = 0;
    };

    videoEl.onerror = () => {
      if (destroyed) return;
      connected = false;
      hlsFailCount++;
      error = t("error.connectFailed");
      scheduleRetry();
    };
  }

  function scheduleRetry() {
    clearTimeout(reconnectTimer);
    if (streamMode === "webrtc" && webrtcFailCount >= MAX_FAILURES) {
      console.warn(`WebRTC failed ${webrtcFailCount}x, switching to HLS`);
      streamMode = "hls";
      webrtcFailCount = 0;
      reconnectTimer = setTimeout(startHLS, 1000);
    } else if (streamMode === "hls" && hlsFailCount >= MAX_FAILURES) {
      console.warn(`HLS failed ${hlsFailCount}x, switching to WebRTC`);
      streamMode = "webrtc";
      hlsFailCount = 0;
      reconnectTimer = setTimeout(startWebRTC, 1000);
    } else {
      reconnectTimer = setTimeout(startStream, streamMode === "webrtc" ? 3000 : 5000);
    }
  }

  function cleanup() {
    if (pc) {
      pc.close();
      pc = null;
    }
  }

  async function toggleFullscreen() {
    if (!document.fullscreenElement) {
      await containerEl.requestFullscreen();
      isFullscreen = true;
    } else {
      await document.exitFullscreen();
      isFullscreen = false;
    }
  }

  function onFullscreenChange() {
    isFullscreen = !!document.fullscreenElement;
  }

  function toggleRecording() {
    toggling = true;

    toast.promise(
      (async () => {
        const res = await fetch(`${getBackendUrl()}/toggle_recording`, {
          method: "POST",
        });
        if (!res.ok) throw new Error();
        const data = await res.json();
        recording = data.message?.toLowerCase().includes("started") ?? false;
        return recording;
      })(),
      {
        loading: recording ? t("toast.recordingStopping") : t("toast.recordingStarting"),
        success: (started) => started ? t("toast.recordingStarted") : t("toast.recordingStopped"),
        error: t("toast.toggleRecordingFailed"),
      },
    ).finally(() => { toggling = false; });
  }

  async function fetchRecordingStatus() {
    try {
      const res = await fetch(`${getBackendUrl()}/recording_status`);
      if (!res.ok) return;
      const data = await res.json();
      recording = data.recording ?? false;
      recordingStartedAt = data.started_at ?? null;
    } catch {
      // Keep default
    }
  }

  async function fetchRotation() {
    try {
      const res = await fetch(`${getBackendUrl()}/settings`);
      if (!res.ok) return;
      const settings = await res.json();
      rotationAngle = Number(settings.RotationAngle) || 0;
      rotationMode = settings.RotationMode || "display";
      scanLines = settings.ScanLines !== false;
    } catch {
      // Keep defaults
    }
  }

  function takeSnapshot() {
    snapping = true;
    toast.promise(
      fetch(`${getBackendUrl()}/snapshot`, { method: "POST" })
        .then((res) => {
          if (!res.ok) throw new Error();
          return res.json();
        }),
      {
        loading: t("status.saving"),
        success: t("toast.snapshotSaved"),
        error: t("toast.snapshotFailed"),
      },
    ).finally(() => { snapping = false; });
  }

  function manualReconnect() {
    error = "";
    connected = false;
    webrtcFailCount = 0;
    hlsFailCount = 0;
    streamMode = "webrtc";
    clearTimeout(reconnectTimer);
    cleanup();
    startStream();
  }

  onMount(() => {
    initLocale();
    startStream();
    fetchRotation();
    fetchRecordingStatus();

    const sse = sseClient();
    sse.registerFallback({
      event: "recording_state",
      endpoint: "/recording_status",
      interval: 5_000,
      transform: (json) => json,
    });
    unsubRecording = sse.on("recording_state", (ev) => {
      recording = ev.recording ?? false;
      recordingStartedAt = ev.started_at ?? null;
    });
  });

  // Recording duration timer - uses backend start timestamp for accuracy
  $effect(() => {
    if (recording) {
      const calcElapsed = () => {
        if (recordingStartedAt) {
          return Math.max(0, Math.floor((Date.now() - new Date(recordingStartedAt).getTime()) / 1000));
        }
        return 0;
      };
      recSeconds = calcElapsed();
      recTimer = setInterval(() => { recSeconds = calcElapsed(); }, 1000);
    } else {
      clearInterval(recTimer);
      recSeconds = 0;
    }
    return () => clearInterval(recTimer);
  });

  function formatRecTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${String(sec).padStart(2, "0")}`;
  }

  onDestroy(() => {
    destroyed = true;
    clearTimeout(reconnectTimer);
    clearInterval(recTimer);
    unsubRecording?.();
    cleanup();
  });
</script>

<svelte:document on:fullscreenchange={onFullscreenChange} />

<div bind:this={containerEl} class="feed-ring {recording ? 'feed-ring-rec' : connected ? 'feed-ring-ok' : ''}" class:fullscreen={isFullscreen}>
<div class="card overflow-hidden transition-shadow duration-700 {connected ? 'shadow-glow-breathe' : ''} {recording ? 'recording-halo' : ''}">
  <!-- Feed -->
  <div class="relative w-full bg-black/80 {isFullscreen ? 'min-h-0 flex-1' : 'aspect-video'}">
    <video
      bind:this={videoEl}
      autoplay
      playsinline
      muted
      class="h-full w-full object-cover {connected ? 'animate-video-reveal' : ''}"
      class:hidden={!connected}
      style:transform={cssRotation ? `rotate(${cssRotation}deg)` : undefined}
      style:transform-origin={cssRotation ? "center center" : undefined}
      style:width={isSideways ? "100%" : undefined}
      style:height={isSideways ? "100%" : undefined}
      style:object-fit={isSideways ? "contain" : undefined}
    ></video>

    <!-- Scan line overlay -->
    {#if connected && scanLines}
      <div class="scan-lines pointer-events-none absolute inset-0 z-10" class:scan-lines-rec={recording}></div>
    {/if}

    {#if !connected}
      <div class="absolute inset-0 flex items-center justify-center">
        {#if error}
          <div class="flex flex-col items-center gap-2.5">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-status-warning/10">
              <Icon icon={alertCircleIcon} class="h-5 w-5 text-status-warning" stroke={2} />
            </div>
            <span class="text-sm text-text-secondary">{error}</span>
            <div class="flex items-center gap-3">
              <span class="text-xs text-text-muted">
                {t("status.reconnecting")}{streamMode === "hls" ? " (HLS)" : ""}
              </span>
              <button onclick={manualReconnect} class="text-xs font-medium text-accent hover:text-accent-hover">{t("btn.retryNow")}</button>
            </div>
          </div>
        {:else}
          <div class="flex flex-col items-center gap-2.5">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-accent/10">
              <Icon icon={cameraIcon} class="h-5 w-5 animate-pulse text-accent" stroke={2} />
            </div>
            <span class="text-sm text-text-secondary">{t("status.connectingToCamera")}</span>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Overlays -->
    <div class="absolute left-0 right-0 top-0 flex items-start justify-between p-3">
      <!-- Left: timestamp area (empty for now) -->
      <div></div>

      <!-- Right: status badges -->
      <div>
        {#if recording}
          <div class="animate-pop flex items-center gap-2 rounded-lg bg-black/60 px-2.5 py-1.5 backdrop-blur-md">
            <span class="h-2 w-2 animate-pulse rounded-full bg-status-critical shadow-[0_0_8px_rgba(240,104,104,0.6)]"></span>
            <span class="text-[0.6875rem] font-semibold tracking-wide text-white/90">{t("badge.rec")}</span>
          </div>
        {:else if connected}
          <div class="animate-fade-in flex items-center gap-1.5 rounded-lg bg-black/60 px-2.5 py-1.5 backdrop-blur-md">
            <span class="h-1.5 w-1.5 rounded-full bg-status-ok shadow-[0_0_6px_rgba(52,217,172,0.5)]"></span>
            <span class="text-[0.6875rem] font-medium tracking-wide text-white/80">{t("badge.live")}{streamMode === "hls" ? " · HLS" : ""}</span>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Controls -->
  <div
    class="controls-bar relative flex items-center justify-between px-3 py-2 sm:px-4 sm:py-2.5
      {isFullscreen
        ? 'fullscreen-controls absolute bottom-0 left-0 right-0 z-20 border-0'
        : 'border-t border-border-subtle'}"
    class:controls-bar-rec={recording}
  >
    <div class="flex items-center gap-1.5">
      {#if connected}
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-surface-overlay px-2 py-1.5 text-[0.625rem] font-semibold uppercase tracking-wider text-text-muted">
          <span class="h-1.5 w-1.5 rounded-full {recording ? 'bg-status-critical animate-pulse' : 'bg-status-ok'}"></span>
          {streamMode === "hls" ? "HLS" : "WebRTC"}
        </span>
      {:else}
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-surface-overlay px-2 py-1.5 text-[0.625rem] font-semibold uppercase tracking-wider text-text-muted/50">
          <span class="h-1.5 w-1.5 rounded-full bg-text-muted/30"></span>
          {t("status.offline")}
        </span>
      {/if}
      {#if recording}
        <span class="tabular-nums text-[0.75rem] font-medium text-status-critical">
          {formatRecTime(recSeconds)}
        </span>
      {/if}
    </div>
    <div class="flex items-center gap-1">
      <button
        onclick={takeSnapshot}
        disabled={snapping || !connected}
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-overlay text-text-muted transition-colors duration-150 hover:bg-surface-raised hover:text-text-secondary disabled:opacity-40"
        title={t("btn.snapshot")}
      >
        <Icon icon={cameraBoltIcon} class="h-4 w-4" stroke={2} />
      </button>

      <button
        onclick={toggleFullscreen}
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-overlay text-text-muted transition-colors duration-150 hover:bg-surface-raised hover:text-text-secondary"
        title={isFullscreen ? t("btn.exitFullscreen") : t("btn.fullscreen")}
      >
        {#if isFullscreen}
          <Icon icon={minimizeIcon} class="h-4 w-4" stroke={2} />
        {:else}
          <Icon icon={maximizeIcon} class="h-4 w-4" stroke={2} />
        {/if}
      </button>

      <button
        onclick={toggleRecording}
        disabled={toggling}
        class="btn-press flex h-8 items-center gap-1.5 rounded-lg px-3 text-[0.8125rem] font-medium transition-colors duration-150
          {recording
            ? 'bg-status-critical/15 text-status-critical hover:bg-status-critical/20'
            : 'bg-accent/15 text-accent hover:bg-accent/20'}
          disabled:opacity-40"
      >
        {#if recording}
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          {t("btn.stop")}
        {:else}
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="6" />
          </svg>
          {t("btn.record")}
        {/if}
      </button>
    </div>
  </div>
</div>
</div>

<style>
  .fullscreen {
    display: flex;
    flex-direction: column;
    background: black;
  }
  .fullscreen video {
    object-fit: contain;
  }

  /* Controls bar overlays the bottom in fullscreen, fades in on hover */
  .fullscreen-controls {
    background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  .fullscreen:hover .fullscreen-controls,
  .fullscreen-controls:focus-within {
    opacity: 1;
  }

  /* ── Scan line overlay ─────────────────────────────────────────────── */
  .scan-lines {
    background: repeating-linear-gradient(
      to bottom,
      transparent 0px,
      transparent 2px,
      rgba(0, 0, 0, 0.06) 2px,
      rgba(0, 0, 0, 0.06) 4px
    );
    mix-blend-mode: multiply;
  }

  /* When recording, scan lines get a red tint */
  .scan-lines-rec {
    background: repeating-linear-gradient(
      to bottom,
      transparent 0px,
      transparent 2px,
      rgba(240, 104, 104, 0.07) 2px,
      rgba(240, 104, 104, 0.07) 4px
    );
  }

  /* ── Control bar recording sweep ───────────────────────────────────── */
  .controls-bar {
    background: var(--color-surface-raised);
    transition: background 0.6s cubic-bezier(0.25, 1, 0.5, 1);
  }

  .controls-bar-rec {
    background: linear-gradient(
      to right,
      color-mix(in srgb, var(--color-surface-raised) 92%, #f06868),
      var(--color-surface-raised)
    );
  }

  /* ── Reduced motion ────────────────────────────────────────────────── */
  @media (prefers-reduced-motion: reduce) {
    .controls-bar { transition: none; }
  }
</style>
