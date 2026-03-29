<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";

  let feedUrl = $state("");
  let recording = $state(false);
  let toggling = $state(false);

  onMount(() => {
    feedUrl = `${getBackendUrl()}/video_feed`;
  });

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
</script>

<div class="card overflow-hidden">
  <!-- Feed -->
  <div class="relative aspect-video w-full bg-black">
    {#if feedUrl}
      <img
        src={feedUrl}
        alt="Live camera feed"
        class="h-full w-full object-contain"
      />
    {:else}
      <div class="flex h-full items-center justify-center text-text-muted">
        <svg class="mr-2 h-5 w-5 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
          <circle cx="12" cy="13" r="4" />
        </svg>
        Connecting...
      </div>
    {/if}

    <!-- Recording indicator -->
    {#if recording}
      <div class="absolute left-3 top-3 flex items-center gap-2 rounded-lg bg-black/60 px-3 py-1.5 backdrop-blur-md">
        <span class="h-2 w-2 animate-pulse rounded-full bg-status-critical shadow-[0_0_8px_rgba(255,61,87,0.6)]"></span>
        <span class="text-xs font-semibold tracking-wide text-status-critical">REC</span>
      </div>
    {/if}

    <!-- Live badge -->
    {#if !recording}
      <div class="absolute left-3 top-3 flex items-center gap-1.5 rounded-lg bg-black/60 px-2.5 py-1 backdrop-blur-md">
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
  </div>
</div>
