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

  const STREAM_PATH = "cam";

  async function startWebRTC() {
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
        // Retry after a short delay
        setTimeout(startWebRTC, 3000);
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
      setTimeout(startWebRTC, 5000);
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
    cleanup();
  });
</script>

<svelte:document on:fullscreenchange={onFullscreenChange} />

<div bind:this={containerEl} class="card overflow-hidden" class:fullscreen={isFullscreen}>
  <!-- Feed -->
  <div class="relative w-full bg-black {isFullscreen ? 'h-full' : 'aspect-[4/3]'}">
    <video
      bind:this={videoEl}
      autoplay
      playsinline
      muted
      class="h-full w-full object-cover"
      class:hidden={!connected}
    ></video>

    {#if !connected}
      <div class="absolute inset-0 flex h-full items-center justify-center text-text-muted">
        {#if error}
          <div class="flex flex-col items-center gap-2">
            <svg class="h-5 w-5 text-status-warning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span class="text-sm">{error}</span>
            <span class="text-xs text-text-muted">Reconnecting...</span>
          </div>
        {:else}
          <div class="flex items-center">
            <svg class="mr-2 h-5 w-5 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            Connecting...
          </div>
        {/if}
      </div>
    {/if}

    <!-- Recording indicator -->
    {#if recording}
      <div class="absolute right-3 top-3 flex items-center gap-2 rounded-lg bg-black/60 px-3 py-1.5 backdrop-blur-md">
        <span class="h-2 w-2 animate-pulse rounded-full bg-status-critical shadow-[0_0_8px_rgba(255,61,87,0.6)]"></span>
        <span class="text-xs font-semibold tracking-wide text-status-critical">REC</span>
      </div>
    {/if}

    <!-- Live badge -->
    {#if connected && !recording}
      <div class="absolute right-3 top-3 flex items-center gap-1.5 rounded-lg bg-black/60 px-2.5 py-1 backdrop-blur-md">
        <span class="h-1.5 w-1.5 rounded-full bg-status-ok shadow-[0_0_6px_rgba(0,230,118,0.5)]"></span>
        <span class="text-[11px] font-semibold tracking-wide text-white/80">LIVE</span>
      </div>
    {/if}
  </div>

  <!-- Controls -->
  <div class="flex items-center justify-between border-t border-border-subtle px-3 py-2.5 sm:px-5 sm:py-3.5">
    <div class="flex items-center gap-2">
      <svg class="h-4 w-4 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
        <circle cx="12" cy="13" r="4" />
      </svg>
      <span class="text-sm font-medium text-text-secondary">Live Feed</span>
    </div>
    <div class="flex items-center gap-2">
      <button
        onclick={toggleRecording}
        disabled={toggling}
        class="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200
          {recording
            ? 'bg-status-critical/12 text-status-critical shadow-[inset_0_0_0_1px_rgba(255,61,87,0.2)] hover:bg-status-critical/20'
            : 'bg-accent/12 text-accent shadow-[inset_0_0_0_1px_rgba(0,111,255,0.2)] hover:bg-accent/20'}
          disabled:opacity-50"
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
        class="flex items-center justify-center rounded-xl p-2 text-text-muted transition-all duration-200 hover:bg-white/5 hover:text-text-primary"
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
