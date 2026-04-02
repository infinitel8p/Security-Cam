<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { apiFetch } from "../lib/fetch";
  import { sseClient } from "../lib/sse";
  import { initLocale, t } from "../i18n";

  let online = $state(false);
  let checked = $state(false);
  let unsubState: (() => void) | null = null;

  async function check() {
    try {
      const res = await apiFetch(`${getBackendUrl()}/recording_status`, {
        signal: AbortSignal.timeout(5000),
      });
      online = res.ok;
    } catch {
      online = false;
    }
    checked = true;
  }

  onMount(() => {
    initLocale();
    check();

    const sse = sseClient();
    unsubState = sse.onStateChange((state) => {
      online = state.connected;
      checked = true;
    });
  });

  onDestroy(() => {
    unsubState?.();
  });
</script>

{#if checked}
  <div class="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface-overlay px-2.5 py-1.5 transition-colors duration-300">
    <span
      class="h-1.5 w-1.5 rounded-full transition-all duration-500
        {online
          ? 'bg-status-ok shadow-[0_0_6px_rgba(52,217,172,0.5)]'
          : 'bg-status-critical animate-pulse'}"
    ></span>
    <span class="text-[0.6875rem] font-medium transition-colors duration-300 {online ? 'text-text-secondary' : 'text-status-critical'}">
      {online ? t("status.backendOnline") : t("status.backendOffline")}
    </span>
  </div>
{:else}
  <div class="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface-overlay px-2.5 py-1.5">
    <span class="h-1.5 w-1.5 rounded-full bg-text-muted/30"></span>
    <span class="text-[0.6875rem] font-medium text-text-muted">…</span>
  </div>
{/if}
