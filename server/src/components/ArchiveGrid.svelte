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
    const base = filename.replace(".mp4", "");
    const date = base.length >= 8
      ? `${base.slice(0, 4)}-${base.slice(4, 6)}-${base.slice(6, 8)}`
      : "Unknown";
    const time = base.length >= 14
      ? `${base.slice(8, 10)}:${base.slice(10, 12)}:${base.slice(12, 14)}`
      : "";
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
</script>

{#if loading}
  <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
    {#each Array(6) as _}
      <div class="card animate-pulse overflow-hidden">
        <div class="aspect-video bg-surface-elevated"></div>
        <div class="space-y-2 p-4">
          <div class="h-4 w-32 rounded bg-surface-elevated"></div>
          <div class="h-3 w-20 rounded bg-surface-elevated"></div>
        </div>
      </div>
    {/each}
  </div>
{:else if error}
  <div class="card px-6 py-12 text-center text-sm text-text-muted">
    Unable to load archive
  </div>
{:else if videos.length === 0}
  <div class="card px-6 py-12 text-center">
    <svg class="mx-auto h-10 w-10 text-text-muted/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
    <p class="mt-3 text-sm text-text-muted">No recordings yet</p>
  </div>
{:else}
  <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
    {#each videos as video (video.path)}
      <div class="card group overflow-hidden">
        <!-- Video player -->
        <div class="relative">
          <video
            src={streamUrl(video.path)}
            class="aspect-video w-full bg-black object-contain"
            controls
            preload="metadata"
          ></video>
        </div>

        <!-- Info + actions -->
        <div class="flex items-center justify-between border-t border-border-subtle px-3 py-2.5 sm:px-4 sm:py-3">
          <div>
            <p class="text-sm font-semibold text-text-primary">{video.date}</p>
            {#if video.time}
              <p class="text-[11px] text-text-muted">{video.time}</p>
            {/if}
          </div>
          <div class="flex gap-0.5 sm:opacity-0 sm:transition-opacity sm:duration-200 sm:group-hover:opacity-100">
            <button
              onclick={() => downloadVideo(video)}
              class="rounded-lg p-2 text-text-muted transition-colors hover:bg-accent/10 hover:text-accent"
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
              class="rounded-lg p-2 text-text-muted transition-colors hover:bg-status-critical/10 hover:text-status-critical"
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
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
  >
    <div class="mx-4 w-full max-w-sm rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-[var(--shadow-lg)]">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-status-critical/12">
        <svg class="h-5 w-5 text-status-critical" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
      </div>
      <h3 class="mt-4 text-base font-semibold text-text-primary">Delete recording?</h3>
      <p class="mt-1.5 text-sm text-text-secondary">
        <span class="font-medium text-text-primary">{deleteTarget.filename}</span> will be permanently deleted.
      </p>
      <div class="mt-6 flex justify-end gap-3">
        <button
          onclick={() => (deleteTarget = null)}
          class="rounded-xl px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-overlay"
        >
          Cancel
        </button>
        <button
          onclick={confirmDelete}
          disabled={deleting}
          class="rounded-xl bg-status-critical/12 px-4 py-2 text-sm font-semibold text-status-critical shadow-[inset_0_0_0_1px_rgba(255,61,87,0.2)] transition-colors hover:bg-status-critical/20 disabled:opacity-50"
        >
          {deleting ? "Deleting..." : "Delete"}
        </button>
      </div>
    </div>
  </div>
{/if}
