<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  interface Video {
    path: string;
    filename: string;
    date: string;
    time: string;
  }

  let videos: Video[] = $state([]);
  let loading = $state(true);
  let error = $state(false);
  let deleteTarget: Video | null = $state(null);
  let deleting = $state(false);

  function parseFilename(filepath: string): Video {
    const filename = filepath.split("/").pop() ?? filepath;
    const match = filename.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    const date = match ? `${match[1]}-${match[2]}-${match[3]}` : "Unknown";
    const time = match ? `${match[4]}:${match[5]}:${match[6]}` : "";
    return { path: filepath, filename, date, time };
  }

  onMount(async () => {
    try {
      const res = await fetch(`${getBackendUrl()}/archive`);
      const paths: string[] = await res.json();
      videos = paths.map(parseFilename).reverse();
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
      videos = videos.filter((v) => v.path !== deleteTarget!.path);
      deleteTarget = null;
    } catch (e) {
      console.error("Failed to delete video:", e);
    } finally {
      deleting = false;
    }
  }

  function formatDate(dateStr: string): string {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return dateStr;
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

{#if loading}
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
{:else if error}
  <div class="card px-6 py-14 text-center">
    <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-status-critical/8">
      <svg class="h-5 w-5 text-status-critical" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    </div>
    <p class="mt-3 text-[13px] text-text-secondary">Unable to load archive</p>
    <p class="mt-1 text-[12px] text-text-muted">Check that the backend is running</p>
  </div>
{:else if videos.length === 0}
  <div class="card px-6 py-14 text-center">
    <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-surface-overlay">
      <svg class="h-5 w-5 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
        <line x1="7" y1="2" x2="7" y2="22" />
        <line x1="17" y1="2" x2="17" y2="22" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <line x1="2" y1="7" x2="7" y2="7" />
        <line x1="2" y1="17" x2="7" y2="17" />
        <line x1="17" y1="7" x2="22" y2="7" />
        <line x1="17" y1="17" x2="22" y2="17" />
      </svg>
    </div>
    <p class="mt-3 text-[13px] text-text-secondary">No recordings yet</p>
    <p class="mt-1 text-[12px] text-text-muted">Recordings will appear here once you start capturing</p>
  </div>
{:else}
  <!-- Count -->
  <p class="text-[12px] text-text-muted">{videos.length} recording{videos.length !== 1 ? "s" : ""}</p>

  <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
    {#each videos as video (video.path)}
      <div class="card-interactive group overflow-hidden">
        <!-- Video preview -->
        <div class="relative bg-black/60">
          <video
            data-src={streamUrl(video.path)}
            use:lazyVideo
            class="aspect-video w-full object-contain"
            controls
            preload="none"
          ></video>
        </div>

        <!-- Info + actions -->
        <div class="flex items-center justify-between border-t border-border-subtle px-3.5 py-2.5">
          <div class="min-w-0">
            <p class="text-[13px] font-medium text-text-primary">{formatDate(video.date)}</p>
            {#if video.time}
              <p class="text-[11px] tabular-nums text-text-muted">{video.time}</p>
            {/if}
          </div>
          <div class="flex shrink-0 gap-0.5 sm:opacity-0 sm:transition-opacity sm:duration-150 sm:group-hover:opacity-100">
            <button
              onclick={() => downloadVideo(video)}
              class="rounded-lg p-2 text-text-muted transition-colors hover:bg-accent-muted hover:text-accent"
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
              class="rounded-lg p-2 text-text-muted transition-colors hover:bg-status-critical/8 hover:text-status-critical"
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
      <h3 class="mt-3 text-[15px] font-semibold text-text-primary">Delete recording?</h3>
      <p class="mt-1 text-[13px] leading-relaxed text-text-secondary">
        <span class="font-medium text-text-primary">{deleteTarget.filename}</span> will be permanently removed.
      </p>
      <div class="mt-5 flex justify-end gap-2.5">
        <button
          onclick={() => (deleteTarget = null)}
          class="rounded-lg px-3.5 py-2 text-[13px] font-medium text-text-secondary transition-colors hover:bg-surface-overlay hover:text-text-primary"
        >
          Cancel
        </button>
        <button
          onclick={confirmDelete}
          disabled={deleting}
          class="rounded-lg bg-status-critical/10 px-3.5 py-2 text-[13px] font-semibold text-status-critical transition-colors hover:bg-status-critical/18 disabled:opacity-40"
        >
          {deleting ? "Deleting..." : "Delete"}
        </button>
      </div>
    </div>
  </div>
{/if}
