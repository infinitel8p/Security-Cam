<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getMediaMtxUrl, getHlsUrl } from "../lib/api";
  import { t } from "../i18n";
  import Icon from "./Icon.svelte";
  import cameraIcon from "../icons/camera.svg?raw";
  import alertCircleIcon from "../icons/alert-circle.svg?raw";

  let videoEl: HTMLVideoElement;
  let pc: RTCPeerConnection | null = null;
  let connected = $state(false);
  let error = $state("");
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let destroyed = false;
  let webrtcFails = 0;
  let hlsFails = 0;
  let streamMode: "webrtc" | "hls" = "webrtc";
  const MAX_FAILURES = 3;

  const STREAM_PATH = "cam";

  function startStream() {
    if (destroyed) return;
    if (streamMode === "hls") startHLS();
    else startWebRTC();
  }

  async function startWebRTC() {
    if (destroyed) return;
    error = "";

    pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });

    pc.addTransceiver("video", { direction: "recvonly" });

    pc.ontrack = (ev) => {
      videoEl.srcObject = ev.streams[0];
      connected = true;
      webrtcFails = 0;
      hlsFails = 0;
    };

    pc.onconnectionstatechange = () => {
      if (pc?.connectionState === "failed" || pc?.connectionState === "disconnected") {
        connected = false;
        error = t("error.streamDisconnected");
        webrtcFails++;
        cleanup();
        scheduleRetry();
      }
    };

    try {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const res = await fetch(`${getMediaMtxUrl()}/${STREAM_PATH}/whep`, {
        method: "POST",
        headers: { "Content-Type": "application/sdp" },
        body: offer.sdp,
      });

      if (!res.ok) throw new Error(`WHEP ${res.status}`);
      await pc.setRemoteDescription({ type: "answer", sdp: await res.text() });
    } catch {
      webrtcFails++;
      error = t("error.connectFailed");
      cleanup();
      scheduleRetry();
    }
  }

  function startHLS() {
    if (destroyed) return;
    error = "";
    videoEl.srcObject = null;
    videoEl.src = `${getHlsUrl()}/${STREAM_PATH}/index.m3u8`;
    videoEl.load();
    videoEl.onloadeddata = () => { connected = true; webrtcFails = 0; hlsFails = 0; };
    videoEl.onerror = () => {
      if (destroyed) return;
      connected = false;
      hlsFails++;
      error = t("error.connectFailed");
      scheduleRetry();
    };
  }

  function scheduleRetry() {
    clearTimeout(reconnectTimer);
    if (streamMode === "webrtc" && webrtcFails >= MAX_FAILURES) {
      streamMode = "hls";
      webrtcFails = 0;
      reconnectTimer = setTimeout(startHLS, 1000);
    } else if (streamMode === "hls" && hlsFails >= MAX_FAILURES) {
      streamMode = "webrtc";
      hlsFails = 0;
      reconnectTimer = setTimeout(startWebRTC, 1000);
    } else {
      reconnectTimer = setTimeout(startStream, streamMode === "webrtc" ? 3000 : 5000);
    }
  }

  function cleanup() {
    if (pc) { pc.close(); pc = null; }
  }

  /** Manual retry from the UI */
  export function manualReconnect() {
    connected = false;
    error = "";
    cleanup();
    clearTimeout(reconnectTimer);
    startStream();
  }

  /** Trigger a reconnect after ISP apply (brief delay for MediaMTX restart) */
  export function reconnect() {
    connected = false;
    error = "";
    cleanup();
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(startStream, 2000);
  }

  onMount(() => startStream());

  onDestroy(() => {
    destroyed = true;
    clearTimeout(reconnectTimer);
    cleanup();
  });
</script>

<div class="relative aspect-video overflow-hidden rounded-lg bg-black">
  <video
    bind:this={videoEl}
    autoplay
    playsinline
    muted
    aria-label="Camera preview"
    class="h-full w-full object-contain {connected ? 'animate-video-reveal' : ''}"
    class:hidden={!connected}
  ></video>

  {#if !connected}
    <div class="absolute inset-0 flex flex-col items-center justify-center gap-2.5 bg-black/80">
      {#if error}
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-status-warning/10">
          <Icon icon={alertCircleIcon} class="h-4 w-4 text-status-warning" stroke={2} />
        </div>
        <span class="text-xs text-center text-text-secondary">{error}</span>
        <div class="flex items-center gap-3">
          <span class="text-[0.625rem] text-text-muted">{t("status.reconnecting")}</span>
          <button onclick={manualReconnect} class="text-[0.625rem] font-medium text-accent hover:text-accent-hover">{t("btn.retryNow")}</button>
        </div>
      {:else}
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10">
          <Icon icon={cameraIcon} class="h-4 w-4 text-accent animate-pulse" stroke={2} />
        </div>
        <span class="text-xs text-text-muted">{t("status.connectingToCamera")}</span>
      {/if}
    </div>
  {/if}
</div>
