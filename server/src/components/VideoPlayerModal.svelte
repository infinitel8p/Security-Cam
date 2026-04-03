<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { t } from "../i18n";
  import Icon from "./Icon.svelte";
  import playerPlayIcon from "../icons/player-play.svg?raw";
  import playerPauseIcon from "../icons/player-pause.svg?raw";
  import volumeIcon from "../icons/volume.svg?raw";
  import volumeOffIcon from "../icons/volume-off.svg?raw";
  import maximizeIcon from "../icons/maximize.svg?raw";
  import minimizeIcon from "../icons/minimize.svg?raw";
  import downloadIcon from "../icons/download.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import chevronLeftIcon from "../icons/chevron-left.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";

  interface VideoMeta {
    reason?: string;
    sensor_type?: string;
    started?: string;
    stopped?: string;
    duration_seconds?: number;
  }

  interface Video {
    path: string;
    filename: string;
    date: string;
    time: string;
    timestamp: number;
    meta?: VideoMeta;
    thumbnail?: string;
    sprite?: string;
  }

  interface Props {
    video: Video;
    videos: Video[];
    onclose: () => void;
    onnavigate: (video: Video) => void;
  }

  let { video, videos, onclose, onnavigate }: Props = $props();

  let videoEl: HTMLVideoElement | null = $state(null);
  let containerEl: HTMLDivElement | null = $state(null);
  let wrapperEl: HTMLDivElement | null = $state(null);
  let playing = $state(false);
  let currentTime = $state(0);
  let duration = $state(0);
  let volume = $state(1);
  let muted = $state(false);
  let playbackRate = $state(1);
  let showControls = $state(true);
  let showSpeedMenu = $state(false);
  let isFullscreen = $state(false);
  let seeking = $state(false);
  let loaded = $state(false);
  let hideTimer: ReturnType<typeof setTimeout> | null = null;

  const speeds = [0.5, 1, 2, 4, 8];

  let currentIndex = $derived(videos.findIndex((v) => v.path === video.path));
  let hasPrev = $derived(currentIndex > 0);
  let hasNext = $derived(currentIndex < videos.length - 1);
  let progress = $derived(duration > 0 ? (currentTime / duration) * 100 : 0);

  function streamUrl(path: string): string {
    return `${getBackendUrl()}/stream_video?video_path=${encodeURIComponent(path)}`;
  }

  function thumbnailUrl(path: string): string {
    return `${getBackendUrl()}/thumbnail?video_path=${encodeURIComponent(path)}`;
  }

  function fmtTime(seconds: number): string {
    if (isNaN(seconds) || seconds < 0) return "0:00";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function fmtDate(dateStr: string): string {
    try {
      const d = new Date(dateStr + "T00:00:00");
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return dateStr;
    }
  }

  function fmtTimeOfDay(time: string): string {
    if (!time) return "";
    const [h, m] = time.split(":").map(Number);
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 || 12;
    return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
  }

  function triggerLabel(meta?: VideoMeta): string | null {
    if (!meta?.reason) return null;
    if (meta.reason === "sensor") return meta.sensor_type ?? "Sensor";
    if (meta.reason === "manual") return "Manual";
    return meta.reason;
  }

  // ── Playback ───────────────────────────────────────────────────────────

  function togglePlay() {
    if (!videoEl) return;
    if (videoEl.paused) videoEl.play();
    else videoEl.pause();
  }

  function handleTimeUpdate() {
    if (!videoEl || seeking) return;
    currentTime = videoEl.currentTime;
  }

  function handleLoadedMetadata() {
    if (!videoEl) return;
    duration = videoEl.duration;
    videoEl.playbackRate = playbackRate;
    videoEl.volume = volume;
    videoEl.muted = muted;
    loaded = true;
    videoEl.play();
  }

  function handlePlay() {
    playing = true;
    scheduleHide();
  }

  function handlePause() {
    playing = false;
    showControls = true;
    if (hideTimer) clearTimeout(hideTimer);
  }

  function handleEnded() {
    playing = false;
    showControls = true;
  }

  // ── Seeking ────────────────────────────────────────────────────────────

  let seekRaf: number | null = null;

  function seekTo(clientX: number, bar: HTMLElement) {
    const rect = bar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    if (videoEl) {
      videoEl.currentTime = pct * duration;
      currentTime = videoEl.currentTime;
    }
  }

  function handleSeekStart(e: MouseEvent | TouchEvent) {
    seeking = true;
    const bar = e.currentTarget as HTMLElement;
    const startX = "touches" in e ? e.touches[0].clientX : e.clientX;
    seekTo(startX, bar);

    const moveHandler = (ev: MouseEvent | TouchEvent) => {
      ev.preventDefault();
      const clientX = "touches" in ev ? (ev as TouchEvent).touches[0]?.clientX ?? 0 : (ev as MouseEvent).clientX;
      if (seekRaf !== null) cancelAnimationFrame(seekRaf);
      seekRaf = requestAnimationFrame(() => {
        seekRaf = null;
        seekTo(clientX, bar);
      });
    };
    const upHandler = () => {
      if (seekRaf !== null) { cancelAnimationFrame(seekRaf); seekRaf = null; }
      seeking = false;
      document.removeEventListener("mousemove", moveHandler);
      document.removeEventListener("mouseup", upHandler);
      document.removeEventListener("touchmove", moveHandler as any);
      document.removeEventListener("touchend", upHandler);
    };
    document.addEventListener("mousemove", moveHandler);
    document.addEventListener("mouseup", upHandler);
    document.addEventListener("touchmove", moveHandler as any, { passive: false });
    document.addEventListener("touchend", upHandler);
  }

  // ── Speed ──────────────────────────────────────────────────────────────

  function setSpeed(speed: number) {
    playbackRate = speed;
    if (videoEl) videoEl.playbackRate = speed;
    showSpeedMenu = false;
    scheduleHide();
  }

  // ── Volume ─────────────────────────────────────────────────────────────

  function toggleMute() {
    muted = !muted;
    if (videoEl) videoEl.muted = muted;
  }

  // ── Fullscreen ─────────────────────────────────────────────────────────

  function toggleFullscreen() {
    if (!wrapperEl) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else wrapperEl.requestFullscreen();
  }

  function handleFullscreenChange() {
    isFullscreen = !!document.fullscreenElement;
  }

  // ── Auto-hide controls ─────────────────────────────────────────────────

  function scheduleHide() {
    if (hideTimer) clearTimeout(hideTimer);
    showControls = true;
    if (playing) {
      hideTimer = setTimeout(() => {
        showControls = false;
        showSpeedMenu = false;
      }, 3000);
    }
  }

  function handlePointerMove() {
    scheduleHide();
  }

  // ── Navigation ─────────────────────────────────────────────────────────

  function navigate(direction: "prev" | "next") {
    if (direction === "prev" && hasPrev) onnavigate(videos[currentIndex - 1]);
    else if (direction === "next" && hasNext) onnavigate(videos[currentIndex + 1]);
  }

  function downloadVideo() {
    const a = document.createElement("a");
    a.href = streamUrl(video.path);
    a.download = video.filename;
    a.click();
  }

  // ── Reset on video change ──────────────────────────────────────────────

  $effect(() => {
    video.path; // track dependency
    playbackRate = 1;
    showSpeedMenu = false;
    showControls = true;
    loaded = false;
    currentTime = 0;
    duration = 0;
    playing = false;
  });

  // ── Keyboard ───────────────────────────────────────────────────────────

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      if (showSpeedMenu) { showSpeedMenu = false; return; }
      onclose();
      return;
    }
    if (e.key === " " || e.key === "k") {
      e.preventDefault();
      togglePlay();
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      if (videoEl) videoEl.currentTime = Math.max(0, videoEl.currentTime - 10);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      if (videoEl) videoEl.currentTime = Math.min(duration, videoEl.currentTime + 10);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      volume = Math.min(1, volume + 0.1);
      if (videoEl) videoEl.volume = volume;
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      volume = Math.max(0, volume - 0.1);
      if (videoEl) videoEl.volume = volume;
    } else if (e.key === "f") {
      toggleFullscreen();
    } else if (e.key === "m") {
      toggleMute();
    }
    scheduleHide();
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────

  onMount(() => {
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.body.style.overflow = "hidden";
  });

  onDestroy(() => {
    if (hideTimer) clearTimeout(hideTimer);
    document.removeEventListener("fullscreenchange", handleFullscreenChange);
    document.body.style.overflow = "";
  });
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  bind:this={wrapperEl}
  class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/92 animate-overlay"
  class:cursor-none={!showControls && playing}
  role="dialog"
  aria-modal="true"
  aria-label={t("archive.player")}
  tabindex="-1"
  onkeydown={handleKeydown}
  onpointermove={handlePointerMove}
>
  <!-- Background click to close -->
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <div class="absolute inset-0" onclick={onclose}></div>

  <!-- Close button -->
  <button
    onclick={onclose}
    class="absolute right-3 top-3 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white/70 backdrop-blur-sm transition-all hover:bg-white/20 hover:text-white {showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}"
    aria-label={t("btn.close")}
  >
    <Icon icon={xIcon} class="h-5 w-5" />
  </button>

  <!-- Prev/Next arrows -->
  {#if hasPrev}
    <button
      onclick={() => navigate("prev")}
      class="absolute left-3 top-1/2 z-20 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white/70 backdrop-blur-sm transition-all hover:bg-white/20 hover:text-white sm:left-6 {showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}"
      aria-label={t("archive.prevVideo")}
    >
      <Icon icon={chevronLeftIcon} class="h-5 w-5" />
    </button>
  {/if}
  {#if hasNext}
    <button
      onclick={() => navigate("next")}
      class="absolute right-3 top-1/2 z-20 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white/70 backdrop-blur-sm transition-all hover:bg-white/20 hover:text-white sm:right-6 {showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}"
      aria-label={t("archive.nextVideo")}
    >
      <Icon icon={chevronRightIcon} class="h-5 w-5" />
    </button>
  {/if}

  <!-- Player container -->
  <div
    bind:this={containerEl}
    class="relative z-10 w-full max-w-5xl px-4 sm:px-14"
    onclick={(e) => { if (e.target === containerEl) togglePlay(); }}
  >
    {#key video.path}
      <!-- Video element -->
      <video
        bind:this={videoEl}
        src={streamUrl(video.path)}
        poster={video.thumbnail ? thumbnailUrl(video.path) : undefined}
        class="w-full rounded-xl bg-black aspect-video object-contain cursor-pointer"
        onclick={togglePlay}
        ontimeupdate={handleTimeUpdate}
        onloadedmetadata={handleLoadedMetadata}
        onplay={handlePlay}
        onpause={handlePause}
        onended={handleEnded}
        preload="auto"
        playsinline
      ></video>
    {/key}

    <!-- Big center play button (when paused and controls visible) -->
    {#if !playing && showControls && loaded}
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none" style="top: 0; bottom: 0;">
        <div
          class="flex h-16 w-16 items-center justify-center rounded-full bg-black/50 text-white/90 backdrop-blur-sm pointer-events-auto cursor-pointer transition-transform duration-200 hover:scale-110"
          onclick={togglePlay}
        >
          <Icon icon={playerPlayIcon} class="h-8 w-8 ml-1" />
        </div>
      </div>
    {/if}

    <!-- Controls overlay -->
    <div
      class="absolute inset-x-0 bottom-0 rounded-b-xl bg-gradient-to-t from-black/80 via-black/40 to-transparent px-4 pb-3 pt-16 transition-opacity duration-300 {showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}"
    >
      <!-- Seek bar -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div
        class="group/seek relative mb-3 h-1 cursor-pointer rounded-full bg-white/20 transition-[height] duration-150 hover:h-1.5"
        onmousedown={handleSeekStart}
        ontouchstart={handleSeekStart}
        role="slider"
        aria-label={t("archive.seek")}
        aria-valuenow={Math.round(currentTime)}
        aria-valuemin={0}
        aria-valuemax={Math.round(duration)}
        tabindex="0"
      >
        <div
          class="absolute inset-y-0 left-0 rounded-full bg-accent"
          style="width: {progress}%"
        ></div>
        <div
          class="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-md opacity-0 transition-opacity group-hover/seek:opacity-100"
          style="left: {progress}%"
        ></div>
      </div>

      <!-- Controls row -->
      <div class="flex items-center gap-2 sm:gap-3">
        <!-- Play/Pause -->
        <button
          onclick={togglePlay}
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white/90 transition-colors hover:bg-white/10 hover:text-white"
          aria-label={playing ? t("archive.pause") : t("archive.play")}
        >
          <Icon icon={playing ? playerPauseIcon : playerPlayIcon} class="h-5 w-5" />
        </button>

        <!-- Time -->
        <span class="shrink-0 text-[0.75rem] font-medium tabular-nums text-white/80">
          {fmtTime(currentTime)}<span class="text-white/40"> / {fmtTime(duration)}</span>
        </span>

        <div class="flex-1"></div>

        <!-- Speed selector -->
        <div class="relative">
          <button
            onclick={(e) => { e.stopPropagation(); showSpeedMenu = !showSpeedMenu; }}
            class="flex h-9 shrink-0 items-center justify-center rounded-lg px-2.5 text-[0.75rem] font-semibold tabular-nums transition-colors hover:bg-white/10 {playbackRate !== 1 ? 'text-accent' : 'text-white/80'}"
            aria-label={t("archive.speed")}
          >
            {playbackRate}x
          </button>
          {#if showSpeedMenu}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
              class="animate-dropdown absolute bottom-full right-0 mb-2 overflow-hidden rounded-xl border border-white/10 bg-surface-overlay/95 py-1 shadow-[var(--shadow-lg)] backdrop-blur-md"
              onclick={(e) => e.stopPropagation()}
            >
              {#each speeds as speed}
                <button
                  onclick={() => setSpeed(speed)}
                  class="flex w-full items-center px-4 py-1.5 text-[0.8125rem] tabular-nums transition-colors hover:bg-white/10 {playbackRate === speed ? 'text-accent font-semibold' : 'text-white/80'}"
                >
                  {speed}x
                </button>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Volume -->
        <button
          onclick={toggleMute}
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white/80 transition-colors hover:bg-white/10 hover:text-white"
          aria-label={muted ? t("archive.unmute") : t("archive.mute")}
        >
          <Icon icon={muted || volume === 0 ? volumeOffIcon : volumeIcon} class="h-[1.125rem] w-[1.125rem]" />
        </button>

        <!-- Fullscreen -->
        <button
          onclick={toggleFullscreen}
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white/80 transition-colors hover:bg-white/10 hover:text-white"
          aria-label={isFullscreen ? t("btn.exitFullscreen") : t("btn.fullscreen")}
        >
          <Icon icon={isFullscreen ? minimizeIcon : maximizeIcon} class="h-[1.125rem] w-[1.125rem]" />
        </button>

        <!-- Download -->
        <button
          onclick={downloadVideo}
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white/80 transition-colors hover:bg-white/10 hover:text-white"
          aria-label={t("btn.download")}
        >
          <Icon icon={downloadIcon} class="h-[1.125rem] w-[1.125rem]" />
        </button>
      </div>
    </div>
  </div>

  <!-- Video info -->
  <div class="relative z-10 mt-3 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 px-4 animate-in stagger-2 {showControls ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300">
    {#if videos.length > 1}
      <span class="text-[0.625rem] tabular-nums text-white/40">{currentIndex + 1} / {videos.length}</span>
    {/if}
    <p class="text-[0.8125rem] font-medium text-white/90">{video.filename}</p>
    {#if video.date}
      <span class="text-[0.75rem] text-white/50">{fmtDate(video.date)}</span>
    {/if}
    {#if video.time}
      <span class="text-[0.75rem] text-white/50">{fmtTimeOfDay(video.time)}</span>
    {/if}
    {#if triggerLabel(video.meta)}
      <span class="rounded-full px-1.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wide
        {video.meta?.reason === 'sensor' ? 'bg-status-warning/20 text-status-warning' : 'bg-accent/20 text-accent'}">
        {triggerLabel(video.meta)}
      </span>
    {/if}
  </div>
</div>
