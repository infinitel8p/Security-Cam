<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface Video {
    path: string;
    filename: string;
    date: string;
    time: string;
    timestamp: number;
  }

  type SortMode = "newest" | "oldest" | "name";
  type FilterMode = "all" | "today" | "week" | "month";
  type ViewMode = "grid" | "list";

  let allVideos: Video[] = $state([]);
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

  function parseFilename(filepath: string): Video {
    const filename = filepath.split("/").pop() ?? filepath;
    const match = filename.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    const date = match ? `${match[1]}-${match[2]}-${match[3]}` : "Unknown";
    const time = match ? `${match[4]}:${match[5]}:${match[6]}` : "";
    const timestamp = match
      ? new Date(`${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}`).getTime()
      : 0;
    return { path: filepath, filename, date, time, timestamp };
  }

  const filteredVideos = $derived.by(() => {
    let result = allVideos;

    // Text search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (v) => v.filename.toLowerCase().includes(q) || v.date.includes(q) || v.time.includes(q),
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

  onMount(async () => {
    try {
      const res = await fetch(`${getBackendUrl()}/archive`);
      const paths: string[] = await res.json();
      allVideos = paths.map(parseFilename);
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  });

  function streamUrl(path: string): string {
    return `${getBackendUrl()}/stream_video?video_path=${encodeURIComponent(path)}&cache_buster=${Date.now()}`;
  }

  function downloadVideo(video: Video) {
    const a = document.createElement("a");
    a.href = streamUrl(video.path);
    a.download = video.filename;
    a.click();
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    deleting = true;
    try {
      await fetch(`${getBackendUrl()}/delete_video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_path: deleteTarget.path }),
      });
      allVideos = allVideos.filter((v) => v.path !== deleteTarget!.path);
      deleteTarget = null;
    } catch (e) {
      console.error("Failed to delete video:", e);
    } finally {
      deleting = false;
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
  const sortLabels: Record<SortMode, string> = { newest: "Newest first", oldest: "Oldest first", name: "Name" };
  const filterLabels: Record<FilterMode, string> = { all: "All time", today: "Today", week: "This week", month: "This month" };

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

{#if loading}
  <div class="space-y-4">
    <!-- Skeleton toolbar -->
    <div class="flex gap-2">
      {#each Array(3) as _}
        <div class="h-9 w-24 animate-pulse rounded-lg bg-surface-elevated"></div>
      {/each}
    </div>
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {#each Array(6) as _}
        <div class="card animate-pulse overflow-hidden">
          <div class="aspect-video bg-surface-elevated"></div>
          <div class="p-3.5">
            <div class="h-4 w-28 rounded bg-surface-elevated"></div>
            <div class="mt-2 h-3 w-16 rounded bg-surface-elevated"></div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{:else if error}
  <div class="card px-6 py-14 text-center">
    <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-status-critical/8">
      <svg class="h-5 w-5 text-status-critical" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    </div>
    <p class="mt-3 text-[0.8125rem] text-text-secondary">Unable to load archive</p>
    <p class="mt-1 text-[0.8125rem] text-text-muted">Check that the backend is running</p>
  </div>
{:else if allVideos.length === 0}
  <div class="card px-6 py-20 text-center">
    <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-overlay">
      <svg class="h-6 w-6 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="m22 8-6 4 6 4V8Z" />
        <rect width="14" height="12" x="2" y="6" rx="2" ry="2" />
      </svg>
    </div>
    <p class="mt-4 text-sm font-medium text-text-secondary">No recordings yet</p>
    <p class="mt-1 text-[0.8125rem] text-text-muted">Recordings will appear here once you start capturing</p>
  </div>
{:else}
  <!-- Toolbar -->
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <!-- Search -->
    <div class="relative max-w-xs flex-1">
      <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <input
        type="text"
        bind:value={search}
        placeholder="Search recordings..."
        class="h-9 w-full rounded-lg border border-border-subtle bg-surface-raised pl-9 pr-3 text-[0.8125rem] text-text-primary placeholder:text-text-muted transition-colors focus:border-accent/40 focus:outline-none focus:ring-1 focus:ring-accent/20"
      />
      {#if search}
        <button
          onclick={() => (search = "")}
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-text-muted hover:text-text-secondary"
        >
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
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
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          {filterLabels[filterMode]}
          <svg class="h-3 w-3 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9" /></svg>
        </button>
        {#if showFilterMenu}
          <div class="absolute right-0 top-full z-20 mt-1.5 w-40 overflow-hidden rounded-xl border border-border-subtle bg-surface-raised shadow-[var(--shadow-md)]">
            {#each filterOptions as mode}
              <button
                onclick={() => { filterMode = mode; showFilterMenu = false; }}
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.8125rem] transition-colors hover:bg-surface-overlay"
                class:text-accent={filterMode === mode}
                class:font-medium={filterMode === mode}
                class:text-text-secondary={filterMode !== mode}
              >
                {#if filterMode === mode}
                  <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
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
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" />
          </svg>
          {sortLabels[sortMode]}
          <svg class="h-3 w-3 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9" /></svg>
        </button>
        {#if showSortMenu}
          <div class="absolute right-0 top-full z-20 mt-1.5 w-40 overflow-hidden rounded-xl border border-border-subtle bg-surface-raised shadow-[var(--shadow-md)]">
            {#each sortOptions as mode}
              <button
                onclick={() => { sortMode = mode; showSortMenu = false; }}
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.8125rem] transition-colors hover:bg-surface-overlay"
                class:text-accent={sortMode === mode}
                class:font-medium={sortMode === mode}
                class:text-text-secondary={sortMode !== mode}
              >
                {#if sortMode === mode}
                  <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
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
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
          </svg>
        </button>
        <div class="w-px bg-border-subtle"></div>
        <button
          onclick={() => (viewMode = "list")}
          class="flex items-center justify-center px-2.5 transition-colors {viewMode === 'list' ? 'bg-accent/10 text-accent' : 'text-text-muted'}"
          title="List view"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
            <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  </div>

  <!-- Results summary -->
  <div class="flex items-center gap-2">
    <p class="text-[0.8125rem] tabular-nums text-text-muted">
      {filteredVideos.length}
      {filteredVideos.length !== allVideos.length ? `of ${allVideos.length}` : ""}
      recording{filteredVideos.length !== 1 ? "s" : ""}
    </p>
    {#if filterMode !== "all" || search}
      <button
        onclick={() => { filterMode = "all"; search = ""; }}
        class="rounded-md bg-accent/8 px-2 py-0.5 text-[0.75rem] font-medium text-accent transition-colors hover:bg-accent/14"
      >
        Clear filters
      </button>
    {/if}
  </div>

  <!-- No results after filter -->
  {#if filteredVideos.length === 0}
    <div class="card px-6 py-14 text-center">
      <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-surface-overlay">
        <svg class="h-5 w-5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </div>
      <p class="mt-3 text-[0.8125rem] text-text-secondary">No recordings match your filters</p>
      <button
        onclick={() => { filterMode = "all"; search = ""; }}
        class="mt-2 text-[0.8125rem] font-medium text-accent hover:text-accent-hover"
      >
        Clear all filters
      </button>
    </div>
  {:else if viewMode === "grid"}
    <!-- Grid view grouped by date -->
    <div class="space-y-6">
      {#each groupedVideos as group (group.date)}
        <div>
          <div class="mb-3 flex items-center gap-3">
            <h3 class="text-[0.8125rem] font-semibold text-text-primary">{group.label}</h3>
            <div class="h-px flex-1 bg-border-subtle"></div>
            <span class="text-[0.6875rem] tabular-nums text-text-muted">
              {group.videos.length} clip{group.videos.length !== 1 ? "s" : ""}
            </span>
          </div>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {#each group.videos as video (video.path)}
              <div class="card-interactive group overflow-hidden">
                <div class="relative bg-black/60">
                  <video
                    data-src={streamUrl(video.path)}
                    use:lazyVideo
                    class="aspect-video w-full object-contain"
                    controls
                    preload="none"
                  ></video>
                  <!-- Time badge overlay -->
                  {#if video.time}
                    <div class="pointer-events-none absolute left-2.5 top-2.5 rounded-md bg-black/60 px-2 py-0.5 text-[0.6875rem] font-medium tabular-nums text-white/90 backdrop-blur-sm">
                      {formatTime(video.time)}
                    </div>
                  {/if}
                </div>
                <div class="flex items-center justify-between border-t border-border-subtle px-3.5 py-2.5">
                  <div class="min-w-0">
                    <p class="text-[0.8125rem] font-medium text-text-primary">{formatDate(video.date)}</p>
                    {#if video.time}
                      <p class="text-[0.6875rem] tabular-nums text-text-muted">{formatTime(video.time)}</p>
                    {/if}
                  </div>
                  <div class="flex shrink-0 gap-0.5 sm:opacity-0 sm:transition-opacity sm:duration-150 sm:group-hover:opacity-100">
                    <button
                      onclick={() => downloadVideo(video)}
                      class="flex h-10 w-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-accent-muted hover:text-accent sm:h-auto sm:w-auto sm:p-2"
                      title="Download"
                    >
                      <svg class="h-[1.125rem] w-[1.125rem] sm:h-4 sm:w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                    </button>
                    <button
                      onclick={() => (deleteTarget = video)}
                      class="flex h-10 w-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-status-critical/8 hover:text-status-critical sm:h-auto sm:w-auto sm:p-2"
                      title="Delete"
                    >
                      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
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
    <!-- List view grouped by date -->
    <div class="space-y-5">
      {#each groupedVideos as group (group.date)}
        <div>
          <div class="mb-2 flex items-center gap-3">
            <h3 class="text-[0.8125rem] font-semibold text-text-primary">{group.label}</h3>
            <div class="h-px flex-1 bg-border-subtle"></div>
            <span class="text-[0.6875rem] tabular-nums text-text-muted">
              {group.videos.length} clip{group.videos.length !== 1 ? "s" : ""}
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
                  <video
                    data-src={streamUrl(video.path)}
                    use:lazyVideo
                    class="h-full w-full object-contain"
                    preload="none"
                  ></video>
                </div>

                <!-- Info -->
                <div class="min-w-0 flex-1">
                  <p class="truncate text-[0.8125rem] font-medium text-text-primary">{video.filename}</p>
                  <div class="mt-0.5 flex items-center gap-2 text-[0.75rem] text-text-muted">
                    <span>{formatDate(video.date)}</span>
                    {#if video.time}
                      <span class="text-border-strong">|</span>
                      <span class="tabular-nums">{formatTime(video.time)}</span>
                    {/if}
                  </div>
                </div>

                <!-- Actions -->
                <div class="flex shrink-0 gap-1 sm:opacity-0 sm:transition-opacity sm:duration-150 sm:group-hover:opacity-100">
                  <button
                    onclick={() => downloadVideo(video)}
                    class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-accent-muted hover:text-accent"
                    title="Download"
                  >
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                  </button>
                  <button
                    onclick={() => (deleteTarget = video)}
                    class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-status-critical/8 hover:text-status-critical"
                    title="Delete"
                  >
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
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
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    onkeydown={(e) => e.key === "Escape" && (deleteTarget = null)}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="absolute inset-0" onclick={() => (deleteTarget = null)}></div>
    <div class="relative w-full max-w-sm rounded-xl border border-border-subtle bg-surface-raised p-5 shadow-[var(--shadow-lg)]">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-status-critical/8">
        <svg class="h-4.5 w-4.5 text-status-critical" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
      </div>
      <h3 class="mt-3 text-sm font-semibold text-text-primary">Delete recording?</h3>
      <p class="mt-1 text-[0.8125rem] leading-relaxed text-text-secondary">
        <span class="break-all font-medium text-text-primary">{deleteTarget.filename}</span> will be permanently removed.
      </p>
      <div class="mt-5 flex justify-end gap-2.5">
        <button
          onclick={() => (deleteTarget = null)}
          class="rounded-lg px-4 py-2.5 text-[0.8125rem] font-medium text-text-secondary transition-colors hover:bg-surface-overlay hover:text-text-primary"
        >
          Cancel
        </button>
        <button
          onclick={confirmDelete}
          disabled={deleting}
          class="rounded-lg bg-status-critical/10 px-4 py-2.5 text-[0.8125rem] font-semibold text-status-critical transition-colors hover:bg-status-critical/18 disabled:opacity-40"
        >
          {deleting ? "Deleting..." : "Delete"}
        </button>
      </div>
    </div>
  </div>
{/if}
