<script lang="ts">
  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";

  interface Props {
    current: string;
  }

  let { current }: Props = $props();

  let browsePath = $state(current);
  let directories: { name: string; path: string }[] = $state([]);
  let loading = $state(false);
  let saving = $state(false);
  let open = $state(false);
  let dirError = $state(false);

  async function loadDirectories(path: string) {
    loading = true;
    dirError = false;
    try {
      const res = await fetch(
        `${getBackendUrl()}/list_directories?path=${encodeURIComponent(path)}`
      );
      const data = await res.json();
      if (data.error) {
        console.error(data.error);
        dirError = true;
        return;
      }
      browsePath = data.current_path;
      directories = data.directories ?? [];
    } catch (e) {
      console.error("Failed to list directories:", e);
      dirError = true;
    } finally {
      loading = false;
    }
  }

  function openBrowser() {
    open = true;
    loadDirectories(current);
  }

  function navigateTo(dir: { name: string; path: string }) {
    loadDirectories(dir.path);
  }

  function goUp() {
    const parent = browsePath.replace(/\/[^/]+\/?$/, "") || "/";
    loadDirectories(parent);
  }

  async function selectPath() {
    saving = true;
    try {
      const res = await fetch(`${getBackendUrl()}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ VideoSaveLocation: browsePath }),
      });
      if (!res.ok) throw new Error();
      current = browsePath;
      open = false;
      toast.success("Save location updated");
    } catch {
      toast.error("Failed to save location");
    } finally {
      saving = false;
    }
  }
</script>

<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
    </div>
    <label class="text-sm font-semibold text-text-primary">Video Save Location</label>
  </div>
  <div class="mt-3 flex items-center gap-3">
    <code class="flex-1 truncate rounded-xl border border-border-default bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-secondary">
      {current}
    </code>
    <button
      onclick={openBrowser}
      class="shrink-0 rounded-xl bg-accent/12 px-4 py-2 text-sm font-semibold text-accent shadow-[inset_0_0_0_1px_rgba(0,111,255,0.2)] transition-colors hover:bg-accent/20"
    >
      Browse
    </button>
  </div>
</div>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    onkeydown={(e) => e.key === "Escape" && (open = false)}
  >
    <div class="mx-4 w-full max-w-md overflow-hidden rounded-2xl border border-border-subtle bg-surface-raised shadow-[var(--shadow-lg)]">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-border-subtle px-5 py-3.5">
        <h3 class="text-sm font-semibold text-text-primary">Select Directory</h3>
        <button
          onclick={() => (open = false)}
          class="flex h-7 w-7 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Current path -->
      <div class="border-b border-border-subtle bg-surface-overlay/50 px-5 py-2">
        <code class="text-[0.6875rem] font-medium text-text-muted">{browsePath}</code>
      </div>

      <!-- Directory list -->
      <div class="max-h-64 overflow-y-auto p-2">
        {#if loading}
          <p class="px-3 py-6 text-center text-sm text-text-muted">Loading...</p>
        {:else if dirError}
          <div class="px-3 py-6 text-center">
            <p class="text-sm text-status-critical">Failed to load directories</p>
            <button onclick={() => loadDirectories(browsePath)} class="mt-2 text-[0.8125rem] font-medium text-accent hover:text-accent-hover">Retry</button>
          </div>
        {:else}
          <button
            onclick={goUp}
            class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-surface-overlay"
          >
            <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            ..
          </button>
          {#each directories as dir (dir.path)}
            <button
              onclick={() => navigateTo(dir)}
              class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-text-primary transition-colors hover:bg-surface-overlay"
            >
              <svg class="h-4 w-4 shrink-0 text-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
              {dir.name}
            </button>
          {/each}
          {#if directories.length === 0}
            <p class="px-3 py-6 text-center text-sm text-text-muted">No subdirectories</p>
          {/if}
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-3 border-t border-border-subtle px-5 py-3.5">
        <button
          onclick={() => (open = false)}
          class="rounded-xl px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-overlay"
        >
          Cancel
        </button>
        <button
          onclick={selectPath}
          disabled={saving}
          class="rounded-xl bg-accent/12 px-4 py-2 text-sm font-semibold text-accent shadow-[inset_0_0_0_1px_rgba(0,111,255,0.2)] transition-colors hover:bg-accent/20 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Select"}
        </button>
      </div>
    </div>
  </div>
{/if}
