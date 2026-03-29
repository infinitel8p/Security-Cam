<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl, getMediaMtxUrl } from "../lib/api";

  let containerEl: HTMLDivElement;
  let videoEl: HTMLVideoElement;
  let pc: RTCPeerConnection | null = null;
  let connected = $state(false);
  let error = $state("");
  let recording = $state(false);
  let toggling = $state(false);
  let isFullscreen = $state(false);
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let destroyed = false;

  const STREAM_PATH = "cam";

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
    };

    pc.onconnectionstatechange = () => {
      if (pc?.connectionState === "failed" || pc?.connectionState === "disconnected") {
        connected = false;
        error = "Stream disconnected";
        cleanup();
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(startWebRTC, 3000);
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
      error = "Failed to connect to stream";
      cleanup();
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(startWebRTC, 5000);
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

  async function toggleRecording() {
    toggling = true;
    try {
      const res = await fetch(`${getBackendUrl()}/toggle_recording`, {
        method: "POST",
      });
      const data = await res.json();
      recording = data.message?.toLowerCase().includes("started") ?? false;
    } catch (e) {
      console.error("Failed to toggle recording:", e);
    } finally {
      toggling = false;
    }
  }

  onMount(() => {
    startWebRTC();
  });

  onDestroy(() => {
    destroyed = true;
    clearTimeout(reconnectTimer);
    cleanup();
  });
</script>

<svelte:document on:fullscreenchange={onFullscreenChange} />

<div bind:this={containerEl} class="card overflow-hidden transition-shadow duration-700 {connected ? 'shadow-[0_0_30px_rgba(79,143,247,0.08),var(--shadow-sm)]' : ''}" class:fullscreen={isFullscreen}>
  <!-- Feed -->
  <div class="relative w-full bg-black/80 {isFullscreen ? 'h-full' : 'aspect-video'}">
    <video
      bind:this={videoEl}
      autoplay
      playsinline
      muted
      class="h-full w-full object-cover"
      class:hidden={!connected}
    ></video>

    {#if !connected}
      <div class="absolute inset-0 flex items-center justify-center">
        {#if error}
          <div class="flex flex-col items-center gap-2.5">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-status-warning/10">
              <svg class="h-5 w-5 text-status-warning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <span class="text-sm text-text-secondary">{error}</span>
            <span class="text-xs text-text-muted">Reconnecting...</span>
          </div>
        {:else}
          <div class="flex flex-col items-center gap-2.5">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-accent/10">
              <svg class="h-5 w-5 animate-pulse text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
            </div>
            <span class="text-sm text-text-secondary">Connecting to camera...</span>
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
          <div class="flex items-center gap-2 rounded-lg bg-black/50 px-2.5 py-1.5 backdrop-blur-sm">
            <span class="h-2 w-2 animate-pulse rounded-full bg-status-critical shadow-[0_0_8px_rgba(240,104,104,0.6)]"></span>
            <span class="text-[0.6875rem] font-semibold tracking-wide text-white/90">REC</span>
          </div>
        {:else if connected}
          <div class="flex items-center gap-1.5 rounded-lg bg-black/50 px-2.5 py-1.5 backdrop-blur-sm">
            <span class="h-1.5 w-1.5 rounded-full bg-status-ok shadow-[0_0_6px_rgba(45,212,168,0.5)]"></span>
            <span class="text-[0.6875rem] font-medium tracking-wide text-white/80">LIVE</span>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Controls -->
  <div class="flex items-center justify-between border-t border-border-subtle px-3 py-2 sm:px-4 sm:py-2.5">
    <div class="flex items-center gap-2">
      <svg class="h-4 w-4 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
        <circle cx="12" cy="13" r="4" />
      </svg>
      <span class="hidden text-[0.8125rem] font-medium text-text-secondary sm:inline">Live Feed</span>
    </div>
    <div class="flex items-center gap-1">
      <button
        onclick={toggleRecording}
        disabled={toggling}
        class="flex min-h-[2.75rem] items-center gap-1.5 rounded-lg px-3.5 text-[0.8125rem] font-medium transition-colors duration-150 sm:min-h-0 sm:py-1.5
          {recording
            ? 'bg-status-critical/10 text-status-critical hover:bg-status-critical/15'
            : 'bg-accent/10 text-accent hover:bg-accent/15'}
          disabled:opacity-40"
      >
        {#if recording}
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          Stop
        {:else}
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="6" />
          </svg>
          Record
        {/if}
      </button>

      <button
        onclick={toggleFullscreen}
        class="flex min-h-[2.75rem] min-w-[2.75rem] items-center justify-center rounded-lg text-text-muted transition-colors duration-150 hover:bg-surface-overlay hover:text-text-secondary sm:min-h-0 sm:min-w-0 sm:p-1.5"
        title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
      >
        {#if isFullscreen}
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
          </svg>
        {:else}
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
          </svg>
        {/if}
      </button>
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
</style>
