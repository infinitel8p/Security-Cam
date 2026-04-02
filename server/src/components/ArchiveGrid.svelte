<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { sseClient } from "../lib/sse";
  import { markSeen } from "../lib/archive-badge";
  import toast from "svelte-5-french-toast";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import searchIcon from "../icons/search.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import filterIcon from "../icons/filter.svg?raw";
  import arrowDownIcon from "../icons/arrow-down.svg?raw";
  import layoutGridIcon from "../icons/layout-grid.svg?raw";
  import listIcon from "../icons/list.svg?raw";
  import downloadIcon from "../icons/download.svg?raw";
  import trashIcon from "../icons/trash.svg?raw";
  import videoIcon from "../icons/video.svg?raw";
  import alertCircleIcon from "../icons/alert-circle.svg?raw";
  import checkIcon from "../icons/check.svg?raw";
  import chevronDownIcon from "../icons/chevron-down.svg?raw";
  import cameraBoltIcon from "../icons/camera-bolt.svg?raw";
  import chevronLeftIcon from "../icons/chevron-left.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";
  import clockIcon from "../icons/clock.svg?raw";

  let deleteButtonEl: HTMLButtonElement | null = null;

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

  type SortMode = "newest" | "oldest" | "name";
  type FilterMode = "all" | "today" | "week" | "month";
  type ViewMode = "grid" | "list";

  interface Snapshot {
    path: string;
    filename: string;
    date: string;
    time: string;
    size: number;
  }

  let allVideos: Video[] = $state([]);
  let allSnapshots: Snapshot[] = $state([]);
  let snapshotsOpen = $state(false);
  let snapshotsExpanded = $state(false);
  let snapLimit = $state(4);

  let resizeTimer: ReturnType<typeof setTimeout> | null = null;

  function updateSnapLimit() {
    if (typeof window === "undefined") return;
    const w = window.innerWidth;
    if (w >= 1024) snapLimit = 5;       // lg: grid-cols-5 → 1 row
    else if (w >= 768) snapLimit = 4;   // md: grid-cols-4 → 1 row
    else if (w >= 640) snapLimit = 6;   // sm: grid-cols-3 → 2 rows
    else snapLimit = 4;                 // base: grid-cols-2 → 2 rows
  }

  function debouncedSnapLimit() {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(updateSnapLimit, 250);
  }
  let deletingSnapshot: string | null = $state(null);
  let expandedSnap: Snapshot | null = $state(null);

  interface Timelapse {
    path: string;
    date: string;
    size: number;
    thumbnail?: string;
  }
  let allTimelapses: Timelapse[] = $state([]);
  let timelapsesOpen = $state(false);
  let timelapsesExpanded = $state(false);
  let deletingTimelapse: string | null = $state(null);
  let loading = $state(true);
  let error = $state(false);
  let deleteTarget: Video | null = $state(null);
  let deleting = $state(false);
  let search = $state("");
  let sortMode: SortMode = $state("newest");
  let filterMode: FilterMode = $state("all");
  let viewMode: ViewMode = $state("grid");
  let showSortMenu = $state(false);
  let showFilterMenu = $state(false);
  let lastSeenTs = $state(0);

  function parseEntry(entry: { path: string; meta?: VideoMeta; thumbnail?: string; sprite?: string }): Video {
    const filepath = entry.path;
    const filename = filepath.split("/").pop() ?? filepath;
    const match = filename.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    const date = match ? `${match[1]}-${match[2]}-${match[3]}` : "Unknown";
    const time = match ? `${match[4]}:${match[5]}:${match[6]}` : "";
    const timestamp = match
      ? new Date(`${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}`).getTime()
      : 0;
    return { path: filepath, filename, date, time, timestamp, meta: entry.meta, thumbnail: entry.thumbnail, sprite: entry.sprite };
  }

  function formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    if (m < 60) return `${m}m ${s}s`;
    const h = Math.floor(m / 60);
    return `${h}h ${m % 60}m`;
  }

  function triggerLabel(meta?: VideoMeta): string | null {
    if (!meta?.reason) return null;
    if (meta.reason === "sensor") return meta.sensor_type ?? "Sensor";
    if (meta.reason === "manual") return "Manual";
    return meta.reason;
  }

  const filteredVideos = $derived.by(() => {
    let result = allVideos;

    // Text search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (v) => v.filename.toLowerCase().includes(q) || v.date.includes(q) || v.time.includes(q)
          || (triggerLabel(v.meta)?.toLowerCase().includes(q) ?? false),
      );
    }

    // Date filter
    if (filterMode !== "all") {
      const now = new Date();
      const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
      const msPerDay = 86400000;
      result = result.filter((v) => {
        if (filterMode === "today") return v.timestamp >= startOfDay;
        if (filterMode === "week") return v.timestamp >= startOfDay - 6 * msPerDay;
        if (filterMode === "month") return v.timestamp >= startOfDay - 29 * msPerDay;
        return true;
      });
    }

    // Sort
    const sorted = [...result];
    if (sortMode === "newest") sorted.sort((a, b) => b.timestamp - a.timestamp);
    else if (sortMode === "oldest") sorted.sort((a, b) => a.timestamp - b.timestamp);
    else sorted.sort((a, b) => a.filename.localeCompare(b.filename));

    return sorted;
  });

  // Group by date
  const groupedVideos = $derived.by(() => {
    const groups: { label: string; date: string; videos: Video[] }[] = [];
    const map = new Map<string, Video[]>();
    for (const v of filteredVideos) {
      const existing = map.get(v.date);
      if (existing) {
        existing.push(v);
      } else {
        const arr = [v];
        map.set(v.date, arr);
        groups.push({ label: formatDateHeading(v.date), date: v.date, videos: arr });
      }
    }
    return groups;
  });

  async function fetchArchive() {
    loading = true;
    error = false;
    try {
      const res = await fetch(`${getBackendUrl()}/archive`);
      if (!res.ok) throw new Error();
      const entries: { path: string; meta?: VideoMeta }[] = await res.json();
      allVideos = entries.map(parseEntry);
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  async function fetchSnapshots() {
    try {
      const res = await fetch(`${getBackendUrl()}/snapshots`);
      if (!res.ok) return;
      const entries: { path: string; size: number }[] = await res.json();
      allSnapshots = entries.map((s) => {
        const filename = s.path.split("/").pop() ?? s.path;
        const match = filename.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
        const date = match ? `${match[1]}-${match[2]}-${match[3]}` : "";
        const time = match ? `${match[4]}:${match[5]}:${match[6]}` : "";
        return { ...s, filename, date, time };
      });
      // Auto-open if new snapshots since last visit
      if (lastSeenTs > 0 && allSnapshots.some((s) => new Date(`${s.date}T${s.time}`).getTime() > lastSeenTs)) {
        snapshotsOpen = true;
      }
    } catch {
      // Non-critical
    }
  }

  function snapshotUrl(path: string): string {
    return `${getBackendUrl()}/snapshot_image?path=${encodeURIComponent(path)}`;
  }

  async function deleteSnapshot(snapshot: Snapshot) {
    deletingSnapshot = snapshot.path;
    try {
      const res = await fetch(`${getBackendUrl()}/delete_snapshot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ snapshot_path: snapshot.path }),
      });
      if (res.ok) {
        allSnapshots = allSnapshots.filter((s) => s.path !== snapshot.path);
        toast.success(t("toast.snapshotDeleted"));
      } else {
        toast.error(t("toast.deleteSnapshotFailed"));
      }
    } catch {
      toast.error(t("toast.deleteSnapshotFailed"));
    } finally {
      deletingSnapshot = null;
    }
  }

  function downloadSnapshot(snapshot: Snapshot) {
    const a = document.createElement("a");
    a.href = snapshotUrl(snapshot.path);
    a.download = snapshot.filename;
    a.click();
  }

  async function fetchTimelapses() {
    try {
      const res = await fetch(`${getBackendUrl()}/timelapse`);
      if (!res.ok) return;
      allTimelapses = await res.json();
      // Auto-open if new timelapses since last visit
      if (lastSeenTs > 0 && allTimelapses.some((tl) => new Date(tl.date).getTime() > lastSeenTs)) {
        timelapsesOpen = true;
      }
    } catch {
      // Non-critical
    }
  }

  function timelapseVideoUrl(path: string): string {
    return `${getBackendUrl()}/timelapse/video?path=${encodeURIComponent(path)}`;
  }

  function timelapseThumbnailUrl(path: string): string {
    return `${getBackendUrl()}/timelapse/thumbnail?path=${encodeURIComponent(path)}`;
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function deleteTimelapse(tl: Timelapse) {
    deletingTimelapse = tl.path;
    try {
      const res = await fetch(`${getBackendUrl()}/timelapse/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: tl.path }),
      });
      if (res.ok) {
        allTimelapses = allTimelapses.filter((t) => t.path !== tl.path);
        toast.success(t("toast.timelapseDeleted"));
      } else {
        toast.error(t("toast.deleteTimelapseFailed"));
      }
    } catch {
      toast.error(t("toast.deleteTimelapseFailed"));
    } finally {
      deletingTimelapse = null;
    }
  }

  function downloadTimelapse(tl: Timelapse) {
    const a = document.createElement("a");
    a.href = timelapseVideoUrl(tl.path);
    a.download = `timelapse_${tl.date}.mp4`;
    a.click();
  }

  function isNewRecording(video: Video): boolean {
    return lastSeenTs > 0 && video.timestamp > lastSeenTs;
  }

  function isNewSnapshot(snap: Snapshot): boolean {
    if (lastSeenTs <= 0 || !snap.date || !snap.time) return false;
    return new Date(`${snap.date}T${snap.time}`).getTime() > lastSeenTs;
  }

  function isNewTimelapse(tl: Timelapse): boolean {
    if (lastSeenTs <= 0 || !tl.date) return false;
    return new Date(tl.date).getTime() > lastSeenTs;
  }

  let newSnapshotCount = $derived(
    lastSeenTs > 0 ? allSnapshots.filter((s) => new Date(`${s.date}T${s.time}`).getTime() > lastSeenTs).length : 0
  );
  let newTimelapseCount = $derived(
    lastSeenTs > 0 ? allTimelapses.filter((tl) => new Date(tl.date).getTime() > lastSeenTs).length : 0
  );

  let unsubArchiveUpdate: (() => void) | null = null;

  onMount(() => {
    initLocale();
    updateSnapLimit();
    window.addEventListener("resize", debouncedSnapLimit);
    // Read the last-seen timestamp before marking as seen
    const stored = localStorage.getItem("lastSeenArchive");
    lastSeenTs = stored ? new Date(stored).getTime() : 0;
    fetchArchive();
    fetchSnapshots();
    fetchTimelapses();
    // Mark archive as seen (clears the nav badge)
    markSeen();

    // Re-fetch archive when sprites/thumbnails are generated (async after recording stops)
    const sse = sseClient();
    unsubArchiveUpdate = sse.on("archive_updated", () => {
      fetchArchive();
    });

    return () => {
      window.removeEventListener("resize", debouncedSnapLimit);
      if (resizeTimer) clearTimeout(resizeTimer);
    };
  });

  onDestroy(() => {
    unsubArchiveUpdate?.();
  });

  function streamUrl(path: string): string {
    return `${getBackendUrl()}/stream_video?video_path=${encodeURIComponent(path)}&cache_buster=${Date.now()}`;
  }

  function thumbnailUrl(path: string): string {
    return `${getBackendUrl()}/thumbnail?video_path=${encodeURIComponent(path)}`;
  }

  function spriteUrl(path: string): string {
    return `${getBackendUrl()}/sprite?video_path=${encodeURIComponent(path)}`;
  }

  // Sprite hover-scrub state
  const SPRITE_FRAMES = 10;
  let hoverVideo: string | null = $state(null);
  let hoverFrame: number = $state(0);

  function handleSpriteHover(e: MouseEvent, video: Video) {
    if (!video.sprite) return;
    hoverVideo = video.path;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    hoverFrame = Math.min(SPRITE_FRAMES - 1, Math.max(0, Math.floor(pct * SPRITE_FRAMES)));
  }

  function handleSpriteLeave() {
    hoverVideo = null;
  }

  // Preload sprite images when cards enter viewport
  function preloadSprite(node: HTMLElement, src: string | undefined) {
    if (!src) return { destroy: () => {} };
    let observer: IntersectionObserver | null = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          const img = new Image();
          img.src = src;
          observer?.disconnect();
          observer = null;
        }
      },
      { rootMargin: "400px" },
    );
    observer.observe(node);
    return { destroy: () => observer?.disconnect() };
  }

  function downloadVideo(video: Video) {
    const a = document.createElement("a");
    a.href = streamUrl(video.path);
    a.download = video.filename;
    a.click();
  }

  function confirmDelete() {
    if (!deleteTarget) return;
    deleting = true;
    const target = deleteTarget;

    toast.promise(
      (async () => {
        const res = await fetch(`${getBackendUrl()}/delete_video`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_path: target.path }),
        });
        if (!res.ok) throw new Error("Server returned an error");
        allVideos = allVideos.filter((v) => v.path !== target.path);
        deleteTarget = null;
      })(),
      {
        loading: t("status.deleting"),
        success: t("toast.recordingDeleted"),
        error: t("toast.deleteRecordingFailed"),
      },
    ).finally(() => { deleting = false; });
  }

  function openDeleteDialog(video: Video, btnEl: HTMLButtonElement) {
    if (document.startViewTransition) {
      // Tag the button as the morph source
      btnEl.style.viewTransitionName = "delete-morph";
      const transition = document.startViewTransition(() => {
        btnEl.style.viewTransitionName = "";
        deleteTarget = video;
      });
      transition.finished.then(() => {
        btnEl.style.viewTransitionName = "";
      });
    } else {
      deleteTarget = video;
    }
  }

  function closeDeleteDialog() {
    if (document.startViewTransition) {
      document.startViewTransition(() => {
        deleteTarget = null;
      });
    } else {
      deleteTarget = null;
    }
  }

  function formatDateHeading(dateStr: string): string {
    try {
      const d = new Date(dateStr + "T00:00:00");
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
      const diffDays = Math.round((today.getTime() - target.getTime()) / 86400000);

      if (diffDays === 0) return "Today";
      if (diffDays === 1) return "Yesterday";
      if (diffDays < 7) return d.toLocaleDateString("en-US", { weekday: "long" });
      return d.toLocaleDateString("en-US", { weekday: "short", month: "long", day: "numeric", year: "numeric" });
    } catch {
      return dateStr;
    }
  }

  function formatTime(time: string): string {
    if (!time) return "";
    const [h, m, s] = time.split(":").map(Number);
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 || 12;
    return `${h12}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")} ${ampm}`;
  }

  function formatDate(dateStr: string): string {
    try {
      const d = new Date(dateStr + "T00:00:00");
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return dateStr;
    }
  }

  const sortOptions: SortMode[] = ["newest", "oldest", "name"];
  const filterOptions: FilterMode[] = ["all", "today", "week", "month"];
  const sortLabels: Record<SortMode, string> = { newest: t("sort.newestFirst"), oldest: t("sort.oldestFirst"), name: t("sort.name") };
  const filterLabels: Record<FilterMode, string> = { all: t("filter.allTime"), today: t("filter.today"), week: t("filter.thisWeek"), month: t("filter.thisMonth") };

  // Close dropdowns on outside click
  function handleGlobalClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest("[data-dropdown]")) {
      showSortMenu = false;
      showFilterMenu = false;
    }
  }

  // Lazy-load video metadata only when card scrolls into view
  function lazyVideo(node: HTMLVideoElement) {
    const src = node.dataset.src!;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          node.src = src;
          node.preload = "metadata";
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return { destroy: () => observer.disconnect() };
  }
</script>

<svelte:window on:click={handleGlobalClick} />

<!-- Snapshots section -->
{#if allSnapshots.length > 0}
  <div class="card overflow-hidden mb-5">
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <button
      onclick={() => { snapshotsOpen = !snapshotsOpen; }}
      class="flex w-full items-center gap-2.5 px-4 py-3 text-left transition-colors hover:bg-surface-overlay"
    >
      <Icon
        icon={chevronRightIcon}
        class="h-4 w-4 text-text-muted transition-transform duration-200 {snapshotsOpen ? 'rotate-90' : ''}"
      />
      <Icon icon={cameraBoltIcon} class="h-4 w-4 text-text-muted" />
      <span class="text-[0.8125rem] font-medium text-text-primary">
        {t("archive.snapshots")}
      </span>
      <span class="rounded-md bg-surface-overlay px-1.5 py-0.5 text-[0.625rem] font-semibold tabular-nums text-text-muted">
        {allSnapshots.length}
      </span>
      {#if newSnapshotCount > 0 && !snapshotsOpen}
        <span class="rounded-md bg-status-critical/10 px-1.5 py-0.5 text-[0.625rem] font-semibold tabular-nums text-status-critical">
          {newSnapshotCount} NEW
        </span>
      {/if}
    </button>

    {#if snapshotsOpen}
      {@const visibleSnaps = snapshotsExpanded ? allSnapshots : allSnapshots.slice(0, snapLimit)}
      {@const hasMore = allSnapshots.length > snapLimit}
      <div class="animate-slide-down border-t border-border-subtle px-4 py-3">
        <div class="grid grid-cols-2 gap-2.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {#each visibleSnaps as snap}
            <div class="group relative overflow-hidden rounded-lg border border-border-subtle bg-black/40 transition-transform duration-200 hover:scale-[1.02]">
              <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
              <img
                src={snapshotUrl(snap.path)}
                alt={snap.filename}
                class="aspect-video w-full cursor-zoom-in object-cover"
                loading="lazy"
                onclick={() => expandedSnap = snap}
                onkeydown={(e) => { if (e.key === 'Enter') expandedSnap = snap; }}
                tabindex="0"
                role="button"
              />
              <!-- Date/time badge -->
              <div class="pointer-events-none absolute left-1.5 top-1.5 flex items-center gap-1">
                <span class="rounded bg-black/60 px-1.5 py-0.5 text-[0.5625rem] font-medium tabular-nums text-white/90 backdrop-blur-sm">
                  {snap.time}
                </span>
                {#if isNewSnapshot(snap)}
                  <span class="animate-pop rounded-full bg-status-critical/90 px-1.5 py-0.5 text-[0.5rem] font-bold uppercase text-white backdrop-blur-sm">
                    {t("badge.new")}
                  </span>
                {/if}
              </div>
              <!-- Actions (visible on hover) -->
              <div class="absolute bottom-0 left-0 right-0 flex items-center justify-end gap-1 bg-gradient-to-t from-black/60 to-transparent px-1.5 py-1.5 sm:opacity-0 sm:transition-opacity sm:group-hover:opacity-100">
                <button
                  onclick={() => downloadSnapshot(snap)}
                  class="flex h-7 w-7 items-center justify-center rounded-md bg-black/40 text-white/80 backdrop-blur-sm transition-colors hover:bg-black/60 hover:text-white"
                  title={t("btn.download")}
                >
                  <Icon icon={downloadIcon} class="h-3.5 w-3.5" />
                </button>
                <button
                  onclick={() => deleteSnapshot(snap)}
                  disabled={deletingSnapshot === snap.path}
                  class="flex h-7 w-7 items-center justify-center rounded-md bg-black/40 text-white/80 backdrop-blur-sm transition-colors hover:bg-status-critical/60 hover:text-white disabled:opacity-40"
                  title={t("btn.delete")}
                >
                  <Icon icon={trashIcon} class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          {/each}
        </div>
        {#if hasMore}
          <button
            onclick={() => snapshotsExpanded = !snapshotsExpanded}
            class="mt-2.5 w-full rounded-lg py-1.5 text-[0.75rem] font-medium text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
          >
            {snapshotsExpanded ? t("btn.showLess") : `${t("btn.showMore")} (${allSnapshots.length - snapLimit})`}
          </button>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<!-- Timelapse section -->
{#if allTimelapses.length > 0}
  <div class="card overflow-hidden mb-5">
    <button
      onclick={() => { timelapsesOpen = !timelapsesOpen; }}
      class="flex w-full items-center gap-2.5 px-4 py-3 text-left transition-colors hover:bg-surface-overlay"
    >
      <Icon
        icon={chevronRightIcon}
        class="h-4 w-4 text-text-muted transition-transform duration-200 {timelapsesOpen ? 'rotate-90' : ''}"
      />
      <Icon icon={clockIcon} class="h-4 w-4 text-text-muted" />
      <span class="text-[0.8125rem] font-medium text-text-primary">
        {t("archive.timelapse")}
      </span>
      <span class="rounded-md bg-surface-overlay px-1.5 py-0.5 text-[0.625rem] font-semibold tabular-nums text-text-muted">
        {allTimelapses.length}
      </span>
      {#if newTimelapseCount > 0 && !timelapsesOpen}
        <span class="rounded-md bg-status-critical/10 px-1.5 py-0.5 text-[0.625rem] font-semibold tabular-nums text-status-critical">
          {newTimelapseCount} NEW
        </span>
      {/if}
    </button>

    {#if timelapsesOpen}
      {@const TL_LIMIT = 3}
      {@const visibleTimelapses = timelapsesExpanded ? allTimelapses : allTimelapses.slice(0, TL_LIMIT)}
      {@const hasMoreTl = allTimelapses.length > TL_LIMIT}
      <div class="animate-slide-down border-t border-border-subtle px-4 py-3">
        <div class="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
          {#each visibleTimelapses as tl}
            <div class="group overflow-hidden rounded-lg border border-border-subtle bg-surface-overlay">
              <video
                src={timelapseVideoUrl(tl.path)}
                poster={tl.thumbnail ? timelapseThumbnailUrl(tl.path) : undefined}
                class="aspect-video w-full object-contain bg-black/60"
                controls
                preload="none"
              ></video>
              <div class="flex items-center justify-between px-3 py-2">
                <div>
                  <p class="text-[0.8125rem] font-medium text-text-primary">{tl.date}</p>
                  <p class="text-[0.625rem] text-text-muted">{formatBytes(tl.size)}</p>
                </div>
                <div class="flex items-center gap-1">
                  <button
                    onclick={() => downloadTimelapse(tl)}
                    class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-surface-raised hover:text-text-secondary"
                    title={t("btn.download")}
                  >
                    <Icon icon={downloadIcon} class="h-4 w-4" />
                  </button>
                  <button
                    onclick={() => deleteTimelapse(tl)}
                    disabled={deletingTimelapse === tl.path}
                    class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-status-critical/8 hover:text-status-critical disabled:opacity-40"
                    title={t("btn.delete")}
                  >
                    <Icon icon={trashIcon} class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
        {#if hasMoreTl}
          <button
            onclick={() => timelapsesExpanded = !timelapsesExpanded}
            class="mt-2.5 w-full rounded-lg py-1.5 text-[0.75rem] font-medium text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
          >
            {timelapsesExpanded ? t("btn.showLess") : `${t("btn.showMore")} (${allTimelapses.length - TL_LIMIT})`}
          </button>
        {/if}
      </div>
    {/if}
  </div>
{/if}

{#if loading}
  <div class="space-y-4 animate-in">
    <!-- Skeleton toolbar -->
    <div class="flex gap-2">
      {#each Array(3) as _}
        <div class="skeleton h-9 w-24 rounded-lg"></div>
      {/each}
    </div>
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {#each Array(6) as _, i}
        <div class="card overflow-hidden animate-in" style="animation-delay: {60 + i * 50}ms">
          <div class="skeleton aspect-video rounded-none"></div>
          <div class="p-3.5">
            <div class="skeleton h-4 w-28"></div>
            <div class="skeleton mt-2 h-3 w-16"></div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{:else if error}
  <div class="card px-6 py-16 text-center">
    <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-status-critical/8">
      <Icon icon={alertCircleIcon} class="h-5 w-5 text-status-critical" stroke={1.5} />
    </div>
    <p class="mt-3 text-[0.8125rem] text-text-secondary">{t("error.archive")}</p>
    <p class="mt-1 text-[0.8125rem] text-text-muted">{t("error.checkBackend")}</p>
    <button onclick={fetchArchive} class="mt-3 text-[0.8125rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
  </div>
{:else if allVideos.length === 0}
  <div class="card px-6 py-16 text-center">
    <div class="animate-float mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-overlay">
      <Icon icon={videoIcon} class="h-6 w-6 text-text-muted" stroke={1.5} />
    </div>
    <p class="mt-4 text-sm font-medium text-text-secondary">{t("empty.archive")}</p>
    <p class="mt-1 text-[0.8125rem] text-text-muted">{t("empty.archiveDesc")}</p>
  </div>
{:else}
  <!-- Toolbar -->
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-3">
    <!-- Search -->
    <div class="relative max-w-xs flex-1">
      <Icon icon={searchIcon} class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      <input
        type="text"
        bind:value={search}
        placeholder={t("input.searchRecordings")}
        class="h-9 w-full rounded-lg border border-border-subtle bg-surface-raised pl-9 pr-3 text-[0.8125rem] text-text-primary placeholder:text-text-muted transition-colors focus:border-accent/40 focus:outline-none focus:ring-1 focus:ring-accent/20"
      />
      {#if search}
        <button
          onclick={() => (search = "")}
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-text-muted hover:text-text-secondary"
          aria-label="Clear search"
        >
          <Icon icon={xIcon} class="h-3.5 w-3.5" />
        </button>
      {/if}
    </div>

    <div class="flex items-center gap-2">
      <!-- Filter dropdown -->
      <div class="relative" data-dropdown>
        <button
          onclick={(e) => { e.stopPropagation(); showFilterMenu = !showFilterMenu; showSortMenu = false; }}
          class="flex h-9 items-center gap-1.5 rounded-lg border bg-surface-raised px-3 text-[0.8125rem] transition-colors hover:border-border-default hover:text-text-primary {filterMode !== 'all' ? 'border-accent/30 text-accent' : 'border-border-subtle text-text-secondary'}"
        >
          <Icon icon={filterIcon} class="h-3.5 w-3.5" />
          {filterLabels[filterMode]}
          <Icon icon={chevronDownIcon} class="h-3 w-3 opacity-50" />
        </button>
        {#if showFilterMenu}
          <div class="animate-dropdown absolute left-0 top-full z-20 mt-1.5 w-40 overflow-hidden rounded-xl border border-border-subtle bg-surface-raised shadow-[var(--shadow-md)]">
            {#each filterOptions as mode}
              <button
                onclick={() => { filterMode = mode; showFilterMenu = false; }}
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.8125rem] transition-colors hover:bg-surface-overlay"
                class:text-accent={filterMode === mode}
                class:font-medium={filterMode === mode}
                class:text-text-secondary={filterMode !== mode}
              >
                {#if filterMode === mode}
                  <Icon icon={checkIcon} class="h-3.5 w-3.5 text-accent" />
                {:else}
                  <span class="h-3.5 w-3.5"></span>
                {/if}
                {filterLabels[mode]}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Sort dropdown -->
      <div class="relative" data-dropdown>
        <button
          onclick={(e) => { e.stopPropagation(); showSortMenu = !showSortMenu; showFilterMenu = false; }}
          class="flex h-9 items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-raised px-3 text-[0.8125rem] text-text-secondary transition-colors hover:border-border-default hover:text-text-primary"
        >
          <Icon icon={arrowDownIcon} class="h-3.5 w-3.5" />
          {sortLabels[sortMode]}
          <Icon icon={chevronDownIcon} class="h-3 w-3 opacity-50" />
        </button>
        {#if showSortMenu}
          <div class="animate-dropdown absolute right-0 top-full z-20 mt-1.5 w-40 overflow-hidden rounded-xl border border-border-subtle bg-surface-raised shadow-[var(--shadow-md)]">
            {#each sortOptions as mode}
              <button
                onclick={() => { sortMode = mode; showSortMenu = false; }}
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.8125rem] transition-colors hover:bg-surface-overlay"
                class:text-accent={sortMode === mode}
                class:font-medium={sortMode === mode}
                class:text-text-secondary={sortMode !== mode}
              >
                {#if sortMode === mode}
                  <Icon icon={checkIcon} class="h-3.5 w-3.5 text-accent" />
                {:else}
                  <span class="h-3.5 w-3.5"></span>
                {/if}
                {sortLabels[mode]}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <!-- View toggle -->
      <div class="flex h-9 overflow-hidden rounded-lg border border-border-subtle bg-surface-raised">
        <button
          onclick={() => (viewMode = "grid")}
          class="flex items-center justify-center px-2.5 transition-colors {viewMode === 'grid' ? 'bg-accent/10 text-accent' : 'text-text-muted'}"
          title="Grid view"
        >
          <Icon icon={layoutGridIcon} class="h-4 w-4" />
        </button>
        <div class="w-px bg-border-subtle"></div>
        <button
          onclick={() => (viewMode = "list")}
          class="flex items-center justify-center px-2.5 transition-colors {viewMode === 'list' ? 'bg-accent/10 text-accent' : 'text-text-muted'}"
          title="List view"
        >
          <Icon icon={listIcon} class="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>

  <!-- Results summary -->
  <div class="flex items-center gap-2 mb-3">
    <p class="text-[0.8125rem] tabular-nums text-text-muted">
      {filteredVideos.length}
      {filteredVideos.length !== allVideos.length ? `of ${allVideos.length}` : ""}
      {filteredVideos.length !== 1 ? t("label.recordings").split(" | ")[1] : t("label.recordings").split(" | ")[0]}
    </p>
    {#if filterMode !== "all" || search}
      <button
        onclick={() => { filterMode = "all"; search = ""; }}
        class="rounded-md bg-accent/8 px-2 py-0.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-accent/14"
      >
        {t("btn.clearFilters")}
      </button>
    {/if}
  </div>

  <!-- No results after filter -->
  {#if filteredVideos.length === 0}
    <div class="card px-6 py-16 text-center">
      <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-surface-overlay">
        <svg class="h-5 w-5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </div>
      <p class="mt-3 text-[0.8125rem] text-text-secondary">{t("empty.noMatches")}</p>
      <button
        onclick={() => { filterMode = "all"; search = ""; }}
        class="mt-2 text-[0.8125rem] font-medium text-accent hover:text-accent-hover"
      >
        {t("btn.clearAllFilters")}
      </button>
    </div>
  {:else if viewMode === "grid"}
    <!-- Grid view grouped by date — with timeline -->
    <div class="archive-timeline relative space-y-6 pl-6 sm:pl-8">
      <!-- Timeline track — translate -50% to center the 1px line on the dot center -->
      <div class="absolute left-3 top-1 bottom-1 w-px -translate-x-1/2 bg-border-subtle sm:left-4" aria-hidden="true">
        <div class="archive-timeline-fill absolute inset-x-0 top-0 bg-accent/40 rounded-full"></div>
      </div>
      {#each groupedVideos as group, gi (group.date)}
        <div>
          <div class="relative mb-3 flex items-center gap-3">
            <!-- Timeline dot — first is larger -->
            <div class="absolute -left-6 sm:-left-8 flex items-center justify-center w-6 sm:w-8">
              <div class="rounded-full border-2 border-surface-base transition-colors {gi === 0 ? 'h-3 w-3 bg-accent ring-2 ring-accent/20' : 'h-2.5 w-2.5 bg-accent/60 ring-2 ring-accent/10'}"></div>
            </div>
            <h3 class="text-[0.8125rem] font-semibold text-text-primary">{group.label}</h3>
            <div class="h-px flex-1 bg-border-subtle"></div>
            <span class="text-[0.6875rem] tabular-nums text-text-muted">
              {group.videos.length} {group.videos.length !== 1 ? t("label.clips").split(" | ")[1] : t("label.clips").split(" | ")[0]}
            </span>
          </div>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {#each group.videos as video (video.path)}
              <div
                class="card-interactive group overflow-hidden"
                use:preloadSprite={video.sprite ? spriteUrl(video.path) : undefined}
              >
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div
                  class="relative bg-black/60"
                  onmousemove={(e) => handleSpriteHover(e, video)}
                  onmouseleave={handleSpriteLeave}
                >
                  <video
                    data-src={streamUrl(video.path)}
                    use:lazyVideo
                    class="aspect-video w-full object-contain"
                    controls
                    preload="none"
                    poster={video.thumbnail ? thumbnailUrl(video.path) : undefined}
                  ></video>
                  <!-- Sprite hover-scrub overlay -->
                  {#if video.sprite && hoverVideo === video.path}
                    <div
                      class="pointer-events-none absolute inset-0 bg-no-repeat"
                      style="background-image: url({spriteUrl(video.path)}); background-size: {SPRITE_FRAMES * 100}% 100%; background-position-x: -{hoverFrame * (100 / SPRITE_FRAMES)}%;"
                    ></div>
                    <div
                      class="pointer-events-none absolute bottom-0 left-0 h-0.5 bg-accent transition-[width] duration-75"
                      style="width: {((hoverFrame + 1) / SPRITE_FRAMES) * 100}%"
                    ></div>
                  {/if}
                  <!-- Overlay badges -->
                  {#if video.time}
                    <div class="pointer-events-none absolute left-2.5 top-2.5 rounded-md bg-black/60 px-2 py-0.5 text-[0.6875rem] font-medium tabular-nums text-white/90 backdrop-blur-sm">
                      {formatTime(video.time)}
                    </div>
                  {/if}
                  {#if video.meta?.duration_seconds}
                    <div class="pointer-events-none absolute right-2.5 top-2.5 rounded-md bg-black/60 px-2 py-0.5 text-[0.6875rem] font-medium tabular-nums text-white/90 backdrop-blur-sm">
                      {formatDuration(video.meta.duration_seconds)}
                    </div>
                  {/if}
                </div>
                <div class="flex items-center justify-between border-t border-border-subtle px-3.5 py-2.5">
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      <p class="text-[0.8125rem] font-medium text-text-primary">{formatDate(video.date)}</p>
                      {#if isNewRecording(video)}
                        <span class="animate-pop rounded-full bg-status-critical/10 px-1.5 py-0.5 text-[0.5625rem] font-semibold uppercase tracking-wide text-status-critical">
                          {t("badge.new")}
                        </span>
                      {/if}
                      {#if triggerLabel(video.meta)}
                        <span class="rounded-full px-1.5 py-0.5 text-[0.5625rem] font-semibold uppercase tracking-wide
                          {video.meta?.reason === 'sensor'
                            ? 'bg-status-warning/10 text-status-warning'
                            : 'bg-accent/10 text-accent'}">
                          {triggerLabel(video.meta)}
                        </span>
                      {/if}
                    </div>
                    <div class="flex items-center gap-1.5 text-[0.6875rem] tabular-nums text-text-muted">
                      {#if video.time}
                        <span>{formatTime(video.time)}</span>
                      {/if}
                      {#if video.meta?.duration_seconds}
                        <span class="text-border-strong">·</span>
                        <span>{formatDuration(video.meta.duration_seconds)}</span>
                      {/if}
                    </div>
                  </div>
                  <div class="flex shrink-0 gap-0.5 sm:opacity-0 sm:transition-opacity sm:duration-150 sm:group-hover:opacity-100">
                    <button
                      onclick={() => downloadVideo(video)}
                      class="flex h-10 w-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-accent-muted hover:text-accent sm:h-auto sm:w-auto sm:p-2"
                      title={t("btn.download")}
                    >
                      <Icon icon={downloadIcon} class="h-[1.125rem] w-[1.125rem] sm:h-4 sm:w-4" />
                    </button>
                    <button
                      onclick={(e) => openDeleteDialog(video, e.currentTarget as HTMLButtonElement)}
                      class="flex h-10 w-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-status-critical/8 hover:text-status-critical sm:h-auto sm:w-auto sm:p-2"
                      title={t("btn.delete")}
                    >
                      <Icon icon={trashIcon} class="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <!-- List view grouped by date — with timeline -->
    <div class="archive-timeline relative space-y-5 pl-6 sm:pl-8">
      <!-- Timeline track — translate -50% to center the 1px line on the dot center -->
      <div class="absolute left-3 top-1 bottom-1 w-px -translate-x-1/2 bg-border-subtle sm:left-4" aria-hidden="true">
        <div class="archive-timeline-fill absolute inset-x-0 top-0 bg-accent/40 rounded-full"></div>
      </div>
      {#each groupedVideos as group, gi (group.date)}
        <div>
          <div class="relative mb-2 flex items-center gap-3">
            <!-- Timeline dot — first is larger -->
            <div class="absolute -left-6 sm:-left-8 flex items-center justify-center w-6 sm:w-8">
              <div class="rounded-full border-2 border-surface-base transition-colors {gi === 0 ? 'h-3 w-3 bg-accent ring-2 ring-accent/20' : 'h-2.5 w-2.5 bg-accent/60 ring-2 ring-accent/10'}"></div>
            </div>
            <h3 class="text-[0.8125rem] font-semibold text-text-primary">{group.label}</h3>
            <div class="h-px flex-1 bg-border-subtle"></div>
            <span class="text-[0.6875rem] tabular-nums text-text-muted">
              {group.videos.length} {group.videos.length !== 1 ? t("label.clips").split(" | ")[1] : t("label.clips").split(" | ")[0]}
            </span>
          </div>
          <div class="overflow-hidden rounded-xl border border-border-subtle">
            {#each group.videos as video, i (video.path)}
              <div
                class="group flex items-center gap-4 bg-surface-raised px-4 py-3 transition-colors hover:bg-surface-overlay"
                class:border-t={i > 0}
                class:border-border-subtle={i > 0}
              >
                <!-- Thumbnail -->
                <div class="relative h-16 w-28 shrink-0 overflow-hidden rounded-lg bg-black/60">
                  {#if video.thumbnail}
                    <img
                      src={thumbnailUrl(video.path)}
                      alt=""
                      class="h-full w-full object-contain"
                      loading="lazy"
                    />
                  {:else}
                    <video
                      data-src={streamUrl(video.path)}
                      use:lazyVideo
                      class="h-full w-full object-contain"
                      preload="none"
                    ></video>
                  {/if}
                </div>

                <!-- Info -->
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <p class="truncate text-[0.8125rem] font-medium text-text-primary">{video.filename}</p>
                    {#if isNewRecording(video)}
                      <span class="shrink-0 rounded-full bg-status-critical/10 px-1.5 py-0.5 text-[0.5625rem] font-semibold uppercase tracking-wide text-status-critical">
                        {t("badge.new")}
                      </span>
                    {/if}
                    {#if triggerLabel(video.meta)}
                      <span class="shrink-0 rounded-full px-1.5 py-0.5 text-[0.5625rem] font-semibold uppercase tracking-wide
                        {video.meta?.reason === 'sensor'
                          ? 'bg-status-warning/10 text-status-warning'
                          : 'bg-accent/10 text-accent'}">
                        {triggerLabel(video.meta)}
                      </span>
                    {/if}
                  </div>
                  <div class="mt-0.5 flex items-center gap-2 text-[0.75rem] text-text-muted">
                    <span>{formatDate(video.date)}</span>
                    {#if video.time}
                      <span class="text-border-strong">|</span>
                      <span class="tabular-nums">{formatTime(video.time)}</span>
                    {/if}
                    {#if video.meta?.duration_seconds}
                      <span class="text-border-strong">|</span>
                      <span class="tabular-nums">{formatDuration(video.meta.duration_seconds)}</span>
                    {/if}
                  </div>
                </div>

                <!-- Actions -->
                <div class="flex shrink-0 gap-1 sm:opacity-0 sm:transition-opacity sm:duration-150 sm:group-hover:opacity-100">
                  <button
                    onclick={() => downloadVideo(video)}
                    class="flex h-10 w-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-accent-muted hover:text-accent sm:h-8 sm:w-8"
                    title={t("btn.download")}
                    aria-label={t("btn.downloadRecording")}
                  >
                    <Icon icon={downloadIcon} class="h-4 w-4" />
                  </button>
                  <button
                    onclick={(e) => openDeleteDialog(video, e.currentTarget as HTMLButtonElement)}
                    class="flex h-10 w-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-status-critical/8 hover:text-status-critical sm:h-8 sm:w-8"
                    title={t("btn.delete")}
                    aria-label={t("btn.deleteRecording")}
                  >
                    <Icon icon={trashIcon} class="h-4 w-4" />
                  </button>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}
{/if}

<!-- Delete confirmation modal -->
{#if deleteTarget}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="animate-overlay fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    onkeydown={(e) => e.key === "Escape" && closeDeleteDialog()}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="absolute inset-0" onclick={closeDeleteDialog}></div>
    <div class="animate-dialog relative w-full max-w-sm rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-[var(--shadow-lg)]" style="view-transition-name: delete-morph;">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-status-critical/8">
        <Icon icon={trashIcon} class="h-4.5 w-4.5 text-status-critical" />
      </div>
      <h3 class="mt-3 text-sm font-semibold text-text-primary">{t("dialog.deleteTitle")}</h3>
      <p class="mt-1 text-[0.8125rem] leading-relaxed text-text-secondary">
        {t("dialog.deleteMessage", { filename: deleteTarget.filename })}
      </p>
      <div class="mt-5 flex justify-end gap-2.5">
        <button
          onclick={closeDeleteDialog}
          class="rounded-lg px-4 py-2.5 text-[0.8125rem] font-medium text-text-secondary transition-colors hover:bg-surface-overlay hover:text-text-primary"
        >
          {t("btn.cancel")}
        </button>
        <button
          onclick={confirmDelete}
          disabled={deleting}
          class="rounded-lg bg-status-critical/10 px-4 py-2.5 text-[0.8125rem] font-semibold text-status-critical transition-colors hover:bg-status-critical/18 disabled:opacity-40"
        >
          {deleting ? t("btn.deleting") : t("btn.delete")}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Snapshot lightbox -->
{#if expandedSnap}
  {@const snapIdx = allSnapshots.indexOf(expandedSnap)}
  {@const hasPrev = snapIdx > 0}
  {@const hasNext = snapIdx < allSnapshots.length - 1}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="animate-overlay fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    onkeydown={(e) => {
      if (e.key === "Escape") expandedSnap = null;
      else if (e.key === "ArrowLeft" && hasPrev) expandedSnap = allSnapshots[snapIdx - 1];
      else if (e.key === "ArrowRight" && hasNext) expandedSnap = allSnapshots[snapIdx + 1];
    }}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="absolute inset-0 cursor-zoom-out" onclick={() => expandedSnap = null}></div>

    <!-- Prev/Next arrows -->
    {#if hasPrev}
      <button
        onclick={() => expandedSnap = allSnapshots[snapIdx - 1]}
        class="absolute left-3 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white/70 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white sm:left-6"
        aria-label="Previous snapshot"
      >
        <Icon icon={chevronLeftIcon} class="h-5 w-5" />
      </button>
    {/if}
    {#if hasNext}
      <button
        onclick={() => expandedSnap = allSnapshots[snapIdx + 1]}
        class="absolute right-3 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white/70 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white sm:right-6"
        aria-label="Next snapshot"
      >
        <Icon icon={chevronRightIcon} class="h-5 w-5" />
      </button>
    {/if}

    {#key expandedSnap.path}
      <img
        src={snapshotUrl(expandedSnap.path)}
        alt={expandedSnap.filename}
        class="animate-fade-in relative max-h-[85vh] max-w-[90vw] cursor-zoom-out rounded-lg object-contain shadow-[0_8px_32px_rgba(0,0,0,0.5)]"
        onclick={() => expandedSnap = null}
      />
    {/key}
    <div class="relative mt-3 flex items-center gap-3 animate-in stagger-2">
      <span class="text-[0.625rem] tabular-nums text-white/50">{snapIdx + 1} / {allSnapshots.length}</span>
      <p class="text-sm font-medium text-white/90">{expandedSnap.filename}</p>
      <button
        onclick={() => { if (expandedSnap) downloadSnapshot(expandedSnap); }}
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white"
        title={t("btn.download")}
      >
        <Icon icon={downloadIcon} class="h-4 w-4" />
      </button>
    </div>
  </div>
{/if}
