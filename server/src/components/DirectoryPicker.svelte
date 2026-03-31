<script lang="ts">
  import { getBackendUrl } from "../lib/api";
  import toast from "svelte-5-french-toast";
  import { t } from "../i18n";
  import Icon from "./Icon.svelte";
  import folderIcon from "../icons/folder.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import chevronLeftIcon from "../icons/chevron-left.svg?raw";

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

  let dialogEl: HTMLDivElement | undefined = $state();
  let previousFocus: HTMLElement | null = null;

  function openBrowser() {
    previousFocus = document.activeElement as HTMLElement;
    open = true;
    loadDirectories(current);
    // Focus the dialog after it renders
    requestAnimationFrame(() => dialogEl?.focus());
  }

  function closeDialog() {
    open = false;
    previousFocus?.focus();
  }

  function trapFocus(e: KeyboardEvent) {
    if (e.key === "Escape") { closeDialog(); return; }
    if (e.key !== "Tab" || !dialogEl) return;

    const focusable = dialogEl.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
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
      toast.success(t("toast.saveLocationUpdated"));
    } catch {
      toast.error(t("toast.saveLocationFailed"));
    } finally {
      saving = false;
    }
  }
</script>

<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <Icon icon={folderIcon} class="h-3.5 w-3.5 text-accent" stroke={2.5} />
    </div>
    <label class="text-sm font-semibold text-text-primary">{t("label.videoSaveLocation")}</label>
  </div>
  <div class="mt-3 flex items-center gap-3">
    <code class="flex-1 min-w-0 truncate rounded-xl border border-border-default bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-secondary" title={current}>
      {current}
    </code>
    <button
      onclick={openBrowser}
      class="shrink-0 rounded-xl bg-accent/12 px-4 py-2 text-sm font-semibold text-accent shadow-[inset_0_0_0_1px_rgba(0,111,255,0.2)] transition-colors hover:bg-accent/20"
    >
      {t("btn.browse")}
    </button>
  </div>
</div>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    bind:this={dialogEl}
    class="animate-overlay fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label={t("dialog.selectDirectory")}
    tabindex="-1"
    onkeydown={trapFocus}
  >
    <div class="animate-dialog mx-4 w-full max-w-md overflow-hidden rounded-2xl border border-border-subtle bg-surface-raised shadow-[var(--shadow-lg)]">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-border-subtle px-5 py-3.5">
        <h3 class="text-sm font-semibold text-text-primary">{t("dialog.selectDirectory")}</h3>
        <button
          onclick={closeDialog}
          class="flex h-7 w-7 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
          aria-label={t("btn.close")}
        >
          <Icon icon={xIcon} class="h-4 w-4" />
        </button>
      </div>

      <!-- Current path -->
      <div class="border-b border-border-subtle bg-surface-overlay/50 px-5 py-2 overflow-hidden">
        <code class="block truncate text-[0.6875rem] font-medium text-text-muted" title={browsePath}>{browsePath}</code>
      </div>

      <!-- Directory list -->
      <div class="max-h-64 overflow-y-auto p-2">
        {#if loading}
          <p class="px-3 py-6 text-center text-sm text-text-muted">{t("status.loading")}</p>
        {:else if dirError}
          <div class="px-3 py-6 text-center">
            <p class="text-sm text-status-critical">{t("error.directories")}</p>
            <button onclick={() => loadDirectories(browsePath)} class="mt-2 text-[0.8125rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
          </div>
        {:else}
          <button
            onclick={goUp}
            disabled={loading}
            aria-label="Go to parent directory"
            class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-surface-overlay disabled:opacity-50"
          >
            <Icon icon={chevronLeftIcon} class="h-4 w-4 shrink-0" />
            ..
          </button>
          {#each directories as dir (dir.path)}
            <button
              onclick={() => navigateTo(dir)}
              disabled={loading}
              class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-text-primary transition-colors hover:bg-surface-overlay disabled:opacity-50"
            >
              <Icon icon={folderIcon} class="h-4 w-4 shrink-0 text-text-muted" />
              <span class="truncate">{dir.name}</span>
            </button>
          {/each}
          {#if directories.length === 0}
            <p class="px-3 py-6 text-center text-sm text-text-muted">{t("empty.noSubdirectories")}</p>
          {/if}
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-3 border-t border-border-subtle px-5 py-3.5">
        <button
          onclick={closeDialog}
          class="rounded-xl px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-overlay"
        >
          {t("btn.cancel")}
        </button>
        <button
          onclick={selectPath}
          disabled={saving}
          class="rounded-xl bg-accent/12 px-4 py-2 text-sm font-semibold text-accent shadow-[inset_0_0_0_1px_rgba(0,111,255,0.2)] transition-colors hover:bg-accent/20 disabled:opacity-50"
        >
          {saving ? t("btn.saving") : t("btn.select")}
        </button>
      </div>
    </div>
  </div>
{/if}
